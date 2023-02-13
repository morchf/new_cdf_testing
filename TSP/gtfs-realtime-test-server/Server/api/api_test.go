package api_test

import (
	"encoding/json"
	"io"
	"net"
	"net/http"
	"os"
	"strings"
	"testing"

	"github.com/gin-gonic/gin"
	"github.com/google/go-cmp/cmp"
	"github.com/gtt/gtfs-realtime-test-server/Server/api"
	"github.com/gtt/gtfs-realtime-test-server/Server/gtfs/pb"
	"github.com/matryer/is"
	"google.golang.org/protobuf/encoding/protojson"
	"google.golang.org/protobuf/proto"
	"google.golang.org/protobuf/testing/protocmp"
)

type TestStep struct {
	Request          func() (*http.Request, error)
	ExpectedStatus   int
	ExpectedProtobuf func() (*pb.FeedMessage, error)
	ExpectedJSON     func() (any, error)
}

func RunTests(t *testing.T, tests map[string][]TestStep) {
	gin.SetMode(gin.ReleaseMode)

	os.Mkdir("testing", 0755)

	client := &http.Client{
		Transport: &http.Transport{
			Dial: func(network, addr string) (net.Conn, error) {
				return net.Dial("unix", "testing/test.sock")
			},
		},
	}

	for name, test := range tests {
		t.Run(name, func(t *testing.T) {
			is := is.New(t)

			os.Remove("testing/test.sock")
			listener, err := net.Listen("unix", "testing/test.sock")
			is.NoErr(err)

			api := api.NewAPI()

			server := &http.Server{Handler: api}
			go server.Serve(listener)
			defer server.Close()

			for _, step := range test {
				req, err := step.Request()
				is.NoErr(err)

				res, err := client.Do(req)
				is.NoErr(err)

				if step.ExpectedStatus == 0 {
					step.ExpectedStatus = 200
				}
				is.Equal(res.StatusCode, step.ExpectedStatus)

				bodyBytes, err := io.ReadAll(res.Body)
				is.NoErr(err)
				if step.ExpectedProtobuf != nil {
					actualProtobuf := &pb.FeedMessage{}
					var err error
					if res.Header.Get("Content-Type") == "application/json" {
						err = protojson.Unmarshal(bodyBytes, actualProtobuf)
					} else {
						is.Equal(res.Header.Get("Content-Type"), "application/protobuf")
						err = proto.Unmarshal(bodyBytes, actualProtobuf)
					}
					is.NoErr(err)

					expectedProtobuf, err := step.ExpectedProtobuf()
					is.NoErr(err)

					is.Equal("", cmp.Diff(
						expectedProtobuf,
						actualProtobuf,
						protocmp.Transform(),
						protocmp.FilterField(
							&pb.FeedMessage{},
							"header",
							cmp.Comparer(func(msg1 protocmp.Message, msg2 protocmp.Message) bool {
								a := msg1.Unwrap().(*pb.FeedHeader)
								b := msg2.Unwrap().(*pb.FeedHeader)
								if a.GetGtfsRealtimeVersion() != b.GetGtfsRealtimeVersion() {
									return false
								}
								if a.GetIncrementality() != b.GetIncrementality() {
									return false
								}
								if a.GetTimestamp() < b.GetTimestamp()-1 || a.GetTimestamp() > b.GetTimestamp()+1 {
									return false
								}
								return true
							}),
						),
					))
				}
				if step.ExpectedJSON != nil {
					is.Equal(strings.Split(res.Header.Get("Content-Type"), "; ")[0], "application/json")

					expectedJSON, err := step.ExpectedJSON()
					is.NoErr(err)

					actualJSON := map[string]any{}
					err = json.Unmarshal(bodyBytes, &actualJSON)
					is.NoErr(err)

					is.Equal("", cmp.Diff(
						expectedJSON,
						actualJSON,
						cmp.Transformer("replaceNoBreakSpace", func(s string) string {
							// proto errors randomly sometimes have this unicode character instead of an ASCII space
							return strings.ReplaceAll(s, "\u00a0", " ")
						}),
					))
				}
			}
		})
	}
}

func SimpleGet(path string) func() (*http.Request, error) {
	return func() (*http.Request, error) {
		return http.NewRequest("GET", "http://foo.com"+path, nil)
	}
}
