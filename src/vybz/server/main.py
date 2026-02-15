"""
src/vybz/server/main.py

The entry point for the Vybz Engine (vybzd).
Updated to use Google ADK v1.24+ Runner and Event Streaming.
"""

import argparse
import uvicorn
from typing import List
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from google.genai import types

from vybz.server.state import ServerState

# Global Runtime State
state = ServerState()

# -----------------------------------------------------------------------------
# Pydantic Models (DTOs)
# -----------------------------------------------------------------------------

class AgentListing(BaseModel):
    id: str
    name: str
    description: str

class SessionInitRequest(BaseModel):
    agent_id: str
    context: str = ""

class SessionInitResponse(BaseModel):
    session_id: str

class SkillDTO(BaseModel):
    id: str
    name: str
    description: str
    instructions: str

class SkillDownlevelRequest(BaseModel):
    skill_id: str

class FileLoadDTO(BaseModel):
    filename: str
    content: str

# -----------------------------------------------------------------------------
# Application Lifecycle
# -----------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[vybzd] Starting up...")
    try:
        state.initialize()
        print("[vybzd] Startup complete.")
    except Exception as e:
        print(f"[vybzd] CRITICAL STARTUP ERROR: {e}")
        raise e
    yield
    print("[vybzd] Shutting down...")

app = FastAPI(title="Vybz Engine", version="0.2.0", lifespan=lifespan)

# -----------------------------------------------------------------------------
# REST Endpoints
# -----------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "agents_available": len(state.agent_templates),
        "active_sessions": len(state.runners),
        "model": state.model_id
    }

@app.get("/agents", response_model=List[AgentListing])
async def list_agents():
    agents = []
    for agent_id, template in state.agent_templates.items():
        agents.append(AgentListing(
            id=agent_id,
            name=template.name,
            description=f"v{template.version}"
        ))
    return agents

@app.post("/session/init", response_model=SessionInitResponse)
async def init_session(request: SessionInitRequest):
    try:
        sid = await state.create_session(request.agent_id, request.context)
        return SessionInitResponse(session_id=sid)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}/skills", response_model=List[SkillDTO])
async def list_session_skills(session_id: str):
    try:
        skills = await state.get_session_skills(session_id)
        return [SkillDTO(id=s.id, name=s.name, description=s.description, instructions=s.instructions) for s in skills]
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/session/{session_id}/skills/uplevel")
async def uplevel_skill(session_id: str, skill: SkillDTO):
    try:
        await state.uplevel_session_skill(session_id, skill.model_dump())
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/session/{session_id}/skills/downlevel")
async def downlevel_skill(session_id: str, request: SkillDownlevelRequest):
    try:
        if await state.downlevel_session_skill(session_id, request.skill_id):
            return {"status": "success"}
        raise HTTPException(status_code=404, detail="Skill not found")
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/session/{session_id}/load")
async def load_context(session_id: str, request: FileLoadDTO):
    try:
        await state.load_session_context(session_id, request.filename, request.content)
        return {"status": "success"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

# -----------------------------------------------------------------------------
# WebSocket Chat (ADK Runner Integration)
# -----------------------------------------------------------------------------

@app.websocket("/session/{session_id}/chat")
async def chat_endpoint(websocket: WebSocket, session_id: str):
    """
    Bidirectional WebSocket using ADK Runner.
    """
    await websocket.accept()

    try:
        runner = state.get_runner(session_id)
    except ValueError:
        await websocket.close(code=4004, reason="Session not found")
        return

    try:
        while True:
            # 1. Receive Input
            data = await websocket.receive_json()
            user_text = data.get("content")
            if not user_text:
                continue

            # 2. Format as GenAI Content
            input_content = types.Content(
                role="user",
                parts=[types.Part(text=user_text)]
            )

            # 3. Execute Runner (Streaming)
            # runner.run returns a generator of events
            try:
                events = runner.run(
                    user_id=state.user_id,
                    session_id=session_id,
                    new_message=input_content
                )


                for event in events:
                    # Handle streaming partials
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if hasattr(part, 'thought') and part.thought:
                                # Sending with a prefix
                                await websocket.send_text(f"\033[36m💭 {part.thought}\033[0m\n")
                                continue

                            # Check for standard text parts
                            if hasattr(part, 'text') and part.text:
                                await websocket.send_text(part.text)
                            # Note: We could handle tool calls here if needed in future

            except Exception as e:
                await websocket.send_text(f"[Error: {str(e)}]")

    except WebSocketDisconnect:
        pass

# -----------------------------------------------------------------------------
# Entry Point
# -----------------------------------------------------------------------------

def start() -> None:
    parser = argparse.ArgumentParser(description="Vybz Engine Server (vybzd)")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    args = parser.parse_args()
    uvicorn.run("vybz.server.main:app", host=args.host, port=args.port, reload=args.reload)

if __name__ == "__main__":
    start()
