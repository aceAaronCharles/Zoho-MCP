#!/usr/bin/env python3
"""
Quick test script to verify the MCP server functionality
"""

import os
import sys
sys.path.insert(0, 'src')

from dotenv import load_dotenv
load_dotenv()

# Import our modules
from app_registry import AppRegistry
from api_router import APIRouter
from zoho_auth import ZohoAuth

def test_app_registry():
    """Test the app registry."""
    print("=" * 60)
    print("Testing App Registry")
    print("=" * 60)
    
    scope = os.getenv('ZOHO_SCOPE', '')
    print(f"\nConfigured scopes: {scope[:100]}...")
    
    registry = AppRegistry(scope)
    
    enabled_apps = registry.list_enabled_apps()
    print(f"\n✅ Total apps in registry: {len(registry.list_all_apps())}")
    print(f"✅ Enabled apps: {len(enabled_apps)}")
    
    print("\n📱 Enabled Apps by Category:")
    categories = registry.get_enabled_categories()
    for category in categories:
        apps = registry.get_apps_by_category(category)
        enabled_in_category = [app for app in apps if app.enabled]
        if enabled_in_category:
            print(f"\n  {category}:")
            for app in enabled_in_category:
                print(f"    • {app.name} ({app.api_version})")
    
    return registry

def test_authentication():
    """Test authentication setup."""
    print("\n" + "=" * 60)
    print("Testing Authentication")
    print("=" * 60)
    
    client_id = os.getenv('ZOHO_CLIENT_ID')
    client_secret = os.getenv('ZOHO_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ ZOHO_CLIENT_ID or ZOHO_CLIENT_SECRET not set in .env")
        return None
    
    print(f"✅ Client ID configured: {client_id[:20]}...")
    print(f"✅ Client Secret configured: {'*' * 20}")
    
    try:
        auth = ZohoAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=os.getenv('ZOHO_REDIRECT_URI', 'http://localhost:8080/callback'),
            scope=os.getenv('ZOHO_SCOPE', ''),
            token_file_path=os.getenv('TOKEN_FILE_PATH', '.zoho_tokens.json'),
            api_domain=os.getenv('ZOHO_API_DOMAIN', 'https://www.zohoapis.com'),
            accounts_domain=os.getenv('ZOHO_ACCOUNTS_DOMAIN', 'https://accounts.zoho.com')
        )
        
        # Check if tokens exist
        if os.path.exists('.zoho_tokens.json'):
            print("✅ Token file exists")
            if auth.is_token_valid():
                print("✅ Tokens are valid")
            else:
                print("⚠️  Tokens exist but may be expired")
        else:
            print("⚠️  No token file found - authentication needed")
            print("   Run authenticate_zoho() tool to authenticate")
        
        return auth
    except Exception as e:
        print(f"❌ Error initializing auth: {e}")
        return None

def test_api_router(registry, auth):
    """Test API router."""
    print("\n" + "=" * 60)
    print("Testing API Router")
    print("=" * 60)
    
    if not auth:
        print("⚠️  Skipping router test - auth not initialized")
        return
    
    try:
        router = APIRouter(auth, registry)
        print("✅ API Router initialized successfully")
        print(f"✅ Default timeout: {router.timeout} seconds")
        
        # Test URL building
        if registry.is_app_enabled("CRM"):
            crm_config = registry.get_app_config("CRM")
            url = router._build_url(crm_config, "Leads", None)
            print(f"✅ Sample CRM URL: {url}")
        
        if registry.is_app_enabled("Books"):
            books_config = registry.get_app_config("Books")
            url = router._build_url(books_config, "invoices", "organization/123456")
            print(f"✅ Sample Books URL: {url}")
        
    except Exception as e:
        print(f"❌ Error testing router: {e}")

def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("🚀 Zoho Ecosystem MCP Server - System Test")
    print("=" * 60)
    
    # Test 1: App Registry
    registry = test_app_registry()
    
    # Test 2: Authentication
    auth = test_authentication()
    
    # Test 3: API Router
    test_api_router(registry, auth)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    if registry and len(registry.list_enabled_apps()) > 0:
        print("✅ App Registry: WORKING")
    else:
        print("❌ App Registry: FAILED")
    
    if auth:
        print("✅ Authentication: CONFIGURED")
    else:
        print("❌ Authentication: NOT CONFIGURED")
    
    print("\n" + "=" * 60)
    print("Next Steps:")
    print("=" * 60)
    print("1. If tokens are expired, you need to authenticate:")
    print("   - The MCP server will open a browser for OAuth")
    print("   - Or manually run: python -c 'from src.zoho_auth import ZohoAuth; ...'")
    print("\n2. To use with AI assistants:")
    print("   - Configure your AI assistant to use this MCP server")
    print("   - Point it to: src/server.py")
    print("   - The AI can then call tools like list_enabled_apps(), books_get_invoices(), etc.")
    print("\n3. Available tools: 70+ tools across 9 Zoho apps")
    print("=" * 60)

if __name__ == "__main__":
    main()
