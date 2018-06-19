# Installation

Download the file install/install.sh and execute it, the first argument will be the id of the otbox.

```
sudo sh install.sh "otbox_name"
```


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

#### changesoftware

request:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/cmd/changesoftware

payload:
    {
        'token':   123,
        'url':     'https://github.com/openwsn-berkeleyopentestbed/releases/REL-1.0.0'
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

#### picturetoscreen

request:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/cmd/picturetoscreen

payload:
    {
        'token': 123,
        'url':   'https://en.wikipedia.org/wiki/Lenna#/media/File:Lenna_(test_image).png'
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

#### colortoscreen

request:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/cmd/colortoscreen

payload:
    {
        'token': 123,
        'r':  255
        'g': 255
        'b': 255
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
#### hostnametoscreen

request:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/cmd/hostnametoscreen

payload:
    {
        'token': 123,
    }
```

response:
```
topic:
    opentestbed/deviceType/box/deviceId/box1/resp/hostnametoscreen

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
	'software_version': <same as changesoftware payload>,
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
        OR
        'hex':         'abcd1234'
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
        'token':   123,
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
