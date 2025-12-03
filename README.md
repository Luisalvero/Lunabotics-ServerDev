# Lunabotics-ServerDev  
High-Performance Telemetry & Control Server for FIU Lunabotics  
Author: **Luis Alvero** **Josselin Gallardo**
Status: Actively Developed  
Languages: **Go**, **Python (prototyping)**  
Subsystems: Telemetry, Command Routing, Data Serialization, Microcontroller Packet Protocols

---

##  Overview

**Lunabotics-ServerDev** is a high-performance telemetry + command server built for the **FIU Lunabotics Team**.  
It handles communication between:

- The **robot's microcontroller** (embedded systems)
- The **local server** (Go backend)
- The **ground control interface** (clients, dashboards, test tools)

This project replaces an early Python prototype with a **faster, more reliable, more scalable Go implementation** designed for real-time robotic control.

The server manages:

- Continuous multi-stream **telemetry ingestion**
- **Bidirectional command routing** (client → robot → client)
- Verified **packet serialization**
- **CRC-based integrity checking**
- Modular **multi-device support**
- A **mock client** for simulation and stress-testing the communication stack

This repository documents the protocol, implementation, and architecture used by the FIU Lunabotics robotics control system.

---

##  Motivation

The original Python implementation served as a functional prototype but presented limits:

- Latency spikes during multi-threaded telemetry bursts  
- Weak concurrency safety  
- Harder scaling as microcontroller packet formats evolved  
- Limited serialization/packet-validation structure  

To support the team's **autonomous navigation**, **sensor fusion**, and **motor-control subsystems**, the backend needed to be:

- More deterministic  
- Lower latency  
- Strongly typed  
- Easier to maintain  
- More resilient to packet failures

**Go (Golang)** was chosen for:

- Built-in concurrency (goroutines + channels)
- High throughput network I/O
- Strong struct typing for packet definitions
- Easier observability + logging
- Clean modularity

---

The server functions as the **central nervous system** of the robot:

- **Receives real-time telemetry** (IMU, motors, environment sensors)
- **Forwards commands** from ground control to the robot
- **Ensures packet integrity** via validation + CRC
- **Maintains structured device profiles**
- **Supports simulation** via the built-in mock client

---

## Features

###  Real-Time Telemetry Parsing  
Supports continuous sensor data streams with low latency.

###  Command Routing  
Client → Server → Robot → Server → Client  
Every packet includes metadata for direction + target device.

###  Mock Client (Simulation)  
Allows testing without physical hardware.  
Simulates:

- packet streams  
- random noise  
- malformed payloads  
- latency spikes  

Useful for verifying system stability.

###  Configurable Device Registry  
JSON-based configuration:

- device types  
- packet formats  
- allowed commands  
- safety limits  

###  Structured Packet Serialization  
Every packet follows:
[header][device_id][type][payload][crc]


This prevents:

- corrupted packets  
- buffer misalignment  
- inconsistent telemetry fields  

###  Logging & Debug Information  
All telemetry and commands can be logged for:

- replay  
- ML/analytics  
- debugging  
- post-run reconstruction  

---

## Installation

### **Prerequisites**
- Go 1.20+
- (Optional) Python for the prototype & testing scripts
- Serial or UDP connection to robot microcontroller

### **Build**
go build -o lunaserver main.go

### **Run**
./lunaserver

### **Clone the Repo**
```sha
git clone https://github.com/Luisalvero/Lunabotics-ServerDev
cd Lunabotics-ServerDev
```
