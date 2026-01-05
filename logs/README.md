# Unify SDK Logging & Tracing

This document covers the logging infrastructure for the Unify SDK: HTTP request traces, Orchestra server traces, and OpenTelemetry tracing.

---

## Log Directory Overview

All logs are organized under `logs/` with three main subdirectories:

| Directory | Purpose | Structure | Control |
|-----------|---------|-----------|---------|
| `logs/unify/` | Unify SDK HTTP traces | JSON files per request | `UNIFY_LOG` + `UNIFY_LOG_DIR` |
| `logs/orchestra/` | Orchestra API traces (server-side) | Per-request JSON with spans | `ORCHESTRA_LOG_DIR` |
| `logs/all/` | Cross-repo OpenTelemetry traces | `{trace_id}.jsonl` per trace | `*_OTEL_LOG_DIR` |

**Note:** Orchestra logs are only populated when running a local Orchestra server. The test infrastructure sets `ORCHESTRA_LOG_DIR` so that if you start a local orchestra, its traces will be captured here.

---

## Unify SDK Logs (`logs/unify/`)

Unify SDK HTTP traces capture all requests to the Orchestra API. These are useful for debugging API issues, inspecting request/response payloads, and correlating with server-side traces.

### Directory Structure

```
logs/unify/
└── 2026-01-05T22-00-00_unifypid12345/
    ├── 14-26-27.611_POST_projects-contexts_210ms_200_no-trace.json
    ├── 14-26-46.175_GET_logs_331ms_200_f124f0d3.json
    ├── 14-27-01.234_POST_logs_PENDING_a1b2c3d4.json
    └── ...
```

### Log File Naming

Files follow the format: `{timestamp}_{METHOD}_{route}_{duration}ms_{status}_{trace_id}.json`

| Component | Example | Description |
|-----------|---------|-------------|
| `timestamp` | `14-26-46.175` | Request start time (HH-MM-SS.mmm) |
| `METHOD` | `GET`, `POST` | HTTP method |
| `route` | `logs`, `projects-contexts` | API route (normalized) |
| `duration` | `331ms`, `PENDING` | Request duration (or PENDING while in-flight) |
| `status` | `200`, `404` | HTTP status code |
| `trace_id` | `f124f0d3` | Last 8 chars of OpenTelemetry trace ID (or `no-trace`) |

### Log File Contents

Each JSON file contains the full request and response:

```json
{
  "trace_id": "099b207f89222185695d25977be454fc",
  "request": {
    "method": "GET",
    "url": "https://api.unify.ai/v0/logs",
    "headers": {"Authorization": "Bearer ..."},
    "params": {"limit": 100}
  },
  "response": {
    "status_code": 200,
    "headers": {"Content-Type": "application/json"},
    "body": [...]
  },
  "duration_ms": 331
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `UNIFY_LOG` | `true` | Master switch for all logging (console + file) |
| `UNIFY_LOG_DIR` | `""` (disabled) | Directory for file logging; if empty, console only |

**Enabling file logging:**
```bash
export UNIFY_LOG=true
export UNIFY_LOG_DIR=/path/to/logs/unify
```

### Debugging In-Flight Requests

If a request hangs, the file remains with `PENDING` in the filename. This is useful for:
- Identifying which requests are timing out
- Debugging network issues
- Spotting slow API calls

### Trace Correlation

The `trace_id` suffix in filenames (last 8 chars) enables correlation with:
- Orchestra server-side traces (in `logs/orchestra/`)
- OpenTelemetry spans in `logs/all/`

---

## Orchestra Logs (`logs/orchestra/`)

Orchestra logs capture server-side API request traces using OpenTelemetry. These are only populated when running a local Orchestra server for development/testing.

### Directory Structure

```
logs/orchestra/
└── 2026-01-05T22-00-00_unifypid12345/
    └── requests/
        ├── 2026-01-05T22-00-01.123_GET_projects_45ms_200_f124f0d3.json
        ├── 2026-01-05T22-00-02.456_POST_logs_120ms_201_a1b2c3d4.json
        └── ...
```

### Log File Naming

Each request generates a JSON file:

```
{datetime}_{METHOD}_{route}_{duration}ms_{status}_{trace_id_short}.json
```

| Component | Example | Description |
|-----------|---------|-------------|
| `datetime` | `2026-01-05T22-00-01.123` | Request start time (millisecond precision) |
| `METHOD` | `GET`, `POST`, `DELETE` | HTTP method |
| `route` | `projects`, `logs` | API route |
| `duration` | `45ms`, `PENDING` | Request duration (or `PENDING` while in-flight) |
| `status` | `200`, `404` | HTTP status code |
| `trace_id_short` | `f124f0d3` | Last 8 chars of OpenTelemetry trace ID |

### Log File Contents

Each JSON file contains the full request trace with all spans:

```json
{
  "trace_id": "099b207f89222185695d25977be454fc",
  "status": "complete",
  "spans": [
    {
      "name": "GET /v0/projects",
      "span_id": "a1b2c3d4e5f6a7b8",
      "parent_span_id": null,
      "start_time": "2026-01-05T22:00:01.123Z",
      "end_time": "2026-01-05T22:00:01.168Z",
      "duration_ms": 45,
      "attributes": {
        "http.method": "GET",
        "http.route": "/v0/projects",
        "http.status_code": 200
      }
    },
    {
      "name": "SELECT projects",
      "span_id": "...",
      "parent_span_id": "a1b2c3d4e5f6a7b8",
      "attributes": { "db.statement": "SELECT ..." }
    }
  ]
}
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHESTRA_LOG_DIR` | `""` (disabled) | Directory for per-request trace files |
| `ORCHESTRA_OTEL_LOG_DIR` | `""` | Directory for OTEL span export (typically `logs/all/`) |

**Note:** These are set automatically by the test infrastructure. Orchestra must be started with these environment variables for logging to work.

### When Are Orchestra Logs Created?

Orchestra logs are only created when:
1. You're running a **local** Orchestra server (not production)
2. The server was started with `ORCHESTRA_LOG_DIR` set
3. Requests are made to the local server

For production API calls, you only get client-side traces in `logs/unify/`.

---

## OpenTelemetry Traces (`logs/all/`)

When OTEL tracing is enabled, both the Unify SDK and Orchestra create spans that can be correlated for distributed tracing analysis.

### Directory Structure

```
logs/all/
└── 2026-01-05T22-00-00_unifypid12345/
    ├── 099b207f89222185695d25977be454fc.jsonl   # All spans for trace 099b207f...
    ├── a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6.jsonl   # All spans for trace a1b2c3d4...
    └── ...
