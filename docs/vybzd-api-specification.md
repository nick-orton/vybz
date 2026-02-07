# Vybz Engine (vybzd) API Specification

The `vybzd` server is a headless service that hosts the Google Agent
Development Kit (ADK) runtime. It manages agent personas, chat history, and
dynamic context injection for the Vibe Coding Workbench.

---

## Global Resources

### Health Check
Returns the current status of the engine and the active model configuration.

*   **URL:** `/health`
*   **Method:** `GET`
*   **URL Params:** None
*   **Data Params:** None
*   **Success Response:**
    *   **Code:** 200 OK
    *   **Content:** `{ "status": "ok", "agents_loaded": 10, "model": "..." }`
*   **Sample Call:**
    ```bash
    curl -X GET http://127.0.0.1:8000/health
    ```

### List Agents
Retrieves all agent personas currently hydrated in the server's squad.

*   **URL:** `/agents`
*   **Method:** `GET`
*   **URL Params:** None
*   **Data Params:** None
*   **Success Response:**
    *   **Code:** 200 OK
    *   **Content:** `[{"id": "junior-dev", "name": "...", "description": "..."}]`
*   **Sample Call:**
    ```bash
    curl -X GET http://127.0.0.1:8000/agents
    ```

---

## Session Management

### Initialize Session
Starts a new stateful chat session. The client should transmit the local
`CodeBase` snapshot during this call to prime the agent's context.

*   **URL:** `/session/init`
*   **Method:** `POST`
*   **URL Params:** None
*   **Data Params:**
    ```json
    {
      "agent_id": "string",
      "context": "string (Markdown representation of codebase)"
    }
    ```
*   **Success Response:**
    *   **Code:** 200 OK
    *   **Content:** `{ "session_id": "UUID" }`
*   **Error Response:**
    *   **Code:** 404 NOT FOUND (If agent_id is invalid)
*   **Sample Call:**
    ```bash
    curl -X POST http://127.0.0.1:8000/session/init \
         -H "Content-Type: application/json" \
         -d '{"agent_id": "junior-dev", "context": "# CodeBase..."}'
    ```

### List Session Skills
Retrieves the list of skills currently attached to the session-scoped agent.

*   **URL:** `/session/:id/skills`
*   **Method:** `GET`
*   **URL Params:** `id=[string] (The session UUID)`
*   **Data Params:** None
*   **Success Response:**
    *   **Code:** 200 OK
    *   **Content:** `[{"id": "...", "name": "...", "instructions": "..."}]`
*   **Sample Call:**
    ```bash
    curl -X GET http://127.0.0.1:8000/session/<uuid>/skills
    ```

### Uplevel Skill
Injects a new capability or updates an existing skill for the duration of the
active session. This triggers an internal system instruction refresh.

*   **URL:** `/session/:id/skills/uplevel`
*   **Method:** `POST`
*   **URL Params:** `id=[string]`
*   **Data Params:**
    ```json
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "instructions": "string (Markdown)"
    }
    ```
*   **Success Response:**
    *   **Code:** 200 OK
    *   **Content:** `{ "status": "success" }`
*   **Sample Call:**
    ```bash
    curl -X POST http://127.0.0.1:8000/session/<uuid>/skills/uplevel \
         -H "Content-Type: application/json" \
         -d '{"id": "sql-pro", "name": "SQL Pro", "instructions": "Use Postgres."}'
    ```

### Downlevel Skill
Removes a specific skill from the session-scoped agent.

*   **URL:** `/session/:id/skills/downlevel`
*   **Method:** `POST`
*   **URL Params:** `id=[string]`
*   **Data Params:** `{ "skill_id": "string" }`
*   **Success Response:**
    *   **Code:** 200 OK
    *   **Content:** `{ "status": "success" }`
*   **Sample Call:**
    ```bash
    curl -X POST http://127.0.0.1:8000/session/<uuid>/skills/downlevel \
         -H "Content-Type: application/json" \
         -d '{"skill_id": "sql-pro"}'
    ```

### Load File Context
Surgically injects a single file's content into the agent's context window.
This data persists across codebase updates.

*   **URL:** `/session/:id/load`
*   **Method:** `POST`
*   **URL Params:** `id=[string]`
*   **Data Params:** `{ "filename": "string", "content": "string" }`
*   **Success Response:**
    *   **Code:** 200 OK
    *   **Content:** `{ "status": "success" }`
*   **Sample Call:**
    ```bash
    curl -X POST http://127.0.0.1:8000/session/<uuid>/load \
         -H "Content-Type: application/json" \
         -d '{"filename": "config.yaml", "content": "key: value"}'
    ```

### Update Session Context
Replaces the `CodeBase` snapshot for the active session. This allows the agent to see file changes made since the session started.

*   **URL:** `/session/:id/context`
*   **Method:** `POST`
*   **URL Params:** `id=[string]`
*   **Data Params:** `{ "context": "string (Full Markdown Snapshot)" }`
*   **Success Response:**
    *   **Code:** 200 OK
    *   **Content:** `{ "status": "success" }`
*   **Sample Call:**
    ```bash
    curl -X POST http://127.0.0.1:8000/session/<uuid>/context \
         -H "Content-Type: application/json" \
         -d '{"context": "# CodeBase..."}'
    ```

---

## Real-Time Interaction

### Chat Stream
A bidirectional WebSocket for real-time streaming.

*   **URL:** `/session/:id/chat`
*   **Protocol:** `ws` or `wss`
*   **URL Params:** `id=[string]`
*   **Message Format:**
    *   **Client Send:** `{"content": "User Prompt"}`
    *   **Server Receive:** Raw text chunks (UTF-8)
*   **Notes:** The server stops sending messages when the generation finishes.
    The connection remains open for follow-up turns.
*   **Sample Call (using wscat):**
    ```bash
    wscat -c ws://127.0.0.1:8000/session/<uuid>/chat
    > {"content": "Hello"}
    < Hi
    < there!
<<<<<<< HEAD
```

## 5. Error Handling

The API uses standard HTTP status codes:
*   `404 Not Found`: The specified `agent_id` or `session_id` does not exist.
*   `422 Unprocessable Entity`: The JSON payload is missing required fields.
*   `500 Internal Server Error`: An error occurred in the ADK runtime or
    upstream Gemini API.

=======
>>>>>>> 47aac04 (docs(vybzd): define initial API specification for the engine)
