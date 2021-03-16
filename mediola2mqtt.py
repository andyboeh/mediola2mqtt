#!/usr/bin/env bashio
# (c) 2021 Andreas Böhler
# License: Apache 2.0


import paho.mqtt.client as mqtt
import socket
import json
import yaml
import os
import sys
import requests

# get variables from bashio into python variables
mediola_host = os.environ["mediola_host"]
mediola_udp_port = os.environ["mediola_udp_port"] 
mqtt_host = os.environ["mqtt_host"] 
mqtt_port = os.environ["mqtt_port"] 
mqtt_username = os.environ["mqtt_username"] 
mqtt_password = os.environ["mqtt_password"] 
mqtt_discovery_prefix = os.environ["mqtt_discovery_prefix"] 
mqtt_topic = os.environ["mqtt_topic"] 
mqtt_debug = os.environ["mqtt_debug"] 
buttons = os.environ["buttons"]
blinds = os.environ["blinds"] 

# struct data in json format
config = {}
config['mediola'] = {}
config['mqtt'] = {}
config['mediola']['host'] = mediola_host
config['mediola']['udp_port'] = int(mediola_udp_port)
config['mqtt']['host'] = mqtt_host
config['mqtt']['port'] = int(mqtt_port)
config['mqtt']['username'] = mqtt_username
config['mqtt']['password'] = mqtt_password
config['mqtt']['discovery_prefix'] = mqtt_discovery_prefix
config['mqtt']['topic'] = mqtt_topic
config['mqtt']['debug'] = mqtt_debug

try:
    blinds_str = "["
    blinds_str += blinds
    blinds_str += "]"
    blinds_str = blinds_str.replace("\n", ", ")
    blinds_json = json.loads(blinds_str)
    if blinds_json:
        config['blinds'] = blinds_json
except:
    print("Binds config error, exception:", Exception)
    exit(1)

try:
    buttons_str = "["
    buttons_str += buttons
    buttons_str += "]"
    buttons_str = buttons_str.replace("\n", ",")
    buttons_json = json.loads(buttons_str)
    if buttons_json:
        config['buttons'] = buttons_json
except:
    print("Button config error, exception:", Exception)
    exit(1)



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
    print("MQTT: " + connect_statuses.get(rc, "Unknown error"))

def on_disconnect(client, userdata, rc):
    if rc != 0:
        print("Unexpected disconnection")
    else:
        print("Disconnected")

def on_message(client, obj, msg):
    print("Msg: " + msg.topic + " " + str(msg.qos) + " " + str(msg.payload))
    # Here we should send a HTTP request to Mediola to open the blind
    dtype, adr = msg.topic.split("_")
    dtype = dtype[dtype.rfind("/")+1:]
    adr = adr[:adr.find("/")]
    print(dtype)
    print(adr)
    for ii in range(0, len(config['blinds'])):
        if dtype == config['blinds'][ii]['type'] and adr == config['blinds'][ii]['adr']:
            if msg.payload == b'open':
              if dtype == 'RT':
                data = "20" + adr
              elif dtype == 'ER':
                data = adr + "01"
              else:
                return
            elif msg.payload == b'close':
              if dtype == 'RT':
                data = "40" + adr
              elif dtype == 'ER':
                data = adr + "00"
              else:
                return
            elif msg.payload == b'stop':
              if dtype == 'RT':
                data = "10" + adr
              elif dtype == 'ER':
                data = adr + "02"
              else:
                return
            else:
              print("Wrong command")
              return
            payload = {
              "XC_FNC" : "SendSC",
              "type" : dtype,
              "data" : data
            }
            url = 'http://' + config['mediola']['host'] + '/command'
            response = requests.get(url, params=payload, headers={'Connection':'close'})
            print(response)

def on_publish(client, obj, mid):
    print("Pub: " + str(mid))

def on_subscribe(client, obj, mid, granted_qos):
    print("Subscribed: " + str(mid) + " " + str(granted_qos))

