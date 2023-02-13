package mqtt_test

import (
	"bytes"
	"encoding/base64"
	"encoding/binary"
	"encoding/json"
	"errors"
	"fmt"
	"strings"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/gtt/gtfs-realtime-test-server/Server/mqtt"
	"github.com/matryer/is"
)

func TestMQTTSpy(t *testing.T) {
	t.Run("Has no MQTTMessages by default", func(t *testing.T) {
		is := is.New(t)

		mqttSpy := mqtt.NewSpy()
		messages, err := mqttSpy.GetMessages(0, nil)
		is.NoErr(err)

		is.Equal(string(messages), `{}`)
	})

	t.Run("Accepts MQTTMessages", func(t *testing.T) {
		is := is.New(t)

		mqttSpy := mqtt.NewSpy()

		inputMsg := mqtt.MQTTMessage{
			Topic: "/foo/45.12L,-100.45H",
			Payload: mqtt.Payload{
				VehGPSLat_ddmmmmmm:  1234,
				VehGPSLon_dddmmmmmm: 5678,
			},
		}

		err := mqttSpy.HandleMessage(makeRawMQTTMessage(inputMsg))
		is.NoErr(err)

		expectedMessages := map[string]mqtt.MQTTMessage{
			inputMsg.Topic: inputMsg,
		}
		actualMessages, err := toMap(mqttSpy.GetMessages(0, nil))
		is.NoErr(err)

		is.Equal("", cmp.Diff(expectedMessages, actualMessages))
	})

	t.Run("Filters by given age", func(t *testing.T) {
		is := is.New(t)

		message1 := mqtt.MQTTMessage{
			Topic: "/foo/vehicle 1/bar/1.23L,4.56H",
			Payload: mqtt.Payload{
				VehGPSVel_mpsd5: 123,
			},
		}
		message2 := mqtt.MQTTMessage{
			Topic: "/foo/vehicle 2/bar/1.23L,4.56H",
			Payload: mqtt.Payload{
				VehSN: 1234,
			},
		}
		message3 := mqtt.MQTTMessage{
			Topic: "/foo/vehicle 3/bar/1.23L,4.56H",
			Payload: mqtt.Payload{
				VehGPSLat_ddmmmmmm: 10,
			},
		}

		spy := mqtt.NewSpy()

		spy.HandleMessage(makeRawMQTTMessage(message1))
		time.Sleep(time.Millisecond * 2)
		spy.HandleMessage(makeRawMQTTMessage(message2))
		spy.HandleMessage(makeRawMQTTMessage(message3))

		expectedMessages := map[string]mqtt.MQTTMessage{
			message2.Topic: message2,
			message3.Topic: message3,
		}
		actualMessages, err := toMap(spy.GetMessages(time.Millisecond, nil))
		is.NoErr(err)

		is.Equal("", cmp.Diff(expectedMessages, actualMessages))
	})

	t.Run("filters by given vehicle Id's", func(t *testing.T) {
		is := is.New(t)

		message1 := mqtt.MQTTMessage{
			Topic: "/foo/vehicle 1/bar/1.23L,4.56H",
			Payload: mqtt.Payload{
				VehGPSVel_mpsd5: 123,
			},
		}
		message2 := mqtt.MQTTMessage{
			Topic: "/foo/vehicle 2/bar/1.23L,4.56H",
			Payload: mqtt.Payload{
				VehSN: 1234,
			},
		}
		message3 := mqtt.MQTTMessage{
			Topic: "/foo/vehicle 3/bar/1.23L,4.56H",
			Payload: mqtt.Payload{
				VehGPSLat_ddmmmmmm: 10,
			},
		}

		spy := mqtt.NewSpy()

		spy.HandleMessage(makeRawMQTTMessage(message1))
		spy.HandleMessage(makeRawMQTTMessage(message2))
		spy.HandleMessage(makeRawMQTTMessage(message3))

		expectedMessages := map[string]mqtt.MQTTMessage{
			message1.Topic: message1,
			message3.Topic: message3,
		}
		actualMessages, err := toMap(spy.GetMessages(0, []string{message1.Topic, message3.Topic}))
		is.NoErr(err)

		is.Equal("", cmp.Diff(expectedMessages, actualMessages))
	})

	t.Run("filters by given age and given vehicle Id's", func(t *testing.T) {
		is := is.New(t)

		message1 := mqtt.MQTTMessage{
			Topic: "/foo/vehicle 1/bar/1.23L,4.56H",
			Payload: mqtt.Payload{
				VehGPSVel_mpsd5: 123,
			},
		}
		message2 := mqtt.MQTTMessage{
			Topic: "/foo/vehicle 2/bar/1.23L,4.56H",
			Payload: mqtt.Payload{
				VehSN: 1234,
			},
		}
		message3 := mqtt.MQTTMessage{
			Topic: "/foo/vehicle 3/bar/1.23L,4.56H",
			Payload: mqtt.Payload{
				VehGPSLat_ddmmmmmm: 10,
			},
		}

		spy := mqtt.NewSpy()

		spy.HandleMessage(makeRawMQTTMessage(message1))
		time.Sleep(time.Millisecond * 2)
		spy.HandleMessage(makeRawMQTTMessage(message2))
		spy.HandleMessage(makeRawMQTTMessage(message3))

		expectedMessages := map[string]mqtt.MQTTMessage{
			message2.Topic: message2,
		}
		actualMessages, err := toMap(spy.GetMessages(time.Millisecond, []string{message1.Topic, message2.Topic}))
		is.NoErr(err)

		is.Equal("", cmp.Diff(expectedMessages, actualMessages))
	})

	t.Run("HandleMessage() returns ErrInvalidInput with bad payload", func(t *testing.T) {
		spy := mqtt.NewSpy()

		err := spy.HandleMessage([]byte(`{
			"topic": "foo",
			"payload": "not a valid base64-encoded payload"
		`))

		if !errors.Is(err, mqtt.ErrInvalidInput) {
			t.Fatalf("Expected an ErrInvalidInput; Got: %v", err)
		}
	})

	t.Run("HandleMessage() returns ErrMissingField with missing topic", func(t *testing.T) {
		spy := mqtt.NewSpy()

		err := spy.HandleMessage([]byte(fmt.Sprintf(`{
			"payload": "%s"
		}`, encodePayload(mqtt.Payload{}))))

		if !errors.Is(err, mqtt.ErrMissingField) {
			t.Fatalf("Expected an ErrMissingField; Got: %v", err)
		}
		if !strings.Contains(err.Error(), "topic") {
			t.Fatalf("Error should be descriptive")
		}
	})
}

func toMap(jsonBytes []byte, err error) (map[string]mqtt.MQTTMessage, error) {
	if err != nil {
		return nil, err
	}
	messages := map[string]mqtt.MQTTMessage{}
	err = json.Unmarshal(jsonBytes, &messages)
	if err != nil {
		return nil, err
	}
	return messages, nil
}

func makeRawMQTTMessage(mqttMsg mqtt.MQTTMessage) []byte {
	return []byte(fmt.Sprintf(
		`{ "topic": "%s", "payload": "%s" }`,
		mqttMsg.Topic,
		encodePayload(mqttMsg.Payload),
	))
}

func encodePayload(payload mqtt.Payload) string {
	payloadBytes := bytes.Buffer{}
	binary.Write(&payloadBytes, binary.LittleEndian, payload)
	return base64.StdEncoding.EncodeToString(payloadBytes.Bytes())
}
