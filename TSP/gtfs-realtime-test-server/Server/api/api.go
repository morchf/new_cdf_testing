package api

import (
	"errors"
	"fmt"
	"log"
	"strconv"
	"time"

	"github.com/gin-gonic/gin"
	"github.com/gtt/gtfs-realtime-test-server/Server/gtfs"
	"github.com/gtt/gtfs-realtime-test-server/Server/mqtt"
)

type Status string

const (
	Success Status = "success"
	Error   Status = "error"
)

type StatusMessage struct {
	Type    Status `json:"type"`
	Message string `json:"message"`
}

func NewAPI() *gin.Engine {
	api := gin.New()

	useGTFSRealtimeAPI(api, "/gtfs-rt/:agency-id/vehiclepositions")
	useGTFSRealtimeAPI(api, "/gtfs-rt/:agency-id/tripupdates")

	mqttSpy := mqtt.NewSpy()

	api.GET("/mqtt", getMQTTMessages(mqttSpy))
	api.POST("/mqtt", handleMQTTMessage(mqttSpy))

	subscriber, err := mqtt.NewSubscriber([]string{})
	if err != nil {
		log.Println(err)
	}
	subscriber.Subscribe(func(mqttMsg []byte) {
		err := mqttSpy.HandleMessage(mqttMsg)
		if err != nil {
			log.Println("Error handling message:", err)
		}
	})

	api.POST("/subscribe", subscribeToTopic(subscriber))

	api.Static("/docs/", "./docs")

	return api
}

func useGTFSRealtimeAPI(api *gin.Engine, path string) {
	feedMessages := map[string]*gtfs.FeedMessage{}

	feedMsgGroup := api.Group(path)
	feedMsgGroup.Use(func(ctx *gin.Context) {
		agencyName := ctx.Param("agency-id")
		feedMsg, ok := feedMessages[agencyName]
		if !ok {
			feedMsg = gtfs.NewFeedMessage(gtfs.NewFrequencyRestrictorFromEnv())
			feedMessages[agencyName] = feedMsg
		}
		ctx.Set("feedMsg", feedMsg)
		ctx.Next()
	})

	feedMsgGroup.GET("", getFeedMessage)
	feedMsgGroup.PUT("", setFeedMessage)
	feedMsgGroup.PATCH("", updateFeedMessage)

	feedEntitiesGroup := feedMsgGroup.Group("/entities")

	feedEntitiesGroup.GET("/:id", getFeedEntity)
	feedEntitiesGroup.POST("", createFeedEntity)
	feedEntitiesGroup.PUT("/:id", setFeedEntity)
	feedEntitiesGroup.PATCH("/:id", updateFeedEntity)
	feedEntitiesGroup.DELETE("/:id", removeFeedEntity)
}

func feedMsgFromCtx(ctx *gin.Context) (*gtfs.FeedMessage, error) {
	value, ok := ctx.Get("feedMsg")
	if !ok {
		return nil, fmt.Errorf("no FeedMessage object")
	}
	feedMsg, ok := value.(*gtfs.FeedMessage)
	if !ok {
		return nil, fmt.Errorf("'feedMsg' is incorrect type; expected *gtfs.FeedMessage")
	}
	return feedMsg, nil
}

