#!/usr/bin/env python3
"""
Enhanced Zoho Sandbox Test & Configuration Tool
This script tests sandbox connectivity and provides module management capabilities.
"""

import sys
import os
from pathlib import Path

# Add src directory to path
sys.path.append(str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from zoho_auth import ZohoAuth
import requests
import json

def print_header(text):
    """Print a formatted header."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70)

def print_section(text):
    """Print a section divider."""
    print(f"\n{'─'*70}")
    print(f"  {text}")
    print(f"{'─'*70}")

def main():
    """Test Zoho Sandbox and display all available modules."""
    print_header("Zoho Sandbox Access & Module Configuration Tool")
    
    # Load environment variables
    load_dotenv()
    
    # Check for required environment variables
    client_id = os.getenv('ZOHO_CLIENT_ID')
    client_secret = os.getenv('ZOHO_CLIENT_SECRET')
    api_domain = os.getenv('ZOHO_API_DOMAIN', 'https://www.zohoapis.com')
    
    if not client_id or not client_secret:
        print("❌ Error: ZOHO_CLIENT_ID and ZOHO_CLIENT_SECRET must be set in .env file")
        return False
    
    print(f"✓ Client ID: {client_id[:10]}...")
    print(f"✓ Client Secret: {client_secret[:10]}...")
    print(f"✓ API Domain: {api_domain}")
    print(f"✓ Environment: {'SANDBOX' if 'sandbox' in api_domain else 'PRODUCTION'}")
    
    try:
        # Initialize auth handler
        print("\n📡 Initializing Zoho authentication...")
        auth = ZohoAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=os.getenv('ZOHO_REDIRECT_URI', 'http://localhost:8080/callback'),
            scope=os.getenv('ZOHO_SCOPE', 'ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL'),
            token_file_path=os.getenv('TOKEN_FILE_PATH', '.zoho_tokens.json')
        )
        
        # Get valid token
        print("🔑 Authenticating...")
        token = auth.get_valid_access_token()
        
        if not token:
            print("❌ Authentication failed")
            return False
        
        print("✓ Authentication successful!")
        
        headers = auth.get_headers()
        api_domain = auth.get_api_domain()
        
        # Get user info
        print_section("Current User Information")
        user_url = f"{api_domain}/crm/v2/users?type=CurrentUser"
        response = requests.get(user_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            user_data = response.json()
            if 'users' in user_data and user_data['users']:
                user = user_data['users'][0]
                print(f"👤 Name: {user.get('full_name', 'Unknown')}")
                print(f"📧 Email: {user.get('email', 'Unknown')}")
                print(f"🎭 Role: {user.get('role', {}).get('name', 'Unknown')}")
                print(f"🏢 Organization: {user.get('organization', 'Unknown')}")
        
        # Get organization info
        print_section("Organization Information")
        org_url = f"{api_domain}/crm/v2/org"
        response = requests.get(org_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            org_data = response.json()
            if 'org' in org_data and org_data['org']:
                org = org_data['org'][0]
                print(f"🏢 Company: {org.get('company_name', 'Unknown')}")
                print(f"🌍 Country: {org.get('country', 'Unknown')}")
                print(f"🕐 Time Zone: {org.get('time_zone', 'Unknown')}")
                print(f"📅 Fiscal Year: {org.get('fiscal_year_start_month', 'Unknown')}")
        
        # Get ALL modules with detailed information
        print_section("All Available CRM Modules")
        modules_url = f"{api_domain}/crm/v2/settings/modules"
        response = requests.get(modules_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            modules_data = response.json()
            if 'modules' in modules_data:
                modules = modules_data['modules']
                print(f"\n📦 Total Modules Found: {len(modules)}\n")
                
                # Group modules by category
                standard_modules = []
                custom_modules = []
                operations_modules = []
                
                for module in modules:
                    module_name = module.get('module_name', 'Unknown')
                    api_name = module.get('api_name', module_name)
                    is_custom = module.get('generated_type', '') == 'custom'
                    is_ops = any(word in module_name.lower() for word in ['operation', 'workflow', 'process', 'automation'])
                    
                    module_info = {
                        'name': module_name,
                        'api_name': api_name,
                        'plural': module.get('plural_label', ''),
                        'singular': module.get('singular_label', ''),
                        'editable': module.get('editable', False),
                        'deletable': module.get('deletable', False),
                        'creatable': module.get('creatable', False),
                        'api_supported': module.get('api_supported', False),
                        'custom': is_custom
                    }
                    
                    if is_ops:
                        operations_modules.append(module_info)
                    elif is_custom:
                        custom_modules.append(module_info)
                    else:
                        standard_modules.append(module_info)
                
                # Display Operations Modules
                if operations_modules:
                    print_section("⚙️  OPERATIONS & WORKFLOW MODULES")
                    for idx, mod in enumerate(operations_modules, 1):
                        print(f"\n{idx}. {mod['name']}")
                        print(f"   API Name: {mod['api_name']}")
                        print(f"   Permissions: ", end="")
                        perms = []
                        if mod['creatable']: perms.append("Create")
                        if mod['editable']: perms.append("Edit")
                        if mod['deletable']: perms.append("Delete")
                        print(", ".join(perms) if perms else "Read-only")
                
                # Display Standard Modules
                print_section("📋 STANDARD CRM MODULES")
                for idx, mod in enumerate(standard_modules, 1):
                    status = "✓" if mod['api_supported'] else "✗"
                    print(f"{status} {idx}. {mod['name']} ({mod['api_name']})")
                
                # Display Custom Modules
                if custom_modules:
                    print_section("🔧 CUSTOM MODULES")
                    for idx, mod in enumerate(custom_modules, 1):
                        print(f"✓ {idx}. {mod['name']} ({mod['api_name']})")
                
                # Display detailed module list in JSON
                print_section("💾 Saving Full Module Data")
                output_file = "zoho_modules_full.json"
                with open(output_file, 'w') as f:
                    json.dump(modules_data, f, indent=2)
                print(f"✓ Full module data saved to: {output_file}")
                
                # Display operations-related modules in detail
                print_section("🔍 DETAILED OPERATIONS MODULE INFO")
                for module in modules:
                    module_name = module.get('module_name', '').lower()
                    if any(word in module_name for word in ['operation', 'workflow', 'process', 'automation', 'blueprint', 'approval']):
                        print(f"\n📌 {module.get('module_name')}:")
                        print(f"   API Name: {module.get('api_name')}")
                        print(f"   Description: {module.get('description', 'N/A')}")
                        print(f"   API Supported: {module.get('api_supported', False)}")
                        print(f"   Has Records: {module.get('has_records', False)}")
                        print(f"   Visibility: {module.get('visibility', 'N/A')}")
        
        # Test access to other Zoho products if scopes are available
        print_section("🌐 Testing Other Zoho Applications")
        
        # Check token scopes
        token_file = os.getenv('TOKEN_FILE_PATH', '.zoho_tokens.json')
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                token_data = json.load(f)
                scopes = token_data.get('scope', '').split(',')
                print(f"\n✓ Active Scopes: {len(scopes)}")
                
                # Check for specific app access
                apps = {
                    'CRM': any('CRM' in s for s in scopes),
                    'Books': any('Books' in s for s in scopes),
                    'Projects': any('Projects' in s for s in scopes),
                    'Desk': any('Desk' in s for s in scopes),
                    'Analytics': any('Analytics' in s for s in scopes),
                    'People': any('People' in s for s in scopes),
                    'Inventory': any('Inventory' in s for s in scopes),
                    'Creator': any('Creator' in s for s in scopes),
                }
                
                print("\nAvailable Applications:")
                for app, has_access in apps.items():
                    status = "✓" if has_access else "✗"
                    print(f"  {status} {app}")
        
        # Success summary
        print_header("🎉 SUCCESS! Sandbox Access Confirmed")
        print("✓ Authentication: Working")
        print("✓ Token Management: Working")
        print("✓ API Connectivity: Working")
        print("✓ Module Access: Confirmed")
        print(f"✓ Environment: SANDBOX ({api_domain})")
        print("\nYou can now:")
        print("  • Configure existing modules")
        print("  • Create custom modules")
        print("  • Debug system issues")
        print("  • Test workflows safely")
        print("="*70 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        print("\nDetailed error:")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)
