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
import Queue
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import pygame
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
    PICTURE_FILENAME              = 'picture'
    INIT_PICTURE_URL              = 'https://upload.wikimedia.org/wikipedia/commons/7/74/Openwsn_logo.png'

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
        self.SerialRxBytePublishers         = {}
        self.SerialportHandlers             = {}
        self.start_time                     = time.time()
        self.change_image_queue             = Queue.Queue()
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

        # create serialport handlers and publishers
        for serialport in MOTE_USB_DEVICES:
            self.SerialportHandlers[serialport]       = SerialportHandler(serialport)
            self.SerialRxBytePublishers[serialport]   = SerialRxBytePublisher(
                                    rxqueue           = self.SerialportHandlers[serialport].rxqueue,
                                    serialport        = serialport,
                                    mqttclient        = self.mqttclient,
                                    mqtttopic         = None
            )
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
        self.image_thread = threading.Thread(
            name    = 'image_thread',
            target  = self._display_image,
        )
        #self.image_thread.start()
        #self._excecute_commands('{0}/{1}'.format(self.mqtttopic_box_cmd_prefix, 'picturetoscreen'), json.dumps({'token': 0, 'url': self.INIT_PICTURE_URL}))


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

        # turn off serial_reader if exist
        for serialport in MOTE_USB_DEVICES:
            self.SerialportHandlers[serialport].disconnectSerialPort()

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

        for e in self.motesinfo:
            if 'EUI64' in e:
                # subscribe to the topics of each mote
                self.mqttclient.subscribe('{0}{1}/cmd/#'.format(self.mqtttopic_mote_prefix, e['EUI64']))
                # set topic of SerialRxBytePublishers
                self.SerialRxBytePublishers[e['serialport']].mqtttopic    = '{0}{1}/notif/fromoteserialbytes'.format(self.mqtttopic_mote_prefix,e['EUI64'])
                # start reading serial port
                self.SerialportHandlers[e['serialport']].connectSerialPort()

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
        reboot_function_thread    = threading.Thread(
            name                  = 'reboot_thread',
            target                = self._reboot_function
        )
        reboot_function_thread.start()

        return {}

    def _mqtt_handler_picturetoscreenn(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/box/deviceId/box1/cmd/picturetoscreen
        '''

        assert deviceType==DEVICETYPE_BOX
        image = Image.open(requests.get(json.loads(payload)['url'], stream=True).raw)
        image.thumbnail((480,320),Image.ANTIALIAS)
        self.change_image_queue.put(image)
        self.change_image_queue.join()
        return {}

    def _mqtt_handler_colortoscreenn(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/box/deviceId/box1/cmd/colortoscreen
        '''
        assert deviceType==DEVICETYPE_BOX
        payload    = json.loads(payload)
        self.change_image_queue.put(Image.new('RGB', (480,320), (payload['r'],payload['g'],payload['b'])))
        self.change_image_queue.join()

    def _mqtt_handler_hostnametoscreenn(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/box/deviceId/box1/cmd/colortoscreen
        '''
        image_to_display  = Image.new('RGB', (480,320), (255,255,0))
        font = ImageFont.truetype("/usr/share/fonts/truetype/freefont/FreeMono.ttf", 80)
        ImageDraw.Draw(image_to_display).text((0, 0),self.OTBOX_ID,(0,0,0), font=font)
        self.change_image_queue.put(image_to_display)
        self.change_image_queue.join()
    # motes

    def _mqtt_handler_program(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/program
        '''
        assert deviceType==DEVICETYPE_MOTE
        assert deviceId!='all'

        payload    = json.loads(payload) # shorthand
        mote       = self._eui64_to_moteinfoelem(deviceId)
        self.SerialportHandlers[mote['serialport']].disconnectSerialPort()
        # store the firmware to load into a temporary file
        with open(self.FIRMWARE_TEMP,'w') as f:
            # download file from url if present
            if 'url' in payload:
                file   = requests.get(payload['url'], allow_redirects=True)
                f.write(file.content)

            # export hex file received if present
            if 'hex' in payload:
                f.write(payload['hex'])
        # turn off serial port reader


        # bootload the mote
        bootload_success = self._bootload_motes(
            serialports      = [mote['serialport']],
            firmware_file    = self.FIRMWARE_TEMP,
        )

        assert len(bootload_success)==1

        # record success of bootload process
        mote['bootload_success']       = bootload_success[0]
        mote['firmware_description']   = payload['description']
        # start serial port reader
        assert mote['bootload_success'] ==True
        self.SerialportHandlers[mote['serialport']].connectSerialPort()
        print 'started'

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
        ## off serial
        mote            = self._eui64_to_moteinfoelem(deviceId)
        pyserialHandler = serial.Serial(mote['serialport'], baudrate=115200)
        pyserialHandler.setDTR(False)
        pyserialHandler.setRTS(True)
        time.sleep(0.2)
        pyserialHandler.setDTR(True)
        pyserialHandler.setRTS(False)
        time.sleep(0.2)
        pyserialHandler.setDTR(False)
        ## start serial
        self.fmoteserial_reader[deviceId].start_reading()

    def _mqtt_handler_disable(self, deviceType, deviceId, payload):
        '''
        opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/disable
        '''
        assert deviceType==DEVICETYPE_MOTE

        payload    = json.loads(payload) # shorthand
        mote       = self._eui64_to_moteinfoelem(deviceId)
        # off serial
        bootload_success     = self._bootload_motes(
            serialports      = [mote['serialport']],
            firmware_file    = self.FIRMWARE_EUI64_RETRIEVAL,
        )
        mote['bootload_success']       = bootload_success[0]
        mote['firmware_description']   = 'FIRMWARE_EUI64_RETRIEVAL'
        assert mote['bootload_success']==True

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
        ongoing_bootloads    = []
        for serialport in serialports:
            # stop serial reader
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

    def _display_image(self):
        pygame.init()
        size       = (pygame.display.Info().current_w, pygame.display.Info().current_h)
        black      = 0, 0, 0
        screen     = pygame.display.set_mode(size,pygame.FULLSCREEN)
        while True:
            if self.change_image_queue.empty()==False:
                picture      = self.change_image_queue.get()
                image        = pygame.image.fromstring(picture.tobytes(), picture.size, picture.mode)
                imagerect    = image.get_rect()
                screen.fill(black)
                screen.blit(image, (240-picture.size[0]/2,160-picture.size[1]/2))
                pygame.display.flip()
                self.change_image_queue.task_done()
            time.sleep(0.2)

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
        self.start()

    def run(self):
        while self.goOn:

            # wait
            time.sleep(self.PUBLICATION_PERIOD)
            try:
                # read queue
                buffer_to_send    = []
                while not self.rxqueue.empty():
                    buffer_to_send += [self.rxqueue.get()]

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
                pass

    #======================== public ==========================================

    def close(self):
        self.goOn = False

class SerialportHandler(threading.Thread):
    '''
    Connects to serial port. Puts received serial bytes in queue. Method to send bytes.

    One per mote.
    Can be started/stopped many times (used when reprogramming).
    '''
    def __init__(self, serialport):

        # store params
        self.serialport           = serialport

        # local variables
        self.rxqueue              = Queue.Queue()
        self.serialHandler        = None
        self.goOn                 = True
        self.pleaseConnect        = False
        self.dataLock             = threading.RLock()

        # initialize thread
        super(SerialportHandler, self).__init__()
        self.name                 = 'SerialportHandler@{0}'.format(self.serialport)
        self.start()

    def run(self):
        while self.goOn:

            try:

                with self.dataLock:
                    pleaseConnect = self.pleaseConnect

                if pleaseConnect:

                    # open serial port
                    self.serialHandler = serial.Serial(self.serialport, baudrate=115200)

                    # read byte
                    while True:
                        c = self.serialHandler.read() # blocking
                        self.rxqueue.put(c)

            except:
                # mote disconnected, or pyserialHandler closed
                print 'coooooooooomienzaaaaaaaaa la exp'
                print traceback.format_exc()
                print 'acaaaaaaaaaaaaba la exp'
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

    #def sendSerialBytes(self):
    #    raise NotImplementedError() # #11

    def close(self):
        self.goOn            = False

    #======================== private =========================================

#============================ main ============================================

if __name__ == '__main__':
    otbox = OtBox()
