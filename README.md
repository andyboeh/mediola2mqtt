# mediola2mqtt - a mediola MQTT gateway

This utility is a simple python script to attach a few components of the 
Mediola AIO gateway to HomeAssistant or other MQTT capable hosts.

## Supported gateways

  * Mediola AIO gateway v4/v4+
  
Reported to work:

  * Mediola AIO gateway v6

## Supported devices

Currently, the following devices are supported/tested:

  * Intertechno push buttons
  * Somfy RTS Blinds
  * Elero Blinds

If you want another device supported by Mediola to be controllable through
this script, create an issue on github.

## Installation

If you run Home Assistant OS (HassOS), you can run it as an addon. Simply create
a new folder "mediola2mqtt" in your local "addons" folder and copy the contents
of the repository there. All configuration is performed within the add-on configuration.

If you do not run HassOS, the configuration is done in `mediola2mqtt.yaml`.

## Usage

Configure your devices in the file mediola2mqtt.yaml / add-on configuration - have
a look at mediola2mqtt.yaml.example for the syntax. If you have MQTT autodiscovery
enabled in your HomeAssistant platform, then the devices will appear automagically.

The devices need to be known to the Gateway in advance, you need IQONTROL or
AIO Creator Neo for the initial configuration. Some steps, like configuring
Elero blinds, can also be performed by running `mediolamanager.py`.

You can retrieve a list of all
known devices by calling `http://mediola.lan/command?XC_FNC=GetStates` in a 
browser. Check for `type` and `adr` fields. Please make sure to define all addresses,
especially for Elero devices, in decimal notation, not Hex! 0F becomes 15 in the
configuration file!

## Multiple Mediola Gateways

The add-on supports connecting to and managing several Gateways. However,
due to limitations in the docker architecture, this is only supported when running
standalone and not in add-on mode.

If you need to enable multiple devices, you need to add an ID to each Mediola
configured and assign the same ID to the buttons and blinds for this Mediola
interface. This is necessary for sending commands to the "correct" Mediola.

## How it works

The Mediola AIO Gateway supports a simple HTTP API for control and broadcasts
status changes via UDP on port 1902 (1901 for v6). The script provides a UDP socket server
that listens for the status changes, interprets them and publishes them via MQTT.
This is useful for buttons/switches, but can also be used for the state
of a blind (only implemented for Elero).

Controlling a blind or other device is done via HTTP, by interpreting MQTT messages
and triggering the HTTP API.
