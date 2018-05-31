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

#============================ defines =========================================

BROKER_ADDRESS = "argus.paris.inria.fr"
OTBOX_VERSION = "0.0.1"
ACTIVE_PORTS  = [1, 3, 5, 7]

#============================ classes =========================================

class OtBox(object):

    '''
    version       = 1.0
    name          = "Opentestbed"

    otbox_cmd     = ["changesoftware","status","discovermotes","displayonscreen"]
    otmot_cmd     = ["reset","disable","program","tomoteserialbytes"]
    mac_addr      = [None]*4
    '''
    HEARTBEAT_PERIOD         = 1
    PREFIX_CMD_HANDLER_NAME  = '_mqtt_handler_'
    PREFIX_CMD_HANDLER_NAME_MOTE  = '_mqtt_handler_mote_'
    OTBUX_SWTORUN_FILENAME   = 'otswtoload.txt'
    PREFIX_USB_PORTS    = '/dev/ttyUSB'
    DISCOVER_MOTES_IMAGE     = '01bsp_eui64_prog.ihex'

    def __init__(self):

        # store params

        # local variables
        self.OTBOX_ID                  = socket.gethostname()
        self.mqtttopic_box_cmd_prefix  = 'opentestbed/deviceType/box/device/{0}/cmd'.format(self.OTBOX_ID)
        self.mqtttopic_box_resp_prefix = 'opentestbed/deviceType/box/device/{0}/resp'.format(self.OTBOX_ID)
        self.mqtttopic_mote_prefix     = 'opentestbed/deviceType/mote/device/'
        self.mqttconnected             = False
        self.start_time = time.time()
        self.motes_usb_ports = ['{0}{1}'.format(self.PREFIX_USB_PORTS,port) for port in ACTIVE_PORTS]
        self.motes = [dict() for x in range(0,len(ACTIVE_PORTS))]

        # connect to MQTT
        self.mqttclient = mqtt.Client(self.OTBOX_ID)
        self.mqttclient.on_connect = self._on_mqtt_connect
        self.mqttclient.on_message = self._on_mqtt_message
        self.mqttclient.connect(BROKER_ADDRESS)
        self.mqttthread = threading.Thread(
            target      = self.mqttclient.loop_forever
        )
        self.mqttthread.start()

    #======================== public ==========================================

    #======================== private =========================================

    # top-level MQTT dispatching

    def _on_mqtt_connect(self, client, userdata, flags, rc):

        # remember I'm now connected
        self.mqttconnected   = True
        returnVal            = dict()

        # subscribe to commands
        for cmdname in self._get_cmd_handler_names():
            client.subscribe('{0}/{1}'.format(self.mqtttopic_box_cmd_prefix,cmdname))

        # say if change software and start up process were right
        try:
            returnVal   = self._mqtt_handler_status(self.mqttclient, 'startup', ' ')
        except Exception as err:
            returnVal   = {
                'success':     False,
                'exception':   str(type(err)),
                'traceback':   traceback.format_exc(),
            }
        else:
            returnVal['success']  = True
        finally:
            self.mqttclient.publish(
                topic   = '{0}/{1}'.format(self.mqtttopic_box_resp_prefix,'status'),
                payload = json.dumps(returnVal),
            )

        # start heartbeat
        self.heartbeatthread = threading.Thread(
            target = self._heartbeatthread_func,
        )
        self.heartbeatthread.start()

    def _get_cmd_handler_names(self):
        return [
            method_name[len(self.PREFIX_CMD_HANDLER_NAME):]
                for method_name in dir(self)
                if (
                    callable(getattr(self, method_name))
                    and
                    method_name.startswith(self.PREFIX_CMD_HANDLER_NAME)
                )
        ]

    def _get_cmd_handler_names_mote(self):
        return [
            method_name[len(self.PREFIX_CMD_HANDLER_NAME_MOTE):]
                for method_name in dir(self)
                if (
                    callable(getattr(self, method_name))
                    and
                    method_name.startswith(self.PREFIX_CMD_HANDLER_NAME_MOTE)
                )
        ]

    def _on_mqtt_message(self, client, userdata, message):

        # find the handler
        list_topic      = message.topic.split('/')
        cmd_name        = list_topic[-1]
        if list_topic[2] == 'mote':
            cmd_handler     = getattr(self, '{0}{1}'.format(self.PREFIX_CMD_HANDLER_NAME_MOTE,cmd_name))
        else:
            cmd_handler     = getattr(self, '{0}{1}'.format(self.PREFIX_CMD_HANDLER_NAME,cmd_name))
        returnVal       = dict()
        # call the handler
        try:
            returnVal   = cmd_handler(client, message.payload, message.topic)
        except Exception as err:
            returnVal = {
                'success':     False,
                'exception':   str(type(err)),
                'traceback':   traceback.format_exc(),
            }
        else:
            returnVal['success'] = True
        finally:
            returnVal['token'] = json.loads(message.payload)['token']
            list_topic[5]    = 'resp'
            self.mqttclient.publish(
                topic   = '/'.join(list_topic),
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

    def _flash_motes(self, ports_to_flash, image_to_flash, motes_information):
        image_loader    = []
        # create one thread to flash each mote, the result is stored in motes_infomation
        for port, result in zip(ports_to_flash, motes_information):
            image_loader.append(threading.Thread(
                target  = cc2538_bsl.main,
                args    =(port, 400000, 0, None, 0,1, 1, 0, 0, 0x80000, '', 0, False, True, 0, image_to_flash, result,))
            )
        for loader in image_loader:
            loader.start()
        for loader in image_loader:
            loader.join()

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
            'software_version': OTBOX_VERSION,
            'currenttime': time.ctime(),
            'starttime': time.ctime(self.start_time),
            'uptime': '{0}'.format(datetime.timedelta(seconds=(time.time()-self.start_time))),
            'motes': self.motes,
        }
        if payload == 'startup':
            data['last_update_status'] = update_info[1]
            data['last_update_token']  = update_info[0]
            data['motes']    = self._mqtt_handler_discovermotes(client, payload, topic)['motes']
        return data

    def _mqtt_handler_discovermotes(self, client, payload, topic):
        # reset motes information and flash image to get mac_address
        self.motes = [dict() for x in range(0,len(ACTIVE_PORTS))]
        self._flash_motes(self.motes_usb_ports, self.DISCOVER_MOTES_IMAGE, self.motes)

        # get mac address from serials ports for motes with flashing_success = True
        for mote_port, mote in zip(self.motes_usb_ports, self.motes):
            mote['serialport']    = mote_port
            if mote['flashing_success'] == True :
                ser     = serial.Serial(port = mote_port,baudrate=115200)
                while True:
                    reading  = ser.readline()
                    if len(reading.split("-")) == 8 and len(reading) == 25:
                        mote['mac_address'] = reading[:len(reading)-2]
                        break

        # subscribe to the topics of each mote
        for mote in self.motes :
            if 'mac_address' in mote.keys():
                for cmdname in self._get_cmd_handler_names_mote():
                    client.subscribe('{0}{1}/cmd/{2}'.format(self.mqtttopic_mote_prefix, mote['mac_address'], cmdname))

        # flash motes with the last firmware version
        # TO_DO
        return {
            'motes': self.motes
        }

    def _mqtt_handler_displayonscreen(self, client, payload, topic):
        raise NotImplementedError()

    # command handlers for motes

    def _mqtt_handler_mote_reset(self, client, payload, topic):
        raise NotImplementedError()

    def _mqtt_handler_mote_txserialframe(self, client, payload, topic):
        raise NotImplementedError()

    def _mqtt_handler_mote_disable(self, client, payload, topic):
        v = {
            'hola': 'hi'
        }
        return v

    def _mqtt_handler_mote_program(self, client, payload, topic):
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
