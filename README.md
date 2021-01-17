# FanController

## Introduction

The FanController module provides a registration point for hardware fan drivers
to register with. This repository contains:

* The documentation of the API (see FanController/prminxml/fancontroller.xml)
* An implementation of the FanController (see FanController)
* An example driver module (see FanDriverDummy)
* Pyromaniac PyModules providing the original implementation (see Pyromaniac)

The CI will build the modules and the documentation.

## Dummy driver module

The Dummy driver module is implemented such that it provides an example of how to
communicate with the FanController module. It should be possible to update the
driver module to communicate with hardware by updating the c/fan code with the
necessary communication with the hardware, and the c/fans code to register the
fans.
