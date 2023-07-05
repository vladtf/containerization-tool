# Implementation

## Table of Contents

- [Implementation](#implementation)
  - [Table of Contents](#table-of-contents)
  - [Scope](#scope)
  - [Design](#design)
  - [Flows](#flows)
  - [Mockup](#mockup)
  - [Monitoring](#monitoring)
  - [Traffic Forwarding](#traffic-forwarding)
  - [Web Interface](#web-interface)
  - [Backend](#backend)
  - [Things to think about](#things-to-think-about)

## Scope

This document is intended to provide a description of the implementation of the Containerization Tool.

## Design

![](svg/containerization-tool-design.drawio.svg)

## Flows

![](svg/general-flow.svg)


## Mockup

Traffic Page:

![](svg/traffic-page-mockup.drawio.svg)

Forwarding Page:

![](svg/forwarding-page-mockup.drawio.svg)

## Monitoring

Implemented using Python because of pyshark library which is a wrapper for tshark.
Pyshark provides a simple interface to capture packets from a network interface.

The script capture the traffic of the container and save it in Kafka.

To be scalable the script will be multi-process and only for the same container multi-thread.

It may also be extended to extract the forwaring rules.

## Traffic Forwarding

Not implemented yet.

May be also an python script that will get instructions from the backend and configure the forwarding rules.

iptables may be used to configure the forwarding rules (not sure yet because iptables might not work in a container).

Also may be implemented using Docker Network Configuration.

## Web Interface

Implemented using React.

Communicate with the backend using REST API (may be to change to other protocol because of the often updates of the traffic).

## Backend

Implemented using Java Spring Boot.

Communicate with the frontend using REST API. Probably to be migrated to Webflux to improve the performance using
non-blocking IO.

Should be able to tell the frontend when to update the displayed data.

Will response of collecting data from the scripts and provide it to the frontend. Also should be able to tell the scripts
how to update the forwarding rules.


## Things to think about

* how backend will tell frontend to update the data?
* how backend will tell scripts to update the forwarding rules?
* is it possible to use iptables in a container?
* how to handle multiple containers?