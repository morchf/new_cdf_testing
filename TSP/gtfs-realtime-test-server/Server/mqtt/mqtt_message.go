package mqtt

import (
	"bytes"
	"encoding/base64"
	"encoding/binary"
	"fmt"
)

type RawMQTTMessage struct {
	Topic   string
	Payload []byte `json:"payload"`
}

func (rawMessage RawMQTTMessage) ToMQTTMessage() (MQTTMessage, error) {
	message := MQTTMessage{
		Topic: rawMessage.Topic,
	}
	payloadReader := bytes.NewReader(rawMessage.Payload)
	err := binary.Read(payloadReader, binary.LittleEndian, &message.Payload)
	if err != nil {
		return MQTTMessage{}, err
	}
	return message, nil
}

type MQTTMessage struct {
	Topic   string  `json:"topic"`
	Payload Payload `json:"payload"`
}

type Payload struct {
	VehSN   uint32 `json:"vehSN"`
	VehRSSI uint16 `json:"vehRSSI"`

	Padding1 uint16 `json:"padding1"`

	VehGPSLat_ddmmmmmm  int32  `json:"vehGPSLat_ddmmmmmm"`
	VehGPSLon_dddmmmmmm int32  `json:"vehGPSLon_dddmmmmmm"`
	VehGPSVel_mpsd5     uint8  `json:"vehGPSVel_mpsd5"`
	VehGPSHdg_deg2      uint8  `json:"vehGPSHdg_deg2"`
	VehGPSCStat         uint16 `json:"vehGPSCStat"`
	VehGPSSatellites    uint32 `json:"vehGPSSatellites"`
	VehVehID            uint16 `json:"vehVehID"`
	VehCityID           uint8  `json:"vehCityID"`
	VehModeOpTurn       uint8  `json:"vehModeOpTurn"`
	VehClass            uint8  `json:"vehClass"`
	ConditionalPriority uint8  `json:"conditionalPriority"`

	Padding2 uint16 `json:"padding2"`

	VehDiagValue uint32 `json:"vehDiagValue"`
}

func (msg MQTTMessage) Raw() []byte {
	payloadBytes := bytes.Buffer{}
	binary.Write(&payloadBytes, binary.LittleEndian, msg.Payload)
	encodedPayload := base64.StdEncoding.EncodeToString(payloadBytes.Bytes())
	return []byte(fmt.Sprintf(`{
		"topic": "%s",
		"payload": "%s"
	}`, msg.Topic, encodedPayload))
}
