import paho.mqtt.client as mqtt
import threading
import time
import json
import requests
import socket
import traceback
import subprocess
import datetime
import cc2538_bsl
import serial
import os

#============================ defines =========================================

BROKER_ADDRESS     = "argus.paris.inria.fr"
OTBOX_VERSION      = "0.0.1"
ACTIVE_PORTS       = [1, 3, 5, 7]

#============================ classes =========================================

class OtBox(object):

    HEARTBEAT_PERIOD              = 1
    PREFIX_CMD_HANDLER_NAME       = '_mqtt_handler_'
    OTBUX_SWTORUN_FILENAME        = 'otswtoload.txt'
    PREFIX_USB_PORTS              = '/dev/ttyUSB'
    PATH_TO_FILE                  = os.path.dirname(__file__)
    DISCOVER_MOTES_IMAGE          = '{0}{1}'.format(PATH_TO_FILE,'/bootloaders/01bsp_eui64_prog.ihex')
    FIRMWARE_IMAGE                = 'firmware_mote.ihex'

    def __init__(self):

        # store params

        # local variables
        self.OTBOX_ID                  = socket.gethostname()
        self.mqtttopic_box_cmd_prefix  = 'opentestbed/deviceType/box/device/{0}/cmd'.format(self.OTBOX_ID)
        self.mqtttopic_mote_prefix     = 'opentestbed/deviceType/mote/device/'
        self.mqttconnected             = False
        self.start_time                = time.time()
        self.motes_usb_ports           = ['{0}{1}'.format(self.PREFIX_USB_PORTS,port) for port in ACTIVE_PORTS]
        self.motes                     = [dict() for x in range(0,len(ACTIVE_PORTS))]

        # connect to MQTT
        self.mqttclient                = mqtt.Client(self.OTBOX_ID)
        self.mqttclient.on_connect     = self._on_mqtt_connect
        self.mqttclient.on_message     = self._on_mqtt_message
        self.mqttclient.connect(BROKER_ADDRESS)
        self.mqttthread                = threading.Thread(
            target                     = self.mqttclient.loop_forever
        )
        self.mqttthread.start()

    #======================== public ==========================================

    #======================== private =========================================

    # top-level MQTT dispatching

    def _on_mqtt_connect(self, client, userdata, flags, rc):

        # remember I'm now connected
        self.mqttconnected   = True
        # subscribe to commands
        client.subscribe('{0}/#'.format(self.mqtttopic_box_cmd_prefix))

        # say if change software and start up process were right
        topic_status    = '{0}/{1}'.format(self.mqtttopic_box_cmd_prefix, 'status')
        self._excecute_command(client, '{"token": "startup"}', topic_status, self._mqtt_handler_status)

        # start heartbeat
        self.heartbeatthread = threading.Thread(
            target  = self._heartbeatthread_func,
        )
        self.heartbeatthread.start()

    def _on_mqtt_message(self, client, userdata, message):
        # find the handler
        cmd_handler     = getattr(self, '{0}{1}'.format(self.PREFIX_CMD_HANDLER_NAME, message.topic.split('/')[-1]))
        # call the handler
        self._excecute_command(client, message.payload, message.topic, cmd_handler)

    def _excecute_command(self, client, payload, topic, methode):
        returnVal       = dict()
        try:
            returnVal   = methode(client, payload, topic)
        except Exception as err:
            returnVal = {
                'success':     False,
                'exception':   str(type(err)),
                'traceback':   traceback.format_exc(),
            }
        else:
            returnVal['success']  = True
        finally:
            returnVal['token']    = json.loads(payload)['token']
            self.mqttclient.publish(
                topic   = topic.replace('cmd', 'resp'),
                payload = json.dumps(returnVal),
            )

    def _get_change_software_info(self):
        #Open file write by otbooload.sh and extract token and success
        with file(self.OTBUX_SWTORUN_FILENAME,'r') as f:
            line        = f.readline()
            file_info   = []
            while line:
                line    = f.readline()
                file_info.append(line[:-1])
        return file_info

    def _flash_motes(self, ports_to_flash, image_to_flash, motes_information, firmware_name):
        image_loader    = []
        # create one thread to flash each mote, the result is stored in motes_infomation
        for port, result in zip(ports_to_flash, motes_information):
            image_loader.append(threading.Thread(
                target  = cc2538_bsl.main,
                args    =(port, 400000, 0, None, 0,1, 1, 0, 0, 0x80000, '', 0, False, True, 0, image_to_flash, result,))
            )
            result['firmware']    = firmware_name
        for loader in image_loader:
            loader.start()
        for loader in image_loader:
            loader.join()

    def _get_mote_index(self, topic):
        for mote in self.motes:
            if mote['EUI64'] == topic.split('/')[4]:
                return self.motes.index(mote)

    def _find_flash_motes(self, topic, firmware_file, firmware_name):
        # see if the comand is for all the motes
        if topic.split('/')[4] == 'all':
            self._flash_motes(self.motes_usb_ports, firmware_file, self.motes, firmware_name)
        else:
            # find the mote with the EUI64 indicated by the topic
            mote_index = self._get_mote_index(topic)
            self._flash_motes([self.motes[mote_index]['serialport'],], firmware_file, [self.motes[mote_index],],firmware_name)

    # command handlers

    def _mqtt_handler_echo(self, client, payload,topic):
        return {}

    def _mqtt_handler_changesoftware(self, client, payload, topic):
        # remember the URL to run
        with file(self.OTBUX_SWTORUN_FILENAME,'w') as f:
            f.write('{0}\n'.format(json.loads(payload)['url']))
            f.write('{0}\n'.format(json.loads(payload)['token']))

        # reboot the computer this program runs on
        subprocess.call(["sudo","reboot"])

    def _mqtt_handler_status(self, client, payload, topic):
        date  = time.gmtime()
        update_info     = self._get_change_software_info()
        data  = {
            'software_version':   OTBOX_VERSION,
            'currenttime':   time.ctime(),
            'starttime':     time.ctime(self.start_time),
            'uptime':   '{0}'.format(datetime.timedelta(seconds=(time.time()-self.start_time))),
            'motes':    self.motes,
        }
        if json.loads(payload)['token'] == 'startup':
            data['last_update_status'] = update_info[1]
            data['last_update_token']  = update_info[0]
            data['motes']    = self._mqtt_handler_discovermotes(client, payload, topic)['motes']
        return data

    def _mqtt_handler_discovermotes(self, client, payload, topic):
        # reset motes information and flash image to get EUI64
        self.motes = [dict() for x in range(0,len(ACTIVE_PORTS))]
        self._flash_motes(self.motes_usb_ports, self.DISCOVER_MOTES_IMAGE, self.motes, 'EUI64')

        # get mac address from serials ports for motes with flashing_success = True
        for mote_port, mote in zip(self.motes_usb_ports, self.motes):
            mote['serialport']    = mote_port
            if mote['flashing_success'] == True :
                ser     = serial.Serial(port = mote_port,baudrate=115200)
                while True:
                    reading  = ser.readline()
                    if len(reading.split("-")) == 8 and len(reading) == 25:
                        mote['EUI64'] = reading[:len(reading)-2]
                        break

        # subscribe to the topics of each mote
        for mote in self.motes :
            if 'EUI64' in mote.keys():
                client.subscribe('{0}{1}/cmd/#'.format(self.mqtttopic_mote_prefix, mote['EUI64']))
        # flash motes with the last firmware version
        # TO_DO
        return {
            'motes': self.motes
        }

    def _mqtt_handler_displayonscreen(self, client, payload, topic):
        raise NotImplementedError()

    # command handlers for motes

    def _mqtt_handler_disable(self, client, payload, topic):
        self._find_flash_motes(topic, self.DISCOVER_MOTES_IMAGE, 'EUI64')
        return {}

    def _mqtt_handler_program(self, client, payload, topic):
        message    = json.loads(payload)
        with file(self.FIRMWARE_IMAGE,'w') as f:
            # download file from url if present
            if 'url' in message.keys():
                file   = requests.get(message['url'], allow_redirects=True)
                f.write(file.content)
            # export hex file received if present
            if 'hex' in message.keys():
                f.write(message['hex'])

        # find the mote and program
        self._find_flash_motes(topic, self.FIRMWARE_IMAGE, message['description'])


    def _mqtt_handler_reset(self, client, payload, topic):
        raise NotImplementedError()

    def _mqtt_handler_txserialframe(self, client, payload, topic):
        raise NotImplementedError()

    # notifications

    def _heartbeatthread_func(self):
        while True:
            # wait a bit
            time.sleep(self.HEARTBEAT_PERIOD)

            # publish a heartbeat message
            self.mqttclient.publish(
                topic   = '/poipoi/poi',
                payload = "raspberry",
            )

#============================ main ============================================

if __name__ == '__main__':
    otbox = OtBox()
