package mqtt_test

import (
	"encoding/json"
	"fmt"
	"log"
	"testing"
	"time"

	"github.com/gtt/gtfs-realtime-test-server/Server/mqtt"
)

func TestSubscriber(t *testing.T) {
	t.SkipNow() // for local testing only
	subscriber, err := mqtt.NewSubscriber(
		[]string{"+"},
	)
	if err != nil {
		t.Fatal(err)
	}

	subscriber.Subscribe(func(mqttMsg []byte) {
		indentedMsg, _ := json.MarshalIndent(json.RawMessage(mqttMsg), "", "\t")
		log.Println(string(indentedMsg))
	})

	subscriber.Subscribe(func(mqttMsg []byte) {
		msg := map[string]any{}
		json.Unmarshal(mqttMsg, &msg)
		fmt.Printf("----%s----\n", msg["latLon"])
	})

	time.Sleep(time.Second * 10)
}
