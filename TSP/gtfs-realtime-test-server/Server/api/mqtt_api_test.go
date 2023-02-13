package api_test

import (
	"bytes"
	"encoding/base64"
	"encoding/binary"
	"fmt"
	"net/http"
	"testing"
	"time"

	"github.com/gtt/gtfs-realtime-test-server/Server/mqtt"
)

func TestMQTTAPI(t *testing.T) {
	tests := map[string][]TestStep{
		"/mqtt returns empty map by default": {
			{
				Request: SimpleGet("/mqtt"),
				ExpectedJSON: func() (any, error) {
					return map[string]any{}, nil
				},
			},
		},
		"/mqtt test": {
			addMQTTMessage(0, mqtt.MQTTMessage{
				Topic: "abc/foo/45.12L,-100.45H",
				Payload: mqtt.Payload{
					VehSN: 123,
				},
			}),
			addMQTTMessage(time.Millisecond*10, mqtt.MQTTMessage{
				Topic: "abc/bar/123,456",
				Payload: mqtt.Payload{
					VehGPSLat_ddmmmmmm: 456,
				},
			}),
			addMQTTMessage(time.Millisecond*10, mqtt.MQTTMessage{
				Topic: "abc/baz/mylatlon",
				Payload: mqtt.Payload{
					VehGPSLon_dddmmmmmm: 789,
				},
			}),
			{
				Request: SimpleGet("/mqtt"),
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"abc/foo/45.12L,-100.45H": map[string]any{
							"topic": "abc/foo/45.12L,-100.45H",
							"payload": map[string]any{
								"conditionalPriority": float64(0),
								"padding1":            float64(0),
								"padding2":            float64(0),
								"vehCityID":           float64(0),
								"vehClass":            float64(0),
								"vehDiagValue":        float64(0),
								"vehGPSCStat":         float64(0),
								"vehGPSHdg_deg2":      float64(0),
								"vehGPSLat_ddmmmmmm":  float64(0),
								"vehGPSLon_dddmmmmmm": float64(0),
								"vehGPSSatellites":    float64(0),
								"vehGPSVel_mpsd5":     float64(0),
								"vehModeOpTurn":       float64(0),
								"vehRSSI":             float64(0),
								"vehSN":               float64(123),
								"vehVehID":            float64(0),
							},
						},
						"abc/bar/123,456": map[string]any{
							"topic": "abc/bar/123,456",
							"payload": map[string]any{
								"conditionalPriority": float64(0),
								"padding1":            float64(0),
								"padding2":            float64(0),
								"vehCityID":           float64(0),
								"vehClass":            float64(0),
								"vehDiagValue":        float64(0),
								"vehGPSCStat":         float64(0),
								"vehGPSHdg_deg2":      float64(0),
								"vehGPSLat_ddmmmmmm":  float64(456),
								"vehGPSLon_dddmmmmmm": float64(0),
								"vehGPSSatellites":    float64(0),
								"vehGPSVel_mpsd5":     float64(0),
								"vehModeOpTurn":       float64(0),
								"vehRSSI":             float64(0),
								"vehSN":               float64(0),
								"vehVehID":            float64(0),
							},
						},
						"abc/baz/mylatlon": map[string]any{
							"topic": "abc/baz/mylatlon",
							"payload": map[string]any{
								"conditionalPriority": float64(0),
								"padding1":            float64(0),
								"padding2":            float64(0),
								"vehCityID":           float64(0),
								"vehClass":            float64(0),
								"vehDiagValue":        float64(0),
								"vehGPSCStat":         float64(0),
								"vehGPSHdg_deg2":      float64(0),
								"vehGPSLat_ddmmmmmm":  float64(0),
								"vehGPSLon_dddmmmmmm": float64(789),
								"vehGPSSatellites":    float64(0),
								"vehGPSVel_mpsd5":     float64(0),
								"vehModeOpTurn":       float64(0),
								"vehRSSI":             float64(0),
								"vehSN":               float64(0),
								"vehVehID":            float64(0),
							},
						},
					}, nil
				},
			},
			{
				Request: SimpleGet("/mqtt?age=0.02"),
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"abc/bar/123,456": map[string]any{
							"topic": "abc/bar/123,456",
							"payload": map[string]any{
								"conditionalPriority": float64(0),
								"padding1":            float64(0),
								"padding2":            float64(0),
								"vehCityID":           float64(0),
								"vehClass":            float64(0),
								"vehDiagValue":        float64(0),
								"vehGPSCStat":         float64(0),
								"vehGPSHdg_deg2":      float64(0),
								"vehGPSLat_ddmmmmmm":  float64(456),
								"vehGPSLon_dddmmmmmm": float64(0),
								"vehGPSSatellites":    float64(0),
								"vehGPSVel_mpsd5":     float64(0),
								"vehModeOpTurn":       float64(0),
								"vehRSSI":             float64(0),
								"vehSN":               float64(0),
								"vehVehID":            float64(0),
							},
						},
						"abc/baz/mylatlon": map[string]any{
							"topic": "abc/baz/mylatlon",
							"payload": map[string]any{
								"conditionalPriority": float64(0),
								"padding1":            float64(0),
								"padding2":            float64(0),
								"vehCityID":           float64(0),
								"vehClass":            float64(0),
								"vehDiagValue":        float64(0),
								"vehGPSCStat":         float64(0),
								"vehGPSHdg_deg2":      float64(0),
								"vehGPSLat_ddmmmmmm":  float64(0),
								"vehGPSLon_dddmmmmmm": float64(789),
								"vehGPSSatellites":    float64(0),
								"vehGPSVel_mpsd5":     float64(0),
								"vehModeOpTurn":       float64(0),
								"vehRSSI":             float64(0),
								"vehSN":               float64(0),
								"vehVehID":            float64(0),
							},
						},
					}, nil
				},
			},
			{
				Request: SimpleGet("/mqtt?topic=abc/foo/45.12L,-100.45H&topic=abc/baz/mylatlon"),
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"abc/foo/45.12L,-100.45H": map[string]any{
							"topic": "abc/foo/45.12L,-100.45H",
							"payload": map[string]any{
								"conditionalPriority": float64(0),
								"padding1":            float64(0),
								"padding2":            float64(0),
								"vehCityID":           float64(0),
								"vehClass":            float64(0),
								"vehDiagValue":        float64(0),
								"vehGPSCStat":         float64(0),
								"vehGPSHdg_deg2":      float64(0),
								"vehGPSLat_ddmmmmmm":  float64(0),
								"vehGPSLon_dddmmmmmm": float64(0),
								"vehGPSSatellites":    float64(0),
								"vehGPSVel_mpsd5":     float64(0),
								"vehModeOpTurn":       float64(0),
								"vehRSSI":             float64(0),
								"vehSN":               float64(123),
								"vehVehID":            float64(0),
							},
						},
						"abc/baz/mylatlon": map[string]any{
							"topic": "abc/baz/mylatlon",
							"payload": map[string]any{
								"conditionalPriority": float64(0),
								"padding1":            float64(0),
								"padding2":            float64(0),
								"vehCityID":           float64(0),
								"vehClass":            float64(0),
								"vehDiagValue":        float64(0),
								"vehGPSCStat":         float64(0),
								"vehGPSHdg_deg2":      float64(0),
								"vehGPSLat_ddmmmmmm":  float64(0),
								"vehGPSLon_dddmmmmmm": float64(789),
								"vehGPSSatellites":    float64(0),
								"vehGPSVel_mpsd5":     float64(0),
								"vehModeOpTurn":       float64(0),
								"vehRSSI":             float64(0),
								"vehSN":               float64(0),
								"vehVehID":            float64(0),
							},
						},
					}, nil
				},
			},
			{
				Request: SimpleGet("/mqtt?age=0.02&topic=abc/foo/45.12L,-100.45H&topic=abc/baz/mylatlon"),
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"abc/baz/mylatlon": map[string]any{
							"topic": "abc/baz/mylatlon",
							"payload": map[string]any{
								"conditionalPriority": float64(0),
								"padding1":            float64(0),
								"padding2":            float64(0),
								"vehCityID":           float64(0),
								"vehClass":            float64(0),
								"vehDiagValue":        float64(0),
								"vehGPSCStat":         float64(0),
								"vehGPSHdg_deg2":      float64(0),
								"vehGPSLat_ddmmmmmm":  float64(0),
								"vehGPSLon_dddmmmmmm": float64(789),
								"vehGPSSatellites":    float64(0),
								"vehGPSVel_mpsd5":     float64(0),
								"vehModeOpTurn":       float64(0),
								"vehRSSI":             float64(0),
								"vehSN":               float64(0),
								"vehVehID":            float64(0),
							},
						},
					}, nil
				},
			},
		},
		"Sends error messages for bad input": {
			{
				Request: func() (*http.Request, error) {
					return http.NewRequest("POST", "http://foo.com/mqtt", bytes.NewReader([]byte(`{
						"vehicleId": "foo"
					}`)))
				},
				ExpectedStatus: 400,
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"type":    "error",
						"message": "MQTT.HandleMessage: EOF: invalid mqtt message",
					}, nil
				},
			},
		},
	}

	RunTests(t, tests)
}

func addMQTTMessage(waitTime time.Duration, mqttMsg mqtt.MQTTMessage) TestStep {
	return TestStep{
		Request: func() (*http.Request, error) {
			time.Sleep(waitTime)
			return http.NewRequest(
				"POST",
				"http://foo.com/mqtt",
				bytes.NewReader(makeRawMQTTMessage(mqttMsg)),
			)
		},
		ExpectedStatus: 200,
		ExpectedJSON: func() (any, error) {
			return map[string]any{
				"type":    "success",
				"message": "Successfully handled MQTT Message",
			}, nil
		},
	}
}

func makeRawMQTTMessage(mqttMsg mqtt.MQTTMessage) []byte {
	return []byte(fmt.Sprintf(
		`{ "topic": "%s", "payload": "%v" }`,
		mqttMsg.Topic,
		encodePayload(mqttMsg.Payload),
	))
}

func encodePayload(payload mqtt.Payload) string {
	payloadBytes := bytes.Buffer{}
	binary.Write(&payloadBytes, binary.LittleEndian, payload)
	return base64.StdEncoding.EncodeToString(payloadBytes.Bytes())
}
