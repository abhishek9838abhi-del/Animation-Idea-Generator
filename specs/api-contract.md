# Frame by Frame: Animation Idea Generator — API Contract

## 1. Base URL & Protocol
- **Base URL**: `http://localhost:8000` (or configured host/port)
- **Protocol**: HTTP/1.1 or HTTP/2, JSON payloads (`Content-Type: application/json`)
- **Encoding**: UTF-8

---

## 2. Endpoints Overview

| Method | Endpoint | Description | Auth | Rate Limit |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/health` | Service health and provider configuration status | None | None |
| `POST` | `/api/generate` | Generates a new structured animation plan from an idea | None | 10 req/min/IP |
| `POST` | `/api/revise` | Revises an existing plan with specific modification instructions | None | 10 req/min/IP |

---

## 3. Data Models & Schemas

### 3.1 Common Enums
- **Runtime**:
  - `"30s"`: ~30 seconds (2–3 scenes)
  - `"1m"`: ~1 minute (4–5 scenes)
  - `"3m"`: ~3 minutes (6–8 scenes)
- **Mood**:
  - `"funny"`, `"heartwarming"`, `"mysterious"`, `"adventurous"`
- **Audience**:
  - `"children"`, `"teens"`, `"general"`
- **Story Complexity**:
  - `"simple"`: Minimal locations, 1–2 characters, straightforward action.
  - `"detailed"`: More nuanced character dynamics, multiple visual beats.

### 3.2 Sub-models

#### `Character`
```json
{
  "name": "Barnaby the Cloud",
  "role": "Protagonist / Outcast",
  "goal": "Wants to produce a fierce lightning strike to join the big thunderstorm"
}
```
- `name` (string): 1 to 50 characters.
- `role` (string): 1 to 100 characters.
- `goal` (string): 1 to 150 characters.

#### `Scene`
```json
{
  "scene_number": 1,
  "description": "Barnaby floats at the edge of a massive, dark anvil storm cloud, trying to look menacing.",
  "visual_suggestion": "Low camera angle looking up at the towering dark storm, with tiny white Barnaby in the foreground.",
  "dialogue": null,
  "sound_suggestions": [
    "Distant ominous thunder rumble",
    "Soft whimsical wind whistle"
  ]
}
```
- `scene_number` (integer): >= 1.
- `description` (string): 10 to 400 characters. Feasible visual action description.
- `visual_suggestion` (string): 10 to 300 characters. Practical camera framing/color note.
- `dialogue` (string | null): Optional narration or spoken line. If `has_dialogue` was `false`, this is `null` or empty.
- `sound_suggestions` (array of strings, optional): Max 4 items, each <= 100 characters.

#### `AnimationPlan`
```json
{
  "title": "Little Spark in the Dark",
  "logline": "A gentle cloud desperate to join an intimidating thunderstorm discovers that a shower of rain is more powerful than lightning.",
  "runtime": "1m",
  "mood": "heartwarming",
  "audience": "children",
  "complexity": "simple",
  "characters": [
    {
      "name": "Barnaby",
      "role": "A fluffy, pint-sized white cloud",
      "goal": "Produce a thunderclap to impress the storm thunderheads"
    },
    {
      "name": "Grom",
      "role": "The towering storm elder",
      "goal": "Maintain an intense, rumbling storm"
    }
  ],
  "scenes": [
    {
      "scene_number": 1,
      "description": "Barnaby strains and squeezes himself until he turns bright red, but only produces a tiny static spark that tickles a passing bird.",
      "visual_suggestion": "Close-up on Barnaby's exaggerated squash-and-stretch straining expressions.",
      "dialogue": null,
      "sound_suggestions": ["Squeaking balloon strain", "Tiny static snap"]
    }
  ],
  "sound_suggestions": [
    "Orchestral build-up shifting from intimidating brass to playful woodwinds",
    "Soft rain crescendo"
  ]
}
```

---

## 4. Endpoint Specifications

### 4.1 Health Check: `GET /api/health`

#### Response `200 OK`
```json
{
  "status": "ok",
  "service": "frame-by-frame-backend",
  "version": "1.0.0",
  "provider": {
    "name": "nvidia",
    "configured": true,
    "model": "meta/llama-3.1-70b-instruct"
  }
}
```
*Note: If `NVIDIA_API_KEY` is missing, `"configured": false` is returned, letting the frontend know the API is running in mock/demo mode.*

---

### 4.2 Generate Plan: `POST /api/generate`

#### Request Body
```json
{
  "idea": "A tiny cloud wants to join a thunderstorm.",
  "runtime": "1m",
  "mood": "heartwarming",
  "audience": "children",
  "has_dialogue": false,
  "complexity": "simple"
}
```

#### Validation Rules
| Field | Type | Required | Constraints |
| :--- | :--- | :--- | :--- |
| `idea` | string | Yes | Min 5 chars, max 500 chars. Stripped of leading/trailing whitespace. |
| `runtime` | string | Yes | Must be one of `["30s", "1m", "3m"]`. |
| `mood` | string | Yes | Must be one of `["funny", "heartwarming", "mysterious", "adventurous"]`. |
| `audience` | string | Yes | Must be one of `["children", "teens", "general"]`. |
| `has_dialogue` | boolean | Yes | `true` or `false`. |
| `complexity` | string | Yes | Must be one of `["simple", "detailed"]`. |

#### Response `200 OK`
Returns an `AnimationPlan` object matching Section 3.2.

---

### 4.3 Revise Plan: `POST /api/revise`

#### Request Body
```json
{
  "previous_plan": {
    "title": "Little Spark in the Dark",
    "logline": "...",
    "runtime": "1m",
    "mood": "heartwarming",
    "audience": "children",
    "complexity": "simple",
    "characters": [...],
    "scenes": [...],
    "sound_suggestions": [...]
  },
  "revision_instruction": "Make the ending funnier by having Barnaby sneeze instead of raining."
}
```

#### Validation Rules
| Field | Type | Required | Constraints |
| :--- | :--- | :--- | :--- |
| `previous_plan` | object | Yes | Valid `AnimationPlan` object. |
| `revision_instruction` | string | Yes | Min 3 chars, max 300 chars. |

#### Response `200 OK`
Returns an updated `AnimationPlan` object reflecting the revision.

---

## 5. Error Responses & Envelopes

All error responses adhere to a consistent error schema:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Too many generation requests. Please wait 45 seconds before trying again.",
    "details": null
  }
}
```

