# EMQX Bridge Service

A high-performance IoT Middleware service built with **Python 3.13** and **FastStream**.
This service acts as a bridge between an EMQX (MQTT) broker and RabbitMQ (AMQP). It intercepts MQTT messages, parses the topics, enriches the JSON payloads, and reliably forwards them to a RabbitMQ exchange.

## 🏗 Architecture

This project is built using **Hexagonal Architecture (Ports and Adapters)** to decouple the core business logic from external frameworks and infrastructure:

* **Core (Domain)**: Pure Python logic for parsing MQTT topics (`[Org]/[Project]/[Device-ID]/[Action]`), extracting `device_id`, generating AMQP routing keys, and enriching payloads.
* **Application (Ports & Services)**: Use case orchestrator (`BridgeService`) and abstract interfaces (`MessagePublisher`).
* **Infrastructure (Adapters)**: External connections including `aiomqtt` (for EMQX), `FastStream` (for RabbitMQ), and configuration management (`pydantic-settings`).

## ✨ Key Features

* **Robust MQTT Subscription**: Connects to EMQX with automatic reconnection and supports MQTT5 Shared Subscriptions (`$share/group/topic`) for horizontal scaling.
* **Dynamic Topic Translation**: Converts MQTT wildcard topics (e.g., `swd/phangan/+/telemetry`) into AMQP routing keys (e.g., `swd.phangan.device_001.telemetry`).
* **Payload Enrichment**: Safely parses JSON payloads and injects the `device_id`. Handles malformed non-JSON data by wrapping it into a standard JSON structure.
* **Resilient Publishing**: Built-in retry logic when publishing to RabbitMQ to prevent data loss.
* **Production-Ready Logging**: Uses `structlog` for structured JSON logging in production and colorful, readable logs during development.

## 🚀 Getting Started

### Prerequisites

* Python >= 3.13
* [uv](https://github.com/astral-sh/uv) (Fast Python package installer and resolver)

### 1. Installation

Clone the repository and install the dependencies using the provided Makefile:

```bash
make install
```

### 2. Configuration

Copy the example environment file and adjust the parameters to match your setup:

```bash
cp .env.example .env
```

**Key Environment Variables:**

* `ENVIRONMENT`: Set to `development` for readable logs or `production` for JSON logs.
* `MQTT_SHARE_GROUP`: Define a group name (e.g., `bridge-workers`) to enable MQTT load balancing across multiple service instances.
* `RABBITMQ_PUBLISH_MAX_RETRIES`: Number of attempts to retry sending a message if RabbitMQ is temporarily unavailable.

### 3. Running the Service

You can run the service locally using:

```bash
make run
```

### 4. Running Tests

The project includes a comprehensive test suite using `pytest`.

```bash
make test
```

## 🛠 Available Makefile Commands

* `make install` - Install dependencies using uv.
* `make run` - Run the application.
* `make test` - Run unit tests.
* `make lint` - Run linter (`ruff check`).
* `make format` - Run formatter (`ruff format`).
* `make clean` - Remove cached files (e.g., `__pycache__`, `.pytest_cache`).

## 🐳 Docker Deployment

The project includes an optimized `Dockerfile` leveraging `uv` for fast dependency installation.

**Build the image:**

```bash
docker build -t emqx-bridge-service .
```

**Run the container:**

```bash
docker run -d \
  --name emqx-bridge \
  --env-file .env \
  --network host \
  emqx-bridge-service
```
