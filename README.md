# PyALTO

The Application-Layer Traffic Optimization ([ALTO](https://tools.ietf.org/html/rfc7285)) server implemented in Python3.

## Description

This is open-source ALTO server implementation. It can be used to provide network topology and data routing cost information to its users.
The project is split into the Server and Collector parts. See below for the description of each.

## ALTO Server

The ALTO Server is the main part of the project. It implementes the ALTO protocol as described by the RFC7285.
Server part alone is enough to implement a minimal version of the ALTO server. 
Such minimal server can be used to provide a pre-configured network topology information.

## Data Collectors

To make ALTO server more feature-rich, network data collectors can be deployed in the virtual network devices.
Data collectors run in the virtual network devices and periodically report counter values of network adapter(s) and the contents of the routers routing table.
