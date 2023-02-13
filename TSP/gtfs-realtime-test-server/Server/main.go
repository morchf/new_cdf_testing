package main

import (
	"bytes"
	"log"
	"net/http"
	"net/http/httptest"
	"os"
	"strings"

	"github.com/gin-gonic/gin"
	"github.com/gtt/gtfs-realtime-test-server/Server/api"
	"github.com/gtt/gtfs-realtime-test-server/Server/mqtt"
)

func main() {
	api := api.NewAPI()
	api.Use(gin.Logger())

	err := subscribeToIoTCore(api)
	if err != nil {
		log.Println("No IoT Core connection:", err)
	}

	log.Println("Listening on port 8080")
	http.ListenAndServe(":8080", api)
}

func subscribeToIoTCore(api *gin.Engine) error {
	topics := strings.Split(os.Getenv("MQTT_TOPICS"), ";")

	mqttSubscriber, err := mqtt.NewSubscriber(topics)
	if err != nil {
		return err
	}
	mqttSubscriber.Subscribe(func(mqttMsg []byte) {
		r, err := http.NewRequest(http.MethodPost, "http://localhost:8080/mqtt", bytes.NewReader(mqttMsg))
		if err != nil {
			log.Println(err)
			return
		}
		w := httptest.NewRecorder()
		api.ServeHTTP(w, r)
		if w.Result().StatusCode != http.StatusOK {
			log.Println(w.Result().Status)
		}
	})
	return nil
}
