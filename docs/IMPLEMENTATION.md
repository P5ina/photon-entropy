# План имплементации PhotonEntropy

## Обзор

**Срок:** 7 дней  
**Цель:** Работающий прототип для защиты курсовой

---

## День 1: Backend — Основа + Docker

### Задачи

1. Инициализация Go проекта
2. Dockerfile и docker-compose
3. Настройка sqlc и goose
4. Базовая структура и роутинг
5. Health endpoint

### Команды

```bash
cd backend
go mod init photon-entropy
go get github.com/gin-gonic/gin
go get modernc.org/sqlite
go get github.com/pressly/goose/v3
```

### Файлы

- [ ] `Dockerfile` — multi-stage build
- [ ] `docker-compose.yml` — сервис + volume для БД
- [ ] `sqlc.yaml` — конфигурация sqlc
- [ ] `main.go` — точка входа, инициализация Gin
- [ ] `config/config.go` — загрузка конфигурации
- [ ] `handlers/health.go` — GET /health

### Dockerfile

```dockerfile
# Build stage
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Установка инструментов
RUN go install github.com/sqlc-dev/sqlc/cmd/sqlc@latest
RUN go install github.com/pressly/goose/v3/cmd/goose@latest

COPY go.mod go.sum ./
RUN go mod download

COPY . .

# Генерация sqlc
RUN sqlc generate

# Сборка
RUN CGO_ENABLED=0 GOOS=linux go build -o /photon-entropy

# Runtime stage
FROM alpine:3.19

RUN apk --no-cache add ca-certificates

WORKDIR /app

COPY --from=builder /photon-entropy .
COPY --from=builder /go/bin/goose /usr/local/bin/goose
COPY db/migrations ./db/migrations

EXPOSE 8080

CMD ["./photon-entropy"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8080:8080"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_PATH=/app/data/photon.db
      - GIN_MODE=release
    restart: unless-stopped
```

### sqlc.yaml

```yaml
version: "2"
sql:
  - engine: "sqlite"
    queries: "db/queries"
    schema: "db/migrations"
    gen:
      go:
        package: "sqlc"
        out: "db/sqlc"
        emit_json_tags: true
        emit_empty_slices: true
```

### Результат дня

```bash
docker-compose up -d
curl http://localhost:8080/health
# {"status": "ok", "timestamp": "..."}
```

---

## День 2: Backend — Миграции + Верификатор

### Задачи

1. Goose миграции для SQLite
2. SQL запросы для sqlc
3. Реализация 4 статистических тестов на Go

### Файлы

- [ ] `db/migrations/001_init.sql` — создание таблиц
- [ ] `db/migrations/002_add_indexes.sql` — индексы
- [ ] `db/queries/commits.sql` — CRUD для коммитов
- [ ] `db/queries/devices.sql` — CRUD для устройств
- [ ] `verifier/tests.go` — FrequencyTest, RunsTest, ChiSquareTest, VarianceTest
- [ ] `verifier/verifier.go` — Verify(samples) → TestResults

### Миграция 001_init.sql

```sql
-- +goose Up
CREATE TABLE devices (
    id TEXT PRIMARY KEY,
    last_seen DATETIME,
    total_commits INTEGER DEFAULT 0,
    average_quality REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE commits (
    id TEXT PRIMARY KEY,
    device_id TEXT NOT NULL,
    raw_samples BLOB NOT NULL,
    timestamps BLOB,
    quality REAL NOT NULL,
    test_frequency_passed INTEGER NOT NULL,
    test_frequency_ratio REAL,
    test_runs_passed INTEGER NOT NULL,
    test_runs_total INTEGER,
    test_runs_max_length INTEGER,
    test_chi_passed INTEGER NOT NULL,
    test_chi_value REAL,
    test_variance_passed INTEGER NOT NULL,
    test_variance_value REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES devices(id)
);

-- +goose Down
DROP TABLE commits;
DROP TABLE devices;
```

### Миграция 002_add_indexes.sql

```sql
-- +goose Up
CREATE INDEX idx_commits_device_id ON commits(device_id);
CREATE INDEX idx_commits_created_at ON commits(created_at);
CREATE INDEX idx_devices_last_seen ON devices(last_seen);

-- +goose Down
DROP INDEX idx_commits_device_id;
DROP INDEX idx_commits_created_at;
DROP INDEX idx_devices_last_seen;
```

### db/queries/commits.sql

```sql
-- name: CreateCommit :one
INSERT INTO commits (
    id, device_id, raw_samples, timestamps, quality,
    test_frequency_passed, test_frequency_ratio,
    test_runs_passed, test_runs_total, test_runs_max_length,
    test_chi_passed, test_chi_value,
    test_variance_passed, test_variance_value
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
RETURNING *;

-- name: GetCommitByID :one
SELECT * FROM commits WHERE id = ?;

-- name: GetCommitsByDevice :many
SELECT * FROM commits 
WHERE device_id = ? 
ORDER BY created_at DESC 
LIMIT ?;

-- name: GetRecentCommits :many
SELECT * FROM commits 
ORDER BY created_at DESC 
LIMIT ?;

-- name: CountCommitsByDevice :one
SELECT COUNT(*) FROM commits WHERE device_id = ?;

-- name: GetAverageQualityByDevice :one
SELECT AVG(quality) FROM commits WHERE device_id = ?;
```

