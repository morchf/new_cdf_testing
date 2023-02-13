package api_test

import (
	"bytes"
	"net/http"
	"testing"
	"time"

	"github.com/gtt/gtfs-realtime-test-server/Server/gtfs"
	"github.com/gtt/gtfs-realtime-test-server/Server/gtfs/pb"
	"google.golang.org/protobuf/proto"
)

func defaultFeedMsg() (*pb.FeedMessage, error) {
	return gtfs.DefaultFeedMsg(), nil
}

func TestGTFSAPI(t *testing.T) {
	tests := map[string][]TestStep{
		// GET => FeedMessage.Get() || FeedMessage.GetJSON()
		"GET /vehiclepositions Protobuf": {
			{
				// Ensure initial state uses 'DefaultFeedMsg'
				Request:          SimpleGet("/gtfs-rt/foo/vehiclepositions"),
				ExpectedProtobuf: defaultFeedMsg,
			},
		},
		"GET /vehiclepositions JSON": {
			{
				// Can also retrieve as JSON (to peek the current state)
				Request: func() (*http.Request, error) {
					req, err := http.NewRequest("GET", "http://foo.com/gtfs-rt/foo/vehiclepositions", nil)
					req.Header.Set("Content-Type", "application/json")
					return req, err
				},
				ExpectedProtobuf: defaultFeedMsg,
			},
		},
		// Make sure /tripupdates endpoint also implements GET
		"GET /tripupdates Protobuf": {
			{
				Request:          SimpleGet("/gtfs-rt/foo/tripupdates"),
				ExpectedProtobuf: defaultFeedMsg,
			},
		},
		"GET /tripupdates JSON": {
			{
				Request: func() (*http.Request, error) {
					req, err := http.NewRequest("GET", "http://foo.com/gtfs-rt/foo/tripupdates", nil)
					req.Header.Set("Content-Type", "application/json")
					return req, err
				},
				ExpectedProtobuf: defaultFeedMsg,
			},
		},
		// PUT => FeedMessage.Set()
		"PUT /vehiclepositions 200": {
			{
				// Set with good data
				Request: func() (*http.Request, error) {
					return http.NewRequest("PUT", "http://foo.com/gtfs-rt/foo/vehiclepositions", bytes.NewReader([]byte(`{
						"header": {
							"gtfsRealtimeVersion": "2.0",
							"incrementality": "DIFFERENTIAL",
							"timestamp": 1234
						},
						"entity": [
							{
								"id": "foo"
							}
						]
					}`)))
				},
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"type":    "success",
						"message": "Successfully set FeedMessage at /gtfs-rt/foo/vehiclepositions",
					}, nil
				},
			},
			{
				// Ensure resource changed as expected
				Request: SimpleGet("/gtfs-rt/foo/vehiclepositions"),
				ExpectedProtobuf: func() (*pb.FeedMessage, error) {
					return &pb.FeedMessage{
						Header: &pb.FeedHeader{
							GtfsRealtimeVersion: proto.String("2.0"),
							Incrementality:      pb.FeedHeader_DIFFERENTIAL.Enum(),
							Timestamp:           proto.Uint64(1234),
						},
						Entity: []*pb.FeedEntity{
							{
								Id: proto.String("foo"),
							},
						},
					}, nil
				},
			},
		},
		"PUT /vehiclepositions 400": {
			{
				// Try to set with bad data
				Request: func() (*http.Request, error) {
					return http.NewRequest("PUT", "http://foo.com/gtfs-rt/foo/vehiclepositions", bytes.NewReader([]byte(`{
						"foo": "bar"
					}`)))
				},
				ExpectedStatus: 400,
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"type":    "error",
						"message": "FeedMessage.Set: proto:\u00a0(line 2:7): unknown field \"foo\": invalid JSON input",
					}, nil
				},
			},
			{
				// Ensure resource did not change
				Request:          SimpleGet("/gtfs-rt/foo/vehiclepositions"),
				ExpectedProtobuf: defaultFeedMsg,
			},
		},
		// PATCH => FeedMessage.Update()
		"PATCH /vehiclepositions 200": {
			{
				// Update with good data
				Request: func() (*http.Request, error) {
					return http.NewRequest("PATCH", "http://foo.com/gtfs-rt/foo/vehiclepositions", bytes.NewReader([]byte(`{
						"header": {
							"timestamp": 1234
						},
						"entity": [
							{
								"id": "foo"
							}
						]
					}`)))
				},
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"type":    "success",
						"message": "Successfully updated FeedMessage at /gtfs-rt/foo/vehiclepositions",
					}, nil
				},
			},
			{
				// Ensure resource changed as expected
				Request: SimpleGet("/gtfs-rt/foo/vehiclepositions"),
				ExpectedProtobuf: func() (*pb.FeedMessage, error) {
					feedMsg := gtfs.DefaultFeedMsg()
					feedMsg.Header.Timestamp = proto.Uint64(1234)
					feedMsg.Entity = append(feedMsg.Entity, &pb.FeedEntity{
						Id: proto.String("foo"),
					})
					return feedMsg, nil
				},
			},
		},
		"PATCH /vehiclepositions 400": {
			{
				// Try to update with bad data
				Request: func() (*http.Request, error) {
					return http.NewRequest("PATCH", "http://foo.com/gtfs-rt/foo/vehiclepositions", bytes.NewReader([]byte(`{
						"foo": "bar"
					}`)))
				},
				ExpectedStatus: 400,
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"type":    "error",
						"message": "FeedMessage.Update: proto: (line 2:7): unknown field \"foo\": invalid JSON input",
					}, nil
				},
			},
			{
				// Ensure resource did not change
				Request:          SimpleGet("/gtfs-rt/foo/vehiclepositions"),
				ExpectedProtobuf: defaultFeedMsg,
			},
		},
		// DELETE => FeedMessage.Remove()
		"DELETE /vehiclepositions 200": {
			{
				// Add a few entities
				Request: func() (*http.Request, error) {
					return http.NewRequest("PATCH", "http://foo.com/gtfs-rt/foo/vehiclepositions", bytes.NewReader([]byte(`{
						"entity": [
							{
								"id": "foo"
							},
							{
								"id": "bar"
							},
							{
								"id": "baz"
							}
						]
					}`)))
				},
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"type":    "success",
						"message": "Successfully updated FeedMessage at /gtfs-rt/foo/vehiclepositions",
					}, nil
				},
			},
			{
				// Delete one
				Request: func() (*http.Request, error) {
					return http.NewRequest("DELETE", "http://foo.com/gtfs-rt/foo/vehiclepositions/entities/bar", nil)
				},
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"type":    "success",
						"message": "Successfully removed entity 'bar'",
					}, nil
				},
			},
			{
				// Ensure resource changed as expected
				Request: SimpleGet("/gtfs-rt/foo/vehiclepositions"),
				ExpectedProtobuf: func() (*pb.FeedMessage, error) {
					feedMsg := gtfs.DefaultFeedMsg()
					feedMsg.Header.Timestamp = proto.Uint64(uint64(time.Now().Unix()))
					feedMsg.Entity = []*pb.FeedEntity{
						{
							Id: proto.String("foo"),
						},
						{
							Id: proto.String("baz"),
						},
					}
					return feedMsg, nil
				},
			},
		},
		"DELETE /vehiclepositions 404": {
			// Try to remove non-existent entity
			{
				Request: func() (*http.Request, error) {
					return http.NewRequest("DELETE", "http://foo.com/gtfs-rt/foo/vehiclepositions/entities/doesnotexist", nil)
				},
				ExpectedStatus: 404,
				ExpectedJSON: func() (any, error) {
					return map[string]any{
						"type":    "error",
						"message": "FeedMessage.RemoveEntity: 'doesnotexist': no entity with that ID",
					}, nil
				},
			},
			// Ensure resource did not change
			{
				Request:          SimpleGet("/gtfs-rt/foo/vehiclepositions"),
				ExpectedProtobuf: defaultFeedMsg,
			},
		},
		"Different agencies have different FeedMessages": {
			{
				Request:          SimpleGet("/gtfs-rt/agency-1/vehiclepositions"),
				ExpectedProtobuf: defaultFeedMsg,
			},
			{
				Request:          SimpleGet("/gtfs-rt/agency-2/vehiclepositions"),
				ExpectedProtobuf: defaultFeedMsg,
			},
			{
				Request: func() (*http.Request, error) {
					return http.NewRequest("POST", "http://foo.com/gtfs-rt/agency-1/vehiclepositions/entities", bytes.NewBuffer([]byte(`
						{
							"id": "my_entity"
						}
					`)))
				},
			},
			{
				Request: SimpleGet("/gtfs-rt/agency-1/vehiclepositions"),
				ExpectedProtobuf: func() (*pb.FeedMessage, error) {
					feedMsg, err := defaultFeedMsg()
					if err != nil {
						return nil, err
					}
					feedMsg.Entity = append(feedMsg.Entity, &pb.FeedEntity{
						Id: proto.String("my_entity"),
					})
					return feedMsg, nil
				},
			},
			{
				Request:          SimpleGet("/gtfs-rt/agency-2/vehiclepositions"),
				ExpectedProtobuf: defaultFeedMsg,
			},
		},
	}

	RunTests(t, tests)
}
