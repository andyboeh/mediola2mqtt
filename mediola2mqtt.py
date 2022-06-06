#!/usr/bin/env python
# (c) 2021 Andreas Böhler
# License: Apache 2.0


import paho.mqtt.client as mqtt
import socket
import json
import yaml
import os
import sys
import requests

if os.path.exists('/data/options.json'):
    print('Running in hass.io add-on mode')
    fp = open('/data/options.json', 'r')
    config = json.load(fp)
    fp.close()
elif os.path.exists('/config/mediola2mqtt.yaml'):
    print('Running in legacy add-on mode')
    fp = open('/config/mediola2mqtt.yaml', 'r')
    config = yaml.safe_load(fp)
    fp.close()
elif os.path.exists('mediola2mqtt.yaml'):
    print('Running in local mode')
    fp = open('mediola2mqtt.yaml', 'r')
    config = yaml.safe_load(fp)
    fp.close()
else:
    print('Configuration file not found, exiting.')
    sys.exit(1)

# Define MQTT event callbacks
def on_connect(client, userdata, flags, rc):
    connect_statuses = {
        0: "Connected",
        1: "incorrect protocol version",
        2: "invalid client ID",
        3: "server unavailable",
        4: "bad username or password",
        5: "not authorised"
    }
    if rc != 0:
        print("MQTT: " + connect_statuses.get(rc, "Unknown error"))
    else:
        setup_discovery()

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection")
    else:
        print("Disconnected")

