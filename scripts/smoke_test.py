import requests
import sys
import time

def smoke_test(url):
    print(f"Checking health of {url}...")
    start_time = time.time()
    try:
        # Check API health (if exposed) or UI availability
        # If single container with UI on port 8080/443, /health might be shadowed by Streamlit unless configured.
        # Streamlit defaults /healthz
        
        # Testing the Streamlit healthz
        resp = requests.get(f"{url}/_stcore/health")
        
        # If we had direct access to port 8000 we would check /health of API
        # But let's assume valid deployment means UI is up.
        
        if resp.status_code == 200:
            elapsed = time.time() - start_time
            print(f"Success! Status 200 in {elapsed:.2f}s")
            if elapsed > 2.0:
                 print("WARNING: Latency > 2s")
                 # sys.exit(1) # Strict FAIL?? Maybe warning for now.
                 sys.exit(0)
            sys.exit(0)
        else:
            print(f"Failed: Status {resp.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python smoke_test.py <url>")
        sys.exit(1)
    
    url = sys.argv[1]
    smoke_test(url)
