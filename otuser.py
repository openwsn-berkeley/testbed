import paho.mqtt.client as mqtt
import sys
from random import randint
import json

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

if command == "changesoftware":
    #mes="Opentestbed,1.0,https://raw.githubusercontent.com/openwsn-berkeley/opentestbed/master/otbox.py,123"
    token=randint(0,1000)
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
    token=randint(0,1000)
    print(topic)
    v={
    'token': token,
    }
    mes=json.dumps(v)
    client.subscribe("opentestbed/deviceType/box/device/"+device+"/resp/discovermotes")
    client.publish(topic,mes)

if command == "status":
    topic="opentestbed/deviceType/box/device/"+device+"/cmd/status"
    token=randint(0,1000)
    print(topic)
    v={
    'token': token,
    }
    mes=json.dumps(v)
    client.subscribe("opentestbed/deviceType/box/device/"+device+"/resp/status")
    client.publish(topic,mes)

client.loop_forever()