```

Files are keyed by the 32-character trace ID. When running as part of a larger system (e.g., Unity), spans from all services are aggregated into the same file.

### Trace File Format (JSONL)

Each `.jsonl` file contains one JSON object per line, representing a span:

```json
{"service": "unify", "trace_id": "099b207f...", "span_id": "a1b2c3d4", "parent_span_id": null, "name": "POST /v0/logs", "start_time": "2026-01-01T14:30:22.500Z", "end_time": "2026-01-01T14:30:23.100Z", "duration_ms": 600, "status": "OK", "attributes": {"http.method": "POST", "http.status_code": 200}}
{"service": "orchestra", "trace_id": "099b207f...", "span_id": "e5f6g7h8", "parent_span_id": "a1b2c3d4", "name": "POST /v0/logs", "start_time": "2026-01-01T14:30:22.550Z", "end_time": "2026-01-01T14:30:23.050Z", "duration_ms": 500, "status": "OK", "attributes": {"http.method": "POST", "http.route": "/v0/logs"}}
```

### Span Attributes

**Unify spans** (HTTP requests to Orchestra):

| Attribute | Description |
|-----------|-------------|
| `http.method` | HTTP method (GET, POST, etc.) |
| `http.url` | Full request URL |
| `http.status_code` | Response status code |
| `http.request.body` | Request body (JSON) |
| `http.response.body` | Response body (JSON) |

**Orchestra spans** (server-side, when running locally):

| Attribute | Description |
|-----------|-------------|
| `http.method` | HTTP method |
| `http.route` | API route pattern |
| `http.status_code` | Response status code |
| `db.statement` | SQL query (for database spans) |
| `db.operation` | Database operation type |

### Environment Variables

**Unify SDK OTEL settings:**

| Variable | Default | Description |
|----------|---------|-------------|
| `UNIFY_OTEL` | `false` | Master switch for Unify SDK OTel tracing |
| `UNIFY_OTEL_ENDPOINT` | `""` | OTLP endpoint for remote export |
| `UNIFY_OTEL_LOG_DIR` | `""` | Directory for file-based span export |

**Orchestra OTEL settings** (server-side):

| Variable | Default | Description |
|----------|---------|-------------|
| `ORCHESTRA_OTEL_LOG_DIR` | `""` | Directory for file-based span export |

**Enabling file-based tracing (all services):**
```bash
# Enable OTEL for all services, writing to same directory for correlation
export UNIFY_OTEL=true
export UNIFY_OTEL_LOG_DIR=/path/to/logs/all
export ORCHESTRA_OTEL_LOG_DIR=/path/to/logs/all  # Server-side
```

### Parent TracerProvider Integration

When the Unify SDK runs within a larger system (e.g., Unity or unillm), it automatically detects and uses the parent's TracerProvider. This ensures all spans share the same trace context for end-to-end correlation.

The integration flow:
1. Parent (Unity/unillm) creates a TracerProvider and root span
2. Unify SDK detects the existing provider and creates child spans
3. Orchestra receives the trace context via HTTP headers and creates server-side spans
4. All spans are exported to the same destination (file or collector)

---

## Reading Trace Files

```bash
# View all spans for a trace (pretty-printed)
cat logs/all/2026-01-05T22-00-00_unifypid12345/099b207f...jsonl | jq -s .

# Find slow HTTP calls (>1s)
cat logs/all/*/*.jsonl | jq -s '[.[] | select(.duration_ms > 1000)]'

# Filter by service
cat logs/all/*/*.jsonl | jq -s '[.[] | select(.service == "orchestra")]'

# Find all database queries
cat logs/all/*/*.jsonl | jq -s '[.[] | select(.attributes["db.statement"] != null)]'
```

---

## Programmatic Configuration

The logging system can be configured at runtime:

```python
from unify.utils.http import configure_log_dir

# Enable file logging
configure_log_dir("/path/to/logs/unify")

# Or via environment
import os
os.environ["UNIFY_LOG_DIR"] = "/path/to/logs/unify"
os.environ["UNIFY_OTEL"] = "true"
os.environ["UNIFY_OTEL_LOG_DIR"] = "/path/to/logs/all"
```

---

## Console Logging

When `UNIFY_LOG=true` (the default), request/response information is logged to the console via Python's logging system.

The logger name is `unify`, so you can configure it via standard Python logging:

```python
import logging
logging.getLogger("unify").setLevel(logging.DEBUG)
```

To see console logs in pytest:
```bash
pytest -s tests/  # -s disables output capture
```