def on_message(client, obj, msg):
    print("Msg: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    # Here we should send a HTTP request to Mediola to open the blind
    dtype, adr = msg.topic.split("_")
    mediolaid = dtype.split("/")[-2]
    dtype = dtype[dtype.rfind("/")+1:]
    adr = adr[:adr.find("/")]
    for ii in range(0, len(config['blinds'])):
        if dtype == config['blinds'][ii]['type'] and adr == config['blinds'][ii]['adr']:
            if isinstance(config['mediola'], list):
                if config['blinds'][ii]['mediola'] != mediolaid:
                    continue
            if msg.payload == b'open':
                if dtype == 'RT':
                    data = "20" + adr
                elif dtype == 'ER':
                    data = format(int(adr), "02x") + "01"
                else:
                    return
            elif msg.payload == b'close':
                if dtype == 'RT':
                    data = "40" + adr
                elif dtype == 'ER':
                    data = format(int(adr), "02x") + "00"
                else:
                    return
            elif msg.payload == b'stop':
                if dtype == 'RT':
                    data = "10" + adr
                elif dtype == 'ER':
                    data = format(int(adr), "02x") + "02"
                else:
                    return
            # extended commands
            elif msg.payload == b'down':
                if dtype == 'RT':
                    data = "40" + adr
                elif dtype == 'ER':
                    data = format(int(adr), "02x") + "00"
                else:
                    return
            elif msg.payload == b'up':
                if dtype == 'RT':
                    data = "20" + adr
                elif dtype == 'ER':
                    data = format(int(adr), "02x") + "01"
                else:
                    return
            elif msg.payload == b'longup':
                if dtype == 'RT':
                    data = "20" + adr
                elif dtype == 'ER':
                    data = format(int(adr), "02x") + "08"
                else:
                    return
            elif msg.payload == b'longdown':
                if dtype == 'RT':
                    data = "40" + adr
                elif dtype == 'ER':
                    data = format(int(adr), "02x") + "09"
                else:
                    return
            elif msg.payload == b'doubleup':
                if dtype == 'RT':
                    data = "20" + adr
                elif dtype == 'ER':
                    data = format(int(adr), "02x") + "0A"
                else:
                    return
            elif msg.payload == b'doubledown':
                if dtype == 'RT':
                    data = "40" + adr
                elif dtype == 'ER':
                    data = format(int(adr), "02x") + "0B"
                else:
                    return
            elif spayload.isnumeric():
                #tilt
                if dtype == 'ER':
                    if int(spayload) > 0:
                        data = format(int(adr), "02x") + "0A"   #double tap up
                    else:
                        data = format(int(adr), "02x") + "0B"   #double tap down
                else:
                    return
            else:
                print("Wrong command: " + str(msg.payload))
                return
            payload = {
              "XC_FNC" : "SendSC",
              "type" : dtype,
              "data" : data
            }
            host = ''
            if isinstance(config['mediola'], list):
                mediolaid = config['blinds'][ii]['mediola']
                for jj in range(0, len(config['mediola'])):
                    if mediolaid == config['mediola'][jj]['id']:
                        host = config['mediola'][jj]['host']
                    if 'password' in config['mediola'][jj] and config['mediola'][jj]['password'] != '':
                        payload['XC_PASS'] = config['mediola'][jj]['password']
            else:
                host = config['mediola']['host']
                if 'password' in config['mediola'] and config['mediola']['password'] != '':
                   payload['XC_PASS'] = config['mediola']['password']
            if host == '':
                print('Error: Could not find matching Mediola!')
                return
            url = 'http://' + host + '/command'
            response = requests.get(url, params=payload, headers={'Connection':'close'})

    for ii in range(0, len(config['switches'])):
        #currently only Intertechno and IR (= "other")
        if dtype != 'IT' and dtype != 'IR':
            continue

        # get address of configured switch
        if 'adr' in config['switches'][ii]:
            cadr = config['switches'][ii]['adr']
        elif dtype == "IT":
            #try to calculate switch address from on_value for auto-learn IT switches, if adr is missing
            cadr = get_IT_address(config['switches'][ii]['on_value'])
        elif dtype == "IR":
            #try to calculate switch address from name for OR switches, if adr is missing
            cadr = get_IR_address(config['switches'][ii]['name'])

        if dtype == config['switches'][ii]['type'] and adr == cadr:
            if isinstance(config['mediola'], list):
                if config['switches'][ii]['mediola'] != mediolaid:
                    continue

            if msg.payload == b'ON':
                if 'on_value' in config['switches'][ii]:
                    data = config['switches'][ii]['on_value']
                elif dtype == "IT" and len(adr) == 3:
                    # old family_code + device_code, A01 - P16
                    data = format((ord(adr[0].upper()) - 65),'X') + format(int(adr[1:]) - 1,'X') + 'E'
                else:
                    print("Missing on_value and unknown type/address: " + dtype + "/" + adr)
                    return
                #print("on_value: = " + data)
            elif msg.payload == b'OFF':
                if 'off_value' in config['switches'][ii]:
                    data = config['switches'][ii]['off_value']
                elif dtype == "IT" and len(adr) == 3:
                    # old family_code + device_code
                    data = format((ord(adr[0].upper()) - 65),'X') + format(int(adr[1:]) - 1,'X') + '6'
                else:
                    print("Missing off_value and unknown type/address: " + dtype + "/" + adr)
                    return
                #print("off_value: = " + data)
            else:
                print("Wrong command")
                return

            if dtype == 'IT':
                payload = {
                    "XC_FNC" : "SendSC",
                    "type" : dtype,
                    "data" : data
                }
            elif dtype == 'IR':
                payload = {
                    "XC_FNC" : "Send2",
                    "type" : "CODE",
                    "ir"   : "01",
                    "code" : data
                }
            host = ''
            if isinstance(config['mediola'], list):
                mediolaid = config['switches'][ii]['mediola']
                for jj in range(0, len(config['mediola'])):
                    if mediolaid == config['mediola'][jj]['id']:
                        host = config['mediola'][jj]['host']
                    if 'password' in config['mediola'][jj] and config['mediola'][jj]['password'] != '':
                        payload['XC_PASS'] = config['mediola'][jj]['password']
            else:
                host = config['mediola']['host']
                if 'password' in config['mediola'] and config['mediola']['password'] != '':
                    payload['XC_PASS'] = config['mediola']['password']
            if host == '':
                print('Error: Could not find matching Mediola!')
                return
            url = 'http://' + host + '/command'
            response = requests.get(url, params=payload, headers={'Connection':'close'})

            #we are done here, end message processing
            return

def on_publish(client, obj, mid):
    print("Pub: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(client, obj, level, string):
    print(string)

def setup_discovery():
    if 'buttons' in config:
        # Buttons are configured as MQTT device triggers
        for ii in range(0, len(config['buttons'])):
            identifier = config['buttons'][ii]['type'] + '_' + config['buttons'][ii]['adr']
            host = ''
            mediolaid = 'mediola'
            if isinstance(config['mediola'], list):
                mediolaid = config['buttons'][ii]['mediola']
                for jj in range(0, len(config['mediola'])):
                    if mediolaid == config['mediola'][jj]['id']:
                        host = config['mediola'][jj]['host']
            else:
                host = config['mediola']['host']
            if host == '':
                print('Error: Could not find matching Mediola!')
                continue
            deviceid = "mediola_buttons_" + host.replace(".", "")
            dtopic = config['mqtt']['discovery_prefix'] + '/device_automation/' + \
                     mediolaid + '_' + identifier + '/config'
            topic = config['mqtt']['topic'] + '/buttons/' + mediolaid + '/' + identifier
            name = "Mediola Button"
            if 'name' in config['buttons'][ii]:
                name = config['buttons'][ii]['name']

            payload = {
              "automation_type" : "trigger",
              "topic" : topic,
              "type" : "button_short_press",
              "subtype" : "button_1",
              "device" : {
                "identifiers" : deviceid,
                "manufacturer" : "Mediola",
                "name" : "Mediola Button",
              },
            }
            payload = json.dumps(payload)
            mqttc.publish(dtopic, payload=payload, retain=True)

    if 'switches' in config:
        for ii in range(0, len(config['switches'])):
            type = config['switches'][ii]['type']

            if 'adr' in config['switches'][ii]:
                adr = config['switches'][ii]['adr']
            elif type == "IT":
                adr = get_IT_address(config['switches'][ii]['on_value'])

            elif type == "IR" and 'name' in config['switches'][ii]:
                adr = get_IR_address(config['switches'][ii]['name'])

            identifier = type + '_' + adr
            host = ''
            mediolaid = 'mediola'
            if isinstance(config['mediola'], list):
                mediolaid = config['buttons'][ii]['mediola']
                for jj in range(0, len(config['mediola'])):
                    if mediolaid == config['mediola'][jj]['id']:
                        host = config['mediola'][jj]['host']
            else:
                host = config['mediola']['host']
            if host == '':
                print('Error: Could not find matching Mediola!')
                continue
            deviceid = "mediola_switches_" + host.replace(".", "")
            dtopic = config['mqtt']['discovery_prefix'] + '/switch/' + \
                     mediolaid + '_' + identifier + '/config'
            topic = config['mqtt']['topic'] + '/switches/' + mediolaid + '/' + identifier
            name = "Mediola Switch"
            if 'name' in config['switches'][ii]:
                name = config['switches'][ii]['name']

            payload = {
              "command_topic" : topic + "/set",
              "payload_on" : "ON",
              "payload_off" : "OFF",
              "optimistic" : True,
              "unique_id" : mediolaid + '_' + identifier,
              "name" : name,
              "device" : {
                "identifiers" : deviceid,
                "manufacturer" : "Mediola",
                "name" : "Mediola Switch",
              },
            }
            # for bidirectional switches, add state channel
            #if config['switches'][ii]['type'] == 'ER':
            #    payload["state_topic"] = topic + "/state"
            payload = json.dumps(payload)
            mqttc.subscribe(topic + "/set")
            mqttc.publish(dtopic, payload=payload, retain=True)

    if 'blinds' in config:
        for ii in range(0, len(config['blinds'])):
            identifier = config['blinds'][ii]['type'] + '_' + config['blinds'][ii]['adr']
            host = ''
            mediolaid = 'mediola'
            if isinstance(config['mediola'], list):
                mediolaid = config['blinds'][ii]['mediola']
                for jj in range(0, len(config['mediola'])):
                    if mediolaid == config['mediola'][jj]['id']:
                        host = config['mediola'][jj]['host']
            else:
                host = config['mediola']['host']
            if host == '':
                print('Error: Could not find matching Mediola!')
                continue
            deviceid = "mediola_blinds_" + host.replace(".", "")
            dtopic = config['mqtt']['discovery_prefix'] + '/cover/' + \
                     mediolaid + '_' + identifier + '/config'
            topic = config['mqtt']['topic'] + '/blinds/' + mediolaid + '/' + identifier
            name = "Mediola Blind"
            if 'name' in config['blinds'][ii]:
                name = config['blinds'][ii]['name']

            payload = {
              "command_topic" : topic + "/set",
              "tilt_command_topic" : topic + "/set",
              "tilt_min" : 0,
              "tilt_max": 1,
              "tilt_closed_value" : 0,
              "tilt_opened_value" : 1,
              "tilt_command_template" : """
                {% set tilt = state_attr(entity_id, "current_tilt_position") %}
                {{ tilt }}""",
              "payload_open" : "open",
              "payload_close" : "close",
              "payload_stop" : "stop",
              "optimistic" : True,
              "device_class" : "blind",
              "unique_id" : mediolaid + '_' + identifier,
              "name" : name,
              "device" : {
                "identifiers" : deviceid,
                "manufacturer" : "Mediola",
                "name" : "Mediola Blind",
              },
            }
            if config['blinds'][ii]['type'] == 'ER':
                payload["state_topic"] = topic + "/state"
            payload = json.dumps(payload)
            mqttc.subscribe(topic + "/set")
            mqttc.publish(dtopic, payload=payload, retain=True)

def handle_button(packet_type, address, state, mediolaid):
    retain = False
    topic = False
    payload = False

    for ii in range(0, len(config['buttons'])):
        if packet_type == config['buttons'][ii]['type']:
            if address == config['buttons'][ii]['adr'].lower():
                if isinstance(config['mediola'], list):
                    if config['buttons'][ii]['mediola'] != mediolaid:
                        continue
                identifier = config['buttons'][ii]['type'] + '_' + config['buttons'][ii]['adr']
                topic = config['mqtt']['topic'] + '/buttons/' + mediolaid + '/' + identifier
                payload = state
    return topic, payload, retain


def handle_blind(packet_type, address, state, mediolaid):
    retain = True
    topic = False
    payload = False

    for ii in range(0, len(config['blinds'])):
        if packet_type == 'ER' and packet_type == config['blinds'][ii]['type']:
            if address == config['blinds'][ii]['adr'].lower():
                if isinstance(config['mediola'], list):
                    if config['blinds'][ii]['mediola'] != mediolaid:
                        continue
                identifier = config['blinds'][ii]['type'] + '_' + config['blinds'][ii]['adr']
                topic = config['mqtt']['topic'] + '/blinds/' + mediolaid + '/' + identifier + '/state'
                payload = 'unknown'
                if state == '01' or state == '0e':
                    payload = 'open'
                elif state == '02' or state == '0f':
                    payload = 'closed'
                elif state == '08' or state == '0a':
                    payload = 'opening'
                elif state == '09' or state == '0b':
                    payload = 'closing'
                elif state == '0d' or state == '05':
                    payload = 'stopped'
    return topic, payload, retain

def get_mediolaid_by_address(addr):
    mediolaid = 'mediola'
    if not isinstance(config['mediola'], list):
        return mediolaid

    for ii in range(0, len(config['mediola'])):
        host = config['mediola'][ii]['host']
        ipaddr = socket.gethostbyname(host)
        if addr[0] == ipaddr:
            mediolaid = config['mediola'][ii]['id']

    return mediolaid

def handle_packet_v4(data, addr):
    try:
        data_dict = json.loads(data)
    except:
        return False

    mediolaid = get_mediolaid_by_address(addr)
    packet_type = data_dict['type']
    topic, payload, retain = handle_button(packet_type,
                             data_dict['data'][0:-2].lower(),
                             data_dict['data'][-2:].lower(),
                             mediolaid)
    if not topic:
        topic, payload, retain = handle_blind(packet_type,
                         format(int(data_dict['data'][0:2].lower(), 16), '02d'),
                         data_dict['data'][-2:].lower(),
                         mediolaid)

    if topic and payload:
        mqttc.publish(topic, payload=payload, retain=retain)
        return True
    else:
        return False

def handle_packet_v6(data, addr):
    try:
        data_dict = json.loads(data)
    except:
        return False

    mediolaid = get_mediolaid_by_address(addr)
    packet_type = data_dict['type']
    address = data_dict['adr'].lower()
    state = data_dict['state'][-2:].lower()
    topic, payload, retain = handle_button(packet_type, address, state, mediolaid)
    if not topic:
        topic, payload, retain = handle_blind(packet_type,
                         format(int(address, 16), '02d'),
                         state,
                         mediolaid)

    if topic and payload:
        mqttc.publish(topic, payload=payload, retain=retain)
        return True
    else:
        return False

#calculate switch address from on_value for IT switches
def get_IT_address(on_value):
    # ITT-1500 new self-learning code
    if len(on_value) == 8:
        #26bit address, (2 bit command), 4 bit channel
        return format(int(on_value,16) & 0xFFFFFFC7,"08x")

    # familiy-code, device-code
    elif len(on_value) == 3:
        #familiy-code A-P -> 0-F
        #device-code 01-16 -> 0-F
        family_code = chr(int(on_value[0],16) + 65)
        device_code = format(int(on_value[1],16) + 1,"02")
        return family_code + device_code
    else:
        #print('Error: cannot calculate IT switch address from on_value = ' + on_value)
        return "0"

#calculate switch "address" from name for IR switches
def get_IR_address(name):
    adr = name.lower()
    adr = ''.join(e for e in adr if e.isalnum() and e.isascii())
    return adr

# Setup MQTT connection
mqttc = mqtt.Client()

mqttc.on_connect = on_connect
mqttc.on_subscribe = on_subscribe
mqttc.on_disconnect = on_disconnect
mqttc.on_message = on_message

if config['mqtt']['debug']:
    print("Debugging messages enabled")
    mqttc.on_log = on_log
    mqttc.on_publish = on_publish

if config['mqtt']['username'] and config['mqtt']['password']:
    mqttc.username_pw_set(config['mqtt']['username'], config['mqtt']['password'])
try:
    mqttc.connect(config['mqtt']['host'], config['mqtt']['port'], 60)
except:
    print('Error connecting to MQTT, will now quit.')
    sys.exit(1)
mqttc.loop_start()

listen_port = 1902
if 'general' in config:
    if 'port' in config['general']:
        listen_port = config['general']['port']

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('',listen_port))

#setup_discovery()

while True:
    valid = False
    data, addr = sock.recvfrom(1024)
    if config['mqtt']['debug']:
        print('Received message: %s' % data)
        mqttc.publish(config['mqtt']['topic'], payload=data, retain=False)

    # For the v4 (and probably v5) gateways, the status packet starts
    # with '{XC_EVT}', but for the v6 it starts with 'STA:'.
    if data.startswith(b'{XC_EVT}'):
        data = data.replace(b'{XC_EVT}', b'')
        if not handle_packet_v4(data, addr):
            if config['mqtt']['debug']:
                print('Error handling v4 packet: %s' % data)
    elif data.startswith(b'STA:'):
        data = data.replace(b'STA:', b'')
        if not handle_packet_v6(data, addr):
            if config['mqtt']['debug']:
                print('Error handling v6 packet: %s' % data)
