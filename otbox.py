import paho.mqtt.client as mqtt
import time

global otbox_id
global otbox_cmd
global otmot_cmd

otbox_id="otbox_01"
otbox_cmd=["changesoftware","status","discovermotes","displayonscreen"]
otmot_cmd=["reset","disable","program","tomoteserialbytes"]

def on_message(client, userdata, message):
    print("message received " ,str(message.payload.decode("utf-8")))
    print("message topic=",message.topic)

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))
    for cmd in otbox_cmd:
        topic="opentestbed/deviceType/box/device/"+otbox_id+"/cmd/"+cmd
        print("subscribing to:"+topic)
        client.subscribe(topic)

broker_address="argus.paris.inria.fr"
#broker_address="iot.eclipse.org"

print("Creating client")
client = mqtt.Client(otbox_id)

client.on_message = on_message
client.on_connect = on_connect

print("Connecting to broker")
client.connect(broker_address)

#client.loop_forever()
client.loop_start()
pub_topic="opentestbed/deviceType/box/device/"+otbox_id
seq=0
while True:
    seq=seq+1
    mes="Hi "+str(seq)
    client.publish(pub_topic,mes)
    time.sleep(1)
