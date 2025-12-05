# PhotonEntropy

Сервис генерации доказуемо честного рандома на основе аппаратного генератора случайных чисел (HRNG).

**Курсовая работа** — Mobile & IoT

## Обзор

PhotonEntropy использует физический шум фоторезистора как источник криптографически качественной энтропии. Система состоит из трёх компонентов:

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│   Raspberry Pi   │       │    Go Backend    │       │   Mobile App     │
│                  │       │                  │       │                  │
│  ┌────────────┐  │       │  ┌────────────┐  │       │  ┌────────────┐  │
│  │ ADS1115    │  │ HTTP  │  │ Verifier   │  │ HTTP  │  │ Dashboard  │  │
│  │ + фоторез. │──┼──────▶│  │ + Storage  │◀─┼──────▶│  │ + Generator│  │
│  └────────────┘  │       │  └────────────┘  │       │  └────────────┘  │
│                  │       │                  │       │                  │
│  Сбор энтропии   │       │  API + SQLite    │       │  Swift/SwiftUI   │
└──────────────────┘       └──────────────────┘       └──────────────────┘
```

## Возможности

### IoT устройство (Raspberry Pi)
- Сбор энтропии с фоторезистора через ADS1115 (16-bit АЦП)
- Автоматическая фильтрация по освещённости (сбор только в темноте)
- Статистические тесты качества перед отправкой
- Периодическая отправка данных на бэкенд

### Backend (Go)
- Приём и верификация энтропии от устройств
- 4 статистических теста качества (Frequency, Runs, Chi-Square, Variance)
- Хранение истории в SQLite
- REST API для мобильного приложения
- Генерация случайных чисел, паролей, UUID

### Mobile (Swift/SwiftUI)
- Дашборд статуса IoT устройства
- Генератор случайных чисел и паролей
- История коммитов с визуализацией качества
- График энтропии в реальном времени

## Архитектура

### API Endpoints

```
IoT → Backend:
  POST /api/v1/entropy/submit     Отправка сырых данных

Mobile → Backend:
  GET  /api/v1/entropy/random     Получить случайное число
  GET  /api/v1/entropy/password   Сгенерировать пароль
  GET  /api/v1/entropy/uuid       Сгенерировать UUID
  GET  /api/v1/device/status      Статус IoT устройства
  GET  /api/v1/device/history     История коммитов
  GET  /api/v1/stats              Общая статистика

Health:
  GET  /health                    Проверка состояния сервера
```

### Модели данных

```go
// Коммит энтропии от устройства
type EntropyCommit struct {
    ID            string    `json:"id"`
    DeviceID      string    `json:"device_id"`
    RawSamples    []int     `json:"raw_samples"`
    Timestamps    []int64   `json:"timestamps"`
    Quality       float64   `json:"quality"`
    TestResults   Tests     `json:"test_results"`
    CreatedAt     time.Time `json:"created_at"`
}

// Результаты тестов
type Tests struct {
    Frequency  TestResult `json:"frequency"`
    Runs       TestResult `json:"runs"`
    ChiSquare  TestResult `json:"chi_square"`
    Variance   TestResult `json:"variance"`
}

// Статус устройства
type DeviceStatus struct {
    DeviceID        string    `json:"device_id"`
    IsOnline        bool      `json:"is_online"`
    LastSeen        time.Time `json:"last_seen"`
    TotalCommits    int       `json:"total_commits"`
    AverageQuality  float64   `json:"average_quality"`
    EntropyPool     int       `json:"entropy_pool_size"`
}
```

## Структура проекта

```
photon-entropy/
├── README.md
├── docs/
│   └── IMPLEMENTATION.md
│
├── iot/                          # Raspberry Pi
│   ├── requirements.txt
│   ├── config.py
│   ├── entropy_collector.py      # Сбор с АЦП
│   ├── entropy_tester.py         # Статистические тесты
│   ├── api_client.py             # HTTP клиент
│   └── main.py                   # Точка входа
│
├── backend/                      # Go сервер
│   ├── Dockerfile
│   ├── compose.yml
│   ├── go.mod
│   ├── go.sum
│   ├── main.go
│   ├── sqlc.yaml                 # Конфигурация sqlc
│   ├── config/
│   │   └── config.go
│   ├── db/
│   │   ├── migrations/           # Goose миграции
│   │   │   ├── 001_init.sql
│   │   │   └── 002_add_indexes.sql
│   │   ├── queries/              # SQL запросы для sqlc
│   │   │   ├── commits.sql
│   │   │   └── devices.sql
│   │   └── sqlc/                 # Сгенерированный код
│   │       ├── db.go
│   │       ├── models.go
│   │       ├── commits.sql.go
│   │       └── devices.sql.go
│   ├── handlers/
│   │   ├── entropy.go            # Приём/выдача энтропии
│   │   ├── device.go             # Статус устройств
│   │   └── stats.go              # Статистика
│   ├── verifier/
│   │   ├── verifier.go           # Главный верификатор
│   │   └── tests.go              # Реализация тестов
│   └── entropy/
│       └── pool.go               # Пул энтропии
│
└── mobile/                       # iOS приложение
    └── PhotonEntropy/
        ├── PhotonEntropyApp.swift
        ├── Models/
        │   ├── EntropyCommit.swift
        │   └── DeviceStatus.swift
        ├── Services/
        │   └── APIService.swift
        ├── ViewModels/
        │   ├── DashboardViewModel.swift
        │   └── GeneratorViewModel.swift
        └── Views/
            ├── DashboardView.swift
            ├── GeneratorView.swift
            ├── HistoryView.swift
            └── Components/
                ├── QualityBadge.swift
                └── EntropyChart.swift
