#!/usr/bin/env python3
"""Quick test of MCP tools"""

import sys
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

from app_registry import AppRegistry
from api_router import APIRouter
from zoho_auth import ZohoAuth
import os

# Initialize
scope = os.getenv('ZOHO_SCOPE', '')
registry = AppRegistry(scope)

auth = ZohoAuth(
    client_id=os.getenv('ZOHO_CLIENT_ID'),
    client_secret=os.getenv('ZOHO_CLIENT_SECRET'),
    redirect_uri=os.getenv('ZOHO_REDIRECT_URI', 'http://localhost:8080/callback'),
    scope=scope,
    token_file_path='.zoho_tokens.json',
    api_domain=os.getenv('ZOHO_API_DOMAIN', 'https://www.zohoapis.com'),
    accounts_domain=os.getenv('ZOHO_ACCOUNTS_DOMAIN', 'https://accounts.zoho.com')
)

router = APIRouter(auth, registry)

# Test: List enabled apps
print("Testing list_enabled_apps():")
enabled = registry.list_enabled_apps()
print(f"Found {len(enabled)} enabled apps:")
for app in enabled:
    print(f"  - {app.name} ({app.category})")

# Test: Make a simple API call (if tokens are valid)
print("\nTesting API call to CRM:")
if auth.is_token_valid():
    result = router.make_request("CRM", "users?type=CurrentUser", "GET")
    if result['status'] == 'success':
        print("✅ API call successful!")
        print(f"Response: {result}")
    else:
        print(f"⚠️  API call failed: {result.get('message')}")
else:
    print("⚠️  Tokens expired - need to re-authenticate")
    print("Run: python -c 'from src.zoho_auth import ZohoAuth; auth = ZohoAuth(...); auth.authorize_interactive()'")
