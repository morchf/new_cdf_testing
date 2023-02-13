package gtfs

import (
	"fmt"
	"sync"
	"time"

	"github.com/gtt/gtfs-realtime-test-server/Server/gtfs/pb"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
)

func DefaultFeedMsg() *pb.FeedMessage {
	return &pb.FeedMessage{
		Header: &pb.FeedHeader{
			GtfsRealtimeVersion: proto.String("1.0"),
			Incrementality:      pb.FeedHeader_FULL_DATASET.Enum(),
			Timestamp:           proto.Uint64(uint64(time.Now().UTC().Unix())),
		},
		Entity: []*pb.FeedEntity{},
	}
}

type FeedMessage struct {
	mu             sync.RWMutex
	feedMsg        *pb.FeedMessage
	freqRestrictor *FrequencyRestrictor
}

func NewFeedMessage(freqRestrictor *FrequencyRestrictor) *FeedMessage {
	return &FeedMessage{
		feedMsg:        proto.Clone(DefaultFeedMsg()).(*pb.FeedMessage),
		freqRestrictor: freqRestrictor,
	}
}

func (feedMsg *FeedMessage) Get() ([]byte, error) {
	if feedMsg.freqRestrictor != nil {
		isTooSoon := feedMsg.freqRestrictor.IsTooSoon()
		feedMsg.freqRestrictor.Reset()
		if isTooSoon {
			return nil, ErrTooSoon
		}
	}

	feedMsg.mu.RLock()
	defer feedMsg.mu.RUnlock()

	return proto.Marshal(feedMsg.feedMsg)
}

func (feedMsg *FeedMessage) GetJSON() ([]byte, error) {
	feedMsg.mu.RLock()
	defer feedMsg.mu.RUnlock()

	return protojson.Marshal(feedMsg.feedMsg)
}

func (feedMsg *FeedMessage) Set(feedMsgJSON []byte) error {
	feedMsg.mu.Lock()
	defer feedMsg.mu.Unlock()

	newFeedMsg := &pb.FeedMessage{}
	err := protojson.Unmarshal(feedMsgJSON, newFeedMsg)
	if err != nil {
		return fmt.Errorf("FeedMessage.Set: %v: %w", err, ErrInvalidJSON)
	}
	feedMsg.feedMsg = newFeedMsg
	return nil
}

func (feedMsg *FeedMessage) Update(feedMsgJSON []byte) error {
	feedMsg.mu.Lock()
	defer feedMsg.mu.Unlock()

	unmarshaller := protojson.UnmarshalOptions{AllowPartial: true}
	partialFeedMsg := &pb.FeedMessage{}
	err := unmarshaller.Unmarshal(feedMsgJSON, partialFeedMsg)
	if err != nil {
		return fmt.Errorf("FeedMessage.Update: %v: %w", err, ErrInvalidJSON)
	}
	feedMsg.updateTimestamp()
	proto.Merge(feedMsg.feedMsg, partialFeedMsg)
	return nil
}

func (feedMsg *FeedMessage) CreateEntity(feedEntityJSON []byte) error {
	feedMsg.mu.Lock()
	defer feedMsg.mu.Unlock()

	feedEntity := &pb.FeedEntity{}
	err := protojson.Unmarshal(feedEntityJSON, feedEntity)
	if err != nil {
		return fmt.Errorf("FeedMessage.CreateEntity: %w: %v", ErrInvalidJSON, err)
	}
	index := findIndexById(*feedEntity.Id, feedMsg.feedMsg.Entity)
	if index != -1 {
		return fmt.Errorf("FeedMessage.CreateEntity: %w: '%s'", ErrIDMustBeUnique, *feedEntity.Id)
	}
	feedMsg.feedMsg.Entity = append(feedMsg.feedMsg.Entity, feedEntity)
	feedMsg.updateTimestamp()
	return nil
}

func (feedMsg *FeedMessage) GetEntity(id string) ([]byte, error) {
	feedMsg.mu.RLock()
	defer feedMsg.mu.RUnlock()

	index := findIndexById(id, feedMsg.feedMsg.Entity)
	if index == -1 {
		return nil, fmt.Errorf("FeedMessage.GetEntity: %w", ErrNotFound)
	}
	entity := feedMsg.feedMsg.Entity[index]
	feedMsg.updateTimestamp()
	return protojson.Marshal(entity)
}

func (feedMsg *FeedMessage) SetEntity(id string, jsonBytes []byte) error {
	feedMsg.mu.Lock()
	defer feedMsg.mu.Unlock()

	index := findIndexById(id, feedMsg.feedMsg.Entity)
	if index == -1 {
		return fmt.Errorf("FeedMessage.SetEntity: %w", ErrNotFound)
	}
	newEntity := &pb.FeedEntity{}
	err := protojson.Unmarshal(jsonBytes, newEntity)
	if err != nil {
		return fmt.Errorf("FeedMessage.SetEntity: %w: %v", ErrInvalidJSON, err)
	}
	feedMsg.feedMsg.Entity[index] = newEntity
	feedMsg.updateTimestamp()
	return nil
}

func (feedMsg *FeedMessage) UpdateEntity(id string, jsonBytes []byte) error {
	feedMsg.mu.Lock()
	defer feedMsg.mu.Unlock()

	index := findIndexById(id, feedMsg.feedMsg.Entity)
	if index == -1 {
		return fmt.Errorf("FeedMessage.UpdateEntity: %w", ErrNotFound)
	}
	newEntity := &pb.FeedEntity{}
	err := protojson.UnmarshalOptions{
		AllowPartial: true,
	}.Unmarshal(jsonBytes, newEntity)
	if err != nil {
		return fmt.Errorf("FeedMessage.UpdateEntity: %w: %v", ErrInvalidJSON, err)
	}
	proto.Merge(feedMsg.feedMsg.Entity[index], newEntity)
	feedMsg.updateTimestamp()
	return nil
}

func (feedMsg *FeedMessage) RemoveEntity(id string) error {
	feedMsg.mu.Lock()
	defer feedMsg.mu.Unlock()

	index := findIndexById(id, feedMsg.feedMsg.Entity)
	if index == -1 {
		return fmt.Errorf("FeedMessage.RemoveEntity: '%s': %w", id, ErrNotFound)
	}
	// splice out element
	feedMsg.feedMsg.Entity = append(feedMsg.feedMsg.Entity[:index], feedMsg.feedMsg.Entity[index+1:]...)
	feedMsg.updateTimestamp()
	return nil
}

func findIndexById(id string, feedEntities []*pb.FeedEntity) int {
	for i, entity := range feedEntities {
		if *entity.Id == id {
			return i
		}
	}
	return -1
}

func (feedMsg *FeedMessage) updateTimestamp() {
	feedMsg.feedMsg.Header.Timestamp = proto.Uint64(uint64(time.Now().Unix()))
}
