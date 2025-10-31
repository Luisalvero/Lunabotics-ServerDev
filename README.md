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
- Reads controller input from `/dev/input/js0` using the `github.com/0xcafed00d/joystick` library.  
- Normalizes raw axis and button values to an 8-bit (0–255) scale.  
- Encodes controller state into JSON and sends it to the server at approximately **33 Hz** (SEND_RATE_HZ).  
- Reconnects automatically if the server or controller disconnects.

#### **Server (server.go)**
- Listens for incoming TCP connections (default: `localhost:8080`).  
- Parses the JSON-encoded controller states.  
- Formats each state into an Arduino-compatible byte packet according to a **JSON configuration file** (`byte_config.json` or `byte_config_8byte.json`).  
- Transmits packets through the serial interface (`/dev/ttyACM0`) to the rover’s Arduino or control board.  
- If no serial device is connected, the system remains in debug mode and logs packets to the console.

#### **Mock Client (mock_client.go)**
- Generates synthetic joystick data at the same 33 Hz rate.
- Can send either **deterministic sine-wave test patterns** or **randomized input values** to emulate controller activity.
- Allows testing of packet formatting and network performance without physical hardware.

#### **Test Harness (test_byte_formatter.py)**
- Python test script used to validate byte-format compatibility between the original Python `RoverState` and the new Go `ByteFormatter` implementation.
- Ensures that identical inputs produce matching byte sequences for all supported configurations.

---

## Directory Layout

```
Lunabotics-ServerDev/
├── client.go
├── server.go
├── mock_client.go
├── test_byte_formatter.py
├── byte_config.json
├── byte_config_8byte.json
├── config_example.json
└── go.mod / go.sum
```

---

## Configuration System

The byte-format layout is fully configurable via JSON.  
Each element of the `"bytes"` array defines how one byte in the packet is constructed.

### Example: 6-byte Python-compatible format
```json
{
  "output_size": 6,
  "bytes": [
    {
      "type": "bits",
      "bits": [
        {"pos": 0, "field": "W"},
        {"pos": 1, "field": "E"},
        {"pos": 2, "field": "S"}
      ]
    },
    {"type": "field", "field": "LjoyX"},
    {"type": "field", "field": "LjoyY"},
    {"type": "field", "field": "RjoyY"},
    {"type": "field", "field": "RT"},
    {
      "type": "bits",
      "bits": [
        {"pos": 5, "field": "LB"},
        {"pos": 6, "field": "RB"},
        {"pos": 7, "field": "N"}
      ]
    }
  ]
}
```

### Example: Extended 8-byte format
```json
{
  "output_size": 8,
  "bytes": [
    {"type": "const", "value": 255},
    {
      "type": "bits",
      "bits": [
        {"pos": 0, "field": "N"},
        {"pos": 1, "field": "E"},
        {"pos": 2, "field": "S"},
        {"pos": 3, "field": "W"},
        {"pos": 4, "field": "LB"},
        {"pos": 5, "field": "RB"},
        {"pos": 6, "field": "SELECT"},
        {"pos": 7, "field": "START"}
      ]
    },
    {"type": "field", "field": "LjoyX"},
    {"type": "field", "field": "LjoyY"},
    {"type": "field", "field": "RjoyX"},
    {"type": "field", "field": "RjoyY"},
    {"type": "field", "field": "RT"},
    {"type": "const", "value": 255}
  ]
}
```

Both files can be switched dynamically by starting the server with:
```bash
./lunabotics-server -config byte_config.json
# or
./lunabotics-server -config byte_config_8byte.json
```

---

## Build Instructions

### Prerequisites
- Fedora or Linux distribution with Go ≥ 1.22
- DualShock 4 controller connected via USB
- (Optional) Arduino or compatible serial interface

Install dependencies:
```bash
sudo dnf install golang joystick -y
go mod tidy
```

### Build
```bash
go build -o lunabotics-server server.go
go build -o lunabotics-client client.go
```

Optional build script:
```bash
chmod +x build.sh
./build.sh
```

---

## Operation

### 1. Start the Server
```bash
./lunabotics-server -config byte_config.json
```
Example output:
```
2025/10/30 21:43:23 Loaded config: 6 bytes output
2025/10/30 21:43:23 Server listening on localhost:8080
```

If the Arduino is not connected:
```
Arduino not connected: no such file or directory (debug mode)
```
Packets will still be printed for validation.

---

### 2. Start the Client
Connect your controller, then run:
```bash
./lunabotics-client
```
Example output:
```
2025/10/30 21:43:42 Controller found: Sony DualShock 4
2025/10/30 21:43:42 Connected to server
```

Move the joysticks and observe the live packet output on the server:
```
Arduino bytes: [A8 97 FC 67 E9 95]
```

---

## Testing Without Hardware

To validate system performance or packet encoding without a controller:
```bash
go run mock_client.go
# or with randomized test data
go run mock_client.go -random
```

Expected server output:
```
State: &{1 1 0 0 0 0 0 0 0 0 152 252 0 102 0 233 0 0 1761875025920}
Arduino bytes: [AA 98 FC 66 E9 95]
```

---

## Packet Verification (Python Test Harness)

To confirm Go and Python parity:
```bash
python3 test_byte_formatter.py --config byte_config.json
```
This runs a suite of reference tests to ensure identical output to the original `RoverState` logic.

Example:
```
Test 1:
  Go formatted   : ['0xA8', '0x7F', '0x7F', '0x7F', '0x00', '0x15']
  Python expected: ['0xA8', '0x7F', '0x7F', '0x7F', '0x00', '0x15']
All tests passed!
```

---

## Hardware Integration Notes

- The default serial target (`/dev/ttyACM0`, 9600 baud) corresponds to the Arduino used in the rover’s control module.
- The Go server can be reconfigured to write to any device by modifying `ARDUINO_PORT` in `server.go`.
- During lab or field operations, the system can run entirely over Ethernet or a Wi-Fi tether between the control station and rover compute unit.
- The modular configuration allows adaptation to new communication boards or higher-resolution control systems without code changes.

---

## Safety and Performance

- The system runs at **33 Hz** to ensure smooth rover response while minimizing network congestion.  
- Each JSON packet is lightweight (< 250 bytes).  
- Serial transmission uses buffered writes with timeout protection.  
- In case of link loss, the rover’s microcontroller can implement a safety timeout on command receipt to halt motion.

---

## Summary

| Component | Description | Language | Frequency |
|------------|--------------|-----------|------------|
| `lunabotics-client` | Reads and sends joystick data | Go | 33 Hz |
| `lunabotics-server` | Formats data and sends to Arduino | Go | 33 Hz |
| `mock_client` | Simulated input generator | Go | 33 Hz |
| `test_byte_formatter.py` | Validation against Python reference | Python | On demand |

---

## Next Steps

- Integrate telemetry feedback channels (sensor data to operator station).  
- Add UDP broadcast mode for multi-client monitoring.  
- Explore higher-frequency or adaptive packet modes for high-precision arm control.  
- Deploy to rover compute unit (Raspberry Pi 4 / Jetson Nano) and field-test serial response latency.

---
