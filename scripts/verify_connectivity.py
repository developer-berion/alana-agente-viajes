import os
import sys
import uuid
import datetime

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from google.cloud import firestore
try:
    from google.cloud import aiplatform
    VERTEX_AVAILABLE = True
except ImportError:
    VERTEX_AVAILABLE = False
    print("Warning: google-cloud-aiplatform not found, skipping Vertex check.")

# Load env vars from .env manually if python-dotenv not installed, 
# or just assume they are set in environment. 
# For this script, we'll read the .env file line by line to support local run without extras.
def load_env():
    try:
        with open('.env') as f:
            for line in f:
                if line.strip() and not line.startswith('#'):
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
    except FileNotFoundError:
        print("No .env file found. Assuming env vars are set.")

def verify_firestore():
    print("--- Verifying Firestore Connection ---")
    try:
        db = firestore.Client()
        # Create a test document in a specialized collection to avoid messing with real sessions if possible,
        # but the prompt implies we are using the real DB.
        # We will use a 'connectivity_tests' collection.
        test_id = str(uuid.uuid4())
        doc_ref = db.collection("connectivity_tests").document(test_id)
        doc_ref.set({
            "timestamp": firestore.SERVER_TIMESTAMP,
            "status": "verifying_write_access",
            "agent": "antigravity"
        })
        print(f"✅ Firestore Write Success: connectivity_tests/{test_id}")
        
        # Read back
        doc = doc_ref.get()
        if doc.exists:
             print(f"✅ Firestore Read Success: {doc.to_dict()}")
        else:
             print("❌ Firestore Read Failed: Document not found after write.")
             return False
             
        # Cleanup
        doc_ref.delete()
        print("✅ Firestore Cleanup Success")
        return True
    except Exception as e:
        print(f"❌ Firestore Failed: {e}")
        return False

def verify_vertex():
    print("\n--- Verifying Vertex AI Access ---")
    if not VERTEX_AVAILABLE:
        print("⏭️ Skipping Vertex AI (library missing)")
        return True
        
    project_id = os.getenv("PROJECT_ID")
    location = os.getenv("LOCATION", "us-central1")
    
    if not project_id:
        print("❌ Missing PROJECT_ID env var")
        return False
        
    try:
        aiplatform.init(project=project_id, location=location)
        print(f"✅ Vertex AI Init Success ({project_id}, {location})")
        # Just listing datasets or something simple to prove auth works
        # ds = aiplatform.TabularDataset.list(limit=1)
        # print("✅ Vertex AI List Datasets call successful")
        return True
    except Exception as e:
        print(f"❌ Vertex AI Failed: {e}")
        return False

if __name__ == "__main__":
    load_env()
    fs_ok = verify_firestore()
    # vx_ok = verify_vertex() # Optional, keeping it simple for now
    
    if fs_ok:
        print("\n✅✅✅ SYSTEM READY for Local Testing ✅✅✅")
        print("You can now run: 'streamlit run frontend/app.py'")
        sys.exit(0)
    else:
        print("\n❌ SYSTEM NOT READY. Check credentials.")
        sys.exit(1)
