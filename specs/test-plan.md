# Frame by Frame: Animation Idea Generator — Test Plan

## 1. Overview & Framework
- **Test Runner**: `pytest` 9.2.0 + `pytest-asyncio` 1.4.1
- **API Testing**: `httpx.AsyncClient` with `ASGITransport` against FastAPI application
- **Mocking**: `unittest.mock` for upstream NVIDIA HTTP calls and environment configurations
- **Coverage Goal**: >= 85% branch coverage across backend modules (schemas, provider adapter, rate limiting, and endpoints).

---

## 2. Test Categories & Scenarios

### 2.1 Acceptance & Functional Tests (`test_functional.py`)

| Test ID | Scenario | Input | Expected Output |
| :--- | :--- | :--- | :--- |
| **TC-FUNC-01** | Standard generation (30s, funny, children, silent, simple) | Valid prompt, `runtime="30s"`, `has_dialogue=False` | 200 OK. `AnimationPlan` returned. Exactly 2–3 scenes. All `dialogue` fields are `null` or silent. |
| **TC-FUNC-02** | Extended generation (3m, adventurous, general, dialogue, detailed) | Valid prompt, `runtime="3m"`, `has_dialogue=True` | 200 OK. 6–8 scenes. At least one scene contains dialogue. |
| **TC-FUNC-03** | Plan revision | Existing `AnimationPlan` + instruction *"Make ending heartwarming"* | 200 OK. Updated plan preserves core characters while ending scene reflects heartwarming tone. |
| **TC-FUNC-04** | Service health check | `GET /api/health` | 200 OK. JSON containing `status="ok"` and provider configuration flag. |

---

### 2.2 Input Validation & Schema Tests (`test_validation.py`)

| Test ID | Scenario | Input | Expected Output |
| :--- | :--- | :--- | :--- |
| **TC-VAL-01** | Prompt too short | `idea="Cat"` (< 5 characters) | 422 Unprocessable Entity with clear error message. |
| **TC-VAL-02** | Prompt too long | `idea="a" * 501` (> 500 characters) | 422 Unprocessable Entity with clear error message. |
| **TC-VAL-03** | Invalid enum values | `runtime="10m"` or `mood="angry"` | 422 Unprocessable Entity detailing allowed enum values. |
| **TC-VAL-04** | Missing required fields | Payload missing `runtime` or `complexity` | 422 Unprocessable Entity. |
| **TC-VAL-05** | Empty revision instruction | `revision_instruction=""` (< 3 characters) | 422 Unprocessable Entity. |

---

### 2.3 Security & Privacy Tests (`test_security.py`)

| Test ID | Scenario | Action | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **TC-SEC-01** | XSS payload injection in prompt | `idea="<script>alert('xss')</script> A tiny cloud"` | Server sanitizes input; client renders strictly as `.textContent`; script never executes. |
| **TC-SEC-02** | Rate limiting enforcement | Send 11 rapid requests within 10 seconds from same IP | Requests 1–10 succeed; Request 11 receives `429 Too Many Requests` with `Retry-After` header. |
| **TC-SEC-03** | Secrets leakage in errors | Force upstream failure with mock containing fake secret key in headers | Error envelope returns generic code `PROVIDER_ERROR`; response body contains zero API keys or server paths. |
| **TC-SEC-04** | Living artist style query | User submits `"in the style of [Named Living Artist]"` | Model prompt instruction actively replaces reference with neutral descriptors. |
| **TC-SEC-05** | Log sanitization | Submit a request | Inspect log outputs: verify authorization tokens and user prompts are redacted. |

---

### 2.4 Provider Failure & Resilience Tests (`test_provider.py`)

| Test ID | Scenario | Mock State | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **TC-PROV-01** | Missing NVIDIA API key | `NVIDIA_API_KEY=""` | Clean `503 Service Unavailable` with message: "AI provider is not configured. Please set NVIDIA_API_KEY." |
| **TC-PROV-02** | Upstream timeout | Mock NVIDIA endpoint delays > timeout threshold | Retries 2 times with backoff, then returns clean `504 Gateway Timeout`. |
| **TC-PROV-03** | Upstream 500 / 502 / 503 | Mock NVIDIA endpoint returns 500 | Retries 2 times, then returns clean `502 Bad Gateway`. |
| **TC-PROV-04** | Markdown code-block output | Upstream returns valid JSON wrapped in ` ```json ... ``` ` | Parser strips code block and validates successfully (200 OK). |
| **TC-PROV-05** | Corrupt/malformed JSON | Upstream returns unparseable text (`"Not a json"`) | Retries or returns `502 Bad Gateway` with safe message: "Provider returned an invalid plan structure." |

---

### 2.5 MCP Boundary Tests (`test_mcp_boundary.py`)

| Test ID | Scenario | Action | Expected Outcome |
| :--- | :--- | :--- | :--- |
| **TC-MCP-01** | Tool allowlist validation | Query tool registry with unapproved tool name `"execute_shell"` | Registry rejects tool with `UnauthorizedToolError`. |
| **TC-MCP-02** | Mock tool execution | Call registered test tool `"mock_sound_search"` with valid query | Tool executes safely and returns validated Pydantic model response. |
| **TC-MCP-03** | Tool argument schema validation | Call mock tool with invalid parameters | Schema validation error raised before execution. |

---

## 3. Execution Commands
```powershell
# Run all automated tests
pytest -v

# Run with coverage report
pytest --cov=app --cov-report=term-missing tests/

# Run specifically security and validation suites
pytest tests/test_security.py tests/test_validation.py -v
```
