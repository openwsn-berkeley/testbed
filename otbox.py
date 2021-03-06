from abc import abstractmethod

import paho.mqtt.client as mqtt
import threading
import time
import json
import requests
import urllib
import socket
import traceback
import subprocess
import datetime
import serial
import serial.tools.list_ports
import os
import re
import Queue
import base64
import argparse
import logging

try: 
    from PIL import Image
    from PIL import ImageFont
    from PIL import ImageDraw
except ImportError as error:
    print(error.__class__.__name__ + ": " + error.message)

# ============================ defines =========================================

logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        '%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

DEVICETYPE_BOX     = 'box'
DEVICETYPE_MOTE    = 'mote'
DEVICETYPE_ALL     = [
    DEVICETYPE_BOX,
    DEVICETYPE_MOTE
]

OTBOX_VERSION      = "1.2.6"

IMAGE_THREAD_NAME       = 'image_thread'
HEARTBEAT_THREAD_NAME   = 'heartbeat_thread'
#============================ classes =========================================

def _getThreadsName():
    threadsName = []
    for t in threading.enumerate():
        threadsName.append(t.getName())
    return threadsName

class Testbed(object):

    def __init__(self, otbox):
        self._otbox = otbox

    @abstractmethod
    def bootload_mote(self, serialport,firmware_file):
        """Flashes the given firmware file to the mote connected to the given serialport"""
        pass

    def on_mqtt_connect(self):
        pass

