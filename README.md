# Galileo Agents

AI agent examples instrumented with Traceloop (OpenLLMetry), exporting traces to Galileo.

## Agents

| Framework | Agent | Span Types |
|-----------|-------|------------|
| LangGraph | Weather | `agent`, `workflow`, `llm`, `tool` |
| LangGraph | Calculator | `agent`, `workflow`, `llm`, `tool` |
| LangGraph | RAG | `agent`, `workflow`, `llm`, `tool`, `retriever` |
| CrewAI | Content | `agent`, `llm`, `tool` |
| CrewAI | Research | `agent`, `llm`, `tool`, `retriever` |

## Setup

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync --all-extras

# Configure environment
cp env.example .env
# Edit .env with your API keys
```

## Run

```bash
# LangGraph
uv run agents-langgraph/weather/agent.py
uv run agents-langgraph/calculator/agent.py
uv run agents-langgraph/rag/agent.py

# CrewAI
uv run agents-crewai/content/crew.py
uv run agents-crewai/research/crew.py

# Custom queries
uv run agents-langgraph/weather/agent.py "What's the forecast for NYC?"
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GALILEO_API_KEY` | Galileo API key |
| `TRACELOOP_BASE_URL` | Traceloop endpoint (default: <https://api.galileo.ai/otel>) |
| `TRACELOOP_HEADERS` | Traceloop headers: `Galileo-API-Key=${GALILEO_API_KEY}` |
| `OPENAI_API_KEY` | OpenAI API key |

## Telemetry

All agents use Traceloop for automatic instrumentation. Traceloop reads `TRACELOOP_BASE_URL` and `TRACELOOP_HEADERS` from environment variables and automatically appends `/v1/traces` to the base URL.

Project and logstream are specified via resource attributes (hardcoded in each agent):

```python
from traceloop.sdk import Traceloop

