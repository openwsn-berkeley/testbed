import paho.mqtt.client as mqtt
import threading
import time
import json
import requests
import socket
import traceback
import subprocess
import datetime
import serial
import os
import re

#============================ defines =========================================

DEVICETYPE_BOX     = 'box'
DEVICETYPE_MOTE    = 'mote'
DEVICETYPE_ALL     = [
    DEVICETYPE_BOX,
    DEVICETYPE_MOTE
]

BROKER_ADDRESS     = "argus.paris.inria.fr"
OTBOX_VERSION      = "0.0.2"
MOTE_USB_DEVICES   = [ # FIXME: make discovery dynamic
    '/dev/ttyUSB1',
    '/dev/ttyUSB3',
    '/dev/ttyUSB5',
    '/dev/ttyUSB7',
]

#============================ classes =========================================

class OtBox(object):

    HEARTBEAT_PERIOD              = 10
    PREFIX_CMD_HANDLER_NAME       = '_mqtt_handler_'
    OTBUX_SWTORUN_FILENAME        = 'otswtoload.json'
    PREFIX_USB_PORTS              = '/dev/ttyUSB'
    FIRMWARE_EUI64_RETRIEVAL      = '{0}{1}'.format(os.getcwd(),'/bootloaders/01bsp_eui64_prog.ihex')
    FIRMWARE_TEMP                 = 'firmware_mote.ihex'

    def __init__(self):

        # store params

        # local variables
        self.OTBOX_ID                       = socket.gethostname()
        self.mqttopic_testbed_prefix        = 'opentestbed/deviceType/'
        self.mqtttopic_box_prefix           = 'opentestbed/deviceType/box/deviceId/{0}'.format(self.OTBOX_ID)
        self.mqtttopic_box_cmd_prefix       = '{0}/cmd'.format(self.mqtttopic_box_prefix)
        self.mqtttopic_box_notif_prefix     = '{0}/notif'.format(self.mqtttopic_box_prefix)
        self.mqtttopic_mote_prefix          = 'opentestbed/deviceType/mote/deviceId/'
        self.mqttconnected                  = False
        self.start_time                     = time.time()
        self.motesinfo                      = [
            {
                'serialport': i,
            } for i in MOTE_USB_DEVICES
        ]

        # connect to MQTT
        self.mqttclient                = mqtt.Client(self.OTBOX_ID)
        self.mqttclient.on_connect     = self._on_mqtt_connect
        self.mqttclient.on_message     = self._on_mqtt_message
        self.mqttclient.connect(BROKER_ADDRESS)
        self.mqttthread                = threading.Thread(
            name                       = 'mqtt_loop_thread',
            target                     = self.mqttclient.loop_forever
        )
        self.mqttthread.start()

    #======================== public ==========================================

    #======================== private =========================================

    #=== top-level MQTT dispatching

    def _on_mqtt_connect(self, client, userdata, flags, rc):

        # remember I'm now connected
        self.mqttconnected   = True

        # subscribe to box commands
        client.subscribe('{0}/#'.format(self.mqtttopic_box_cmd_prefix))
        client.subscribe('opentestbed/deviceType/box/deviceId/all/cmd/#')

        # run the status command
        self._excecute_commands('{0}/{1}'.format(self.mqtttopic_box_cmd_prefix, 'discovermotes'), '{"token": 0}')

        # start heartbeat thread
        self.heartbeatthread = threading.Thread(
            name    = 'heartbeat_thread',
            target  = self._heartbeatthread_func,
        )
        self.heartbeatthread.start()

    def _on_mqtt_message(self, client, userdata, message):

        # call the handler
        self._excecute_commands(message.topic, message.payload)

    def _excecute_commands(self, topic, payload):
        # parse the topic to extract deviceType, deviceId and cmd ([0-9\-]+)
        try:
            m = re.search('opentestbed/deviceType/([a-z]+)/deviceId/([\w,\-]+)/cmd/([a-z]+)', topic)
            deviceType  = m.group(1)
            deviceId    = m.group(2)
            cmd         = m.group(3)

            # verify params
            assert deviceType in DEVICETYPE_ALL
            if deviceId=='all':
                if deviceType == DEVICETYPE_MOTE:
                    commands_handlers    = []
                    for e in self.motesinfo:
                        if 'EUI64' in e:
                            commands_handlers     += [threading.Thread(
                                                            name   = '{0}_command_handler'.format(e['EUI64']),
                                                            target = self._excecute_command_safely,
                                                            args   = (deviceType, e['EUI64'], payload, cmd))
                                                        ]
                    for handler in commands_handlers:
                        handler.start()
                    for handler in commands_handlers:
                        handler.join()
                else:
                    self._excecute_command_safely(deviceType, self.OTBOX_ID , payload, cmd)
            else:
                self._excecute_command_safely(deviceType, deviceId, payload, cmd)
        except:
            pass

    def _excecute_command_safely(self, deviceType, deviceId, payload, cmd):
        '''
        Executes the handler of a command in a try/except environment so exception doesn't crash server.
        '''
        returnVal       = {}
        try:
            # find the handler
            cmd_handler = getattr(self, '{0}{1}'.format(self.PREFIX_CMD_HANDLER_NAME, cmd))

            # call the handler
            returnVal['returnVal'] =  cmd_handler(deviceType, deviceId, payload)

        except Exception as err:
            returnVal = {
                'success':     False,
                'exception':   str(type(err)),
                'traceback':   traceback.format_exc(),
            }
        else:
            returnVal['success']  = True
        finally:
            try:
                returnVal['token']    = json.loads(payload)['token']
            except:
                pass

            self.mqttclient.publish(
                topic   = '{0}{1}/deviceId/{2}/resp/{3}'.format(self.mqttopic_testbed_prefix,deviceType,deviceId,cmd),
                payload = json.dumps(returnVal),
            )

    #=== command handlers

    # box

    def _mqtt_handler_echo(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/box/deviceId/box1/cmd/echo
        '''
        assert deviceType==DEVICETYPE_BOX

        return json.loads(payload)

    def _mqtt_handler_status(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/box/deviceId/box1/cmd/status
        '''
        assert deviceType==DEVICETYPE_BOX

        returnVal       = {
            'software_version':   OTBOX_VERSION,
            'currenttime':        time.ctime(),
            'starttime':          time.ctime(self.start_time),
            'uptime':             '{0}'.format(datetime.timedelta(seconds=(time.time()-self.start_time))),
            'motes':              self.motesinfo,
        }

        with file(self.OTBUX_SWTORUN_FILENAME,'r') as f:
            update_info = f.read()
        returnVal['last_changesoftware_succesful']    = json.loads(update_info)['last_changesoftware_succesful']
        returnVal['threads_name']       = []
        for t in threading.enumerate():
            returnVal['threads_name'].append(t.getName())

        return returnVal

    def _mqtt_handler_discovermotes(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/box/deviceId/box1/cmd/discovermotes
        '''
        assert deviceType==DEVICETYPE_BOX

        serialports = [e['serialport'] for e in self.motesinfo]

        # bootload EUI64 retrieval firmware on all motes
        bootload_successes = self._bootload_motes(
            serialports           = serialports,
            firmware_file         = self.FIRMWARE_EUI64_RETRIEVAL,
        )
        for (idx,e) in enumerate(self.motesinfo):
            e['firmware_description'] = 'FIRMWARE_EUI64_RETRIEVAL'
            e['bootload_success']     = bootload_successes[idx]

        # get EUI64 from serials ports for motes with bootload_success = True
        for e in self.motesinfo:
            if e['bootload_success']==True:
                ser     = serial.Serial(e['serialport'],baudrate=115200)
                while True:
                    line  = ser.readline()
                    if len(line.split("-")) == 8 and len(line) == 25:
                        e['EUI64'] = line[:len(line)-2]
                        break

        # subscribe to the topics of each mote
        for e in self.motesinfo:
            if 'EUI64' in e:
                self.mqttclient.subscribe('{0}{1}/cmd/#'.format(self.mqtttopic_mote_prefix, e['EUI64']))

        self.mqttclient.subscribe('{0}{1}/cmd/#'.format(self.mqtttopic_mote_prefix, 'all'))

        return {
            'motes': self.motesinfo
        }

    def _mqtt_handler_changesoftware(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/box/deviceId/box1/cmd/changesoftware
        '''
        assert deviceType==DEVICETYPE_BOX

        # remember the URL to run
        with file(self.OTBUX_SWTORUN_FILENAME,'w') as f:
            f.write(payload)

        # reboot the computer this program runs on
        subprocess.call(["sudo","reboot"])

        return {}

    def _mqtt_handler_picturetoscreen(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/box/deviceId/box1/cmd/picturetoscreen
        '''
        assert deviceType==DEVICETYPE_BOX

        raise NotImplementedError()

    def _mqtt_handler_colortoscreen(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/box/deviceId/box1/cmd/colortoscreen
        '''
        assert deviceType==DEVICETYPE_BOX

        raise NotImplementedError()

    # motes

    def _mqtt_handler_program(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/program
        '''
        assert deviceType==DEVICETYPE_MOTE
        assert deviceId!='all'

        payload    = json.loads(payload) # shorthand
        mote       = self._eui64_to_moteinfoelem(deviceId)

        # store the firmware to load into a temporary file
        with open(self.FIRMWARE_TEMP,'w') as f:

            # download file from url if present
            if 'url' in payload:
                file   = requests.get(payload['url'], allow_redirects=True)
                f.write(file.content)

            # export hex file received if present
            if 'hex' in payload:
                f.write(payload['hex'])

        # bootload the mote
        bootload_success = self._bootload_motes(
            serialports      = [mote['serialport']],
            firmware_file    = self.FIRMWARE_TEMP,
        )
        assert len(bootload_success)==1

        # record success of bootload process
        mote['bootload_success']     = bootload_success[0]
        mote['firmware_description'] = payload['description']

    def _mqtt_handler_tomoteserialbytes(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/tomoteserialbytes
        '''
        assert deviceType==DEVICETYPE_MOTE

        raise NotImplementedError()

    def _mqtt_handler_reset(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/reset
        '''
        assert deviceType==DEVICETYPE_MOTE

        raise NotImplementedError()

    def _mqtt_handler_disable(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/disable
        '''
        assert deviceType==DEVICETYPE_MOTE

        payload    = json.loads(payload) # shorthand
        mote       = self._eui64_to_moteinfoelem(deviceId)

        bootload_success = self._bootload_motes(
            serialports      = [mote['serialport']],
            firmware_file    = self.FIRMWARE_EUI64_RETRIEVAL,
        )
        mote['bootload_success']     = bootload_success[0]
        mote['firmware_description'] = 'EUI64'

    #=== heartbeat

    def _heartbeatthread_func(self):

        while True:
            # wait a bit
            time.sleep(self.HEARTBEAT_PERIOD)
            # publish a heartbeat message
            self.mqttclient.publish(
                topic   = '{0}/heartbeat'.format(self.mqtttopic_box_notif_prefix),
                payload = json.dumps({'software_version': OTBOX_VERSION}),
            )

    #=== helpers

    # bootload

    def _bootload_motes(self, serialports, firmware_file):
        '''
        bootloads firmware_file onto multiple motes in parallel
        '''

        # start bootloading each mote
        ongoing_bootloads = []
        for serialport in serialports:
            ongoing_bootloads +=[
                subprocess.Popen(['python', 'bootloaders/cc2538-bsl.py', '-e', '--bootloader-invert-lines', '-w', '-b', '400000', '-p', serialport, firmware_file])
            ]

        returnVal = []
        for ongoing_bootload in ongoing_bootloads:
            # wait for this bootload process to finish
            ongoing_bootload.wait()

            # record whether bootload worked or not
            returnVal += [ongoing_bootload.returncode== 0]

        return returnVal

    # misc

    def _eui64_to_moteinfoelem(self, eui64):
        returnVal = None
        for m in self.motesinfo:
            if m['EUI64']==eui64:
                assert returnVal==None
                returnVal = m
                break
        assert returnVal!=None
        return returnVal

#============================ main ============================================

if __name__ == '__main__':
    otbox = OtBox()
