# Containerization Tool

## Table of Contents

- [Containerization Tool](#containerization-tool)
  - [Table of Contents](#table-of-contents)
  - [Description](#description)
  - [Documentation](#documentation)
  - [Start the Tool](#start-the-tool)
    - [Local Environment](#local-environment)
      - [Prerequisites](#prerequisites)
      - [Start-up scripts](#start-up-scripts)
      - [Start-up steps](#start-up-steps)
      - [Start the tool in Docker](#start-the-tool-in-docker)
  - [Utils](#utils)
  - [Application Structure](#application-structure)
  - [Screenshots](#screenshots)

## Description

Because most of the issue of containerization of an application comes from networking mapping,
this tool is designed to help developers to install the application in a container and run it.

By monitoring the network traffic of the application, the tool will create reports of the incoming and outgoing traffic of the application.
The developer can see the report in an web interface and decide how to map the network traffic of the application.

## Documentation

- [Similar Tools](documentation/similar-tools.md)
- [Implementation](documentation/implementation.md)

## Start the Tool

### Local Environment

#### Prerequisites

> Following prerequisites are required to run the tool locally and were tested during development.

1. Os: *Ubuntu 23.04*

2. Bash:

> TODO: to add bash requirements as a table

3. Pyton Version:
```bash
❯ python --version
Python 3.11.2
```

6. Docker:
```bash
❯ docker --version
Docker version 25.0.2, build 29cf629

❯ docker-compose --version
docker-compose version 1.29.2, build unknown
```

#### Start-up scripts

- prepare.sh:
  - create a virtual environment and install the required dependencies
  - export the required environment variables
  - define bash log functions
  - export some useful bash aliases

- quick-start.sh:
  - starts docker-compose with the required containers (kafka, zookeeper, mysql, fluentd)
  - create the network for the containers deployed by the tool
  - create a first test container in that network

- start-all.sh:
  - starts a tmux session with the required windows
  - run `start-containers-manager.sh` - starts the containers manager python script
  - run `start-monitoring-forwarding-rules.sh` - starts the monitoring and forwarding rules python script
  - run `start-monitoring-traffic.sh` - starts the monitoring traffic python script
  - TODO: to add a window for the azure backend server

- clean.sh:
  - stop docker-compose
  - remove all the containers linked to tool network
  - remove the network
  - stop frontend and backend servers



#### Start-up steps

1. Prepare the environment (it should be sourced when running any of the other scripts, the source is checked)
```bash
source prepare.sh
```

2. Start the required containers
```bash
./quick-start.sh
```

3. Start monitoring scripts
```bash
./start-all.sh
```

4. Start the frontend server
```bash
cd frontend

npm install
npm start
```

5. Start the backend server
```bash
cd backend
mvn spring-boot:run
```

6. Start Azure backend server
```bash
cd monitoring
export FLASK_APP=azure-backend
flask run
```

7. Azure setup: TODO

#### Start the tool in Docker

TODO: to create a single docker compose file that will start all the containers required by the tool to work e2e


## Utils

Directory [util](util) contains some useful scripts that can be used to see how some features of the tool work.

## Application Structure

<img src="documentation/svg/containerization-tool-design.drawio.svg" width="100%">

## Screenshots

Home Page:

<img src="documentation/screenshots/home-page.jpeg" width="50%">

Containers Page:

<img src="documentation/screenshots/containers-page.jpeg" width="50%">


Forwarding Rules Page:

<img src="documentation/screenshots/forwarding-page.jpeg" width="50%">

Messages Page:

<img src="documentation/screenshots/messages-page.jpeg" width="50%">

Azure Page:

<img src="documentation/screenshots/azure_page.png" width="50%">
