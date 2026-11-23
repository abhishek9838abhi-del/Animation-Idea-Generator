# Frame by Frame: Animation Idea Generator 🎬

> A secure, spec-driven web application helping beginners, animation students, and small creative teams turn rough ideas into structured, feasible short-animation production outlines.

---

## 🌟 Key Features

1. **Structured Production Plans**:
   - Title & Logline
   - Characters (Name, Role, concrete immediate Goal)
   - Scene-by-scene breakdown (Action description, visual/camera suggestion, optional dialogue/narration, sound notes)
   - Overall sound and music palette
2. **Pacing & Constraint Controls**:
   - **Runtime**: 30 seconds (2–3 scenes), 1 minute (4–5 scenes), or 3 minutes (6–8 scenes).
   - **Mood**: Funny, Heartwarming, Mysterious, or Adventurous.
   - **Audience**: Children, Teens, or General (Pixar-style universal resonance).
   - **Dialogue Control**: Strict visual pantomime (silent) or dialogue-enabled.
   - **Complexity**: Simple (1–2 characters, single location) or Detailed (multiple visual beats).
3. **Interactive In-Browser Editor**:
   - Edit any field directly in the browser (title, logline, character goals, scene descriptions, visual framing, dialogue).
4. **Context-Aware Story Revisions**:
   - Request targeted iterations (e.g., *"Make the ending funnier"*, *"Simplify to one location"*) while preserving established characters and tone.
5. **One-Click Export**:
   - Export and copy the entire formatted animation plan directly to your clipboard in clean Markdown.
6. **Security & Privacy Guardrails**:
   - **XSS Immunity**: Pure DOM `.textContent` and `.value` rendering; zero raw HTML execution.
   - **Zero Persistence**: No database, no user accounts, no disk logging of creative prompts.
   - **Rate Limiting**: In-memory token bucket (10 requests/minute/IP).
   - **Living Artist Policy**: Automatically translates style requests into neutral artistic descriptors to respect artist intellectual property.
   - **Confidentiality Warning**: Clear informational notice that creative teams should not submit sensitive trade secrets to public endpoints.

---

## 🏗️ Architecture

```
Browser UI (Vanilla HTML5 / CSS3 / ES6)
   │
   ▼ JSON over HTTP
Application Backend (FastAPI / Python 3.14 + Pydantic v2)
   ├── Rate Limiter (In-Memory Token Bucket)
   ├── Input Validation & Safety Sanitizer
   ├── Extensible MCP Tool Registry (Server-side allowlist)
   └── NVIDIA Provider Adapter (HTTPX Async Client + Tenacity Retries)
         │
         ▼ Bearer Token Auth
   NVIDIA NIM / Hosted Model API (OpenAI-Compatible /v1/chat/completions)
```

Detailed architectural, API, and behavioral specifications are located in the [specs/](file:///d:/ML%20mini%20Project/specs) directory:
- [requirements.md](file:///d:/ML%20mini%20Project/specs/requirements.md)
- [architecture.md](file:///d:/ML%20mini%20Project/specs/architecture.md)
- [api-contract.md](file:///d:/ML%20mini%20Project/specs/api-contract.md)
- [ai-behavior.md](file:///d:/ML%20mini%20Project/specs/ai-behavior.md)
- [test-plan.md](file:///d:/ML%20mini%20Project/specs/test-plan.md)
- [implementation-plan.md](file:///d:/ML%20mini%20Project/specs/implementation-plan.md)

---

## 🚀 Quickstart & Installation

### 1. Requirements
- Python 3.10+ (tested with Python 3.14)
- No Node.js build step required.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Configure NVIDIA API (Optional for Live Mode)
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and set your credentials:
```ini
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_BASE_URL=https://integrate.api.nvidia.com/v1
NVIDIA_MODEL=meta/llama-3.1-70b-instruct
```

> **Note**: If `NVIDIA_API_KEY` is not provided, the application runs in **Dev / Mock Mode**, providing schema-valid, realistic animation plans so you can test all features and the full UI locally without an API key!

### 4. Run Application Server
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Open your browser to:
👉 **http://127.0.0.1:8000**

---

## 🧪 Running Automated Tests

Run the complete test suite (26 unit, integration, and security tests):
```bash
pytest -v
```

---

## 🛡️ Model Context Protocol (MCP) Extensibility

The application backend includes an extensible Model Context Protocol boundary in `app/mcp/`:
- **Server-Side Host**: The browser never connects directly to external tools or MCP endpoints.
- **Strict Allowlist**: Only explicitly registered tools in `app/mcp/registry.py` can be discovered or executed.
- **Schema Validation**: All tool parameters and outputs are strictly validated via Pydantic schemas.
- **Demonstration Tool**: Includes `sound_library_search` as an architectural template for future studio tool additions.
