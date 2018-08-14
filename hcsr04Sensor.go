package main

import (
	"time"

	"github.com/stianeikeland/go-rpio"
)

type UltrasonicSensor interface {
	MeasureDistance() (cm float32)
}

type HCSR04 struct {
	echoPin RaspberryPiPin
	pingPin RaspberryPiPin
}

func NewHCSR04Sensor(pingPin int, echoPin int) UltrasonicSensor {

	hcsr04 := new(HCSR04)
	hcsr04.pingPin = NewRaspberryPiPin(pingPin)
	hcsr04.echoPin = NewRaspberryPiPin(echoPin)

	return hcsr04
}

func (hcsr04 *HCSR04) MeasureDistance() (cm float32) {
	hcsr04.initPins()

	hcsr04.pingPin.WriteState(rpio.High)
	time.Sleep(time.Microsecond * 15)
	hcsr04.pingPin.WriteState(rpio.Low)

	for i := 0; hcsr04.echoPin.ReadState() == rpio.Low; i++ {
	}
	startTime := time.Now()
	for hcsr04.echoPin.ReadState() == rpio.High {
	}
	endTime := time.Now()

	distance := float32(endTime.UnixNano()-startTime.UnixNano()) / float32(58*time.Microsecond)
	return distance
}
func (hcsr04 *HCSR04) initPins() {
	hcsr04.echoPin.SetMode(rpio.Output)
	hcsr04.pingPin.SetMode(rpio.Output)
	hcsr04.echoPin.WriteState(rpio.Low)
	hcsr04.pingPin.WriteState(rpio.Low)
	time.Sleep(time.Microsecond)
	hcsr04.echoPin.SetMode(rpio.Input)
}