### Standard Error Codes

| Status Code | Error Code | Description / Cause |
| :--- | :--- | :--- |
| `400` | `INVALID_INPUT` | Input string too short/long, or contains invalid characters. |
| `400` | `ARTIST_STYLE_RESTRICTION` | Direct imitation of a named living artist requested; advice on neutral descriptors provided. |
| `422` | `SCHEMA_VALIDATION_ERROR` | Request body missing fields or invalid types. |
| `429` | `RATE_LIMIT_EXCEEDED` | Client has made more than 10 requests within a 60-second window. |
| `502` | `PROVIDER_ERROR` | Upstream NVIDIA API returned a 5xx error or unexpected payload. |
| `503` | `PROVIDER_NOT_CONFIGURED` | `NVIDIA_API_KEY` is not configured on the server. |
| `504` | `PROVIDER_TIMEOUT` | Upstream NVIDIA API did not respond within the configured timeout window. |
| `500` | `INTERNAL_SERVER_ERROR` | Unexpected backend runtime error. Details masked to prevent security leaks. |

### Rate Limit Headers
When rate limits are applied, the following headers are included in responses:
- `X-RateLimit-Limit`: `10`
- `X-RateLimit-Remaining`: Remaining tokens in current window
- `Retry-After`: Seconds to wait before retrying (on `429` responses)
