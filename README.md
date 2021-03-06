# WiFi Configuration

To setup the WiFi network connection of the Raspberry pi, just add the following lines to /etc/wpa_supplicant/wpa_supplicant.conf

```
network={
	ssid="SSID"
	psk="password"
	key_mgmt=WPA-PSK
}

```

# Installation

Download the file install/install.sh and execute it, the first argument will be the id of the otbox.

```
sudo sh install.sh "otbox_name"
```


# API
Notes:
- the first part of the topic is 'opentestbed', 'iotlab' or 'wilab' depending on the testbed on which it is deployed. All examples in this README assume 'opentestbed'
- cmd messages MUST contain a 'token' field
- resp messages MUST contain a 'token' field, which echoes the 'echo' field of the cmd
- resp messages MUST contain a 'success' field, either true or false. If false, resp message MUST contain 'exception' and 'traceback' fields
- deviceId of 'all' allowed
- code runs using http://supervisord.org/

## box

### commands

#### echo

request:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/cmd/echo

payload:
    {
        'token':   123,
        'payload': 'some random payload'
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/resp/echo

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": {
            "token": 123,
            "payload": "some random payload"
        }
    }
```

#### status

request:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/cmd/status

payload:
    {
        'token': 123
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/resp/status

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": {
            "uptime": "20:29:14.499249",
            "software_version": "1.0.6",
            "currenttime": "Fri Sep 21 12:28:57 2018",
            "last_changesoftware_succesful": true,
            "motes": [
                {
                    "firmware_description": "build\\openmote-b-24ghz_armgcc\\projects\\common\\01bsp_leds_prog.ihex",
                    "EUI64": "00-12-4b-00-14-b5-b6-47",
                    "bootload_success": true,
                    "serialport": "/dev/ttyUSB1"
                },
                {
                    "firmware_description": "build\\openmote-b-24ghz_armgcc\\projects\\common\\01bsp_leds_prog.ihex",
                    "EUI64": "00-12-4b-00-14-b5-b6-18",
                    "bootload_success": true,
                    "serialport": "/dev/ttyUSB3"
                },
                {
                    "firmware_description": "build\\openmote-b-24ghz_armgcc\\projects\\common\\01bsp_leds_prog.ihex",
                    "EUI64": "00-12-4b-00-14-b5-b5-f2",
                    "bootload_success": true,
                    "serialport": "/dev/ttyUSB5"
                },
                {
                    "firmware_description": "build\\openmote-b-24ghz_armgcc\\projects\\common\\01bsp_leds_prog.ihex",
                    "EUI64": "00-12-4b-00-14-b5-b5-7e",
                    "bootload_success": true,
                    "serialport": "/dev/ttyUSB7"
                }
            ],
            "starttime": "Thu Sep 20 15:59:42 2018",
            "threads_name": [
                "MainThread",
                "SerialRxBytePublisher@/dev/ttyUSB1",
                "otbox20_command_status",
                "mqtt_loop_thread",
                "SerialRxBytePublisher@/dev/ttyUSB3",
                "SerialportHandler@/dev/ttyUSB5",
                "SerialRxBytePublisher@/dev/ttyUSB7",
                "image_thread",
                "SerialportHandler@/dev/ttyUSB1",
                "SerialportHandler@/dev/ttyUSB7",
                "SerialportHandler@/dev/ttyUSB3",
                "heartbeat_thread",
                "SerialRxBytePublisher@/dev/ttyUSB5"
            ],
            "IP_address": "128.93.113.24",
            "host_name": "otbox08",
            "location": "A115 Salle de reunion"
        }
    }
```

#### discovermotes

request:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/cmd/discovermotes

payload:
    {
        'token': 123
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/resp/discovermotes

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": {
            "motes": [
                {
                    "firmware_description": "FIRMWARE_EUI64_RETRIEVAL",
                    "EUI64": "00-12-4b-00-14-b5-b6-48",
                    "bootload_success": true,
                    "serialport": "/dev/ttyUSB1"
                },
                {
                    "firmware_description": "FIRMWARE_EUI64_RETRIEVAL",
                    "EUI64": "00-12-4b-00-14-b5-b5-97",
                    "bootload_success": true,
                    "serialport": "/dev/ttyUSB3"
                },
                {
                    "firmware_description": "FIRMWARE_EUI64_RETRIEVAL",
                    "EUI64": "00-12-4b-00-14-b5-b6-0b",
                    "bootload_success": true,
                    "serialport": "/dev/ttyUSB5"
                },
                {
                    "firmware_description": "FIRMWARE_EUI64_RETRIEVAL",
                    "EUI64": "00-12-4b-00-14-b5-b5-65",
                    "bootload_success": true,
                    "serialport": "/dev/ttyUSB7"
                }
            ]
        }
    }
