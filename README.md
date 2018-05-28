Files description: 

- 01bsp_eui64_prog.ihex: Binary used to get MAC address of motes.
- cc2538-bsl.py: File used to load binary file to the motes.
- example.sh: There are somes examples of how to use otuser.py.
- otbox.py: The code that each raspberry Pi is running.
- otuser.py: This file is used for testing, is an example of how to communicate with the boxes.
- supervisord.conf: This is the configuration file of supervisord, which is a software used to keep otuser.py always running.


# API
Notes:
- cmd messages MUST contain a 'token' field
- resp messages MUST contain a 'token' field, which echoes the 'echo' field of the cmd
- resp messages MUST contain a 'success' field, either true or false. If false, resp message MUST contain 'exception' and 'traceback' fields
- deviceId of 'all' allowed
- code runs using http://supervisord.org/

## Box

### cmd

```
/opentestbed/deviceType/box/deviceId/box1/cmd/echo
{
    'token':   123
}
                                            /changesoftware
{
    'token':   123,
    'version': 123,
    'url': 'https://github.com/openwsn-berkeley/opentestbed/releases/REL-1.0.0'
}
                                             /status
{
    'token': 123,
}
                                             /discovermotes
{
    'token': 123,
}
                                             /displayonscreen
{
    'token': 123,
    'url': 'https://en.wikipedia.org/wiki/Lenna#/media/File:Lenna_(test_image).png',
    'rgb': 'aabbcc',
}
```

### resp

```
/opentestbed/deviceType/box/deviceId/box1/resp/echo
{
    'token': 123,
    'success': true,
}
                                              /changesoftware
{
    'token':   123,
    'success': true,
}
                                               /status
{
    'token': 123,
    'success': true,
    'software_version': <same as changesoftware payload>,
    'currenttime':'poipoipo UTC',
    'starttime':  'poipoipo UTC',
    'uptime':     123, # seconds
    'motes': [
        {
            'serialport': '/dev/ttyUSB0',
            'EUI64':      '11-11-11-11-11-11-11-11',
            'firmware':    <same as program payload>
        },
        ...
    ]
}
                                               /discovermotes
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
                                               /displayonscreen
{
    'token': 123,
    'success': true,
}
```

### notif

```
/opentestbed/deviceType/box/deviceId/box1/notif/status
{
    <same as status response, without the token field>
}
                                               /heartbeat
{
}
                                               /crashreport
{
    'exception': name,
    'traceback': name
}
```

## mote

### cmd

```
/opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/reset
{
    'token': 123,
}
                                                                 /disable
{
    'token': 123,
}
                                                                 /program
{
    'token': 123,
    'description': ['name','version'],
    'url': 'https://openwsn-builder.paris.inria.fr/job/Firmware/poipoipo.bin',
    'hex': '010203040505066',
}
/opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/cmd/tomoteserialbytes
{
    'token': 123,
    'serialbytes': '12efab0080',
}
```

### resp

```
/opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/resp/reset
{
    'token': 123,
    'success': true,
}
                                                                   /txserialframe
{
    'token': 123,
    'success': true,
}
                                                                   /disable
{
    'token': 123,
    'success': true,
}
                                                                   /program
{
    'token': 123,
    'success': true,
}
```

### notif

```
/opentestbed/deviceType/mote/deviceId/01-02-03-04-05-06-07-08/notif/fromoteserialbytes
{
    'serialbytes': '12efab0080',
}
```
