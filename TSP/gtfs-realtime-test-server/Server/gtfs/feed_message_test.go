package gtfs_test

import (
	"encoding/json"
	"errors"
	"fmt"
	"testing"
	"time"

	"github.com/google/go-cmp/cmp"
	"github.com/gtt/gtfs-realtime-test-server/Server/gtfs"
	"github.com/gtt/gtfs-realtime-test-server/Server/gtfs/pb"
	"github.com/matryer/is"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/testing/protocmp"
)

func TestFeedMessage(t *testing.T) {
	type TestCase struct {
		Action              func(feedMsg *gtfs.FeedMessage) error
		ExpectedFeedMessage *pb.FeedMessage
		ExpectedErr         error
	}

	testCases := map[string]TestCase{
		"Uses DefaultFeedMessage": {
			ExpectedFeedMessage: gtfs.DefaultFeedMsg(),
		},

		// Set()
		"Set() sets feed message": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.Set([]byte(`{
					"header": {
						"gtfsRealtimeVersion": "foo",
						"incrementality": "DIFFERENTIAL",
						"timestamp": 1234
					},
					"entity": [
						{
							"id": "entity 1"
						}
					]
				}`))
			},
			ExpectedFeedMessage: &pb.FeedMessage{
				Header: &pb.FeedHeader{
					GtfsRealtimeVersion: proto.String("foo"),
					Incrementality:      pb.FeedHeader_DIFFERENTIAL.Enum(),
					Timestamp:           proto.Uint64(1234),
				},
				Entity: []*pb.FeedEntity{
					{
						Id: proto.String("entity 1"),
					},
				},
			},
		},
		"Set() does not set feed message with invalid input": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.Set([]byte(`invalid json`))
			},
			ExpectedErr:         gtfs.ErrInvalidJSON,
			ExpectedFeedMessage: gtfs.DefaultFeedMsg(),
		},
		"Set() does not set feed message with incomplete input": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.Set([]byte(`{
					"header": {
						"timestamp": 1234
					}
				}`))
			},
			ExpectedErr:         gtfs.ErrInvalidJSON,
			ExpectedFeedMessage: gtfs.DefaultFeedMsg(),
		},

		// Update()
		"Update() updates feed header": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.Update([]byte(`{
					"header": {
						"incrementality": "DIFFERENTIAL"
					}
				}`))
			},
			ExpectedFeedMessage: func() *pb.FeedMessage {
				feedMsg := gtfs.DefaultFeedMsg()
				feedMsg.Header.Incrementality = pb.FeedHeader_DIFFERENTIAL.Enum()
				return feedMsg
			}(),
		},
		"Update() does not update feed message with invalid input": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.Update([]byte(`invalid json`))
			},
			ExpectedErr:         gtfs.ErrInvalidJSON,
			ExpectedFeedMessage: gtfs.DefaultFeedMsg(),
		},
		"Update() adds feed entities": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.Update([]byte(`{
					"entity": [ 
						{
							"id": "vehicle_0001",
							"vehicle": {
								"vehicle": { 
									"id": "0001",
									"label": "1"
								},
								"position": {
									"latitude": 45.123,
									"longitude": -100.456
								},
								"timestamp": 1234
							}
						}
					]
				}`))
				if err != nil {
					return err
				}
				return feedMsg.Update([]byte(`{
					"entity": [ 
						{
							"id": "vehicle_0002",
							"vehicle": {
								"vehicle": { 
									"id": "0002",
									"label": "2"
								},
								"position": {
									"latitude": 40.999,
									"longitude": -99.111
								},
								"timestamp": 1235
							}
						}
					]
				}`))
			},
			ExpectedFeedMessage: &pb.FeedMessage{
				Header: proto.Clone(gtfs.DefaultFeedMsg().Header).(*pb.FeedHeader),
				Entity: []*pb.FeedEntity{
					{
						Id: proto.String("vehicle_0001"),
						Vehicle: &pb.VehiclePosition{
							Vehicle: &pb.VehicleDescriptor{
								Id:    proto.String("0001"),
								Label: proto.String("1"),
							},
							Position: &pb.Position{
								Latitude:  proto.Float32(45.123),
								Longitude: proto.Float32(-100.456),
							},
							Timestamp: proto.Uint64(1234),
						},
					},
					{
						Id: proto.String("vehicle_0002"),
						Vehicle: &pb.VehiclePosition{
							Vehicle: &pb.VehicleDescriptor{
								Id:    proto.String("0002"),
								Label: proto.String("2"),
							},
							Position: &pb.Position{
								Latitude:  proto.Float32(40.999),
								Longitude: proto.Float32(-99.111),
							},
							Timestamp: proto.Uint64(1235),
						},
					},
				},
			},
		},
		"Update() appends to entity list": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.Update([]byte(`{
					"entity": [ 
						{
							"id": "vehicle_0001",
							"vehicle": {
								"vehicle": { 
									"id": "0001",
									"label": "1"
								},
								"position": {
									"latitude": 45.123,
									"longitude": -100.456
								},
								"timestamp": 1234
							}
						}
					]
				}`))
				if err != nil {
					return err
				}
				return feedMsg.Update([]byte(`{
					"entity": [ 
						{
							"id": "vehicle_0001",
							"vehicle": {
								"vehicle": { 
									"id": "0002",
									"label": "2"
								},
								"position": {
									"latitude": 40.999,
									"longitude": -99.111
								},
								"timestamp": 1235
							}
						}
					]
				}`))
			},
			ExpectedFeedMessage: &pb.FeedMessage{
				Header: proto.Clone(gtfs.DefaultFeedMsg().Header).(*pb.FeedHeader),
				Entity: []*pb.FeedEntity{
					{
						Id: proto.String("vehicle_0001"),
						Vehicle: &pb.VehiclePosition{
							Vehicle: &pb.VehicleDescriptor{
								Id:    proto.String("0001"),
								Label: proto.String("1"),
							},
							Position: &pb.Position{
								Latitude:  proto.Float32(45.123),
								Longitude: proto.Float32(-100.456),
							},
							Timestamp: proto.Uint64(1234),
						},
					},
					{
						Id: proto.String("vehicle_0001"),
						Vehicle: &pb.VehiclePosition{
							Vehicle: &pb.VehicleDescriptor{
								Id:    proto.String("0002"),
								Label: proto.String("2"),
							},
							Position: &pb.Position{
								Latitude:  proto.Float32(40.999),
								Longitude: proto.Float32(-99.111),
							},
							Timestamp: proto.Uint64(1235),
						},
					},
				},
			},
		},
		"Update() updates timestamp": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.Update([]byte(fmt.Sprintf(`{
					"header": {
						"timestamp": %d
					}
				}`, time.Now().UTC().Unix()-20)))
			},
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Header.Timestamp = proto.Uint64(uint64(time.Now().UTC().Unix() - 20))
				return copyOfDefaultMsg
			}(),
		},
		"Update() automatically sets timestamp if not set": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.Update([]byte(fmt.Sprintf(`{
					"header": {
						"timestamp": %d
					}
				}`, time.Now().UTC().Unix()-20)))
				if err != nil {
					return err
				}
				return feedMsg.Update([]byte(`{
					"header": {
						"incrementality": "DIFFERENTIAL"
					}
				}`))
			},
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Header.Incrementality = pb.FeedHeader_DIFFERENTIAL.Enum()
				copyOfDefaultMsg.Header.Timestamp = proto.Uint64(uint64(time.Now().UTC().Unix()))
				return copyOfDefaultMsg
			}(),
		},

		// CreateEntity()
		"CreateEntity() creates an entity": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.CreateEntity([]byte(`{
					"id": "foo"
				}`))
			},
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Entity = append(copyOfDefaultMsg.Entity, &pb.FeedEntity{
					Id: proto.String("foo"),
				})
				return copyOfDefaultMsg
			}(),
		},
		"CreateEntity() id must be unique": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.CreateEntity([]byte(`{
					"id": "foo"
				}`))
				if err != nil {
					return err
				}
				return feedMsg.CreateEntity([]byte(`{
					"id": "foo"
				}`))
			},
			ExpectedErr: gtfs.ErrIDMustBeUnique,
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Entity = append(copyOfDefaultMsg.Entity, &pb.FeedEntity{
					Id: proto.String("foo"),
				})
				return copyOfDefaultMsg
			}(),
		},
		"CreateEntity() fails with bad input": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.CreateEntity([]byte(`{
					"foo": "bar"
				}`))
			},
			ExpectedErr:         gtfs.ErrInvalidJSON,
			ExpectedFeedMessage: gtfs.DefaultFeedMsg(),
		},

		// GetEntity()
		"GetEntity() gets an entity by its id": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.CreateEntity([]byte(`{
					"id": "foo"
				}`))
				if err != nil {
					return err
				}
				bytes, err := feedMsg.GetEntity("foo")
				if err != nil {
					return err
				}
				expectedFeedEntity := map[string]any{
					"id": "foo",
				}
				actualFeedEntity := map[string]any{}
				json.Unmarshal(bytes, &actualFeedEntity)
				if diff := cmp.Diff(expectedFeedEntity, actualFeedEntity); diff != "" {
					return fmt.Errorf(diff)
				}
				return nil
			},
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Entity = append(copyOfDefaultMsg.Entity, &pb.FeedEntity{
					Id: proto.String("foo"),
				})
				return copyOfDefaultMsg
			}(),
		},
		"GetEntity() fails with nonexistent id": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				bytes, err := feedMsg.GetEntity("doesnotexist")
				if bytes != nil {
					return fmt.Errorf("bytes should be nil")
				}
				return err
			},
			ExpectedErr:         gtfs.ErrNotFound,
			ExpectedFeedMessage: gtfs.DefaultFeedMsg(),
		},

		// SetEntity()
		"SetEntity() fails with nonexistent id": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.SetEntity("doesnotexist", []byte(``))
			},
			ExpectedErr:         gtfs.ErrNotFound,
			ExpectedFeedMessage: gtfs.DefaultFeedMsg(),
		},
		"SetEntity() sets the entity with the given id": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.CreateEntity([]byte(`{
					"id": "foo",
					"vehicle": {
						"vehicle": {
							"id": "bar",
							"label": "uno"
						},
						"position": {
							"latitude": 40,
							"longitude": 100
						},
						"timestamp": 1234
					}
				}`))
				if err != nil {
					return err
				}
				return feedMsg.SetEntity("foo", []byte(`{
					"id": "foo"
				}`))
			},
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Entity = append(copyOfDefaultMsg.Entity, &pb.FeedEntity{
					Id: proto.String("foo"),
				})
				return copyOfDefaultMsg
			}(),
		},
		"SetEntity() fails with bad input": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.CreateEntity([]byte(`{
					"id": "foo"
				}`))
				if err != nil {
					return err
				}
				return feedMsg.SetEntity("foo", []byte(`{"foo": "bar"}`))
			},
			ExpectedErr: gtfs.ErrInvalidJSON,
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Entity = append(copyOfDefaultMsg.Entity, &pb.FeedEntity{
					Id: proto.String("foo"),
				})
				return copyOfDefaultMsg
			}(),
		},

		// UpdateEntity()
		"UpdateEntity() updates an entity": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.CreateEntity([]byte(`{
					"id": "foo",
					"vehicle": {
						"vehicle": {
							"id": "bar",
							"label": "uno"
						},
						"position": {
							"latitude": 40,
							"longitude": 100
						},
						"timestamp": 1234
					}
				}`))
				if err != nil {
					return err
				}
				return feedMsg.UpdateEntity("foo", []byte(`{
					"vehicle": {
						"position": {
							"latitude": 41
						}
					}
				}`))
			},
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Entity = append(copyOfDefaultMsg.Entity, &pb.FeedEntity{
					Id: proto.String("foo"),
					Vehicle: &pb.VehiclePosition{
						Vehicle: &pb.VehicleDescriptor{
							Id:    proto.String("bar"),
							Label: proto.String("uno"),
						},
						Position: &pb.Position{
							Latitude:  proto.Float32(41),
							Longitude: proto.Float32(100),
						},
						Timestamp: proto.Uint64(1234),
					},
				})
				return copyOfDefaultMsg
			}(),
		},
		"UpdateEntity() fails with nonexistent id": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				return feedMsg.UpdateEntity("doesnotexist", []byte(``))
			},
			ExpectedErr:         gtfs.ErrNotFound,
			ExpectedFeedMessage: gtfs.DefaultFeedMsg(),
		},
		"UpdateEntity() fails with bad input": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.CreateEntity([]byte(`{
					"id": "foo"
				}`))
				if err != nil {
					return err
				}
				return feedMsg.UpdateEntity("foo", []byte(`{"foo": "bar"}`))
			},
			ExpectedErr: gtfs.ErrInvalidJSON,
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Entity = append(copyOfDefaultMsg.Entity, &pb.FeedEntity{
					Id: proto.String("foo"),
				})
				return copyOfDefaultMsg
			}(),
		},

		// RemoveEntity()
		"RemoveEntity() removes an entity": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.Update([]byte(`{
					"entity": [ 
						{
							"id": "vehicle_0001",
							"vehicle": {
								"vehicle": { 
									"id": "0001",
									"label": "1"
								},
								"position": {
									"latitude": 45.123,
									"longitude": -100.456
								},
								"timestamp": 1234
							}
						},
						{
							"id": "vehicle_0002",
							"vehicle": {
								"vehicle": { 
									"id": "0002",
									"label": "2"
								},
								"position": {
									"latitude": 40.999,
									"longitude": -99.111
								},
								"timestamp": 1235
							}
						},
						{
							"id": "vehicle_0003",
							"vehicle": {
								"vehicle": { 
									"id": "0003",
									"label": "3"
								},
								"position": {
									"latitude": 40.999,
									"longitude": -99.111
								},
								"timestamp": 1235
							}
						}
					]
				}`))
				if err != nil {
					return err
				}
				return feedMsg.RemoveEntity("vehicle_0002")
			},
			ExpectedFeedMessage: &pb.FeedMessage{
				Header: proto.Clone(gtfs.DefaultFeedMsg().Header).(*pb.FeedHeader),
				Entity: []*pb.FeedEntity{
					{
						Id: proto.String("vehicle_0001"),
						Vehicle: &pb.VehiclePosition{
							Vehicle: &pb.VehicleDescriptor{
								Id:    proto.String("0001"),
								Label: proto.String("1"),
							},
							Position: &pb.Position{
								Latitude:  proto.Float32(45.123),
								Longitude: proto.Float32(-100.456),
							},
							Timestamp: proto.Uint64(1234),
						},
					},
					{
						Id: proto.String("vehicle_0003"),
						Vehicle: &pb.VehiclePosition{
							Vehicle: &pb.VehicleDescriptor{
								Id:    proto.String("0003"),
								Label: proto.String("3"),
							},
							Position: &pb.Position{
								Latitude:  proto.Float32(40.999),
								Longitude: proto.Float32(-99.111),
							},
							Timestamp: proto.Uint64(1235),
						},
					},
				},
			},
		},
		"RemoveEntity() returns ErrNotFound with bad id": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.Update([]byte(`{
					"entity": [ 
						{
							"id": "vehicle_0001",
							"vehicle": {
								"vehicle": { 
									"id": "0001",
									"label": "1"
								},
								"position": {
									"latitude": 45.123,
									"longitude": -100.456
								},
								"timestamp": 1234
							}
						},
						{
							"id": "vehicle_0002",
							"vehicle": {
								"vehicle": { 
									"id": "0002",
									"label": "2"
								},
								"position": {
									"latitude": 40.999,
									"longitude": -99.111
								},
								"timestamp": 1235
							}
						},
						{
							"id": "vehicle_0003",
							"vehicle": {
								"vehicle": { 
									"id": "0003",
									"label": "3"
								},
								"position": {
									"latitude": 40.999,
									"longitude": -99.111
								},
								"timestamp": 1235
							}
						}
					]
				}`))
				if err != nil {
					return err
				}
				return feedMsg.RemoveEntity("vehicle_0004") // doesn't exist
			},
			ExpectedErr: gtfs.ErrNotFound,
			ExpectedFeedMessage: &pb.FeedMessage{
				Header: proto.Clone(gtfs.DefaultFeedMsg().Header).(*pb.FeedHeader),
				Entity: []*pb.FeedEntity{
					{
						Id: proto.String("vehicle_0001"),
						Vehicle: &pb.VehiclePosition{
							Vehicle: &pb.VehicleDescriptor{
								Id:    proto.String("0001"),
								Label: proto.String("1"),
							},
							Position: &pb.Position{
								Latitude:  proto.Float32(45.123),
								Longitude: proto.Float32(-100.456),
							},
							Timestamp: proto.Uint64(1234),
						},
					},
					{
						Id: proto.String("vehicle_0002"),
						Vehicle: &pb.VehiclePosition{
							Vehicle: &pb.VehicleDescriptor{
								Id:    proto.String("0002"),
								Label: proto.String("2"),
							},
							Position: &pb.Position{
								Latitude:  proto.Float32(40.999),
								Longitude: proto.Float32(-99.111),
							},
							Timestamp: proto.Uint64(1235),
						},
					},
					{
						Id: proto.String("vehicle_0003"),
						Vehicle: &pb.VehiclePosition{
							Vehicle: &pb.VehicleDescriptor{
								Id:    proto.String("0003"),
								Label: proto.String("3"),
							},
							Position: &pb.Position{
								Latitude:  proto.Float32(40.999),
								Longitude: proto.Float32(-99.111),
							},
							Timestamp: proto.Uint64(1235),
						},
					},
				},
			},
		},
		"RemoveEntity() updates timestamp": {
			Action: func(feedMsg *gtfs.FeedMessage) error {
				err := feedMsg.Update([]byte(fmt.Sprintf(`{
					"header": {
						"timestamp": %d
					},
					"entity": [
						{
							"id": "foo"
						}
					]
				}`, time.Now().UTC().Unix()-20)))
				if err != nil {
					return err
				}
				return feedMsg.RemoveEntity("foo")
			},
			ExpectedFeedMessage: func() *pb.FeedMessage {
				copyOfDefaultMsg := proto.Clone(gtfs.DefaultFeedMsg()).(*pb.FeedMessage)
				copyOfDefaultMsg.Header.Timestamp = proto.Uint64(uint64(time.Now().UTC().Unix()))
				return copyOfDefaultMsg
			}(),
		},
	}

	for name, test := range testCases {
		t.Run(name, func(t *testing.T) {
			is := is.New(t)

			feedMsg := gtfs.NewFeedMessage(nil)

			if test.Action != nil {
				err := test.Action(feedMsg)
				if test.ExpectedErr == nil {
					is.NoErr(err)
				} else {
					is.True(errors.Is(err, test.ExpectedErr))
				}
			}

			actualFeedMsg := &pb.FeedMessage{}
			feedMsgBytes, err := feedMsg.Get()
			is.NoErr(err)
			err = proto.Unmarshal(feedMsgBytes, actualFeedMsg)
			is.NoErr(err)

			expectedFeedMsgJSON, err := protojson.Marshal(test.ExpectedFeedMessage)
			is.NoErr(err)
			actualFeedMsgJSON, err := feedMsg.GetJSON()
			is.NoErr(err)

			is.Equal("", cmp.Diff(test.ExpectedFeedMessage, actualFeedMsg, protocmp.Transform()))
			is.Equal(string(expectedFeedMsgJSON), string(actualFeedMsgJSON))
		})
	}

	t.Run("Get() is restricted by allowedFrequency", func(t *testing.T) {
		frequencyRestrictor := gtfs.NewFrequencyRestrictor(0.01)
		feedMsg := gtfs.NewFeedMessage(frequencyRestrictor)

		_, err := feedMsg.Get()
		if err != nil {
			t.Fatalf("Expected no err; Got: %v", err)
		}
		time.Sleep(time.Millisecond * 5)
		_, err = feedMsg.Get()
		if err != gtfs.ErrTooSoon {
			t.Fatalf("Expected ErrTooSoon; Got: %v", err)
		}
	})
}
