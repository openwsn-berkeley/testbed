import paho.mqtt.client as mqtt
import threading
import time
import json

#============================ defines =========================================

BROKER_ADDRESS = "argus.paris.inria.fr"

#============================ classes =========================================

class OtBox(object):
    
    '''
    version       = 1.0
    name          = "Opentestbed"
    
    otbox_cmd     = ["changesoftware","status","discovermotes","displayonscreen"]
    otmot_cmd     = ["reset","disable","program","tomoteserialbytes"]
    mac_addr      = [None]*4
    '''
    HEARTBEAT_PERIOD = 1
    
    def __init__(self):
        
        # store params
        
        # local variables
        self.OTBOX_ID                  = 'TODO'
        self.mqtttopic_box_cmd_prefix  = "opentestbed/deviceType/box/device/{0}/cmd".format(self.OTBOX_ID)
        self.mqttconnected             = False
        self.mqttregistrations         = [
            ('changesoftware', self._mqtt_handler_changesoftware),
        ]
        
        # connect to MQTT
        self.mqttclient = mqtt.Client(self.OTBOX_ID)
        self.mqttclient.on_connect = self._on_mqtt_connect
        self.mqttclient.on_message = self._on_mqtt_message
        self.mqttclient.connect(BROKER_ADDRESS)
        self.mqttthread = threading.Thread(
            target = self.mqttclient.loop_forever,
        )
        self.mqttthread.start()
    
    #======================== public ==========================================
    
    #======================== private =========================================
    
    # top-level MQTT dispatching
    
    def _on_mqtt_connect(self, client, userdata, flags, rc):
        
        # remember I'm now connected
        self.mqttconnected = True
        
        # subscribe to commands
        for (topic_suffix,_) in self.mqttregistrations:
            client.subscribe('{0}/{1}'.format(self.mqtttopic_box_cmd_prefix,topic_suffix))
        
        # start heartbeat
        self.heartbeatthread = threading.Thread(
            target = self._heartbeatthread_func,
        )
        self.heartbeatthread.start()
    
    def _on_mqtt_message(self, client, userdata, message):
        print(message.topic)
        '''
        if message.topic == (box_prefix+"/cmd/changesoftware"):
            change_software(client,message.payload)
        if message.topic == (box_prefix+"/cmd/discovermotes"):
            discovermotes(client,message.payload)
        '''
    
    # command handlers
    
    def _mqtt_handler_changesoftware(self, client, payload):
        print("Changing software")
        print(payload)
        topic_resp=box_prefix+"/resp/changesoftware"
        try:
            mes        = json.loads(payload)
            name       = mes['description'][0]
            version    = mes['description'][1]
            link       = mes['url']
            token      = mes['token']
            subprocess.call(["mv", "otbox.py","otbox_old.py"])
            r          = requests.get(link, allow_redirects=True)
            open('otbox.py', 'wb').write(r.content)
            v          = {
                'token':    token,
                'sucess':   True,
            }
            info       = client.publish(topic_resp,json.dumps(v))
            os._exit(0)
        except:
            v={
                'token': token,
                'sucess': False,
                'exception': str(sys.exc_info()[0]),
                'traceback':traceback.format_exc(),
            }
            client.publish(topic_resp,json.dumps(v))
            subprocess.call(["mv", "otbox_old.py","otbox.py"])
    
    '''
    class img_loader(Thread):
        def __init__(self, port, image):
            Thread.__init__(self)
            self.port = port
            self.img = image
            self.result=0

        def run(self):
            self.result=subprocess.call(["python","cc2538-bsl.py","-e","--bootloader-invert-lines","-w","-b","400000","-p",self.port,self.img])
            if self.result == 1:
                self.result=subprocess.call(["python","cc2538-bsl.py","-e","--bootloader-invert-lines","-w","-b","400000","-p",self.port,self.img])

    def discovermotes(client,payload):
        mes=json.loads(payload)
        token=mes['token']
        topic_resp=box_prefix+"/resp/discovermotes"
        ports=["/dev/ttyUSB1","/dev/ttyUSB3","/dev/ttyUSB5","/dev/ttyUSB7"]
        image="01bsp_eui64_prog.ihex"
        try:
            prog0=img_loader(ports[0],image)
            prog1=img_loader(ports[1],image)
            prog2=img_loader(ports[2],image)
            prog3=img_loader(ports[3],image)
            prog0.start()
            prog1.start()
            prog2.start()
            prog3.start()
            prog0.join()
            prog1.join()
            prog2.join()
            prog3.join()
            result=[prog0.result,prog1.result,prog2.result,prog3.result]
            #result=[0,1,1,1]
            success=True
            ports_problems=[]
            for i in range(0,4):
                if result[i] == 0:
                    ser = serial.Serial(port=ports[i],baudrate=115200)
                    while True:
                        reading = ser.readline()
                        if len(reading.split("-")) == 8:
                            mac=str(reading)
                            mac_addr[i]=mac[:len(mac)-2]
                            break
                else:
                    success=False
                    ports_problems.append(ports[i])

            print(mac_addr)
            response=dict()
            motes=[dict() for x in range(4)]
            for i in range(0,4):
                motes[i]['serialPort']=ports[i]
                motes[i]['EUI64']=mac_addr[i]
            response['token']=token
            response['sucess']=success
            response['motes']=motes
            if success == False:
                response['exception']= "Communication in serial port failed"
                response['traceback']= "Problems in ports:" + ', '.join(ports_problems)
            message=json.dumps(response)
            client.publish(topic_resp,message)
        except:
            response=dict()
            response['token']=token
            response['sucess']=False
            response['exception']= str(sys.exc_info()[0])
            response['traceback']=traceback.format_exc()
            message=json.dumps(response)
            client.publish(topic_resp,message)

    # heartbeat
    while True:
        seq=seq+1
        mes="Hi "+str(seq)
        
        time.sleep(1)
    '''
    
    # notifications
    
    def _heartbeatthread_func(self):
        while True:
            # wait a bit
            time.sleep(self.HEARTBEAT_PERIOD)
            
            # publish a heartbeat message
            self.mqttclient.publish(
                topic   = '/poipoi',
                payload = json.dumps({}),
            )

#============================ main ============================================

if __name__ == '__main__':
    otbox = OtBox()
