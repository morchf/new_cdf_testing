package mqtt

import (
	"encoding/json"
	"fmt"
	"sync"
	"time"

	"golang.org/x/exp/slices"
)

var ErrInvalidInput = fmt.Errorf("invalid mqtt message")
var ErrMissingField = fmt.Errorf("missing field")

type MQTTRecord struct {
	timestamp time.Time
	message   MQTTMessage
}

type Spy struct {
	mu      sync.RWMutex
	records map[string]MQTTRecord
}

func NewSpy() *Spy {
	return &Spy{
		records: make(map[string]MQTTRecord),
	}
}

func (spy *Spy) GetMessages(ageThreshold time.Duration, topics []string) ([]byte, error) {
	spy.mu.RLock()
	defer spy.mu.RUnlock()

	messages := map[string]MQTTMessage{}
	for id, record := range spy.records {
		// Filter out messages not in topics
		if topics != nil && !slices.Contains(topics, id) {
			continue
		}
		// Filter out expired messages
		if ageThreshold > 0 && time.Since(record.timestamp) > ageThreshold {
			continue
		}
		messages[id] = record.message
	}
	return json.Marshal(messages)
}

func (spy *Spy) HandleMessage(mqttJSON []byte) error {
	spy.mu.Lock()
	defer spy.mu.Unlock()

	rawMessage := RawMQTTMessage{}
	json.Unmarshal(mqttJSON, &rawMessage)
	newMessage, err := rawMessage.ToMQTTMessage()
	if err != nil {
		return fmt.Errorf("MQTT.HandleMessage: %v: %w", err, ErrInvalidInput)
	}
	if newMessage.Topic == "" {
		return fmt.Errorf("MQTT.HandleMessage: %w: %s", ErrMissingField, "topic")
	}
	spy.records[newMessage.Topic] = MQTTRecord{
		timestamp: time.Now(),
		message:   newMessage,
	}
	return nil
}
