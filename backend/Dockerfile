# Build stage
FROM golang:1.25-alpine AS builder

WORKDIR /app

# Install build dependencies
RUN apk add --no-cache git

# Install tools
RUN go install github.com/sqlc-dev/sqlc/cmd/sqlc@latest
RUN go install github.com/pressly/goose/v3/cmd/goose@latest

# Copy go mod files
COPY go.mod go.sum ./
RUN go mod download

# Copy source
COPY . .

# Generate sqlc
RUN sqlc generate

# Build
RUN CGO_ENABLED=0 GOOS=linux go build -o /photon-entropy

# Runtime stage
FROM alpine:3.19

RUN apk --no-cache add ca-certificates

WORKDIR /app

COPY --from=builder /photon-entropy .
COPY --from=builder /go/bin/goose /usr/local/bin/goose
COPY db/migrations ./db/migrations

# Create data directory
RUN mkdir -p /app/data

EXPOSE 8082

CMD ["./photon-entropy"]
