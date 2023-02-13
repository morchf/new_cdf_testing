ARG BASE_CONTAINER_REPO="docker.io"
FROM ${BASE_CONTAINER_REPO}/golang:1.19-alpine as builder

WORKDIR /build

RUN addgroup -S user & adduser -S user

RUN apk add --no-cache ca-certificates

# Dependencies
COPY go.mod .
COPY go.sum .

RUN go mod download

# Source Files
COPY main.go .
COPY gtfs gtfs
COPY mqtt mqtt
COPY api api

# Build
RUN GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o test-server
RUN chown user:user test-server


# Final image
FROM scratch

WORKDIR /home/user

USER user

COPY --from=builder /build/test-server                  /bin/
COPY --from=builder /lib/ld-musl-x86_64.so.1            /lib/
COPY --from=builder /etc/ssl/certs/ca-certificates.crt  /etc/ssl/certs/

COPY --from=builder /etc/passwd /etc/

COPY docs docs

CMD [ "test-server" ]
