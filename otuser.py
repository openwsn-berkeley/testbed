import paho.mqtt.client as mqtt
import sys
from random import randint

broker_address="argus.paris.inria.fr"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

def on_message(client, userdata, message):
    print("Resonse = "+message.payload)
    client.disconnect()


device = sys.argv[1]
command=sys.argv[2]

print("Creating client")
client = mqtt.Client("user")

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker")
client.connect(broker_address)

if command == "changesoftware":
    #mes="Opentestbed,1.0,https://raw.githubusercontent.com/openwsn-berkeley/opentestbed/master/otbox.py,123"
    name=sys.argv[3]
    version=sys.argv[4]
    link=sys.argv[5]
    token=randint(0,100)
    mes=name+","+version+","+link+","+str(token)
    topic="opentestbed/deviceType/box/device/"+device+"/cmd/changesoftware"
    print(name)
    print(version)
    print(link)
    print(token)
    print(mes)
    print(topic)
    client.subscribe("opentestbed/deviceType/box/device/"+device+"/resp/changesoftware")
    client.publish(topic,mes)

client.loop_forever()