```

## Аппаратные требования

### Компоненты

| Компонент | Описание | Примерная цена |
|-----------|----------|----------------|
| Raspberry Pi | Любая модель с I2C | $35-55 |
| ADS1115 | 16-bit АЦП модуль | $3-5 |
| Фоторезистор | GL5528 или аналог | $0.5 |
| Резистор 10kΩ | Делитель напряжения | $0.1 |
| Провода | Dupont jumper | $2 |

### Схема подключения

```
Raspberry Pi            ADS1115                 Датчик
     │                     │                       │
 3.3V├─────────────────────┤VDD                    │
     │                     │           ┌───────────┤
  SDA├─────────────────────┤SDA        │    Фоторезистор
     │                     │           │           │
  SCL├─────────────────────┤SCL        │     ┌─────┴─────┐
     │                     │           │     │           │
  GND├─────────────────────┤GND        │     │  10kΩ     │
     │                     │           │     │           │
     │                  A0 ├───────────┴─────┴───────────┤
     │                     │                             │
     │                 GND ├─────────────────────────────┘
```

## Быстрый старт

### 1. Backend (Docker)

```bash
cd backend

# Запуск с docker-compose
docker-compose up -d

# Или вручную
docker build -t photon-entropy .
docker run -p 8080:8080 -v $(pwd)/data:/app/data photon-entropy
```

Сервер запустится на `http://localhost:8080`

### Разработка (без Docker)

```bash
cd backend

# Установка инструментов
go install github.com/sqlc-dev/sqlc/cmd/sqlc@latest
go install github.com/pressly/goose/v3/cmd/goose@latest

# Миграции
goose -dir db/migrations sqlite3 ./data/photon.db up

# Генерация sqlc
sqlc generate

# Запуск
go run main.go
```

### 2. IoT устройство

```bash
cd iot
pip install -r requirements.txt
python main.py --server http://your-server:8080
```

### 3. Mobile

Открыть `mobile/PhotonEntropy.xcodeproj` в Xcode и запустить.

## Конфигурация

### IoT (config.py)

```python
SERVER_URL = "http://192.168.1.100:8080"
DEVICE_ID = "pi-001"
COLLECT_INTERVAL = 30        # секунд между сборами
SAMPLES_PER_COMMIT = 500     # сэмплов на коммит
LIGHT_THRESHOLD = 2000       # порог освещённости
```

### Backend (config.yaml)

```yaml
server:
  port: 8080
  host: "0.0.0.0"

database:
  path: "./photon_entropy.db"

entropy:
  min_samples: 100
  min_quality: 0.5
  pool_size: 4096

device:
  offline_timeout: 120  # секунд
```

## Статистические тесты

Каждый коммит энтропии проверяется 4 тестами:

| Тест | Описание | Критерий прохождения |
|------|----------|---------------------|
| **Frequency** | Баланс единиц и нулей | 45-55% единиц |
| **Runs** | Отсутствие длинных серий | Серии < 2×log₂(n) |
| **Chi-Square** | Равномерность 2-bit комбинаций | χ² < 7.81 |
| **Variance** | Дисперсия младших битов | 0.5-1.5× от ожидаемой |

Качество = процент пройденных тестов (0%, 25%, 50%, 75%, 100%)

## Скриншоты

*Добавить скриншоты мобильного приложения*

## Технологии

- **IoT**: Python 3, adafruit-circuitpython-ads1x15
- **Backend**: Go 1.21+, Gin, SQLite, sqlc, goose, Docker
- **Mobile**: Swift 5, SwiftUI, iOS 16+

## Лицензия

MIT

## Автор

Timur ([P5ina](https://github.com/P5ina)) — Курсовая работа, Mobile & IoT, 2025

