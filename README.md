# Installation

To run the opentestbed script in a raspberry you have to follow the followings instructions:

1. Change the hostname of your raspberry to a unique name, in our case we have named each box as "otboxYY" (YY from 01 to 20). 
```
sudo nano /etc/hostname
```
2. Install the modules described in "requirements.txt"

3. Install supervisord and place "/bootloaders/supervisord.conf" in "/etc/". Now configure supervisord to run at boot, to do it follow the following instructions:
    - type in the command line 
    ```
    sudo crontab -e
    ```
    - Copy and paste at the end of the file the following line:\
    ```
    @reboot sudo supervisord
    ```
4. Place the file "otbootload.sh", that is in the folder "bootloaders/", in "/homeopentestbed/"

5. In "/homeopentestbed/" create a folder named "latest".

6. Place the file "otswtoload.txt" in "homeopentestbed/latest/". You may want to modify this file by changing the first line with the url of the release that you want to run in your box.

7. Reboot your raspberry pi.

When the raspberry boot, it downloads the opentestbed code, discovers the motes and it sends a status response to its topic.

# API
Notes:
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
    opentestbed/deviceType/box/deviceId/box1/cmd/echo

payload:
    {
        'token':   123,
        'payload': 'some random payload'
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/resp/echo

payload:
    {
        'token':   123,
        'success': true
        'payload': 'some random payload'
    }
```

#### changesoftware

request:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/cmd/changesoftware

payload:
    {
        'token':   123,
        'version': 123,
        'url': 'https://github.com/openwsn-berkeleyopentestbed/releases/REL-1.0.0'
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/resp/changesoftware

payload:
    {
        'token':   123,
        'success': true
    }
```

#### status

request:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/cmd/status

payload:
    {
        'token': 123
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/resp/status

payload:
    {
        'token': 123,
        'success': true,
        'software_version': <same as changesoftware payload>,
        'currenttime':      'poipoipo UTC',
        'starttime':        'poipoipo UTC',
        'uptime':           123, # seconds
        'motes': [
            {
                'serialport': '/dev/ttyUSB0',
                'EUI64':      '11-11-11-11-11-11-11-11',
                'firmware':    <same as program payload>
            },
            ...
        ]
    }
```

#### discovermotes

request:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/cmd/discovermotes

payload:
    {
        'token': 123
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/resp/discovermotes

payload:
    {
        'token': 123,
        'success': true,
        'motes': [
            {
                'serialport': '/dev/ttyUSB0',
                'EUI64':      '11-11-11-11-11-11-11-11',
            },
            {
                'serialport': '/dev/ttyUSB1',
                'EUI64':      '11-11-11-11-11-11-11-11',
            },
            ...
        ]
    }
```

#### colortoscreen

request:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/cmd/colortoscreen

payload:
    {
        'token': 123,
        'rgb':   'aabbcc'
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/resp/colortoscreen

payload:
    {
        'token':   123,
        'success': true
    }
```

#### picturetoscreen

request:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/cmd/picturetoscreen

payload:
    {
        'token': 123,
        'url':   'https://en.wikipedia.org/wiki/Lenna#/media/File:Lenna_(test_image).png',
        'rgb':   'aabbcc'
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/resp/picturetoscreen

payload:
    {
        'token':   123,
        'success': true
    }
```

### notifications

#### heartbeat

```
topic:
    opentestbed/deviceType/box/deviceId/box1/notif/heartbeat

payload:
    {
    }
```

#### crashreport

```
topic:
    opentestbed/deviceType/box/deviceId/box1/notif/crashreport

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
        'token':       123,
        'description': ['name','version'],
        'url':         'https://github.com/openwsn-berkeley/opentestbed/archive/REL-0.0.2.zip'
    }
```

response:
```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/resp/program

payload:
    {
        'token':   123,
        'success': true
    }
```

#### tomoteserialbytes

request:
```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/tomoteserialbytes

payload:
    {
        'token':       123,
        'serialbytes': '12efab0080'
    }
```

response:
```
topic:
opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/resp/tomoteserialbytes

payload:
    {
        'token': 123,
        'success': true
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
        'token': 123,
        'success': true
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
        'token': 123,
        'success': true
    }
```

### notifications

```
topic:
    opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/notif/fromoteserialbytes

payload:
    {
        'serialbytes': '12efab0080'
    }
```
