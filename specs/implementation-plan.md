# Frame by Frame: Animation Idea Generator — Implementation Plan

This implementation plan maps directly to the user stories and acceptance criteria defined in [requirements.md](file:///d:/ML%20mini%20Project/specs/requirements.md).

---

## Task Breakdown & Traceability Matrix

### Phase 1: Environment & Core Configuration
- [ ] **Task 1.1: Project Directory Structure & Dependencies**
  - Create standard application structure (`app/`, `app/mcp/`, `static/`, `tests/`).
  - Generate `requirements.txt` locking core dependencies (`fastapi`, `uvicorn`, `pydantic`, `httpx`, `tenacity`, `python-dotenv`, `pytest`, `pytest-asyncio`).
  - Generate `.env.example` documenting `NVIDIA_API_KEY`, `NVIDIA_BASE_URL`, `NVIDIA_MODEL`, `NVIDIA_TIMEOUT_SECONDS`, and `NVIDIA_MAX_RETRIES`.
  - *Maps to*: US-5 (Safe configuration management).

- [ ] **Task 1.2: Settings & Environment Management**
  - Implement `app/config.py` using `pydantic-settings` to safely load configuration from `.env`.
  - Ensure sensitive values are masked in `__repr__` and logs.
  - *Maps to*: US-5, Architecture Section 2.3.

---

### Phase 2: Domain Schemas & Validation
- [ ] **Task 2.1: Data Models & Pydantic Validation**
  - Implement `app/schemas.py`:
    - Enums: `RuntimeEnum`, `MoodEnum`, `AudienceEnum`, `ComplexityEnum`.
    - Models: `Character`, `Scene`, `AnimationPlan`.
    - Request Models: `GenerateRequest`, `ReviseRequest`.
    - Error Envelope: `ErrorDetail`, `ErrorResponse`.
  - Add field validators (string trimming, character length constraints: Idea 5–500 chars, Revision 3–300 chars).
  - *Maps to*: US-1, US-3, US-5; API Contract Section 3.

---

### Phase 3: AI Provider Layer & Prompt Orchestration
- [ ] **Task 3.1: Prompt Builder & Style Guard**
  - Implement `app/prompts.py`:
    - System prompt builder with strict scene counts, runtime mapping, and beginner feasibility rules.
    - Living artist style filter and neutral descriptor converter.
    - Revision prompt builder incorporating prior plan and delta instructions.
  - *Maps to*: US-1, US-3, US-6; AI Behavior Section 2 & 4.

- [ ] **Task 3.2: NVIDIA Provider Adapter**
  - Implement `app/provider.py`:
    - Async HTTP client via `httpx.AsyncClient`.
    - Bounded exponential backoff retries with jitter via `tenacity` on 429 and 5xx errors.
    - Robust JSON extractor handling raw strings, markdown code blocks (` ```json `), and malformed structures.
    - Clean error mapping to custom exceptions (`ProviderNotConfiguredError`, `ProviderTimeoutError`, `ProviderAPIError`, `ProviderJSONParseError`).
  - *Maps to*: US-1, US-3, US-5; Architecture Section 2.3.

---

### Phase 4: MCP Architectural Boundary
- [ ] **Task 4.1: Extensible MCP Client Boundary & Tool Registry**
  - Implement `app/mcp/registry.py` and `app/mcp/boundary.py`:
    - Tool registration interface (`BaseTool`, `ToolDefinition`).
    - Tool allowlist validator to prevent arbitrary tool execution.
    - Schema validation for arguments and results.
    - Stub demonstration of future tool: `SoundLibrarySearchTool`.
  - *Maps to*: Architecture Section 3; Test Plan Section 2.5.

---

### Phase 5: FastAPI Backend & API Endpoints
- [ ] **Task 5.1: Rate Limiting & Safe Error Handling Middleware**
  - Implement in-memory token bucket rate limiter (10 req/min/IP).
  - Implement global exception handlers translating internal errors into safe, structured JSON envelopes without stack traces or sensitive headers.
  - *Maps to*: US-5; Architecture Section 5; API Contract Section 5.

- [ ] **Task 5.2: API Endpoints Implementation**
  - Implement `app/main.py`:
    - `GET /api/health`: Service status and provider readiness.
    - `POST /api/generate`: Plan generation endpoint.
    - `POST /api/revise`: Plan revision endpoint.
    - Mount `/static` directory for the web frontend.
  - *Maps to*: US-1, US-3; API Contract Section 4.

---

### Phase 6: Frontend Development
- [ ] **Task 6.1: Semantic HTML5 Structure (`static/index.html`)**
  - Hero section with title and product premise.
  - Intuitive input form with character counter, runtime selector, mood selector, audience selector, dialogue toggle, and complexity toggle.
  - Editable output container for Title, Logline, Characters, Scenes, and Sound Notes.
  - Revision request bar and modal.
  - Safety and informational disclaimers (AI suggestions require review; confidential information notice).
  - *Maps to*: US-1, US-2, US-3, US-5.

- [ ] **Task 6.2: Clean, Accessible Styling (`static/styles.css`)**
  - Modern typography, high-contrast accessible color palette, responsive layout for mobile and desktop.
  - Card-based scene layout with visual indicators for runtime and mood.
  - Visual loading states (spinners, disabled buttons during generation).
  - *Maps to*: US-1, US-2.

- [ ] **Task 6.3: Client-Side Logic & Security (`static/app.js`)**
  - Form validation and dynamic character counting.
  - Safe DOM population using `.textContent` and `.value` (strictly zero `innerHTML` to prevent XSS).
  - In-browser plan editing allowing direct modification of all fields.
  - Revision request handler passing current plan state + instruction back to the server.
  - One-click copy-to-clipboard functionality with toast feedback.
  - *Maps to*: US-2, US-3, US-4, US-5.

---

### Phase 7: Automated Testing & Verification
- [ ] **Task 7.1: Unit & Schema Tests**
  - Implement `tests/test_validation.py` covering all edge cases (lengths, enums, malformed payloads).
- [ ] **Task 7.2: Provider Adapter & Mock Tests**
  - Implement `tests/test_provider.py` covering timeout retries, markdown stripping, missing API keys, and server error handling.
- [ ] **Task 7.3: Security & Rate-Limiting Tests**
  - Implement `tests/test_security.py` verifying rate limiting, XSS payload safety, and log sanitization.
- [ ] **Task 7.4: End-to-End API Tests**
  - Implement `tests/test_functional.py` covering `/api/health`, `/api/generate`, and `/api/revise`.
- [ ] **Task 7.5: MCP Boundary Tests**
  - Implement `tests/test_mcp.py` verifying allowlist enforcement and schema checks.
- [ ] **Task 7.6: Execute Test Suite**
  - Run all tests and verify 100% pass rate.
  - *Maps to*: Test Plan Sections 2.1–2.5.

---

### Phase 8: Final Review & Handoff
- [ ] **Task 8.1: Validation Report**
  - Document all implemented endpoints, test execution results, and operational instructions.
  - Detail environment variables needed to connect live NVIDIA endpoints.