```

#### changesoftware

request:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/cmd/changesoftware

payload:
    {
        "version": "develop",
        "url": "https://github.com/openwsn-berkeley/opentestbed/archive/develop.zip",
        "token": 123
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/resp/changesoftware

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": {}
    }
```

#### picturetoscreen

request:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/cmd/picturetoscreen

payload:
    {
        "url": "https://team.inria.fr/eva/files/2018/07/testboxlogo_inria.jpg",
        "token": "picrotator"
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/resp/picturetoscreen

payload:
    {
        "token": "picrotator",
        "success": true,
        "returnVal": {}
    }
```

#### colortoscreen

request:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/cmd/colortoscreen

payload:
    {
        "r": 0,
        "g": 0,
        "b": 255,
        "token": 123
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/resp/colortoscreen

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": null
    }
```
#### hostnametoscreen

request:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/cmd/hostnametoscreen

payload:
    {
        'token': 123,
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/resp/hostnametoscreen

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": null
    }
```

#### changelocation

request:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/cmd/changelocation

payload:
    {
        "location": "A102",
        "token": 123
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/resp/changelocation

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": null
    }
```

### notifications

#### heartbeat

```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/notif/heartbeat

payload:
    {
        "software_version": "1.0.6"
    }
```

#### crashreport

```
topic:
    opentestbed/deviceType/box/deviceId/otbox01/notif/crashreport

payload:
    {
        'exception': name,
        'traceback': name
    }
```

## mote

### commands

#### program

request:
```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/program

payload:
    {
        "description": "bsp_eui64",
        "url": "https://raw.githubusercontent.com/openwsn-berkeley/opentestbed/master/bootloaders/01bsp_eui64_prog.ihex",
        "token": 123
    }

or

payload:
    {
        "description": "01bsp_leds_prog.hex",
        "hex": "OjAyMDAwMDA0MDAyMERBCjoxMDAwMDAwMEE0NEEwMDIwNDUyNDIwMDAyOTI0MjAwMDM1MjQyMDAwNzMKOjEwMDAxMDAwM0QyNDIwMDAzRDI0MjAwMDNEMjQyMDAwMDAwMDAwMDA1RAo6MTAwMDIwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAzRDI0MjAwMDRGCjoxMDAwMzAwMDNEMjQyMDAwMDAwMDAwMDAzRDI0MjAwMDNEMjQyMDAwM0QKOjEwMDA0MDAwM0QyNDIwMDAzRDI0MjAwMDNEMjQyMDAwM0QyNDIwMDBBQwo6MTAwMDUwMDAwMDAwMDAwMDNEMjQyMDAwM0QyNDIwMDAzRDI0MjAwMDFECjoxMDAwNjAwMDNEMjQyMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMEYKOjEwMDA3MDAwMDAwMDAwMDAwMDAwMDAwMDNEMjQyMDAwMDAwMDAwMDBGRgo6MTAwMDgwMDAwMDAwMDAwMDAwMDAwMDAwM0QyNDIwMDAzRDI0MjAwMDZFCjoxMDAwOTAwMDNEMjQyMDAwM0QyNDIwMDAzRDI0MjAwMDNEMjQyMDAwNUMKOjEwMDBBMDAwM0QyNDIwMDAzRDI0MjAwMDNEMjQyMDAwM0QyNDIwMDA0Qwo6MTAwMEIwMDAzRDI0MjAwMDNEMjQyMDAwM0QyNDIwMDAzRDI0MjAwMDNDCjoxMDAwQzAwMDNEMjQyMDAwM0QyNDIwMDAzRDI0MjAwMDNEMjQyMDAwMkMKOjEwMDBEMDAwM0QyNDIwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDA5Rgo6MTAwMEUwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDEwCjoxMDAwRjAwMDNEMjQyMDAwMDAwMDAwMDAzRDI0MjAwMDNEMjQyMDAwN0QKOjEwMDEwMDAwMDAwMDAwMDAwMDAwMDAwMDAwMDAw...",
        "token": 123
    }

```

response:
```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/resp/program

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": null
    }
```

#### tomoteserialbytes

request:
```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/tomoteserialbytes

payload:
    {
        "serialbytes": [
            126,
            1,
            241,
            225,
            126
        ],
        "token": 123
    }
```

response:
```
topic:
opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/resp/tomoteserialbytes

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": null
    }
```

#### reset

request:
```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/reset

payload:
    {
        'token': 123
    }
```

response:
```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/resp/reset

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": null
    }
```

#### disable

request:
```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/disable

payload:
    {
        'token': 123
    }
```

response:
```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/resp/disable

payload:
    {
        "token": 123,
        "success": true,
        "returnVal": null
    }
```

### notifications

```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/notif/frommoteserialbytes

payload:
    {
        "serialbytes": [
            49,
            50,
            45,
            48,
            53,
            13,
            10,
            48,
            48,
            45,
            49,
            45
        ]
    }
```