class OpenTestbed(Testbed):

    INIT_PICTURE_URL              = 'https://upload.wikimedia.org/wikipedia/commons/7/74/Openwsn_logo.png'

    def __init__(self, otbox):
        super(OpenTestbed,self).__init__(otbox)

        self.baudrate = 115200
        self.mote_usb_devices = [
            '/dev/openmote-b_1',
            '/dev/openmote-b_2',
            '/dev/openmote-b_3',
            '/dev/openmote-b_4',
        ]

        self.firmware_eui64_retrieval = os.path.join(os.path.dirname(__file__), 'bootloaders', 'opentestbed',
                                                     '01bsp_eui64_prog.ihex')
        self.firmware_temp = os.path.join(os.path.dirname(__file__), 'bootloaders', 'opentestbed', 'firmware_mote_{0}.ihex')

    def bootload_mote(self, serialport, firmware_file):
    
        bootloader_backdoor_enabled   = False
        extended_linear_address_found = False
        
        # make sure bootloader backdoor is configured correctly
        with open(firmware_file,'r') as f:
            for line in f:
                
                # looking for data at address 0027FFD4
                # refer to: https://en.wikipedia.org/wiki/Intel_HEX#Record_types
                
                # looking for upper 16bit address 0027
                if len(line)>=15 and line[:15] == ':020000040027D3':
                    extended_linear_address_found = True
                    
                # check the lower 16bit address FFD4
                
                # | 1:3 byte count | 3:7 address | 9:17 32-bit field of the lock bit page (the last byte is backdoor configuration) |
                # 'F6' = 111        1                               0           110
                #        reserved   backdoor and bootloader enable  active low  PA pin used for backdoor enabling (PA6)
                if len(line)>=17 and extended_linear_address_found and line[3:7] == 'FFD4' and int(line[1:3], 16)>4  and line[9:17] == 'FFFFFFF6':
                    bootloader_backdoor_enabled = True
                    break
        
        assert bootloader_backdoor_enabled
        
        return subprocess.Popen(
                ['python', 'bootloaders/cc2538-bsl.py', '-e', '--bootloader-invert-lines', '-w', '-b', '400000',
                 '-p', serialport, firmware_file], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def _display_image(self):
        import pygame
        pygame.init()

        size       = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        black      = 0, 0, 0
        screen     = pygame.display.set_mode(size,pygame.FULLSCREEN)
        while True:
            if self._otbox.change_image_queue.empty()==False:
                picture      = self._otbox.change_image_queue.get()
                image        = pygame.image.fromstring(picture.tobytes(), picture.size, picture.mode)
                imagerect    = image.get_rect()
                screen.fill(black)
                screen.blit(image, (240-picture.size[0]/2,160-picture.size[1]/2))
                pygame.display.flip()
                self._otbox.change_image_queue.task_done()
            time.sleep(0.2)

    def on_mqtt_connect(self):
        # start heartbeat thread
        currentThreads = _getThreadsName()

        if IMAGE_THREAD_NAME not in currentThreads:
            self.image_thread = threading.Thread(
                name=IMAGE_THREAD_NAME,
                target=self._display_image,
            )
            self.image_thread.start()
            self._mqtt_handler_picturetoscreen('box','all',json.dumps({'token': 0, 'url': OpenTestbed.INIT_PICTURE_URL}))

    def _mqtt_handler_picturetoscreen(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/box/deviceId/box1/cmd/picturetoscreen
        '''
        assert deviceType==DEVICETYPE_BOX
        image = Image.open(requests.get(json.loads(payload)['url'], stream=True).raw)
        image.thumbnail((480,320),Image.ANTIALIAS)
        self._otbox.change_image_queue.put(image)
        self._otbox.change_image_queue.join()
        return {}

    def _mqtt_handler_colortoscreen(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/box/deviceId/box1/cmd/colortoscreen
        '''
        assert deviceType==DEVICETYPE_BOX
        payload    = json.loads(payload)
        self._otbox.change_image_queue.put(Image.new('RGB', (480,320), (payload['r'],payload['g'],payload['b'])))
        self._otbox.change_image_queue.join()

    def _mqtt_handler_hostnametoscreen(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/box/deviceId/box1/cmd/hostnametoscreen
        '''
        image_to_display  = Image.new('RGB', (480,320), (255,255,0))
        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 80)
        ImageDraw.Draw(image_to_display).text((0, 0),self._otbox.OTBOX_ID,(0,0,0), font=font)
        self._otbox.change_image_queue.put(image_to_display)
        self._otbox.change_image_queue.join()


class IotLabTestbed(Testbed):

    def __init__(self, otbox):
        super(IotLabTestbed, self).__init__(otbox)

        self.baudrate = 500000
        self.mote_usb_devices = [
            '/dev/ttyUSB1'
        ]

        self.firmware_eui64_retrieval = os.path.join(os.path.dirname(__file__), 'bootloaders', 'iotlab',
                                                     '01bsp_eui64_prog')
        self.firmware_temp = os.path.join(os.path.dirname(__file__), 'bootloaders', 'iotlab', '03oos_openwsn_prog_{0}')

    def bootload_mote(self, serialport, firmware_file):
        return  subprocess.Popen(['flash_a8_m3', firmware_file], stdout=subprocess.PIPE,
                                                       stderr=subprocess.PIPE)

    def on_mqtt_connect(self):
        # in case of IoT-LAB mote discovery is started immediately upon `otbox.py` startup
        payload_status = {
            'token': 123
        }
        self._otbox._mqtt_handler_discovermotes('box', 'all', json.dumps(payload_status))

class WilabTestbed(Testbed):

    def __init__(self, otbox):
        super(WilabTestbed, self).__init__(otbox)

        self.logger = logging.getLogger("WilabTestbed")
        self.baudrate = 115200

        # discover serial ports
        self.mote_usb_devices = sorted(portinfo.device for portinfo in serial.tools.list_ports.comports())

        self.logger.info("Discovered Motes %s", str(self.mote_usb_devices))

        self.firmware_eui64_retrieval = os.path.join(os.path.dirname(__file__), 'bootloaders', 'wilab',
                                                     'eui64-retriever.hex')
        self.firmware_temp = os.path.join(os.path.dirname(__file__), 'bootloaders', 'wilab',
                                          'firmware_{0}.hex')

    def bootload_mote(self, serialport, firmware_file):
        cmd = ['python', 'bootloaders/cc2538-bsl.py', '-e', '-w', '-v', '-b', '460800', '-a', '0x00202000',
               '-p', serialport, firmware_file]
        self.logger.debug("Executing %s", str(cmd))
        return subprocess.Popen(cmd,   stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    def on_mqtt_connect(self):
        # in case of WiLab mote discovery is started immediately upon `otbox.py` startup
        payload_status = {
            'token': 123
        }
        self._otbox._mqtt_handler_discovermotes('box', 'all', json.dumps(payload_status))


AVAILABLE_TESTBEDS = {
    'opentestbed': OpenTestbed,
    'iotlab': IotLabTestbed,
    'wilab': WilabTestbed
}

class OtBox(object):

    HEARTBEAT_PERIOD              = 10
    PREFIX_CMD_HANDLER_NAME       = '_mqtt_handler_'
    OTBOX_SWTORUN_FILENAME        = 'otswtoload.json'
    LOCATION_FILE_NAME            = 'location.txt'
    NEW_SOFTWARE_FILE_NAME        = 'new_software.zip'

    def __init__(self, testbed, broker):
        self.testbed = testbed
        self.broker = broker

        self.logger = logging.getLogger('OtBox')
        self.logger.info("Starting OTBox in testbed '%s' with broker '%s'", self.testbed, self.broker)

        self.tb = AVAILABLE_TESTBEDS[self.testbed](self)

        # local variables
        self.OTBOX_ID = socket.gethostname().split('.')[0]
        self.logger.info("Registering as %s", self.OTBOX_ID)
        self.mqttopic_testbed_prefix        = '{0}/deviceType/'.format(self.testbed)
        self.mqtttopic_box_prefix           = '{0}/deviceType/box/deviceId/{1}'.format(self.testbed, self.OTBOX_ID)
        self.mqtttopic_box_cmd_prefix       = '{0}/cmd'.format(self.mqtttopic_box_prefix)
        self.mqtttopic_box_notif_prefix     = '{0}/notif'.format(self.mqtttopic_box_prefix)
        self.mqtttopic_mote_prefix          = '{0}/deviceType/mote/deviceId/'.format(self.testbed)
        self.mqttconnected                  = False
        self.SerialRxBytePublishers         = {}
        self.SerialportHandlers             = {}
        self.start_time                     = time.time()
        self.change_image_queue             = Queue.Queue()
        self.motesinfo                      = []
        self.serialports_available          = self._discover_serialports_availables()
        try:
            with open('../{0}'.format(OtBox.LOCATION_FILE_NAME), 'r') as f:
                self.location               = f.read()
        except:
            self.location                   = 'not available'

        # connect to MQTT
        self.mqttclient                = mqtt.Client(self.OTBOX_ID)
        self.mqttclient.on_connect     = self._on_mqtt_connect
        self.mqttclient.on_message     = self._on_mqtt_message
        self.mqttclient.connect(self.broker)

        # create serialport handlers and publishers
        for serialport in self.tb.mote_usb_devices:
            self.SerialportHandlers[serialport]       = SerialportHandler(serialport, baudrate=self.tb.baudrate)
            self.SerialRxBytePublishers[serialport]   = SerialRxBytePublisher(
                                    rxqueue           = self.SerialportHandlers[serialport].rxqueue,
                                    serialport        = serialport,
                                    mqttclient        = self.mqttclient,
                                    mqtttopic         = None
            )

        # start mqtt client
        self.mqttthread                = threading.Thread(
            name                       = 'mqtt_loop_thread',
            target                     = self.mqttclient.loop_forever
        )
        self.mqttthread.start()


    #======================== public ==========================================

    #======================== private =========================================

    #=== top-level MQTT dispatching

    def _on_mqtt_connect(self, client, userdata, flags, rc):

        self.logger.info("Connected to MQTT")

        # remember I'm now connected
        self.mqttconnected   = True

        # subscribe to box commands (device-specific and 'all')
        # note that unknown commands will be ignored by _execute_command_safely 
        client.subscribe('{0}/#'.format(self.mqtttopic_box_cmd_prefix))
        client.subscribe('{0}/deviceType/box/deviceId/all/cmd/#'.format(self.testbed))

        # start heartbeat thread
        currentThreads  = _getThreadsName()

        if HEARTBEAT_THREAD_NAME not in currentThreads:
            self.heartbeatthread = threading.Thread(
                name    = HEARTBEAT_THREAD_NAME,
                target  = self._heartbeatthread_func,
            )
            self.heartbeatthread.start()

        self.tb.on_mqtt_connect()


    def _on_mqtt_message(self, client, userdata, message):

        # call the handler
        self._excecute_commands(message.topic, message.payload)

    def _excecute_commands(self, topic, payload):
        # parse the topic to extract deviceType, deviceId and cmd ([0-9\-]+)
        try:
            m = re.search('{0}/deviceType/([a-z]+)/deviceId/([\w,\-]+)/cmd/([a-z]+)'.format(self.testbed), topic)
            if m is None:
                self.logger.debug("Ignoring topic '%s': could not parse", topic)
                return

            deviceType  = m.group(1)
            deviceId    = m.group(2)
            cmd         = m.group(3)

            # verify params
            assert deviceType in DEVICETYPE_ALL
            device_to_comand      = []
            commands_handlers     = []
            if deviceId=='all':
                if deviceType == DEVICETYPE_MOTE:
                     for e in self.motesinfo:
                         if 'EUI64' in e:
                             device_to_comand    += [e['EUI64'],]
                else:
                    device_to_comand   = [self.OTBOX_ID,]
            else:
                device_to_comand      += [deviceId,]

            for d in device_to_comand:
                commands_handlers     += [threading.Thread(
                                name   = '{0}_command_{1}'.format(d, cmd),
                                target = self._excecute_command_safely,
                                args   = (deviceType, d, payload, cmd))
                                            ]
            for handler in commands_handlers:
                handler.start()
        except:
            self.logger.exception("Could not parse command with topic %s", topic)

    def _excecute_command_safely(self, deviceType, deviceId, payload, cmd):
        '''
        Executes the handler of a command in a try/except environment so exception doesn't crash server.
        '''
        self.logger.debug("Executing command %s", cmd)
        returnVal       = {}
        try:
            payload = payload.decode('utf8')
        except:
            self.logger.warning("Could not decode payload")

        try:
            # find the handler
            cmd_handler = getattr(self, '{0}{1}'.format(OtBox.PREFIX_CMD_HANDLER_NAME, cmd), None)

            if cmd_handler is None:
                cmd_handler = getattr(self.tb, '{0}{1}'.format(OtBox.PREFIX_CMD_HANDLER_NAME, cmd), None)

            if cmd_handler is None:
                self.logger.debug("Ignoring unknown command '%s'" % cmd)
                return

            # call the handler
            returnVal['returnVal'] =  cmd_handler(deviceType, deviceId, payload)

        except Exception as err:
            self.logger.exception("Exception while executing %s",cmd)
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
                self.logger.warning("Could not fetch token from payload")
                pass

            self.mqttclient.publish(
                topic   = '{0}{1}/deviceId/{2}/resp/{3}'.format(self.mqttopic_testbed_prefix,deviceType,deviceId,cmd),
                payload = json.dumps(returnVal),
            )

    #=== command handlers

    # box

    def _mqtt_handler_echo(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/box/deviceId/box1/cmd/echo
        '''
        assert deviceType==DEVICETYPE_BOX

        return json.loads(payload)

    def _mqtt_handler_status(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/box/deviceId/box1/cmd/status
        '''
        assert deviceType==DEVICETYPE_BOX

        # Checks if `hostname -I` is a valid command
        try:
            ip_addresses = subprocess.check_output(["hostname", "-I"])
        except subprocess.CalledProcessError:
            ip_addresses = subprocess.check_output(["hostname", "-i"])

        ip_addresses =ip_addresses.decode('utf8').rstrip()

        returnVal       = {
                'software_version':   OTBOX_VERSION,
                'currenttime':        time.ctime(),
                'starttime':          time.ctime(self.start_time),
                'uptime':             '{0}'.format(datetime.timedelta(seconds=(time.time()-self.start_time))),
                'motes':              self.motesinfo,
                'IP_address':         ip_addresses,
                'host_name':          self.OTBOX_ID,
                'location':           self.location,
            }

        try:
            with open(OtBox.OTBOX_SWTORUN_FILENAME, 'r') as f:
                update_info = f.read()
                returnVal['last_changesoftware_succesful'] = json.loads(update_info)['last_changesoftware_succesful']
        except Exception as e:
            self.logger.exception("Could not read %s", OtBox.OTBOX_SWTORUN_FILENAME)

        returnVal['threads_name']       = _getThreadsName()

        self.logger.debug("Returning status '%s'", str(returnVal))

        return returnVal

    def _mqtt_handler_discovermotes(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/box/deviceId/box1/cmd/discovermotes
        '''
        assert deviceType==DEVICETYPE_BOX

        # turn off serial_reader if exist
        for serialport in self.tb.mote_usb_devices:
            self.SerialportHandlers[serialport].disconnectSerialPort()

        # discover serialports available
        self.serialports_available          = self._discover_serialports_availables()

        self.logger.info("Discovered serial ports %s", str(self.serialports_available))

        # bootload EUI64 retrieval firmware on all motes
        bootload_successes = self._bootload_motes(
            serialports           = self.serialports_available,
            firmware_file         = self.tb.firmware_eui64_retrieval,
        )
        for (idx,e) in enumerate(self.motesinfo):
            e['firmware_description'] = 'FIRMWARE_EUI64_RETRIEVAL'
            e['bootload_success']     = bootload_successes[idx]

        # get EUI64 from serials ports for motes with bootload_success = True
        for e in self.motesinfo:
            if e['bootload_success']==True:
                ser     = serial.Serial(e['serialport'],baudrate=self.tb.baudrate)
                while True:
                    line = ser.readline()
                    line = line.strip()
                    if len(line.split("-")) == 8 and len(line) == 23:
                        e['EUI64'] = line
                        self.logger.info("Found EUI64 %s for mote at %s", e['EUI64'], e['serialport'])
                        break
                    else:
                        self.logger.debug("No EUI64 found in '%s'", line)

        for e in self.motesinfo:
            if 'EUI64' in e:
                # subscribe to the topics of each mote
                self.mqttclient.subscribe('{0}{1}/cmd/#'.format(self.mqtttopic_mote_prefix, e['EUI64']))
                # set topic of SerialRxBytePublishers
                self.SerialRxBytePublishers[e['serialport']].mqtttopic    = '{0}{1}/notif/frommoteserialbytes'.format(self.mqtttopic_mote_prefix,e['EUI64'])
                # start reading serial port
                self.SerialportHandlers[e['serialport']].connectSerialPort()


        self.mqttclient.subscribe('{0}{1}/cmd/#'.format(self.mqtttopic_mote_prefix, 'all'))

        return {
            'motes': self.motesinfo
        }

    def _mqtt_handler_changesoftware(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/box/deviceId/box1/cmd/changesoftware
        '''
        assert deviceType==DEVICETYPE_BOX

        r     = requests.get(json.loads(payload)['url'])
        open(OtBox.NEW_SOFTWARE_FILE_NAME, 'wb').write(r.content)
        subprocess.call(['unzip', '-o', OtBox.NEW_SOFTWARE_FILE_NAME])
        subprocess.call('mv opentestbed* new_software', shell=True)
        subprocess.call('cp new_software/install/* ../', shell=True )

        # remember the URL to run
        with open(OtBox.OTBOX_SWTORUN_FILENAME, 'w') as f:
            f.write(payload)

        # reboot the computer this program runs on
        reboot_function_thread    = threading.Thread(
            name                  = 'reboot_thread',
            target                = self._reboot_function
        )
        reboot_function_thread.start()

        return {}


    def _mqtt_handler_changelocation(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/box/deviceId/box1/cmd/changelocation
        '''
        assert deviceType==DEVICETYPE_BOX
        self.location   = json.loads(payload)['location']
        with open('../{0}'.format(OtBox.LOCATION_FILE_NAME), 'w') as f:
            f.write(self.location)

    # motes

    def _mqtt_handler_program(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/program
        '''
        assert deviceType==DEVICETYPE_MOTE
        assert deviceId!='all'

        payload    = json.loads(payload) # shorthand
        mote       = self._eui64_to_moteinfoelem(deviceId)
        
        # disconnect from the serialports
        self.SerialportHandlers[mote['serialport']].disconnectSerialPort()
        time.sleep(2) # wait 2 seconds to release the serial ports
        
        if 'url' in payload and payload['url'].startswith("ftp://"):
            # use urllib to get firmware from ftp server (requests doesn't support for ftp)
            urllib.urlretrieve(payload['url'],self.tb.firmware_temp.format(deviceId))
            urllib.urlcleanup()
        else:
            # store the firmware to load into a temporary file
            with open(self.tb.firmware_temp.format(deviceId), 'wb') as f:
                if 'url' in payload: # download file from url if present
                    file   = requests.get(payload['url'], allow_redirects=True)
                    f.write(file.content)
                elif 'hex' in payload: # export hex file received if present
                    f.write(base64.b64decode(payload['hex']))
                else:
                    assert "The supported keys {0}, {1} are not in the payload. ".format('url','hex')

        # bootload the mote
        bootload_success = self._bootload_motes(
            serialports      = [mote['serialport']],
            firmware_file    = self.tb.firmware_temp.format(deviceId),
        )

        assert len(bootload_success)==1

        # record success of bootload process
        mote['bootload_success']       = bootload_success[0]
        mote['firmware_description']   = payload['description']

        assert mote['bootload_success'] ==True
        self.SerialportHandlers[mote['serialport']].connectSerialPort()
        self.logger.debug('started listening to serial for %s', mote['serialport'])
        return True

    def _mqtt_handler_tomoteserialbytes(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/tomoteserialbytes
        '''
        assert deviceType==DEVICETYPE_MOTE
        payload    = json.loads(payload)
        mote       = self._eui64_to_moteinfoelem(deviceId)
        serialHandler = serial.Serial(mote['serialport'], baudrate=self.tb.baudrate, xonxoff=True)
        serialHandler.write(bytearray(payload['serialbytes']))
        self.SerialportHandlers[mote['serialport']].connectSerialPort()

    def _mqtt_handler_reset(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/reset
        '''
        assert deviceType==DEVICETYPE_MOTE

        mote            = self._eui64_to_moteinfoelem(deviceId)
        self.SerialportHandlers[mote['serialport']].disconnectSerialPort()
        pyserialHandler = serial.Serial(mote['serialport'], baudrate=self.tb.baudrate)
        pyserialHandler.setDTR(False)
        pyserialHandler.setRTS(True)
        time.sleep(0.2)
        pyserialHandler.setDTR(True)
        pyserialHandler.setRTS(False)
        time.sleep(0.2)
        pyserialHandler.setDTR(False)

        ## start serial
        self.SerialportHandlers[mote['serialport']].connectSerialPort()


    def _mqtt_handler_disable(self, deviceType, deviceId, payload):
        '''
        {{TESTBED}}/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/disable
        '''
        assert deviceType==DEVICETYPE_MOTE

        payload    = json.loads(payload) # shorthand
        mote       = self._eui64_to_moteinfoelem(deviceId)
        # off serial
        self.SerialportHandlers[mote['serialport']].disconnectSerialPort()
        bootload_success     = self._bootload_motes(
            serialports      = [mote['serialport']],
            firmware_file    = self.tb.firmware_eui64_retrieval,
        )
        mote['bootload_success']       = bootload_success[0]
        mote['firmware_description']   = 'FIRMWARE_EUI64_RETRIEVAL'
        assert mote['bootload_success']==True

    #=== heartbeat

    def _heartbeatthread_func(self):
        while True:
            # wait a bit
            time.sleep(OtBox.HEARTBEAT_PERIOD)
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
        ongoing_bootloads    = {}
        for serialport in serialports:
        
            # simply the name
            port = serialport.split('/')[-1]
        
            # stop serial reader
            ongoing_bootloads[port] = self.tb.bootload_mote(serialport, firmware_file)

        returnVal = []
        for ongoing_bootload in ongoing_bootloads:
            # wait for this bootload process to finish
            (stdout, stderr) = ongoing_bootloads[ongoing_bootload].communicate()
            
            # record the last output of bootload process
            with open("log_{0}.txt".format(ongoing_bootload),'w') as f:
                f.write("stdout: {0} stderr {1}".format(stdout,stderr))

            # record whether bootload worked or not
            returnVal += [ongoing_bootloads[ongoing_bootload].returncode== 0]

        self.logger.debug("Finished bootload_motes with returnVal %s", str(returnVal))
        return returnVal

    # misc
    def _eui64_to_moteinfoelem(self, eui64):
        returnVal = None
        for m in self.motesinfo:
            if 'EUI64' in m:
                if m['EUI64']==eui64:
                    assert returnVal==None
                    returnVal = m
                    break
        assert returnVal!=None
        return returnVal

    def _reboot_function(self):
        time.sleep(3)
        subprocess.call(["sudo","reboot"])



    def _discover_serialports_availables(self):
        serialports_available     = []
        self.motesinfo            = []

        self.logger.debug("Checking which serial ports are available from list %s", self.tb.mote_usb_devices)
        for serialport in self.tb.mote_usb_devices:
            try:
                ser     = serial.Serial(serialport)
                serialports_available  += [serialport,]
                ser.close()
                self.logger.info("Successfully probed serial port %s", serialport)
            except:
                self.logger.warning("Could not setup connection to %s", serialport)
                pass

        self.motesinfo  = [
            {
                'serialport': i,
            } for i in serialports_available
        ]
        return serialports_available

class SerialRxBytePublisher(threading.Thread):

    PUBLICATION_PERIOD = 1

    def __init__(self,rxqueue,serialport,mqttclient,mqtttopic):

        # store params
        self.rxqueue    = rxqueue
        self.mqttclient = mqttclient
        self.mqtttopic  = mqtttopic

        # local variables
        self.goOn       = True

        # initialize thread
        threading.Thread.__init__(self)
        self.name       = 'SerialRxBytePublisher@{0}'.format(serialport)
        self.logger = logging.getLogger(self.name)
        self.start()

    def run(self):
        while self.goOn:

            # wait
            time.sleep(self.PUBLICATION_PERIOD)
            try:
                # read queue
                buffer_to_send    = []
                while not self.rxqueue.empty():
                    temp_reading  = self.rxqueue.get()
                    for i in temp_reading:
                        buffer_to_send += [ord(i)]
                # publish
                if buffer_to_send:
                    payload = {
                        'serialbytes': buffer_to_send,
                    }
                    self.mqttclient.publish(
                        topic   = self.mqtttopic,
                        payload = json.dumps(payload),
                    )
            except:
                self.logger.exception("Error while writing serial output")

    #======================== public ==========================================

    def close(self):
        self.goOn = False

class SerialportHandler(threading.Thread):
    '''
    Connects to serial port. Puts received serial bytes in queue. Method to send bytes.

    One per mote.
    Can be started/stopped many times (used when reprogramming).
    '''
    def __init__(self, serialport, baudrate):

        # store params
        self.serialport           = serialport
        self.baudrate             = baudrate

        # local variables
        self.rxqueue              = Queue.Queue()
        self.serialHandler        = None
        self.goOn                 = True
        self.pleaseConnect        = False
        self.dataLock             = threading.RLock()

        # initialize thread
        super(SerialportHandler, self).__init__()
        self.name                 = 'SerialportHandler@{0}'.format(self.serialport)
        self.logger = logging.getLogger(self.name)
        self.start()

    def run(self):
        while self.goOn:

            try:

                with self.dataLock:
                    pleaseConnect = self.pleaseConnect

                if pleaseConnect:

                    # open serial port
                    self.serialHandler = serial.Serial(self.serialport, baudrate=self.baudrate)

                    # read byte
                    while True:
                        waitingbytes   = self.serialHandler.inWaiting()
                        if waitingbytes != 0:
                            c = self.serialHandler.read(waitingbytes) # blocking
                            self.rxqueue.put(c)
                            time.sleep(0.1)

            except:
                # mote disconnected, or pyserialHandler closed
                # destroy pyserial instance
                self.serialHandler = None

            # wait
            time.sleep(1)

    #======================== public ==========================================

    def connectSerialPort(self):
        with self.dataLock:
            self.pleaseConnect = True

    def disconnectSerialPort(self):
        with self.dataLock:
            self.pleaseConnect = False
        try:
            self.serialHandler.close()
        except:
            pass

    def close(self):
        self.goOn            = False

    #======================== private =========================================

#============================ main ============================================

if __name__ == '__main__':

    # parse args
    parser = argparse.ArgumentParser()
    parser.add_argument("--testbed", nargs="?", default="opentestbed", choices=['iotlab', 'opentestbed','wilab'])
    parser.add_argument("--broker", nargs="?", default="argus.paris.inria.fr")
    parser.add_argument("-v", "--verbose", help="increase output verbosity",
                        action="count")
    args = parser.parse_args()

    if args.verbose >= 2:
        logger.setLevel(logging.DEBUG)
    elif args.verbose == 1:
        logger.setLevel(logging.INFO)
    else:
        logger.setLevel(logging.WARNING)

    otbox = OtBox(testbed=args.testbed, broker=args.broker)