Traceloop.init(
    app_name="weather-agent",
    resource_attributes={
        "galileo.project.name": "galileo-agents",
        "galileo.logstream.name": "weather-agent",
    },
)
```

Traceloop automatically instruments LangGraph workflows and CrewAI crews, generating spans for agents, tools, LLM calls, and retrievers.

## Instrumentation Recommendations

Galileo's OTLP provider conforms to [OpenTelemetry](https://opentelemetry.io/) and [OpenInference](https://github.com/Arize-ai/openinference) semantic conventions. To ensure your spans are valid and properly processed, follow these guidelines.

### Semantic Conventions

1. **OpenTelemetry GenAI Agent Spans**: [Semantic Conventions for GenAI agent and framework spans](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/)
2. **OpenInference**: [OpenInference Semantic Conventions](https://github.com/Arize-ai/openinference/blob/main/python/openinference-semantic-conventions/src/openinference/semconv/trace/__init__.py)

### Minimum Requirements for Valid Spans

For a span to be considered valid, it must include the following **required** attributes:

#### For Agent Spans

| Attribute | Requirement Level | Description | Example |
|-----------|------------------|-------------|---------|
| `gen_ai.operation.name` | **Required** | The name of the operation being performed | `invoke_agent`, `create_agent` |
| `gen_ai.provider.name` | **Required** | The Generative AI provider | `openai`, `anthropic`, `gcp.vertex_ai` |
| Span name | **Required** | Should follow format: `invoke_agent {gen_ai.agent.name}` or `invoke_agent` | `invoke_agent Math Tutor` |
| Span kind | **Required** | Should be `CLIENT` for remote agents or `INTERNAL` for in-process agents | `CLIENT`, `INTERNAL` |
| **Input** | **Required** | Input messages or data. Use `gen_ai.input.messages` (OpenTelemetry) or `input.value` (OpenInference) | `[{"role": "user", "content": "..."}]` |
| **Output** | **Required** | Output messages or data. Use `gen_ai.output.messages` (OpenTelemetry) or `output.value` (OpenInference) | `[{"role": "assistant", "content": "..."}]` |

#### For LLM Spans

| Attribute | Requirement Level | Description | Example |
|-----------|------------------|-------------|---------|
| `gen_ai.operation.name` | **Required** | The name of the operation | `chat`, `text_completion`, `embeddings` |
| `gen_ai.provider.name` | **Required** | The Generative AI provider | `openai`, `anthropic` |
| `gen_ai.request.model` | Conditionally Required | The name of the GenAI model | `gpt-4`, `claude-3-opus` |
| **Input** | **Required** | Input messages or prompts. Use `gen_ai.input.messages` (OpenTelemetry) or `llm.input_messages` (OpenInference) | `[{"role": "user", "content": "..."}]` |
| **Output** | **Required** | Output messages or completions. Use `gen_ai.output.messages` (OpenTelemetry) or `llm.output_messages` (OpenInference) | `[{"role": "assistant", "content": "..."}]` |

#### For Tool Execution Spans

| Attribute | Requirement Level | Description | Example |
|-----------|------------------|-------------|---------|
| `gen_ai.operation.name` | **Required** | Should be `execute_tool` | `execute_tool` |
| `tool.name` (OpenInference) | **Required** | Name of the tool being used | `get_weather`, `calculate` |
| **Input** | **Required** | Tool call arguments. Use `gen_ai.tool.call.arguments` (OpenTelemetry) or `input.value` (OpenInference) | `{"location": "NYC", "unit": "fahrenheit"}` |
| **Output** | **Required** | Tool call result. Use `gen_ai.tool.call.result` (OpenTelemetry) or `output.value` (OpenInference) | `{"temperature": 72, "condition": "sunny"}` |

#### For Retriever Spans

| Attribute | Requirement Level | Description | Example |
|-----------|------------------|-------------|---------|
| `db.operation` | **Required** | Database operation type. Should be `query` or `search` | `query`, `search` |
| `openinference.span.kind` (OpenInference) | Conditionally Required | Should be `retriever` when using OpenInference | `retriever` |
| **Input** | **Required** | Query string or search input. Use `gen_ai.input.messages` (OpenTelemetry) or `input.value` (OpenInference) | `"What is machine learning?"` |
| **Output** | **Required** | Retrieved documents. Use `gen_ai.output.messages` with document list (OpenTelemetry) or `retrieval.documents` (OpenInference) | `[{"id": "doc1", "content": "..."}, {"id": "doc2", "content": "..."}]` |

**Note**: Retriever spans are typically detected automatically when `db.operation` is set to `query` or `search`. The output should be a list of documents, which will be formatted appropriately by Galileo's OTLP provider.

### Framework-Specific Guidelines

**Important**: Each framework may have its own instrumentation guidelines and conventions. Always refer to the framework-specific documentation.

When using automatic instrumentation libraries (like Traceloop/OpenLLMetry), they typically handle these requirements automatically. However, when creating custom spans, ensure you follow both the OpenTelemetry GenAI conventions and any framework-specific guidelines.

### Error Handling

For spans that end in an error, you **must** include:

- `error.type`: Describes the class of error (e.g., `timeout`, `500`, exception name)
- Span status: Should be set to `ERROR` with appropriate error description

### Additional Resources

- [OpenTelemetry GenAI Semantic Conventions](https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-agent-spans/)
- [OpenInference Semantic Conventions](https://github.com/Arize-ai/openinference/blob/main/python/openinference-semantic-conventions/src/openinference/semconv)

## Direct POST Calls to Galileo OTLP Endpoint

You can make direct POST calls to the Galileo OTLP endpoint to send OTLP packets. This is useful for custom integrations or when you need to send pre-generated OTLP data.

### Endpoint

```
POST https://api.galileo.ai/otel/v1/traces
```

### Headers

The following headers are required:

| Header | Description |
|--------|-------------|
| `Galileo-API-Key` | Your Galileo API key |
| `project` or `projectid` | Project name or project ID (at least one required) |
| `logstream` or `logstreamid` | Logstream name or logstream ID (at least one required) |
| `Content-Type` | Must be `application/x-protobuf` |

**Project and Logstream Headers:**
- You must provide at least one of `project` or `projectid` (project name or project ID)
- You must provide at least one of `logstream` or `logstreamid` (logstream name or logstream ID)

### Request Body

The request body should contain OTLP packets in protobuf format (binary). The payload should be an `ExportTraceServiceRequest` message as defined in the OpenTelemetry Protocol specification.

### Example using Python

See [shared/otel.py](shared/otel.py) for an example. You can run it with:

```bash
uv run shared/otel.py --api-key YOUR_KEY --project PROJECT_NAME --logstream LOGSTREAM_NAME
```

The script supports the following arguments:
- `--api-key` (required): Your Galileo API key
- `--project` or `--projectid` (at least one required): Project name or project ID
- `--logstream` or `--logstreamid` (at least one required): Logstream name or logstream ID
- `--url` (optional): API endpoint URL (default: `https://api.galileo.ai/otel/v1/traces`)
- `--directory` (optional): Directory containing `.bin` trace files (default: `agents-langgraph/weather/otlp_trace`)

