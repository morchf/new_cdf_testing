package gtfs

import "fmt"

var ErrInvalidJSON = fmt.Errorf("invalid JSON input")
var ErrNotFound = fmt.Errorf("no entity with that ID")
var ErrIDMustBeUnique = fmt.Errorf("entity id must be unique")
var ErrTooSoon = fmt.Errorf("calling api too frequently")
