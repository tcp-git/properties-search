import json
import os
from fastapi.testclient import TestClient
from api_service import app
from dotenv import load_dotenv

# Load env to prevent startup errors if keys are missing (though app handles it gracefully)
load_dotenv()

def export_openapi():
    print("⏳ Generating OpenAPI schema...")
    
    # Get OpenAPI JSON
    openapi_data = app.openapi()
    
    # Save to file
    output_file = "openapi.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(openapi_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ OpenAPI schema exported to: {os.path.abspath(output_file)}")
    print("👉 You can now import this file into Postman.")

if __name__ == "__main__":
    export_openapi()