### HTTP Responses

The OTLP endpoint returns the following HTTP status codes:

#### Success Responses

**200 OK**

- The request was successfully processed. The response body contains an `ExportTraceServiceResponse` in JSON format.
- Example response:

  ```json
  {}
  ```

- If some spans were rejected, the response includes partial success information:

  ```json
  {
    "partialSuccess": {
      "rejectedSpans": 5,
      "errorMessage": "Group 0: Run not found for logstream ..."
    }
  }
  ```

  Each error message is prefixed with `"Group <N>: "` indicating which resource span group was affected. Multiple error messages are semicolon-separated.

  **Rejection Scenarios:**

  | Scenario | Error Message | Retryable? | Details |
  |----------|--------------|------------|---------|
  | Run not found | `"Run not found"` | No | The associated run or logstream must be created first. |
  | No GenAI patterns detected | `"No GenAI patterns detected in spans. Ensure spans contain standard OTEL GenAI attributes or are from a supported framework."` | No | Spans must include `gen_ai.*` OTEL attributes or come from a supported framework (Strands, Mastra, CrewAI, PydanticAI, Vercel, Traceloop, OpenInference). |
  | Missing span ID | `"Missing required field 'id' (span_id): Every span must have a unique identifier"` | No | Structural issue — every span must have a unique identifier. |
  | Missing trace ID | `"Missing required field 'trace_id': Every span must belong to a trace"` | No | Structural issue — every span must belong to a trace. |
  | Schema validation failure | `"Galileo schema validation failed for field '<field>': <detail>"` | No | The span doesn't conform to the expected schema. |
  | Validation model error | `"Validation error converting trace dict to Trace model"` | No | Pydantic validation failure during trace conversion. |
  | Processor exception | `"Span dropped due to unexpected processor exception."` | Possibly | Could indicate a transient server-side issue. |
  | Processor failure | `"Span dropped after processor failure."` | No | The span data could not be processed. |

  **Retry Guidance:**

  Almost all rejections are **permanent** — they result from validation failures, missing required fields, or spans that don't match expected GenAI patterns. Retrying the same payload will produce the same result.

  The only potentially transient rejection is `"Span dropped due to unexpected processor exception."`, which may indicate a temporary server-side issue. If encountered, retry with exponential backoff (e.g., 1s, 2s, 4s).

  **Recommendation:** Log the `errorMessage` from any `partialSuccess` response to diagnose and fix rejected spans at the source.

#### Error Responses

**401 Unauthorized**

- The API key is missing or invalid.
- Response body:

  ```json
  {
    "detail": "API Key is missing"
  }
  ```

  or

  ```json
  {
    "detail": "Invalid API Key"
  }
  ```

**404 Not Found**

- The specified project was not found and could not be created.
- Response body:

  ```json
  {
    "detail": "Project not found."
  }
  ```

**415 Unsupported Media Type**

- The `Content-Type` header is not `application/x-protobuf`.
- Response body:

  ```json
  {
    "detail": "<content-type> is not supported, content_type needs to be: 'application/x-protobuf'"
  }
  ```

**422 Unprocessable Entity**

- The request could not be processed. Common reasons:
  - No spans found in the request
  - Trace processing failed
  - Log stream ID is required but not provided
- Response body examples:

  ```json
  {
    "detail": "No spans found in request."
  }
  ```

  ```json
  {
    "detail": "log_stream_id is required."
  }
  ```

  ```json
  {
    "detail": "Trace processing failed: <error message>"
  }
  ```

### Response Format

All responses are returned as JSON. Success responses follow the OpenTelemetry Protocol `ExportTraceServiceResponse` format, which may include:

- `partialSuccess.rejectedSpans`: Number of spans that were rejected
- `partialSuccess.errorMessage`: Error messages describing why spans were rejected

Even when the HTTP status is 200, you should check for `partialSuccess` in the response to determine if all spans were successfully processed.
