package mqtt

import (
	"context"
	"encoding/base64"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"net/url"
	"sync"
	"time"

	"github.com/aws/aws-sdk-go-v2/aws"
	v4 "github.com/aws/aws-sdk-go-v2/aws/signer/v4"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/iot"
	mqtt "github.com/eclipse/paho.mqtt.golang"
)

const (
	serviceName  = "iotdevicegateway"
	emptyPayload = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
)

type Callback func(mqttMsg []byte)

type Subscriber struct {
	mu        sync.Mutex
	callbacks []Callback
	awsCfg    aws.Config
	endpoint  string
}

type SubscriberOptions struct {
	BrokerEndpoint string
	Topics         []string
}

func NewSubscriber(topics []string) (*Subscriber, error) {
	return NewSubscriberWithContext(context.TODO(), topics)
}

func NewSubscriberWithContext(ctx context.Context, topics []string) (*Subscriber, error) {
	awsCfg, err := config.LoadDefaultConfig(ctx)
	if err != nil {
		return nil, fmt.Errorf("NewSubscriber: no AWS config: %v", err)
	}

	descEndpointOutput, err := iot.NewFromConfig(awsCfg).DescribeEndpoint(ctx, &iot.DescribeEndpointInput{
		EndpointType: aws.String("iot:Data-ATS"),
	})
	if err != nil {
		return nil, fmt.Errorf("NewSubscriber: unable to get endpoint URL: %w", err)
	}
	endpoint := *descEndpointOutput.EndpointAddress

	return &Subscriber{
		callbacks: []Callback{},
		awsCfg:    awsCfg,
		endpoint:  endpoint,
	}, nil
}

func (subscriber *Subscriber) SubscribeToTopic(topic string) error {
	log.Println("Subscribing to:", subscriber.endpoint)
	client, err := connectToMQTT(context.TODO(), subscriber.endpoint, subscriber.awsCfg)
	if err != nil {
		return fmt.Errorf("NewSubscriber: %v", err)
	}
	log.Println("\t", topic)
	return waitForToken(context.TODO(), client.Subscribe(topic, 0, func(_ mqtt.Client, m mqtt.Message) {
		message := map[string]any{
			"topic":   m.Topic(),
			"payload": base64.StdEncoding.EncodeToString(m.Payload()),
		}
		messageBytes, _ := json.Marshal(message)
		subscriber.mu.Lock()
		defer subscriber.mu.Unlock()
		for _, callback := range subscriber.callbacks {
			callback(messageBytes)
		}
	}))
}

func (s *Subscriber) Subscribe(callback Callback) {
	s.mu.Lock()
	defer s.mu.Unlock()
	s.callbacks = append(s.callbacks, callback)
}

func connectToMQTT(ctx context.Context, endpoint string, awsCfg aws.Config) (mqtt.Client, error) {
	reqURL, err := url.Parse(fmt.Sprintf("wss://%s:443/mqtt", endpoint))
	if err != nil {
		return nil, fmt.Errorf("invalid endpoint URL: %w", err)
	}
	req := &http.Request{
		Method: "GET",
		URL:    reqURL,
	}

	creds, err := awsCfg.Credentials.Retrieve(ctx)
	if err != nil {
		return nil, fmt.Errorf("unable to retrieve AWS credentials: %w", err)
	}
	sessionToken := creds.SessionToken
	creds.SessionToken = ""
	presignedURL, _, err := v4.NewSigner().PresignHTTP(
		ctx,
		creds,
		req,
		emptyPayload,
		serviceName,
		awsCfg.Region,
		time.Now(),
	)
	if err != nil {
		return nil, fmt.Errorf("unable to sign request with AWS v4: %w", err)
	}
	if sessionToken != "" {
		presignedURL += "&X-Amz-Security-Token=" + url.QueryEscape(sessionToken)
	}

	clientOpts := mqtt.NewClientOptions()
	clientOpts.AddBroker(presignedURL)

	client := mqtt.NewClient(clientOpts)
	err = waitForToken(ctx, client.Connect())
	if err != nil {
		return nil, err
	}

	return client, nil
}

func waitForToken(ctx context.Context, token mqtt.Token) error {
	deadline, hasDeadline := ctx.Deadline()
	var didResolve bool
	if !hasDeadline {
		didResolve = token.Wait()
	} else {
		didResolve = token.WaitTimeout(time.Until(deadline))
	}
	if !didResolve {
		return fmt.Errorf("timed out")
	}
	if err := token.Error(); err != nil {
		return err
	}
	return nil
}
