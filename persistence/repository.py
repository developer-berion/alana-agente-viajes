import os
import uuid
from typing import List, Dict, Any
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter

# Initialize Firestore Client
# Note: In production, credentials should be handled via environment variables or workload identity.
_db = None

def _get_db():
    global _db
    if _db is None:
        _db = firestore.Client()
    return _db

def _validate_session_id(session_id: str):
    """
    Validates that the session_id is a valid UUID v4.
    Raises ValueError if invalid.
    """
    try:
        val = uuid.UUID(session_id, version=4)
        if str(val) != session_id:
             raise ValueError("Malformed UUID")
    except ValueError:
        raise ValueError(f"Invalid session_id: {session_id}. Must be a valid UUID v4.")

def get_session(session_id: str) -> List[Dict[str, Any]]:
    """
    Retrieves the full message history for a given session_id.
    Messages are sorted by timestamp ascending.
    """
    _validate_session_id(session_id)
    
    session_ref = _get_db().collection("sessions").document(session_id)
    messages_ref = session_ref.collection("messages")
    
    # Order by timestamp to maintain conversation flow
    query = messages_ref.order_by("timestamp", direction=firestore.Query.ASCENDING)
    results = query.stream()
    
    history = []
    for doc in results:
        data = doc.to_dict()
        # Ensure timestamp is serialized or kept as object depending on usage. 
        # For internal usage, datetime objects are fine.
        history.append(data)
        
    return history

def save_message(session_id: str, message: Dict[str, Any]) -> str:
    """
    Appends a message to the session's history.
    Uses an append-only strategy (subcollection).
    
    Args:
        session_id: Valid UUID v4 string.
        message: Dictionary containing 'role', 'content', and optional 'metadata'.
        
    Returns:
        The ID of the newly created message document.
    """
    _validate_session_id(session_id)
    
    # Enforce basic schema validation here if needed, 
    # though strict schema is also good practice at the API layer.
    if "role" not in message or "content" not in message:
        raise ValueError("Message must contain 'role' and 'content'.")

    # Add server-side timestamp for consistent ordering
    if "timestamp" not in message:
        message["timestamp"] = firestore.SERVER_TIMESTAMP

    session_ref = _get_db().collection("sessions").document(session_id)
    
    # Ensure the session document exists (optional, could just write to subcollection)
    # Writing to the parent doc helps with listing sessions later if needed.
    if not session_ref.get().exists:
        session_ref.set({"created_at": firestore.SERVER_TIMESTAMP})

    # Add message to subcollection
    message_ref = session_ref.collection("messages").document()
    message_ref.set(message)
    
    return message_ref.id
