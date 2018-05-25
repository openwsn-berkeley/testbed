import paho.mqtt.client as mqtt

broker_address="argus.paris.inria.fr"

def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

def on_message(client, userdata, message):
    print("Resonse = "+message.payload)

print("Creating client")
client = mqtt.Client("user")

client.on_connect = on_connect
client.on_message = on_message

print("Connecting to broker")
client.connect(broker_address)

mes="Opentestbed,1.0,https://raw.githubusercontent.com/openwsn-berkeley/opentestbed/master/otbox.py,123"
topic="opentestbed/deviceType/box/device/otbox_01/cmd/changesoftware"
client.subscribe("opentestbed/deviceType/box/device/otbox_01/resp/changesoftware")
client.publish(topic,mes)
client.loop_forever()
