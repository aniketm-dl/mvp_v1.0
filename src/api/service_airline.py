"""
Streamlined FastAPI service for Airline Digital Twins only.
This version focuses on airline endpoints without requiring the full e-commerce infrastructure.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional
from uuid import uuid4
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse, PlainTextResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import yaml
import json
import time
import os
from pathlib import Path

# Airline module imports
from src.airline.twin_card import load_twin_card
from src.airline.schemas import (
    OfferAcceptanceTask,
    DecisionContext,
    DecisionResponse,
    TwinDecision,
    create_legroom_offer,
    create_wifi_offer,
    create_lounge_offer,
    create_priority_boarding_offer,
    create_baggage_offer
)
from src.airline.prompt_composer import compose_prompts
from src.airline.llm_gateway import LLMGateway
from src.airline.chat_handler import ChatHandler

app = FastAPI(title="Darpan Digital Twins - Airline")

# CORS - Allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Airline configuration
_AIRLINE_CONFIG_PATH = Path("CONFIGS/airline/twin_config.yaml")
_AIRLINE_GATEWAY = LLMGateway(_AIRLINE_CONFIG_PATH) if _AIRLINE_CONFIG_PATH.exists() else None
_AIRLINE_TWINS_DIR = Path("DATA/airline/twins")
_AIRLINE_PROMPTS_DIR = Path("PROMPTS/airline")
_CONVERSATIONS_DIR = Path("DATA/airline/conversations")
_CHAT_HANDLER = ChatHandler(_CONVERSATIONS_DIR, _AIRLINE_GATEWAY) if _AIRLINE_GATEWAY else None

OFFER_FACTORIES = {
    "legroom": create_legroom_offer,
    "wifi": create_wifi_offer,
    "lounge": create_lounge_offer,
    "boarding": create_priority_boarding_offer,
    "baggage": create_baggage_offer
}

# Pydantic models
class AirlineDecisionRequest(BaseModel):
    twin_id: str = Field(..., description="Twin identifier (e.g., twin_001)")
    offer_type: str = Field(..., description="Offer type: legroom, wifi, lounge, boarding, baggage")
    discount_pct: float = Field(..., description="Discount percentage (0.0 to 1.0)")
    flight_length: str = Field(default="medium", description="Flight length: short, medium, long")
    trip_purpose: str = Field(default="business", description="Trip purpose: business, leisure")
    time_pressure: str = Field(default="medium", description="Time pressure: low, medium, high")
    recent_delays: str = Field(default="minor", description="Recent delays: none, minor, major")
    seed: Optional[int] = Field(default=None, description="Random seed for determinism")

class AirlineBatchDecisionRequest(BaseModel):
    twin_ids: List[str] = Field(..., description="List of twin identifiers")
    offer_type: str = Field(..., description="Offer type")
    discount_pct: float = Field(..., description="Discount percentage")
    flight_length: str = Field(default="medium")
    trip_purpose: str = Field(default="business")
    time_pressure: str = Field(default="medium")
    recent_delays: str = Field(default="minor")
    seed: Optional[int] = Field(default=None)

class ChatMessageRequest(BaseModel):
    twin_id: str = Field(..., description="Twin identifier")
    message: str = Field(..., description="User message")
    conversation_id: Optional[str] = Field(default=None, description="Conversation ID (creates new if not provided)")

class ChatExperimentRequest(BaseModel):
    twin_id: str = Field(..., description="Twin identifier")
    conversation_id: str = Field(..., description="Conversation ID")
    offer_type: str = Field(..., description="Offer type")
    discount_pct: float = Field(..., description="Discount percentage")
    flight_length: str = Field(default="medium")
    trip_purpose: str = Field(default="business")
    time_pressure: str = Field(default="medium")
    recent_delays: str = Field(default="minor")
    seed: Optional[int] = Field(default=None)

# Health endpoint
@app.get("/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "airline-twins",
        "llm_gateway": "initialized" if _AIRLINE_GATEWAY else "not_initialized"
    }

@app.get("/airline/twins")
def airline_twins_list() -> Dict[str, Any]:
    """List all available airline twins."""
    if not _AIRLINE_TWINS_DIR.exists():
        return {"twins": [], "error": "Airline twins directory not found"}

    twins = []
    for twin_file in sorted(_AIRLINE_TWINS_DIR.glob("twin_*.json")):
        with open(twin_file) as f:
            twin_data = json.load(f)
            twins.append({
                "id": twin_data["id"],
                "label": twin_data["label"],
                "demographics": twin_data["demographics"],
                "psychographics": twin_data["psychographics"],
                "travel_profile": twin_data["travel_profile"]
            })

    return {"twins": twins, "count": len(twins)}

@app.post("/airline/decide")
def airline_decide(req: AirlineDecisionRequest) -> Dict[str, Any]:
    """Make a single airline twin decision."""
    if not _AIRLINE_GATEWAY:
        raise HTTPException(status_code=500, detail="Airline LLM gateway not initialized. Check OPENAI_API_KEY.")

    # Load twin
    twin_path = _AIRLINE_TWINS_DIR / f"{req.twin_id}.json"
    if not twin_path.exists():
        raise HTTPException(status_code=404, detail=f"Twin {req.twin_id} not found")

    twin = load_twin_card(twin_path)

    # Create offer
    if req.offer_type not in OFFER_FACTORIES:
        raise HTTPException(status_code=422, detail=f"Invalid offer type: {req.offer_type}")

    offer_factory = OFFER_FACTORIES[req.offer_type]
    offer = offer_factory(discount_pct=req.discount_pct)

    # Create context
    context = DecisionContext(
        flight_length=req.flight_length,
        trip_purpose=req.trip_purpose,
        time_pressure=req.time_pressure,
        recent_delays=req.recent_delays
    )

    # Create task
    task = OfferAcceptanceTask(offer=offer, context=context)

    # Compose prompts
    system_prompt, user_prompt = compose_prompts(twin, task, _AIRLINE_PROMPTS_DIR)

    # Get decision
    try:
        decision_dict, llm_metadata = _AIRLINE_GATEWAY.get_decision(
            system_prompt,
            user_prompt,
            seed=req.seed
        )

        response = DecisionResponse.from_dict(decision_dict)

        metadata = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "seed": req.seed,
            "llm_metadata": llm_metadata
        }

        twin_decision = TwinDecision(
            twin_id=twin.id,
            twin_label=twin.label,
            task=task,
            response=response,
            metadata=metadata
        )

        return twin_decision.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Decision failed: {str(e)}")

@app.post("/airline/batch_decide")
def airline_batch_decide(req: AirlineBatchDecisionRequest) -> Dict[str, Any]:
    """Make decisions for multiple airline twins."""
    results = []
    errors = []

    for twin_id in req.twin_ids:
        try:
            decision_req = AirlineDecisionRequest(
                twin_id=twin_id,
                offer_type=req.offer_type,
                discount_pct=req.discount_pct,
                flight_length=req.flight_length,
                trip_purpose=req.trip_purpose,
                time_pressure=req.time_pressure,
                recent_delays=req.recent_delays,
                seed=req.seed
            )
            decision = airline_decide(decision_req)
            results.append(decision)
        except Exception as e:
            errors.append({"twin_id": twin_id, "error": str(e)})

    return {
        "results": results,
        "errors": errors,
        "total": len(req.twin_ids),
        "successful": len(results),
        "failed": len(errors)
    }

@app.get("/airline/decisions/export")
def airline_decisions_export(format: str = "json") -> Any:
    """Export decision ledger."""
    ledger_path = Path("DATA/airline/decisions/ledger.csv")

    if not ledger_path.exists():
        raise HTTPException(status_code=404, detail="Decision ledger not found")

    if format == "csv":
        with open(ledger_path, "r") as f:
            csv_content = f.read()
        return PlainTextResponse(content=csv_content, media_type="text/csv")

    elif format == "json":
        import pandas as pd
        df = pd.read_csv(ledger_path)
        return JSONResponse(content=df.to_dict(orient="records"))

    else:
        raise HTTPException(status_code=422, detail="Format must be 'csv' or 'json'")

# ============================================================================
# CHAT ENDPOINTS
# ============================================================================

@app.post("/airline/chat")
def airline_chat(req: ChatMessageRequest) -> Dict[str, Any]:
    """Send a message to a twin and get response."""
    if not _CHAT_HANDLER:
        raise HTTPException(status_code=500, detail="Chat handler not initialized. Check OPENAI_API_KEY.")

    try:
        response = _CHAT_HANDLER.send_message(
            twin_id=req.twin_id,
            message=req.message,
            conversation_id=req.conversation_id,
            twins_dir=_AIRLINE_TWINS_DIR
        )
        return response

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")

@app.post("/airline/chat/experiment")
def airline_chat_experiment(req: ChatExperimentRequest) -> Dict[str, Any]:
    """Run an experiment within a chat conversation."""
    if not _AIRLINE_GATEWAY:
        raise HTTPException(status_code=500, detail="Airline LLM gateway not initialized. Check OPENAI_API_KEY.")

    if not _CHAT_HANDLER:
        raise HTTPException(status_code=500, detail="Chat handler not initialized.")

    # Load conversation to verify it exists
    try:
        conversation = _CHAT_HANDLER.load_conversation(req.conversation_id)
        if conversation["twin_id"] != req.twin_id:
            raise HTTPException(
                status_code=400,
                detail=f"Conversation {req.conversation_id} is for twin {conversation['twin_id']}, not {req.twin_id}"
            )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Run the experiment (same as /airline/decide)
    twin_path = _AIRLINE_TWINS_DIR / f"{req.twin_id}.json"
    if not twin_path.exists():
        raise HTTPException(status_code=404, detail=f"Twin {req.twin_id} not found")

    twin = load_twin_card(twin_path)

    # Create offer
    if req.offer_type not in OFFER_FACTORIES:
        raise HTTPException(status_code=422, detail=f"Invalid offer type: {req.offer_type}")

    offer_factory = OFFER_FACTORIES[req.offer_type]
    offer = offer_factory(discount_pct=req.discount_pct)

    # Create context
    context = DecisionContext(
        flight_length=req.flight_length,
        trip_purpose=req.trip_purpose,
        time_pressure=req.time_pressure,
        recent_delays=req.recent_delays
    )

    # Create task
    task = OfferAcceptanceTask(offer=offer, context=context)

    # Compose prompts
    system_prompt, user_prompt = compose_prompts(twin, task, _AIRLINE_PROMPTS_DIR)

    # Get decision
    try:
        decision_dict, llm_metadata = _AIRLINE_GATEWAY.get_decision(
            system_prompt,
            user_prompt,
            seed=req.seed
        )

        response = DecisionResponse.from_dict(decision_dict)

        metadata = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
            "seed": req.seed,
            "llm_metadata": llm_metadata
        }

        twin_decision = TwinDecision(
            twin_id=twin.id,
            twin_label=twin.label,
            task=task,
            response=response,
            metadata=metadata
        )

        return {
            "conversation_id": req.conversation_id,
            "decision": twin_decision.to_dict()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Experiment failed: {str(e)}")

@app.get("/airline/chat/history")
def airline_chat_history(twin_id: Optional[str] = None) -> Dict[str, Any]:
    """Get conversation history, optionally filtered by twin."""
    if not _CHAT_HANDLER:
        raise HTTPException(status_code=500, detail="Chat handler not initialized.")

    try:
        conversations = _CHAT_HANDLER.list_conversations(twin_id=twin_id)
        return {
            "conversations": conversations,
            "count": len(conversations)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load history: {str(e)}")

@app.get("/airline/chat/conversation/{conversation_id}")
def airline_chat_conversation(conversation_id: str) -> Dict[str, Any]:
    """Get a specific conversation with all messages."""
    if not _CHAT_HANDLER:
        raise HTTPException(status_code=500, detail="Chat handler not initialized.")

    try:
        conversation = _CHAT_HANDLER.load_conversation(conversation_id)
        return conversation
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to load conversation: {str(e)}")

@app.delete("/airline/chat/conversation/{conversation_id}")
def airline_chat_delete(conversation_id: str) -> Dict[str, Any]:
    """Delete a conversation."""
    if not _CHAT_HANDLER:
        raise HTTPException(status_code=500, detail="Chat handler not initialized.")

    success = _CHAT_HANDLER.delete_conversation(conversation_id)
    if success:
        return {"success": True, "message": f"Conversation {conversation_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")
