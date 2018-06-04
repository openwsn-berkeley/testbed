import paho.mqtt.client as mqtt
import sys
from random import randint
import json
#============================ defines =========================================

BROKER_ADDRESS     = "argus.paris.inria.fr"


#============================ classes =========================================
class Ottest(object):

    MAX_TOKEN                = 1000
    PREFIX_CMD_HANDLER_NAME  = '_cmd_message_'

    def __init__(self, configuration):
        self.mqtttopic_prefix          = 'opentestbed/deviceType/'
        self.parameters                = configuration
        self.mqttclient                = mqtt.Client('ottest')
        self.mqttclient.on_connect     = self._test_connect
        self.mqttclient.on_message     = self._test_message
        self.mqttclient.connect(BROKER_ADDRESS)
        self.mqttclient.loop_forever()

    #======================== public ==========================================

    #======================== private =========================================
    def _test_connect(self, client, userdata, flags, rc):
        print rc
        self._send_comand(client, self.parameters)

    def _test_message(self, client, userdata, message):
        print json.loads(message.payload)
        client.disconnect()

    def _device_type(self, id_device):
        if len(id_device.split('-')) >= 6:
            return 'mote'
        else:
            return 'box'

    def _send_comand(self, client, options):
        token = randint(0,1000)
        topic_cmd  = '{0}{1}/device/{2}/cmd/{3}'.format(self.mqtttopic_prefix,
                                self._device_type(options[1]), options[1], options[2],)

        cmd_send   = getattr(self, '{0}{1}'.format(self.PREFIX_CMD_HANDLER_NAME, options[2]),self._cmd_message_)
        v          = cmd_send(options)
        v['token'] = token
        print 'The token is: {0}'.format(token)
        if options[2] == 'changesoftware':
            topic_resp  = topic_cmd.replace('changesoftware', 'status')
            self.mqttclient.subscribe(topic_resp.replace('cmd', 'resp'))
        else:
            self.mqttclient.subscribe(topic_cmd.replace('cmd', 'resp'))
        self.mqttclient.publish(topic_cmd,json.dumps(v))

    def _cmd_message_(self, options):
        v     = dict()
        for index in range(3, len(options)-1,2):
            v[options[index]]  = options[index+1]
        return v

    def _cmd_message_displayonscreen(self, options):
        v     = dict()
        return {}

    def _cmd_message_program(self, options):
        v     = dict()
        if 'url' in options:
            return self._cmd_message_(options)
        if 'hex' in options:
            v = self._cmd_message_(options)
            with file(v['hex'],'r') as f:
                v['hex']     = f.read()
            return v
        return {}

#============================ main ============================================

if __name__ == '__main__':
    ottest = Ottest(sys.argv)