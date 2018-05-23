# testbed
This repository holds the source code for deploying testbed based on MQTT

# Project Architecture

In this project we are going to have 20 boxes, each one has one Raspberry Pi and 4 OpenMots. All of them are connected to the internet and will interact with the user's machine using the MQTT protocol. For that we have to define some "topics" and notation.

## Notation

### Boxes

To identify a box, the id for each one has the following format:

	rpi_XX

Where "XX" is a serial number, in our case from 01 to 20.

### Mots

To identify a mot in a box, the id for each mot has the following format:

	mot_YY

Where "YY" is a number from 01 to 04.

### Commands and responses

Each command has a command id (**cmd_id**), and each response corresponds to a command, so the response id is like: **rsp_cmd_id**

## Topics

The system has two principal types of topics, the command topics and the response topics. The client, who is running in the boxes, is subscribed to the command topics and publish in the response topics, for the user is the opposite.

### Dealing with Mots

When the user wants to send a command to a mot, the topic where we have to publish has the following format:

	testbed/rpi_XX/mot_YY/cmd/cmd_id

To receive the response, the topic in which the user have to be subscribed has the following format:

	testbed/rpi_XX/mot_YY/rsp/rsp_cmd_id

#### Commands id for Mots

1. flash: the box should have the new firmware, it could be using git or just sending the file.
2. reset:
3. getSerialOutput: 
4. getMacAddr:

### Dealing with boxes

There is also the option to send the same command to all the mots connected to a Raspberry Pi or others specific commands for the Raspberry. To do that the topic where the user's machine has to publihs has the following format:

	testbed/rpi_XX/cmd/cmd_id

To receive the response the topic to subscribe should has the following format:

	testbed/rpi_XX/rsp/rsp_cmd_id

#### Commands id for boxes

1. The same Mots command: In this case the 4 mots of the box will execute the same command. (getSerialOutput?)
	* For the getMacAddr command, the client have to send the MAC address with her corresponding Mot id (mot_YY)
2. setImage: Send the image link or send image file
3. getLocation?

### Dealing with the whole system

When the user wants that all the boxes execute the same command, he had to publish to a topic with the following format:

	testbed/cmd/cmd_id

And to receive the information, the user's machine have to be subscribed to a topic having the following format:

	testbed/rsp/rsp_cmd_id

The commands id for the whole system are the same as for the boxes.