def on_log(client, obj, level, string):
    print(string)

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

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(('',config['mediola']['udp_port']))

# Set up discovery structure

if 'buttons' in config:
    # Buttons are configured as MQTT device triggers
    for ii in range(0, len(config['buttons'])):
        identifier = config['buttons'][ii]['type'] + '_' + config['buttons'][ii]['adr']
        dtopic = config['mqtt']['discovery_prefix'] + '/device_automation/' + \
                 identifier + '/config'
        topic = config['mqtt']['topic'] + '/buttons/' + identifier
        name = "Mediola Button"
        if 'name' in config['buttons'][ii]['type']:
            name = config['buttons'][ii]['name']

        payload = {
          "automation_type" : "trigger",
          "topic" : topic,
          "type" : "button_short_press",
          "subtype" : "button_1",
          "device" : {
            "identifiers" : identifier,
            "manufacturer" : "Mediola",
            "name" : "Mediola Button",
          },
        }
        payload = json.dumps(payload)
        mqttc.publish(dtopic, payload=payload, retain=True)

if 'blinds' in config:
    for ii in range(0, len(config['blinds'])):
        identifier = config['blinds'][ii]['type'] + '_' + config['blinds'][ii]['adr']
        dtopic = config['mqtt']['discovery_prefix'] + '/cover/' + \
                 identifier + '/config'
        topic = config['mqtt']['topic'] + '/blinds/' + identifier
        name = "Mediola Blind"
        if 'name' in config['blinds'][ii]:
            name = config['blinds'][ii]['name']

        payload = {
          "command_topic" : topic + "/set",
          "payload_open" : "open",
          "payload_close" : "close",
          "payload_stop" : "stop",
          "optimistic" : True,
          "device_class" : "blind",
          "unique_id" : identifier,
          "name" : name,
          "device" : {
            "identifiers" : identifier,
            "manufacturer" : "Mediola",
            "name" : "Mediola Blind",
          },
        }
        if config['blinds'][ii]['type'] == 'ER':
            payload["state_topic"] = topic + "/state"
        payload = json.dumps(payload)
        mqttc.subscribe(topic + "/set")
        mqttc.publish(dtopic, payload=payload, retain=True)

while True:
    data, addr = sock.recvfrom(1024)
    if config['mqtt']['debug']:
        print('Received message: %s' % data)
        mqttc.publish(config['mqtt']['topic'], payload=data, retain=False)
    if data.startswith(b'{XC_EVT}'):
        data = data.replace(b'{XC_EVT}', b'')
        data_dict = json.loads(data)
        for ii in range(0, len(config['buttons'])):
            if data_dict['type'] == config['buttons'][ii]['type']:
                if data_dict['data'][0:-2].lower() == config['buttons'][ii]['adr'].lower():
                    identifier = config['buttons'][ii]['type'] + '_' + config['buttons'][ii]['adr']
                    topic = config['mqtt']['topic'] + '/buttons/' + identifier
                    payload = data_dict['data'][-2:]
                    mqttc.publish(topic, payload=payload, retain=False)
        for ii in range(0, len(config['blinds'])):
            if data_dict['type'] == 'ER' and data_dict['type'] == config['blinds'][ii]['type']:
                if data_dict['data'][0:2].lower() == config['blinds'][ii]['adr'].lower():
                    identifier = config['blinds'][ii]['type'] + '_' + config['blinds'][ii]['adr']
                    topic = config['mqtt']['topic'] + '/blinds/' + identifier + '/state'
                    state = data_dict['data'][-2:].lower()
                    payload = 'unknown'
                    if state == '01' or state == '0e':
                        payload = 'open'
                    elif state == '02' or state == '0f':
                        payload = 'closed'
                    elif state == '08' or state == '0a':
                        payload = 'opening'
                    elif state == '09' or state == '0b':
                        payload = 'closing'
                    mqttc.publish(topic, payload=payload, retain=True)
