package gtfs

import (
	"os"
	"strconv"
	"sync"
	"time"
)

type FrequencyRestrictor struct {
	mu        sync.RWMutex
	frequency time.Duration
	nextTime  time.Time
}

func NewFrequencyRestrictor(frequency float64) *FrequencyRestrictor {
	return &FrequencyRestrictor{
		frequency: time.Duration(float64(time.Second) * frequency),
		nextTime:  time.Now(),
	}
}

func NewFrequencyRestrictorFromEnv() *FrequencyRestrictor {
	allowedFrequencyStr := os.Getenv("ALLOWED_FREQUENCY")
	allowedFrequency, err := strconv.ParseFloat(allowedFrequencyStr, 64)
	if err != nil {
		allowedFrequency = 0
	}
	return NewFrequencyRestrictor(allowedFrequency)
}

func (r *FrequencyRestrictor) IsTooSoon() bool {
	r.mu.RLock()
	defer r.mu.RUnlock()
	return time.Now().Before(r.nextTime)
}

func (r *FrequencyRestrictor) Reset() {
	r.mu.Lock()
	defer r.mu.Unlock()
	r.nextTime = time.Now().Add(r.frequency)
}
