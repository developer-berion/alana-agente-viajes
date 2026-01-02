import streamlit as st
import requests
import uuid
import os

# Configuration
API_URL = os.getenv("API_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Travel-Mind B2B",
    page_icon="✈️",
    layout="wide"
)

def init_session():
    """Initialize session ID from URL or generate new one."""
    # Check if session_id is in query params
    params = st.query_params
    if "session_id" in params:
        st.session_state.session_id = params["session_id"]
    elif "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
        # Update URL
        st.query_params["session_id"] = st.session_state.session_id

def reset_session():
    """Generate a new session ID and clear state."""
    st.session_state.session_id = str(uuid.uuid4())
    st.query_params["session_id"] = st.session_state.session_id
    # Rerun to clear chat history defined by session ID
    st.rerun()

def fetch_history(session_id):
    """Fetch chat history from API."""
    try:
        response = requests.get(f"{API_URL}/sessions/{session_id}")
        if response.status_code == 200:
            return response.json().get("messages", [])
        elif response.status_code == 404:
            return []
        else:
            st.error(f"Error fetching history: {response.text}")
            return []
    except Exception as e:
        st.error(f"Connection error: {e}")
        return []

def send_message(session_id, message):
    """Send message to API."""
    try:
        payload = {"session_id": session_id, "message": message}
        # Add Idempotency Key (Optional implementation detail, using UUID)
        headers = {"X-Idempotency-Key": str(uuid.uuid4())}
        response = requests.post(f"{API_URL}/messages", json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Error sending message: {response.text}")
            return None
    except Exception as e:
        st.error(f"Connection error: {e}")
        return None

# --- Main App Logic ---

init_session()
session_id = st.session_state.session_id

# Sidebar
with st.sidebar:
    st.title("Travel-Mind ✈️")
    st.markdown(f"**Session ID:** `{session_id}`")
    
    if st.button("New Chat", type="primary"):
        reset_session()
        
    st.markdown("---")
    st.markdown("### Debug Info")
    st.markdown(f"API: `{API_URL}`")

# Main Chat Area
st.title("Asesor B2B")

# Load History
# We fetch history on every rerun to stay synced with DB source of truth
history = fetch_history(session_id)

# Display Messages
for msg in history:
    role = msg.get("role", "user")
    content = msg.get("content", "")
    
    with st.chat_message(role):
        st.markdown(content)
        
        # Display Citations/Metadata if present (Grounding)
        metadata = msg.get("metadata", {})
        if metadata and "citations" in metadata:
            citations = metadata.get("citations", [])
            if citations:
                st.caption("Sources:")
                for cit in citations:
                    # Assuming citation structure, adapting to generic display
                    st.markdown(f"- {str(cit)}")

# Chat Input
if prompt := st.chat_input("Escribe tu solicitud de viaje..."):
    # Optimistic UI: Display user message immediately
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Send to API
    with st.spinner("Consultando promociones..."):
        response_data = send_message(session_id, prompt)
        
    if response_data:
        # Display Agent Response
        # The history update happens on rerun, but we can display immediately too
        with st.chat_message("model"):
            st.markdown(response_data.get("response", "Error getting response"))
            
            # Citations (mock check for now as API might return empty list)
            citations = response_data.get("citations", [])
            if citations:
                st.caption("Sources:")
                for cit in citations:
                    st.markdown(f"- {str(cit)}")
        
        # Force a rerun to fetch consistent state from DB if desired, 
        # but Streamlit might handle the flow naturally on next interaction.
        # To be safe and consistent with "SSOT = DB", we could rerun, 
        # but it might feel jumpy. Let's leave it as append-UI and fetch-next-run.
