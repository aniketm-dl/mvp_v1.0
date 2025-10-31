"""
Chat Service Layer for Airline Twin Chat System
Connects ChatHandler to FastAPI endpoints
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
from uuid import uuid4
import json
from datetime import datetime

from src.airline.chat_handler import ChatHandler
from src.airline.llm_gateway import LLMGateway
from fastapi import HTTPException

# Initialize chat handler with the airline LLM gateway
_CONVERSATIONS_DIR = Path("DATA/airline/conversations")
_CONVERSATIONS_DIR.mkdir(parents=True, exist_ok=True)

# Initialize LLM Gateway for airline twins
_LLM_GATEWAY = LLMGateway(config_path=Path("CONFIGS/airline/twin_config.yaml"))

# Initialize Chat Handler
_CHAT_HANDLER = ChatHandler(
    conversations_dir=_CONVERSATIONS_DIR,
    llm_gateway=_LLM_GATEWAY
)

# In-memory cache for active conversations
_CONVERSATION_CACHE = {}

class ChatService:
    """Service layer for chat operations"""

    @staticmethod
    def send_message(
        twin_id: str,
        message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Send a message to a twin and get response"""
        try:
            # Generate conversation ID if not provided
            if not conversation_id:
                conversation_id = f"conv_{uuid4().hex[:12]}"

            # Send message through chat handler
            response = _CHAT_HANDLER.send_message(
                twin_id=twin_id,
                message=message,
                conversation_id=conversation_id
            )

            # Format response for frontend
            return {
                "conversation_id": conversation_id,
                "user_message": {
                    "id": f"msg_{uuid4().hex[:8]}",
                    "role": "user",
                    "content": message,
                    "timestamp": datetime.utcnow().isoformat()
                },
                "twin_response": {
                    "id": f"msg_{uuid4().hex[:8]}",
                    "role": "assistant",
                    "content": response.get("reply", "I need to think about that."),
                    "timestamp": datetime.utcnow().isoformat(),
                    "twin_id": twin_id
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")

    @staticmethod
    def get_conversations(
        twin_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get list of conversations, optionally filtered by twin"""
        try:
            conversations = []
            conv_files = list(_CONVERSATIONS_DIR.glob("*.json"))

            # Sort by modification time (most recent first)
            conv_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

            for conv_file in conv_files[offset:offset + limit]:
                try:
                    with open(conv_file, 'r') as f:
                        conv = json.load(f)

                    # Filter by twin_id if specified
                    if twin_id and conv.get("twin_id") != twin_id:
                        continue

                    # Add metadata
                    conv["id"] = conv_file.stem
                    conv["file_path"] = str(conv_file)

                    # Create preview from last message
                    if conv.get("messages"):
                        last_user_msg = next(
                            (m for m in reversed(conv["messages"]) if m.get("role") == "user"),
                            None
                        )
                        conv["preview"] = last_user_msg["content"][:100] if last_user_msg else "No messages"
                        conv["message_count"] = len(conv["messages"])
                    else:
                        conv["preview"] = "Empty conversation"
                        conv["message_count"] = 0

                    conversations.append(conv)
                except Exception as e:
                    print(f"Error reading conversation {conv_file}: {e}")
                    continue

            return {
                "conversations": conversations,
                "count": len(conversations),
                "has_more": len(conv_files) > offset + limit
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading conversations: {str(e)}")

    @staticmethod
    def get_conversation(conversation_id: str) -> Dict[str, Any]:
        """Get a specific conversation by ID"""
        try:
            conv_path = _CONVERSATIONS_DIR / f"{conversation_id}.json"
            if not conv_path.exists():
                # Try without extension if it's already a full filename
                conv_path = _CONVERSATIONS_DIR / conversation_id
                if not conv_path.exists():
                    raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

            with open(conv_path, 'r') as f:
                conv = json.load(f)

            conv["id"] = conversation_id
            return conv
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error loading conversation: {str(e)}")

    @staticmethod
    def delete_conversation(conversation_id: str) -> Dict[str, Any]:
        """Delete a conversation"""
        try:
            conv_path = _CONVERSATIONS_DIR / f"{conversation_id}.json"
            if not conv_path.exists():
                raise HTTPException(status_code=404, detail=f"Conversation {conversation_id} not found")

            # Delete the file
            conv_path.unlink()

            # Remove from cache if present
            if conversation_id in _CONVERSATION_CACHE:
                del _CONVERSATION_CACHE[conversation_id]

            return {
                "success": True,
                "message": f"Conversation {conversation_id} deleted successfully"
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error deleting conversation: {str(e)}")

    @staticmethod
    def export_conversation(
        conversation_id: str,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Export a conversation in various formats"""
        try:
            conv = ChatService.get_conversation(conversation_id)

            if format == "json":
                return conv

            elif format == "csv":
                # Convert to CSV format
                import csv
                import io

                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Timestamp", "Role", "Content", "Twin ID"])

                for msg in conv.get("messages", []):
                    writer.writerow([
                        msg.get("timestamp", ""),
                        msg.get("role", ""),
                        msg.get("content", ""),
                        conv.get("twin_id", "")
                    ])

                return {
                    "format": "csv",
                    "content": output.getvalue(),
                    "filename": f"{conversation_id}.csv"
                }

            elif format == "markdown":
                # Convert to Markdown format
                lines = [
                    f"# Conversation with Twin {conv.get('twin_id', 'Unknown')}",
                    f"**Created:** {conv.get('created_at', 'Unknown')}",
                    f"**Updated:** {conv.get('updated_at', 'Unknown')}",
                    "",
                    "## Messages",
                    ""
                ]

                for msg in conv.get("messages", []):
                    role = "User" if msg.get("role") == "user" else "Twin"
                    lines.append(f"### {role}")
                    lines.append(f"*{msg.get('timestamp', '')}*")
                    lines.append("")
                    lines.append(msg.get("content", ""))
                    lines.append("")

                return {
                    "format": "markdown",
                    "content": "\n".join(lines),
                    "filename": f"{conversation_id}.md"
                }

            else:
                raise HTTPException(status_code=422, detail=f"Unsupported format: {format}")

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error exporting conversation: {str(e)}")

    @staticmethod
    def get_chat_analytics(
        twin_id: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get chat analytics and metrics"""
        try:
            conversations = ChatService.get_conversations(twin_id)["conversations"]

            # Calculate metrics
            total_conversations = len(conversations)
            total_messages = sum(c.get("message_count", 0) for c in conversations)
            avg_messages = total_messages / total_conversations if total_conversations > 0 else 0

            # Twin distribution
            twin_counts = {}
            for conv in conversations:
                tid = conv.get("twin_id", "unknown")
                twin_counts[tid] = twin_counts.get(tid, 0) + 1

            # Topic analysis (simple keyword extraction)
            common_topics = {}
            topic_keywords = {
                "price": ["price", "cost", "expensive", "cheap", "discount", "deal"],
                "comfort": ["seat", "legroom", "comfort", "space", "cramped"],
                "service": ["service", "staff", "help", "support", "crew"],
                "loyalty": ["points", "miles", "rewards", "loyalty", "status"],
                "delay": ["delay", "late", "on-time", "schedule", "punctual"],
                "upgrade": ["upgrade", "business", "first class", "premium"]
            }

            for conv in conversations:
                for msg in conv.get("messages", []):
                    if msg.get("role") == "user":
                        content = msg.get("content", "").lower()
                        for topic, keywords in topic_keywords.items():
                            if any(kw in content for kw in keywords):
                                common_topics[topic] = common_topics.get(topic, 0) + 1

            # Sort topics by frequency
            sorted_topics = sorted(common_topics.items(), key=lambda x: x[1], reverse=True)[:5]

            return {
                "overview": {
                    "total_conversations": total_conversations,
                    "total_messages": total_messages,
                    "avg_messages_per_conversation": round(avg_messages, 2),
                    "active_twins": len(twin_counts)
                },
                "by_twin": twin_counts,
                "common_topics": dict(sorted_topics),
                "time_range": {
                    "start": start_date or "all",
                    "end": end_date or "all"
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error generating analytics: {str(e)}")

    @staticmethod
    def compare_twin_responses(
        message: str,
        twin_ids: List[str],
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Get responses from multiple twins for comparison"""
        try:
            responses = {}

            for twin_id in twin_ids:
                try:
                    # Create temporary conversation for each twin
                    temp_conv_id = f"compare_{uuid4().hex[:8]}"
                    response = ChatService.send_message(
                        twin_id=twin_id,
                        message=message,
                        conversation_id=temp_conv_id,
                        context=context
                    )
                    responses[twin_id] = response["twin_response"]
                except Exception as e:
                    responses[twin_id] = {
                        "error": str(e),
                        "content": f"Error getting response from {twin_id}"
                    }

            return {
                "message": message,
                "responses": responses,
                "analysis": {
                    "response_count": len(responses),
                    "successful_responses": sum(1 for r in responses.values() if "error" not in r)
                }
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error comparing responses: {str(e)}")

# Initialize service
chat_service = ChatService()