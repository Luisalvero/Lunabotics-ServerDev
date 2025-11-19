# FIU Lunabotics Controller System (Go Implementation)

## Overview
The **Lunabotics Controller System** is a real-time control and telemetry layer designed to connect a human-operated controller (e.g., DualShock 4) to the rover’s microcontroller through a modular and configurable communication interface.  

This Go-based system replaces the original Python prototype while preserving identical byte-format compatibility. It introduces improved modularity, stability, and performance for research and competition operations under FIU’s NASA Lunabotics program.

The system operates as a **client-server pair**:
- The **client** runs on the operator workstation, reading live joystick data and transmitting encoded controller state packets over TCP at 33 Hz.
- The **server** runs on the rover’s compute module (or a laptop tethered via USB), converting incoming JSON packets into formatted byte streams and outputting them to the Arduino over serial.

---

## System Architecture

### Components

#### **Client (client.go)**
Lunabotics Controller — Quick Guide

This README gives concise instructions for running the server and client, explains the CRC framing used on the wire, and documents the configurable ByteFormatter templates.

Server
- Location: `server.go`.
- Purpose: listen for controller packets, verify CRC, format bytes and send to serial Arduino.
- Start (default port 8080):

  go run server.go crc.go

- To select a different port:

  go run server.go crc.go -port 18080

- Behavior:
  - Reads framed packets from TCP: 4-byte big-endian length N, then N bytes (payload + 4-byte CRC).
  - Verifies CRC before decoding JSON payload. If CRC fails, packet is dropped and logged.
  - Converts verified ControllerState JSON into Arduino bytes using `ByteFormatter` and writes to serial (`/dev/ttyACM0`) or logs in debug mode.

Client
- Location: `client.go` (real controller) and `mock_client.go` (simulated input).
- Purpose: read controller or generate test data, send JSON payloads to server.
- Sending format (on the wire):
  1) 4-byte big-endian uint32 = length (payload + 4 CRC bytes)
  2) payload bytes (JSON-marshalled ControllerState)
  3) 4-byte big-endian CRC-32 (CRC computed over the payload only)

- Example: if payload is 5 bytes, the wire will be: [00 00 00 09] [5 payload bytes] [4 CRC bytes].
- Run mock client (local server):

  go run mock_client.go crc.go -server 127.0.0.1:8080

CRC support (crc.go)
- File: `crc.go`.
- Algorithm: CRC-32 using polynomial 0x04C11DB7 (IEEE / CCITT-32). Implemented using `crc32.ChecksumIEEE`.
- API:
  - `var MaxPacketSize` — maximum payload size in bytes (default 8192). Adjust as needed.
  - `ComputeCRC([]byte) uint32` — compute CRC for a payload.
  - `AppendCRC([]byte) []byte` — returns payload with 4 CRC bytes appended (big-endian).
  - `VerifyPacket([]byte) (payload []byte, ok bool)` — given payload+crc, returns payload and whether CRC matched.

ByteFormatter templates (configurable JSON)
- The server converts JSON ControllerState into a fixed-length byte array for Arduino using `ByteFormatter` and a `ByteConfig`.
- Config structure (high level):
  - `output_size` (int): total bytes in the formatted packet.
  - `bytes` (array): list of per-byte mappings. Each entry maps one output byte and has a `type` field.

Supported byte mapping types
1) `const`
   - Fields: `value` (0-255)
   - Behavior: the output byte is the constant value.
   - Use when a fixed marker or start/end sentinel is required.

2) `field`
   - Fields: `field` (string, name of ControllerState field)
   - Behavior: output byte = value of the named field (uint8 fields are used directly).
   - Example: `{"type":"field","field":"LjoyX"}`

3) `bits`
   - Fields: `bits` (array of `{pos, field}`)
   - Behavior: construct an output byte by setting bits at positions `pos` when the corresponding ControllerState `field` is non-zero.
   - Useful for packing booleans into a single byte (buttons).
   - Example:
     {
       "type": "bits",
       "bits": [ {"pos":0, "field":"W"}, {"pos":1, "field":"E"} ]
     }

Default templates included
- `byte_config.json` — a 6-byte Python-compatible format (start byte, 4 payload bytes, end byte).
- `byte_config_8byte.json` — an 8-byte extended format (start/end constants, packed bits, and fields).

Switching templates
- Start server with `-config <file>` to load a different byte mapping config:

  go run server.go crc.go -config byte_config_8byte.json

Notes & troubleshooting
- Multi-binary layout: `client.go` and `mock_client.go` are both `package main` with `main()` in the same directory. Build them separately (or move each into `cmd/<name>/` for cleaner multi-target builds).
- If `go run server.go` fails with port in use, pick another port: `-port 18080`.
- `MaxPacketSize` guards the server from very large or malicious packet lengths; increase if you must support larger payloads, but keep memory/time constraints in mind.

Quick example: what the server receives and validates
- Client sends JSON payload (e.g. `{"N":1,...}`) → client marshals to bytes `P`.
- Client computes CRC = CRC32(P), appends as 4 big-endian bytes → packet = P || CRC
- Client prefixes total length N = len(packet) as 4-byte big-endian header and sends: [len][packet]
- Server reads [len], reads packet, splits last 4 bytes as CRC, recomputes CRC over payload, compares; if equal, processes payload.

