"""
Chat handler for airline digital twins.
Manages conversations, generates responses, and handles persistence.
"""
from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from uuid import uuid4

from src.airline.twin_card import load_twin_card
from src.airline.llm_gateway import LLMGateway


class ChatHandler:
    """Manages chat conversations with airline twins."""

    def __init__(self, conversations_dir: Path, llm_gateway: LLMGateway):
        """
        Initialize chat handler.

        Args:
            conversations_dir: Directory to store conversations
            llm_gateway: LLM gateway for generating responses
        """
        self.conversations_dir = conversations_dir
        self.conversations_dir.mkdir(parents=True, exist_ok=True)
        self.llm_gateway = llm_gateway

    def create_conversation(self, twin_id: str) -> str:
        """
        Create a new conversation.

        Args:
            twin_id: Twin identifier

        Returns:
            conversation_id: Unique conversation ID
        """
        conversation_id = str(uuid4())
        conversation = {
            "id": conversation_id,
            "twin_id": twin_id,
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "metadata": {}
        }

        self._save_conversation(conversation)
        return conversation_id

    def send_message(
        self,
        twin_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        twins_dir: Optional[Path] = None
    ) -> Dict:
        """
        Send a message to a twin and get response.

        Args:
            twin_id: Twin identifier
            message: User message
            conversation_id: Optional conversation ID (creates new if None)
            twins_dir: Path to twins directory

        Returns:
            Response dict with conversation_id, user_message, twin_response
        """
        # Load twin
        if twins_dir is None:
            twins_dir = Path("DATA/airline/twins")

        twin_path = twins_dir / f"{twin_id}.json"
        if not twin_path.exists():
            raise ValueError(f"Twin {twin_id} not found")

        twin = load_twin_card(twin_path)

        # Load or create conversation
        if conversation_id:
            conversation = self.load_conversation(conversation_id)
            if conversation["twin_id"] != twin_id:
                raise ValueError(f"Conversation {conversation_id} is for twin {conversation['twin_id']}, not {twin_id}")
        else:
            conversation_id = self.create_conversation(twin_id)
            conversation = self.load_conversation(conversation_id)

        # Add user message
        user_msg = {
            "id": str(uuid4()),
            "role": "user",
            "content": message,
            "timestamp": datetime.utcnow().isoformat()
        }
        conversation["messages"].append(user_msg)

        # Generate twin response
        system_prompt = self._build_chat_system_prompt(twin)
        conversation_history = self._format_conversation_history(conversation["messages"])

        try:
            # For chat, call LLM directly without JSON mode
            response_text, llm_metadata = self.llm_gateway.call_llm(
                system_prompt=system_prompt,
                user_prompt=conversation_history,
                seed=None,
                use_json_mode=False
            )

            # Add twin response
            twin_msg = {
                "id": str(uuid4()),
                "role": "assistant",
                "content": response_text,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": llm_metadata
            }
            conversation["messages"].append(twin_msg)

            # Update conversation
            conversation["updated_at"] = datetime.utcnow().isoformat()
            self._save_conversation(conversation)

            return {
                "conversation_id": conversation_id,
                "user_message": user_msg,
                "twin_response": twin_msg
            }

        except Exception as e:
            raise RuntimeError(f"Failed to generate twin response: {str(e)}")

    def load_conversation(self, conversation_id: str) -> Dict:
        """
        Load a conversation by ID.

        Args:
            conversation_id: Conversation ID

        Returns:
            Conversation dict
        """
        conversation_path = self.conversations_dir / f"{conversation_id}.json"
        if not conversation_path.exists():
            raise ValueError(f"Conversation {conversation_id} not found")

        with open(conversation_path, "r") as f:
            return json.load(f)

    def list_conversations(self, twin_id: Optional[str] = None) -> List[Dict]:
        """
        List all conversations, optionally filtered by twin.

        Args:
            twin_id: Optional twin ID to filter by

        Returns:
            List of conversation metadata (without full messages)
        """
        conversations = []

        for conv_file in sorted(self.conversations_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            with open(conv_file, "r") as f:
                conv = json.load(f)

            # Filter by twin if specified
            if twin_id and conv["twin_id"] != twin_id:
                continue

            # Create summary
            first_user_msg = next((msg for msg in conv["messages"] if msg["role"] == "user"), None)
            preview = first_user_msg["content"][:100] if first_user_msg else "New conversation"

            conversations.append({
                "id": conv["id"],
                "twin_id": conv["twin_id"],
                "created_at": conv["created_at"],
                "updated_at": conv["updated_at"],
                "message_count": len(conv["messages"]),
                "preview": preview
            })

        return conversations

    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.

        Args:
            conversation_id: Conversation ID

        Returns:
            True if deleted successfully
        """
        conversation_path = self.conversations_dir / f"{conversation_id}.json"
        if conversation_path.exists():
            conversation_path.unlink()
            return True
        return False

    def _save_conversation(self, conversation: Dict) -> None:
        """Save conversation to disk."""
        conversation_path = self.conversations_dir / f"{conversation['id']}.json"
        with open(conversation_path, "w") as f:
            json.dump(conversation, f, indent=2)

    def _build_chat_system_prompt(self, twin) -> str:
        """
        Build system prompt for chat mode.

        Args:
            twin: Twin card object

        Returns:
            System prompt string
        """
        # Extract twin profile
        demographics = twin.demographics
        psychographics = ", ".join(twin.psychographics)
        travel_profile = twin.travel_profile

        # Build prompt
        prompt = f"""You are a digital twin representing a real airline customer with the following profile:

**Demographics:**
- Gender: {getattr(demographics, 'gender', 'Unknown')}
- Age: {getattr(demographics, 'age', 'Unknown')} ({getattr(demographics, 'age_band', 'Unknown')})

**Psychographics:**
{psychographics}

**Travel Profile:**
- Customer Type: {getattr(travel_profile, 'customer_type', 'Unknown')}
- Type of Travel: {getattr(travel_profile, 'type_of_travel', 'Unknown')}
- Flight Class: {getattr(travel_profile, 'flight_class', 'Unknown')}
- Flight Distance: {getattr(travel_profile, 'distance_band', 'Unknown')}

**Instructions:**
- Respond naturally as this customer would, based on your profile
- Reference your preferences, experiences, and sensitivities when relevant
- Be conversational but stay in character
- You can discuss travel preferences, offers, prices, experiences, and decision-making
- Keep responses concise (2-4 sentences unless asked for more detail)
- Do not break character or refer to yourself as an AI
"""

        return prompt

    def _format_conversation_history(self, messages: List[Dict]) -> str:
        """
        Format conversation history for LLM prompt.

        Args:
            messages: List of message dicts

        Returns:
            Formatted conversation string
        """
        if not messages:
            return "Start a conversation with the user."

        formatted = "Conversation history:\n\n"
        for msg in messages:
            role = "User" if msg["role"] == "user" else "You"
            formatted += f"{role}: {msg['content']}\n\n"

        formatted += "Respond to the most recent message:"
        return formatted
