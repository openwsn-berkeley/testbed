import paho.mqtt.client as mqtt
import sys
from random import randint
import json
#============================ defines =========================================

BROKER_ADDRESS     = "argus.paris.inria.fr"


#============================ classes =========================================

'''
global device

max_token=1000
device = sys.argv[1]
command=sys.argv[2]
broker_address="argus.paris.inria.fr"
box_prefix="opentestbed/deviceType/box/device/"+device

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

def on_message(client, userdata, message):
    resp=json.loads(message.payload)
    print(resp)
    client.disconnect()


print("Creating client")
client = mqtt.Client("user")

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker")
client.connect(broker_address)
token=randint(0,1000)

if command == "changesoftware":
    #mes="Opentestbed,1.0,https://raw.githubusercontent.com/openwsn-berkeley/opentestbed/master/otbox.py,123"
    name=sys.argv[3]
    version=sys.argv[4]
    link=sys.argv[5]
    v={
    'token': token,
    'description':[name,version],
    'url': link,
    }

    #mes=name+","+version+","+link+","+str(token)
    mes=json.dumps(v)
    topic="opentestbed/deviceType/box/device/"+device+"/cmd/changesoftware"
    print("Token sent: "+str(token))
    print box_prefix+"/resp/changesoftware"
    client.subscribe("opentestbed/deviceType/box/device/"+device+"/resp/status")
    client.publish(topic,mes)


if command == "discovermotes":
    topic="opentestbed/deviceType/box/device/"+device+"/cmd/discovermotes"
    print(topic)
    v={
    'token': token,
    }
    mes=json.dumps(v)
    client.subscribe("opentestbed/deviceType/box/device/"+device+"/resp/discovermotes")
    client.publish(topic,mes)

if command == "status":
    topic="opentestbed/deviceType/box/device/"+device+"/cmd/status"
    print(topic)
    v={
    'token': token,
    }
    mes=json.dumps(v)
    client.subscribe("opentestbed/deviceType/box/device/"+device+"/resp/status")
    client.publish(topic,mes)

if command == "disable":
    topic="opentestbed/deviceType/mote/device/"+device+"/cmd/disable"
    print(topic)
    v={
    'token': token,
    }
    mes=json.dumps(v)
    client.subscribe("opentestbed/deviceType/mote/device/"+device+"/resp/disable")
    client.publish(topic,mes)

if command == "disable":
    topic="opentestbed/deviceType/mote/device/"+device+"/cmd/disable"
    print(topic)
    v={
    'token': token,
    }
    mes=json.dumps(v)
    client.subscribe("opentestbed/deviceType/mote/device/"+device+"/resp/disable")
    client.publish(topic,mes)

if command == 'program':
    topic="opentestbed/deviceType/mote/device/"+device+"/cmd/program"
    print(topic)
    print token
    name = sys.argv[3]
    version   = sys.argv[4]
    option    = sys.argv[5]
    new_program    = sys.argv[6]
    v={
    'token': token,
    'description':[name,version],
    }

    if option == 'url':
        v['url']   = new_program
    if option == 'file':
        with file(new_program,'r') as f:
            v['hex']   = f.read()
    mes  = json.dumps(v)
    client.subscribe("opentestbed/deviceType/mote/device/"+device+"/resp/program")
    client.publish(topic,mes)

client.loop_forever()
'''

class Ottest(object):

    MAX_TOKEN                = 1000
    PREFIX_CMD_HANDLER_NAME  = '_cmd_'

    def __init__(self, configuration):
        self.mqtttopic_prefix          = 'opentestbed/deviceType/'
        self.parameters                = configuration
        self.mqttclient                = mqtt.Client('ottest')
        self.mqttclient.on_connect     = self._test_connect
        self.mqttclient.on_message     = self._test_message
        self.mqttclient.connect(BROKER_ADDRESS)
        self._send_comand(self.mqttclient, configuration)

#arg ---- mote/box ----  id_device ---- cmd ----
    #======================== public ==========================================

    #======================== private =========================================
    def _test_connect(self, client, userdata, flags, rc):
        print rc

    def _test_message(self, client, userdata, message):
        print json.loads(message.payload)
        client.disconnect()

    def _send_comand(self, client, options):
        token = randint(0,1000)
        v     = dict()
        topic_cmd = '{0}{1}/device/{2}/cmd/{3}'.format(self.mqtttopic_prefix,
                                options[1], options[2], options[3],)


        
        for index in range(4, len(options)-1,2):
            v[options[index]]  = options[index+1]
        v={
            'token': token,
        }



        print topic_cmd
        print v

    def _cmd_displayonscreen(self, options):
        raise NotImplementedError()

    def _cmd_program(self, options):
        raise NotImplementedError()

#============================ main ============================================

if __name__ == '__main__':
    ottest = Ottest(sys.argv)