func getFeedMessage(ctx *gin.Context) {
	feedMsg, err := feedMsgFromCtx(ctx)
	if err != nil {
		ctx.JSON(500, StatusMessage{Type: Error, Message: err.Error()})
	}

	var feedMsgBytes []byte
	var contentType string

	if ctx.ContentType() == "application/json" {
		feedMsgBytes, err = feedMsg.GetJSON()
		contentType = "application/json"
	} else {
		feedMsgBytes, err = feedMsg.Get()
		contentType = "application/protobuf"
	}

	if err == gtfs.ErrTooSoon {
		ctx.JSON(400, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	if err != nil {
		ctx.JSON(500, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	ctx.Data(200, contentType, feedMsgBytes)
}

func setFeedMessage(ctx *gin.Context) {
	feedMsg, err := feedMsgFromCtx(ctx)
	if err != nil {
		ctx.JSON(500, StatusMessage{Type: Error, Message: err.Error()})
	}

	body, _ := ctx.GetRawData()
	err = feedMsg.Set(body)
	if err != nil {
		ctx.JSON(400, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	ctx.JSON(200, StatusMessage{
		Type:    Success,
		Message: fmt.Sprintf("Successfully set FeedMessage at %s", ctx.Request.URL.Path),
	})
}

func updateFeedMessage(ctx *gin.Context) {
	feedMsg, err := feedMsgFromCtx(ctx)
	if err != nil {
		ctx.JSON(500, StatusMessage{Type: Error, Message: err.Error()})
	}

	body, _ := ctx.GetRawData()
	err = feedMsg.Update(body)
	if err != nil {
		ctx.JSON(400, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	ctx.JSON(200, StatusMessage{
		Type:    Success,
		Message: fmt.Sprintf("Successfully updated FeedMessage at %s", ctx.Request.URL.Path),
	})
}

func getFeedEntity(ctx *gin.Context) {
	feedMsg, err := feedMsgFromCtx(ctx)
	if err != nil {
		ctx.JSON(500, StatusMessage{Type: Error, Message: err.Error()})
	}

	id := ctx.Param("id")
	bytes, err := feedMsg.GetEntity(id)
	if err != nil {
		ctx.JSON(404, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	ctx.Data(200, "application/json", bytes)
}

func createFeedEntity(ctx *gin.Context) {
	feedMsg, err := feedMsgFromCtx(ctx)
	if err != nil {
		ctx.JSON(500, StatusMessage{Type: Error, Message: err.Error()})
	}

	body, _ := ctx.GetRawData()
	err = feedMsg.CreateEntity(body)
	if err != nil {
		ctx.JSON(400, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	ctx.JSON(200, StatusMessage{
		Type:    Success,
		Message: "Successfully created entity",
	})
}

func setFeedEntity(ctx *gin.Context) {
	feedMsg, err := feedMsgFromCtx(ctx)
	if err != nil {
		ctx.JSON(500, StatusMessage{Type: Error, Message: err.Error()})
	}

	id := ctx.Param("id")
	body, _ := ctx.GetRawData()
	err = feedMsg.SetEntity(id, body)
	if errors.Is(err, gtfs.ErrNotFound) {
		ctx.JSON(404, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	if err != nil {
		ctx.JSON(400, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	ctx.JSON(200, StatusMessage{
		Type:    Success,
		Message: fmt.Sprintf("Successfully set entity '%s'", id),
	})
}

func updateFeedEntity(ctx *gin.Context) {
	feedMsg, err := feedMsgFromCtx(ctx)
	if err != nil {
		ctx.JSON(500, StatusMessage{Type: Error, Message: err.Error()})
	}

	id := ctx.Param("id")
	body, _ := ctx.GetRawData()
	err = feedMsg.UpdateEntity(id, body)
	if errors.Is(err, gtfs.ErrNotFound) {
		ctx.JSON(404, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	if err != nil {
		ctx.JSON(400, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	ctx.JSON(200, StatusMessage{
		Type:    Success,
		Message: fmt.Sprintf("Successfully updated entity '%s'", id),
	})

}

func removeFeedEntity(ctx *gin.Context) {
	feedMsg, err := feedMsgFromCtx(ctx)
	if err != nil {
		ctx.JSON(500, StatusMessage{Type: Error, Message: err.Error()})
	}

	id := ctx.Param("id")
	err = feedMsg.RemoveEntity(id)
	if err != nil {
		ctx.JSON(404, StatusMessage{
			Type:    Error,
			Message: err.Error(),
		})
		return
	}
	ctx.JSON(200, StatusMessage{
		Type:    Success,
		Message: fmt.Sprintf("Successfully removed entity '%s'", id),
	})
}

func getMQTTMessages(spy *mqtt.Spy) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		ageThreshold, err := strconv.ParseFloat(ctx.Query("age"), 64)
		if err != nil {
			ageThreshold = 0
		}
		topics := ctx.QueryArray("topic")
		if len(topics) == 0 {
			topics = nil
		}
		messages, err := spy.GetMessages(time.Duration(float64(time.Second)*ageThreshold), topics)
		if err != nil {
			ctx.JSON(500, StatusMessage{
				Type:    Error,
				Message: err.Error(),
			})
			return
		}
		ctx.Data(200, "application/json", messages)
	}
}

func handleMQTTMessage(spy *mqtt.Spy) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		rawMQTTJSON, _ := ctx.GetRawData()
		err := spy.HandleMessage(rawMQTTJSON)
		if err != nil {
			ctx.JSON(400, StatusMessage{
				Type:    Error,
				Message: err.Error(),
			})
			return
		}
		ctx.JSON(200, StatusMessage{
			Type:    Success,
			Message: "Successfully handled MQTT Message",
		})
	}
}

func subscribeToTopic(subscriber *mqtt.Subscriber) gin.HandlerFunc {
	return func(ctx *gin.Context) {
		body := struct {
			Topic string `json:"topic"`
		}{}
		err := ctx.BindJSON(&body)
		if err != nil {
			ctx.JSON(400, StatusMessage{
				Type:    Error,
				Message: err.Error(),
			})
			return
		}
		topic := body.Topic
		err = subscriber.SubscribeToTopic(topic)
		if err != nil {
			ctx.JSON(500, StatusMessage{
				Type:    Error,
				Message: err.Error(),
			})
			return
		}
		ctx.JSON(200, StatusMessage{
			Type:    Success,
			Message: fmt.Sprintf("Subscribed to '%s'", topic),
		})
	}
}
