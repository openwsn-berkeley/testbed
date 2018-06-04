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
4. Place the file "otbootload.sh", that is in the folder "bootloaders/", in "/home/opentestbed/"

5. In "/home/opentestbed/" create a folder named "latest".

6. Place the file "otswtoload.txt" in "home/opentestbed/latest/". You may want to modify this file by changing the first line with the url of the release that you want to run in your box.

7. Reboot your raspberry pi.

When the raspberry boot, it downloads the opentestbed code, discovers the motes and it sends a status response to its topic.

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
```

```
/opentestbed/deviceType/box/deviceId/box1/cmd/changesoftware
{
    'token':   123,
    'version': 123,
    'url': 'https://github.com/openwsn-berkeley/opentestbed/releases/REL-1.0.0'
}
```

```
/opentestbed/deviceType/box/deviceId/box1/cmd/status
{
    'token': 123,
}
```

```
/opentestbed/deviceType/box/deviceId/box1/cmd/discovermotes
{
    'token': 123,
}
```

```
/opentestbed/deviceType/box/deviceId/box1/cmd/displayonscreen
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
```

```
                                              /changesoftware
{
    'token':   123,
    'success': true,
}
```

```
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
```

```
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
```

```
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
```

```
                                               /heartbeat
{
}
```

```
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
