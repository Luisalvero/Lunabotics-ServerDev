package main

import (
    "encoding/binary"
    "hash/crc32"
)

// MaxPacketSize is the maximum allowed payload size (in bytes) for a single packet.
// Other parts of the program can modify this variable if a different maximum is needed.
var MaxPacketSize = 8192

// ComputeCRC computes CRC-32 (IEEE polynomial 0x04C11DB7) for the given data.
func ComputeCRC(data []byte) uint32 {
    return crc32.ChecksumIEEE(data)
}

// AppendCRC appends a 4-byte big-endian CRC to the end of data and returns the new slice.
func AppendCRC(data []byte) []byte {
    crc := ComputeCRC(data)
    out := make([]byte, len(data)+4)
    copy(out, data)
    binary.BigEndian.PutUint32(out[len(data):], crc)
    return out
}

// VerifyPacket verifies a packet that is structured as: payload (len bytes) followed by 4-byte CRC.
// It returns the payload (a slice copy) and whether the CRC matched.
func VerifyPacket(payloadWithCRC []byte) (payload []byte, ok bool) {
    if len(payloadWithCRC) < 4 {
        return nil, false
    }
    payloadLen := len(payloadWithCRC) - 4
    payload = make([]byte, payloadLen)
    copy(payload, payloadWithCRC[:payloadLen])
    expected := binary.BigEndian.Uint32(payloadWithCRC[payloadLen:])
    return payload, ComputeCRC(payload) == expected
}
