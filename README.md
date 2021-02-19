# mediola2mqtt - a mediola MQTT gateway

This utility is a simple python script to attach a few components of the 
Mediola AIO gateway to HomeAssistant or other MQTT capable hosts.

## Supported gateways

  * Mediola AIO gateway v4

## Supported devices

Currently, the following devices are supported/tested:

  * Intertechno push buttons
  * Somfy RTS Blinds
  * Elero Blinds

## Installation

If you run Home Assistant OS (HassOS), you can run it as an addon. Simply create
a new folder "mediola2mqtt" in your local "addons" folder and copy the contents
of the repository there. Then, copy the file `mediola2mqtt.yaml.example` to the "config" directory
as `mediola2.mqtt.yaml` and adapt it to your needs. All configuration is
performed in this file.

## Usage

Configure your devices in the file mediola2mqtt.yaml - have a look at mediola2mqtt.yaml.example
for the syntax. If you have MQTT autodiscovery enabled in your HomeAssistant platform,
then the devices will appear automagically. 

The devices need to be known to the Gateway in advance, you need IQONTROL or
AIO Creator Neo for the initial configuration. You can retrieve a list of all
known devices by calling `http://mediola.lan/command?XC_FNC=GetStates` in a 
browser. Check for `type` and `adr` fields.

## How it works

The Mediola AIO Gateway v4 supports a simple HTTP API for control and broadcasts
status changes via UDP on port 1902. The script provides a UDP socket server
that listens for the status changes, interprets them and publishes them via MQTT.
This is useful for buttons/switches, but could also be used for the state
of a blind (not yet implemented).

Controlling a blind or other device is done via HTTP, by interpreting MQTT messages
and triggering the HTTP API.
