"""Test harness for verifying Go Lunabotics byte formatting.

This script emulates the Go `ByteFormatter` logic in Python so you can
compare its output against the existing Python `RoverState.get_arduino_data()`
function.  It reads a byte‑mapping configuration from a JSON file, accepts
sample controller states, and prints both the Go formatted bytes and the
expected Python bytes side by side.  Use it to verify that your Go server
produces the same Arduino packet as the original Python implementation for
any number of input states.

Usage:

    python test_byte_formatter.py --config byte_config.json \
        --state '{"N":1,"E":0,"S":1,"W":0,"LB":1,"RB":0,"LjoyX":123,"LjoyY":200,"RjoyY":50,"RT":10}'

If `--state` is omitted, the script runs a few predefined test cases.
"""

import argparse
import json
from typing import Dict, Any, List


def load_config(filename: str) -> Dict[str, Any]:
    """Load the byte‑mapping configuration from a JSON file."""
    with open(filename, "r", encoding="utf-8") as f:
        return json.load(f)


def format_state(state: Dict[str, int], config: Dict[str, Any]) -> bytes:
    """Replicate the Go `ByteFormatter.Format` logic using Python data structures."""
    output_size: int = config.get("output_size", 6)
    bytes_mapping: List[Dict[str, Any]] = config.get("bytes", [])

    # Initialise output with zeros and optionally set default start/end bytes
    output: List[int] = [0] * output_size
    if output_size == 6:
        # These constants (0b10101000 and 0b00010101) come from the Python
        # RoverState.get_arduino_data() implementation.  They set reserved bits
        # in the first and last packet bytes.  The Go version preserves them
        # when applying bit masks.
        output[0] = 0b10101000
        output[-1] = 0b00010101

    for i, byte_map in enumerate(bytes_mapping):
        if i >= output_size:
            break
        t = byte_map.get("type")
        if t == "const":
            output[i] = byte_map.get("value", 0)
        elif t == "field":
            # Copy the numeric value for this field directly into the packet.
            field_name = byte_map.get("field")
            output[i] = int(state.get(field_name, 0)) & 0xFF
        elif t == "bits":
            # Build a bitmask from one or more fields.  Preserve the default
            # bits in the first and last byte when using the 6‑byte format.
            b = output[i] if (output_size == 6 and (i == 0 or i == output_size - 1)) else 0
            for bit_mapping in byte_map.get("bits", []):
                pos = int(bit_mapping.get("pos", 0))
                field_name = bit_mapping.get("field")
                if state.get(field_name, 0):
                    b |= 1 << pos
            output[i] = b & 0xFF
    return bytes(output)


def python_reference(state: Dict[str, int]) -> bytes:
    """Compute the expected Arduino packet using the original Python logic."""
    start_byte = 0b10101000
    end_byte = 0b00010101
    # Set bits based on button presses
    if state.get("S"):
        start_byte |= 0b00000100
    if state.get("E"):
        start_byte |= 0b00000010
    if state.get("W"):
        start_byte |= 0b00000001
    if state.get("N"):
        end_byte |= 0b10000000
    if state.get("RB"):
        end_byte |= 0b01000000
    if state.get("LB"):
        end_byte |= 0b00100000
    return bytes([
        start_byte,
        state.get("LjoyX", 0) & 0xFF,
        state.get("LjoyY", 0) & 0xFF,
        state.get("RjoyY", 0) & 0xFF,
        state.get("RT", 0) & 0xFF,
        end_byte,
    ])


def run_tests(config: Dict[str, Any]):
    """Run a few built‑in test cases to validate the configuration."""
    test_states = [
        # No buttons pressed, joysticks centred
        {"N": 0, "E": 0, "S": 0, "W": 0, "LB": 0, "RB": 0, "LjoyX": 127, "LjoyY": 127, "RjoyY": 127, "RT": 0},
        # All directional buttons pressed
        {"N": 1, "E": 1, "S": 1, "W": 1, "LB": 0, "RB": 0, "LjoyX": 0, "LjoyY": 0, "RjoyY": 0, "RT": 0},
        # Bumpers pressed, triggers and joysticks at extremes
        {"N": 1, "E": 0, "S": 0, "W": 0, "LB": 1, "RB": 1, "LjoyX": 255, "LjoyY": 0, "RjoyY": 255, "RT": 255},
    ]
    for idx, state in enumerate(test_states, 1):
        go_bytes = format_state(state, config)
        py_bytes = python_reference(state)
        print(f"Test {idx}:")
        print(f"  State: {state}")
        print(f"  Go formatted   : {[f'0x{b:02X}' for b in go_bytes]}")
        print(f"  Python expected: {[f'0x{b:02X}' for b in py_bytes]}")
        assert go_bytes == py_bytes, "Mismatch between Go and Python output"
    print("All tests passed!\n")


def main():
    parser = argparse.ArgumentParser(description="Validate Go byte formatting against the original Python logic")
    parser.add_argument("--config", required=True, help="Path to JSON config file (e.g., byte_config.json)")
    parser.add_argument("--state", help="JSON object with controller state values to test (overrides built‑in cases)")
    args = parser.parse_args()

    config = load_config(args.config)
    if args.state:
        state = json.loads(args.state)
        go_bytes = format_state(state, config)
        py_bytes = python_reference(state)
        print(f"State: {state}")
        print(f"Go formatted   : {[f'0x{b:02X}' for b in go_bytes]}")
        print(f"Python expected: {[f'0x{b:02X}' for b in py_bytes]}")
        if go_bytes == py_bytes:
            print("Result: PASS (outputs match)")
        else:
            print("Result: FAIL (outputs differ)")
    else:
        run_tests(config)


if __name__ == "__main__":
    main()
