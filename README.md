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

## Usage

Configure your devices in the file config.yaml - have a look at config.yaml.example
for the syntax. If you have MQTT autodiscovery enabled in your HomeAssistant platform,
then the devices will appear automagically. 
