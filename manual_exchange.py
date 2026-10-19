import os
import logging
from dotenv import load_dotenv
from src.zoho_auth import ZohoAuth

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def manual_exchange(code):
    print(f"Attempting to exchange code: {code}")
    
    auth = ZohoAuth(
        client_id=os.getenv('ZOHO_CLIENT_ID'),
        client_secret=os.getenv('ZOHO_CLIENT_SECRET'),
        redirect_uri=os.getenv('ZOHO_REDIRECT_URI'),
        scope=os.getenv('ZOHO_SCOPE')
    )
    
    # Manually exchange code
    success = auth._exchange_code_for_tokens(code)
    
    if success:
        print("\n✅ SUCCESS: Tokens obtained and saved to .zoho_tokens.json")
    else:
        print("\n❌ FAILURE: Could not exchange code for tokens.")

if __name__ == "__main__":
    # Supply the one-time code with: ZOHO_AUTH_CODE=... python manual_exchange.py
    auth_code = os.getenv("ZOHO_AUTH_CODE", "")
    if not auth_code:
        raise SystemExit("Set ZOHO_AUTH_CODE to the code from the Zoho redirect URL.")
    manual_exchange(auth_code)