### db/queries/devices.sql

```sql
-- name: CreateDevice :one
INSERT INTO devices (id) VALUES (?) RETURNING *;

-- name: GetDevice :one
SELECT * FROM devices WHERE id = ?;

-- name: UpdateDeviceStats :exec
UPDATE devices 
SET last_seen = ?, total_commits = ?, average_quality = ?
WHERE id = ?;

-- name: UpsertDevice :one
INSERT INTO devices (id, last_seen, total_commits, average_quality)
VALUES (?, ?, ?, ?)
ON CONFLICT(id) DO UPDATE SET
    last_seen = excluded.last_seen,
    total_commits = excluded.total_commits,
    average_quality = excluded.average_quality
RETURNING *;

-- name: GetAllDevices :many
SELECT * FROM devices ORDER BY last_seen DESC;

-- name: GetOnlineDevices :many
SELECT * FROM devices 
WHERE last_seen > datetime('now', '-2 minutes')
ORDER BY last_seen DESC;
```

### Генерация кода

```bash
# Применить миграции
goose -dir db/migrations sqlite3 ./data/photon.db up

# Сгенерировать Go код
sqlc generate
```

### Результат дня

```go
verifier := NewVerifier()
result := verifier.Verify(samples)
// result.Quality = 1.0, result.Tests.Frequency.Passed = true

// sqlc сгенерировал типобезопасные методы
queries.CreateCommit(ctx, sqlc.CreateCommitParams{...})
```

---

## День 3: Backend — API Endpoints

### Задачи

1. POST /api/v1/entropy/submit — приём от Pi
2. GET /api/v1/entropy/random — генерация рандома
3. GET /api/v1/device/status — статус устройства
4. GET /api/v1/device/history — история коммитов
5. Entropy Pool для накопления

### Файлы

- [ ] `handlers/entropy.go` — Submit, Random, Password, UUID
- [ ] `handlers/device.go` — Status, History
- [ ] `entropy/pool.go` — EntropyPool с thread-safe доступом

### Пример хендлера с sqlc

```go
func (h *EntropyHandler) Submit(c *gin.Context) {
    var req SubmitRequest
    if err := c.ShouldBindJSON(&req); err != nil {
        c.JSON(400, gin.H{"error": err.Error()})
        return
    }

    // Верификация
    result := h.verifier.Verify(req.RawSamples)
    
    // Сохранение через sqlc
    commit, err := h.queries.CreateCommit(c, sqlc.CreateCommitParams{
        ID:                   uuid.New().String(),
        DeviceID:             req.DeviceID,
        RawSamples:           encodeIntSlice(req.RawSamples),
        Quality:              result.Quality,
        TestFrequencyPassed:  boolToInt(result.Frequency.Passed),
        TestFrequencyRatio:   sql.NullFloat64{Float64: result.Frequency.Ratio, Valid: true},
        // ...
    })
    
    // Обновление статистики устройства
    h.queries.UpsertDevice(c, sqlc.UpsertDeviceParams{
        ID:             req.DeviceID,
        LastSeen:       sql.NullTime{Time: time.Now(), Valid: true},
        TotalCommits:   count + 1,
        AverageQuality: avgQuality,
    })

    c.JSON(200, CommitResponse{
        ID:       commit.ID,
        Quality:  commit.Quality,
        Accepted: result.Quality >= 0.5,
    })
}
```

### API контракты

```
POST /api/v1/entropy/submit
Request:
{
    "device_id": "pi-001",
    "raw_samples": [2643, 2701, 2589, ...],
    "timestamps": [1699001234567, ...]
}
Response:
{
    "id": "abc123",
    "quality": 1.0,
    "tests": {...},
    "accepted": true
}

GET /api/v1/entropy/random?min=1&max=100
Response:
{
    "value": 42,
    "source_commit": "abc123",
    "generated_at": "..."
}
```

### Результат дня

Полностью работающий API, можно тестировать через curl/Postman.

---

## День 4: IoT — Клиент для Pi

### Задачи

1. Рефакторинг существующего кода в модули
2. HTTP клиент для отправки на бэкенд
3. Конфигурация и CLI аргументы
4. Автоматический цикл сбора

### Файлы

- [ ] `iot/config.py` — настройки
- [ ] `iot/entropy_collector.py` — класс LightEntropyPool (из существующего)
- [ ] `iot/entropy_tester.py` — класс EntropyTester (из существующего)
- [ ] `iot/api_client.py` — PhotonEntropyClient
- [ ] `iot/main.py` — главный цикл

### Главный цикл

```python
while True:
    # 1. Собираем энтропию
    samples, timestamps = collector.collect(duration=30)
    
    # 2. Локальная проверка качества
    quality = tester.test(samples)
    if quality < 0.5:
        logger.warning("Low quality, skipping")
        continue
    
    # 3. Отправка на сервер
    response = client.submit(samples, timestamps)
    logger.info(f"Submitted: {response['id']}, quality: {response['quality']}")
    
    # 4. Пауза
    time.sleep(COLLECT_INTERVAL)
```

