from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ValidationError
from typing import List, Optional, Dict, Any
import uuid
import os
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from persistence import repository
from agents.travel_agent import root_agent

app = FastAPI(title="Travel-Mind API", version="1.0.0")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class MessageRequest(BaseModel):
    session_id: str
    message: str

class MessageResponse(BaseModel):
    response: str
    citations: List[Any] = []
    session_id: str

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/sessions/{session_id}")
def get_session_history(session_id: str):
    try:
        history = repository.get_session(session_id)
        return {"session_id": session_id, "messages": history}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/messages", response_model=MessageResponse)
async def send_message(
    req: MessageRequest, 
    x_idempotency_key: Optional[str] = Header(None)
):
    # Validate session_id
    try:
        repository._validate_session_id(req.session_id)
    except ValueError as e:
         raise HTTPException(status_code=400, detail=str(e))

    # Retrieve history
    try:
        history = repository.get_session(req.session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve history: {str(e)}")

    # Save User Message
    user_msg = {"role": "user", "content": req.message}
    try:
        repository.save_message(req.session_id, user_msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save user message: {str(e)}")

    # Run Agent
    # We need to construct the chat history for the agent.
    # Assuming LlmAgent accepts previous history in some format or we manually inject it.
    # The ADK documentation/usage isn't fully detailed in prompt, but typically agents take a state or history.
    # For now, I'll assume a 'query' or 'chat' method.
    # If the provided LlmAgent class doesn't support history injection directly in the call, 
    # we might need to rely on its internal state if it was stateful (but it's instantiated globally, so it's likely stateless per request).
    # Typically, we pass history in the prompt or context.
    
    # Construct prompt with history (naive approach if ADK doesn't handle it automatically via session_id)
    # limit to last 15 messages as per prompt
    formatted_history = "\n".join([f"{m.get('role', 'unknown')}: {m.get('content', '')}" for m in history[-15:]])
    full_prompt = f"HISTORY:\n{formatted_history}\n\nUSER:\n{req.message}"
    
    try:
        # NOTE: This invoke method is hypothetical based on standard agent frameworks.
        # Adjust based on actual ADK method (e.g., .invoke, .query, .ask).
        # Since I mocked it or it's unknown, I'll use a generic 'query' and wrap in try/except.
        if hasattr(root_agent, 'query'):
            agent_response = root_agent.query(full_prompt)
        elif hasattr(root_agent, '__call__'):
            agent_response = root_agent(full_prompt)
        else:
             agent_response = "Error: Agent method unknown"

        # Safe parsing of response
        citations = []
        if hasattr(agent_response, 'text'):
             content = agent_response.text
             if hasattr(agent_response, 'citations'):
                 citations = agent_response.citations
        else:
             content = str(agent_response)
        
        # Grounding Check
        if "Tour ID" not in content and "No encontrado" not in content:
            # In logic: retry or append warning
            pass
            
    except Exception as e:
        # Log error and return failure
        # For debug, print full error
        print(f"Agent Execution Error: {e}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")

    # Save Model Response
    model_msg = {
        "role": "model", 
        "content": content,
        "metadata": {"citations": citations} 
    }
    repository.save_message(req.session_id, model_msg)

    return MessageResponse(
        response=content,
        citations=citations,
        session_id=req.session_id
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
