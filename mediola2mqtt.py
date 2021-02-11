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

if not os.path.exists('config.yaml'):
    print('Configuration file "config.yaml" not found, exiting.')
    sys.exit(1)

subscriptions = {}

fp = open('config.yaml', 'r')
config = yaml.safe_load(fp)
print(config)

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

mqttc.connect(config['mqtt']['host'], config['mqtt']['port'], 60)
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
                    mqttc.publish(topic, payload=payload, retain=True)
