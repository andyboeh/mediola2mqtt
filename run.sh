#!/usr/bin/with-contenv bashio

#declare variables
declare  mediola_host
declare  mediola_udp_port
declare  mqtt_host
declare  mqtt_port
declare  mqtt_username
declare  mqtt_password
declare  mqtt_discovery_prefix
declare  mqtt_topic
declare  mqtt_debug
declare  buttons
declare  blinds

#map values from configuration into variables
mediola_host=$(bashio::config 'mediola.host')
mediola_udp_port=$(bashio::config 'mediola.udp_port')
mqtt_host=$(bashio::config 'mqtt.host')
mqtt_port=$(bashio::config 'mqtt.port')
mqtt_username=$(bashio::config 'mqtt.username')
mqtt_password=$(bashio::config 'mqtt.password')
mqtt_discovery_prefix=$(bashio::config 'mqtt.discovery_prefix')
mqtt_topic=$(bashio::config 'mqtt.topic')
mqtt_debug=$(bashio::config 'mqtt.debug')
buttons=$(bashio::config 'buttons')
blinds=$(bashio::config 'blinds')


#export variables, so python can reach them
export  mediola_host
export  mediola_udp_port
export  mqtt_host
export  mqtt_port
export  mqtt_username
export  mqtt_password
export  mqtt_discovery_prefix
export  mqtt_topic
export  mqtt_debug
export  buttons
export  blinds

python3 -u ./mediola2mqtt.py