import os
import vertexai
from vertexai.preview.generative_models import GenerativeModel, Tool, grounding

# Try to import ADK, if not found, use standard SDK implementation wrapping
try:
    from google.adk.agents import LlmAgent
    from google.adk.tools import agent_tool
    from google.adk.tools import VertexAiSearchTool
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    print("INFO: google.adk not found. Using Standard Vertex AI SDK implementation.")

# Configuration
PROJECT_ID = os.getenv("PROJECT_ID", "pdf-to-markdown-483017")
LOCATION = os.getenv("LOCATION", "us-central1")
DATA_STORE_ID = os.getenv("DATA_STORE_ID", "projects/pdf-to-markdown-483017/locations/global/collections/default_collection/dataStores/dato_1767316786678")

# Initialize Vertex AI
try:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
except Exception as e:
    print(f"WARNING: Vertex AI Init failed: {e}")

if ADK_AVAILABLE:
    # --- ORIGINAL ADK IMPLEMENTATION (If library existed) ---
    agente_de_viajes_vertex_ai_search_agent = LlmAgent(
      name='Agente_de_viajes_vertex_ai_search_agent',
      model='gemini-2.5-pro',
      description=('Agent specialized in performing Vertex AI Search.'),
      sub_agents=[],
      instruction='Use the VertexAISearchTool to find information using Vertex AI Search.',
      tools=[
        VertexAiSearchTool(data_store_id=DATA_STORE_ID)
      ],
    )
    root_agent = LlmAgent(
      name='Agente_de_viajes',
      model='gemini-2.5-pro',
      description=('Agente de viajes especializado...'),
      sub_agents=[],
      instruction='ROLE\nYou are a senior B2B Travel Advisor...',
      tools=[agent_tool.AgentTool(agent=agente_de_viajes_vertex_ai_search_agent)],
    )

else:
    # --- STANDARD VERTEX AI SDK IMPLEMENTATION (Fallback) ---
    class VertexStandardAgent:
        def __init__(self):
            # Define Tools (Grounding)
            # Data Store ID format needs to be correct for standard SDK
            # Standard SDK usually expects the full resource name for grounding
            
            # Clean up double slashes just in case
            ds_path = DATA_STORE_ID.replace("//", "/")
            
            self.tools = [
                Tool.from_retrieval(
                    retrieval=grounding.Retrieval(
                        source=grounding.VertexAISearch(datastore=ds_path)
                    )
                )
            ]
            
            self.model = GenerativeModel(
                "gemini-2.0-pro-exp-02-05", 
                tools=self.tools,
                system_instruction="""ROLE
You are a senior B2B Travel Advisor. You do not “chat with PDFs”; you use the promotions to build confident travel recommendations.

CORE OBJECTIVE
When the user asks for a trip (e.g., “quiero un viaje a Turquía”), you must:
1. Interpret the intent.
2. Search the knowledge base (promotions PDFs) for matching itineraries.
3. Provide a clear recommendation plus 2–4 alternative options.
4. Ask only the minimum necessary questions.
5. Explicitly state INCLUDES / NOT INCLUDED / IMPORTANT NOTES.

RESPONSE FORMAT (MANDATORY)
- BLUF (1–2 lines): Best recommendation.
- Options (ranked): 2–4 options with Tour name, ID, Duration, Highlights, Departures, Includes, Not Included.
- Key tradeoffs: Comparison bullets.
- Clarifying questions: Max 3.
- Next step.

BEHAVIOR RULES
- Act like a professional travel agent.
- Never invent information. Only use what is explicitly in the PDFs (grounding).
- If information is missing, say “Not specified within the available promotions”.

GROUNDING / CITATIONS
- Always rely on the provided context (grounding).
"""
            )

        def query(self, prompt: str):
            # Create a chat session (stateless for this wrapper, or stateful if we keep history)
            # The API caller manages history string construction, but for Vertex Chat, 
            # ideally we pass the history object.
            # For simplicity in this wrapper, we'll treat it as a single turn with context 
            # or rely on the prompt containing the history.
            
            # Note: prompt passed here already has HISTORY: ... constructed in main.py
            # But Grounding works best with specific queries.
            # For this 'Shim', we will send the full prompt.
            
            chat = self.model.start_chat()
            response = chat.send_message(prompt)
            
            # Extract text and citations
            text = response.text
            
            # Attempt to extract citations/grounding metadata
            citations = []
            if response.candidates and response.candidates[0].grounding_metadata.grounding_chunks:
                for chunk in response.candidates[0].grounding_metadata.grounding_chunks:
                    if chunk.retrieved_context:
                        citations.append(chunk.retrieved_context.uri) # Or title
                        
            # Return an object that mimics what main.py expects (object with .text or str)
            # We will return the text, and rely on main.py to handle it?
            # main.py expects: agent_response (obj or str).
            # If string, main.py fails to get citations.
            # I should return a simple object.
            
            class AgentResponse:
                def __init__(self, text, citations):
                    self.text = text
                    self.citations = citations
                def __str__(self):
                    return self.text
            
            return AgentResponse(text, citations)
            
        def __call__(self, prompt: str):
            return self.query(prompt)

    root_agent = VertexStandardAgent()
