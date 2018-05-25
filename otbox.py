import paho.mqtt.client as mqtt
import time
import subprocess
import requests
import os

global otbox_id
global otbox_cmd
global otmot_cmd
global name
global version
global box_prefix

otbox_id="otbox_01"
box_prefix="opentestbed/deviceType/box/device/"+otbox_id
otbox_cmd=["changesoftware","status","discovermotes","displayonscreen"]
otmot_cmd=["reset","disable","program","tomoteserialbytes"]

def change_software(client,payload):
    print("Changing software")
    print(payload)
    topic_resp=box_prefix+"/resp/changesoftware"
    try:
        name,version,link,token=payload.split(",")
        subprocess.call(["mv", "otbox.py","otbox_old.py"])
        print(link)
        r = requests.get(link, allow_redirects=True)
        open('otbox.py', 'wb').write(r.content)
        print(client.publish(topic_resp,"true,"+token))
        os._exit(0)
    except ValueError:
        err="Wrong input format"
        print(err)
        client.publish(topic_resp,err)
    except:
        err="Wrong Link"
        print(err)
        client.publish(topic_resp,err+","+token)
        subprocess.call(["mv", "otbox_old.py","otbox.py"])

def on_message(client, userdata, message):
    print(message.topic)
    if message.topic == (box_prefix+"/cmd/changesoftware"):
        change_software(client,message.payload)

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
