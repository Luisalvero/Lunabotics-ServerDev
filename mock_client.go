package main

import (
	"encoding/json"
	"flag"
	"fmt"
	"math"
	"math/rand"
	"net"
	"time"
)

// Must match server.go's JSON field names
type ControllerState struct {
	North       uint8 `json:"N"`
	East        uint8 `json:"E"`
	South       uint8 `json:"S"`
	West        uint8 `json:"W"`
	LeftBumper  uint8 `json:"LB"`
	RightBumper uint8 `json:"RB"`
	LeftStick   uint8 `json:"LS"`
	RightStick  uint8 `json:"RS"`
	Select      uint8 `json:"SELECT"`
	Start       uint8 `json:"START"`

	LeftX        uint8 `json:"LjoyX"`
	LeftY        uint8 `json:"LjoyY"`
	RightX       uint8 `json:"RjoyX"`
	RightY       uint8 `json:"RjoyY"`
	LeftTrigger  uint8 `json:"LT"`
	RightTrigger uint8 `json:"RT"`
	DPadX        int8  `json:"dX"`
	DPadY        int8  `json:"dY"`

	Timestamp int64 `json:"ts"`
}

// simple wave 0..255 centered on 127 for pretty output
func wave(t float64, phase float64) uint8 {
	s := 0.5 + 0.5*math.Sin(2*math.Pi*(t+phase))
	return uint8(s * 255.0)
}

func main() {
	server := flag.String("server", "127.0.0.1:8080", "server address host:port")
	hz := flag.Float64("hz", 33, "send frequency")
	random := flag.Bool("random", false, "send random values instead of smooth wave")
	flag.Parse()

	conn, err := net.Dial("tcp", *server)
	if err != nil {
		panic(err)
	}
	defer conn.Close()
	fmt.Println("Connected to", *server)

	ticker := time.NewTicker(time.Duration(float64(time.Second) / *hz))
	defer ticker.Stop()
	start := time.Now()

	enc := json.NewEncoder(conn) // newline-delimited JSON objects

	for range ticker.C {
		elapsed := time.Since(start).Seconds()

		var lx, ly, ry, rt uint8
		if *random {
			lx = uint8(rand.Intn(256))
			ly = uint8(rand.Intn(256))
			ry = uint8(rand.Intn(256))
			rt = uint8(rand.Intn(256))
		} else {
			lx = wave(elapsed, 0.00)  // LjoyX
			ly = wave(elapsed, 0.25)  // LjoyY
			ry = wave(elapsed, 0.50)  // RjoyY
			rt = wave(elapsed, 0.125) // RT
		}

		state := ControllerState{
			// flip some buttons occasionally so you see bit changes
			North:       uint8((int(elapsed) / 2) % 2),
			East:        uint8((int(elapsed) / 3) % 2),
			South:       uint8((int(elapsed) / 5) % 2),
			West:        uint8((int(elapsed) / 7) % 2),
			LeftBumper:  uint8((int(elapsed) / 4) % 2),
			RightBumper: uint8((int(elapsed) / 6) % 2),

			LeftX:        lx,
			LeftY:        ly,
			RightY:       ry,
			RightTrigger: rt,

			Timestamp: time.Now().UnixMilli(),
		}

		if err := enc.Encode(&state); err != nil {
			fmt.Println("encode error:", err)
			return
		}
	}
}