### Результат дня

Pi автоматически собирает и отправляет энтропию на сервер.

---

## День 5: Mobile — UI + API

### Задачи

1. Создание Xcode проекта
2. API сервис для связи с бэкендом
3. Модели данных (Codable)
4. Dashboard View — статус устройства

### Файлы

- [ ] `APIService.swift` — async/await HTTP клиент
- [ ] `Models/` — EntropyCommit, DeviceStatus, RandomResponse
- [ ] `DashboardView.swift` — главный экран
- [ ] `DashboardViewModel.swift` — логика

### Dashboard UI

```
┌─────────────────────────────────┐
│         PhotonEntropy           │
├─────────────────────────────────┤
│                                 │
│    ◉ Device Online              │
│    pi-001                       │
│                                 │
│    ┌─────────┐ ┌─────────┐     │
│    │ Quality │ │ Commits │     │
│    │  100%   │ │   142   │     │
│    └─────────┘ └─────────┘     │
│                                 │
│    Last update: 30 sec ago      │
│                                 │
├─────────────────────────────────┤
│  [Generator]  [History]  [More] │
└─────────────────────────────────┘
```

### Результат дня

Мобилка показывает реальный статус устройства с бэкенда.

---

## День 6: Mobile — Генератор + История

### Задачи

1. Generator View — генерация рандома
2. History View — список коммитов
3. Компоненты (QualityBadge, Chart)
4. Pull-to-refresh, loading states

### Generator UI

```
┌─────────────────────────────────┐
│         🎲 Generator            │
├─────────────────────────────────┤
│                                 │
│    ┌─────────────────────┐      │
│    │                     │      │
│    │         42          │      │
│    │                     │      │
│    └─────────────────────┘      │
│                                 │
│    Range: [1]  to  [100]        │
│                                 │
│    [ Generate Number ]          │
│                                 │
│    ─────────────────────        │
│                                 │
│    [ Generate Password ]        │
│    Length: 16  ●●●○○            │
│                                 │
│    [ Generate UUID ]            │
│                                 │
└─────────────────────────────────┘
```

### History UI

```
┌─────────────────────────────────┐
│          📜 History             │
├─────────────────────────────────┤
│                                 │
│  ┌───────────────────────────┐  │
│  │ abc123       ✓ 100%       │  │
│  │ 500 samples  2 min ago    │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ def456       ✓ 100%       │  │
│  │ 500 samples  5 min ago    │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ghi789       ⚠ 75%        │  │
│  │ 320 samples  8 min ago    │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

### Результат дня

Полнофункциональное мобильное приложение.

---

## День 7: Интеграция + Polish

### Задачи

1. End-to-end тестирование всей системы
2. Обработка ошибок везде
3. README с скриншотами
4. Подготовка демо для защиты

### Чеклист

- [ ] Pi → Backend работает стабильно
- [ ] Backend → Mobile работает стабильно
- [ ] Обработка офлайна Pi (статус меняется)
- [ ] Обработка офлайна Backend (мобилка показывает ошибку)
- [ ] Нет крашей при edge cases
- [ ] Скриншоты в README
- [ ] Демо-скрипт для защиты

### Демо-сценарий для защиты

```
1. Показать железку (Pi + датчик)
2. Запустить сбор, показать логи
3. Открыть мобилку — статус Online
4. Сгенерировать число через приложение
5. Показать историю коммитов
6. Накрыть датчик рукой — показать как меняется raw
7. Включить свет — показать что сбор приостанавливается
8. Объяснить статистические тесты
```

---

## Итого

| День | Компонент | Часов | Результат |
|------|-----------|-------|-----------|
| 1 | Backend основа | 3-4 | Gin + структура |
| 2 | Backend верификатор | 4-5 | Тесты + SQLite |
| 3 | Backend API | 3-4 | Все endpoints |
| 4 | IoT клиент | 3-4 | Автосбор + отправка |
| 5 | Mobile UI | 4-5 | Dashboard |
| 6 | Mobile фичи | 4-5 | Generator + History |
| 7 | Polish | 3-4 | Тесты + демо |

**Всего:** ~25-30 часов

---

## Риски и митигация

| Риск | Вероятность | Митигация |
|------|-------------|-----------|
| Не успеваю мобилку | Средняя | Минимальный UI, без анимаций |
| Проблемы с сетью Pi→Backend | Низкая | Локальный сервер, один WiFi |
| Датчик ведёт себя странно | Низкая | Есть запасной фоторезистор |
| Go незнакомый | Средняя | Простой код, много примеров |

---

## Бонусы (если останется время)

- [ ] WebSocket для realtime обновлений
- [ ] График энтропии в мобилке (Charts framework)
- [ ] Dark mode
- [ ] Несколько устройств
- [x] Docker для бэкенда (уже в плане)
- [ ] CI/CD (GitHub Actions)
- [ ] Prometheus метрики

