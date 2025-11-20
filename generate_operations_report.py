#!/usr/bin/env python3
"""
Zoho Operations App Report Generator
Generates a comprehensive report on operations features including Approvals, Workflows, and Blueprints
"""

import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from zoho_auth import ZohoAuth
import requests
import json
from datetime import datetime

def print_section(title, char="="):
    """Print formatted section header."""
    print(f"\n{char*80}")
    print(f"  {title}")
    print(f"{char*80}")

def make_request(url, headers):
    """Make API request with error handling."""
    try:
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Status {response.status_code}: {response.text}"
    except Exception as e:
        return None, str(e)

def main():
    print_section("ZOHO CRM OPERATIONS APP REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Environment: SANDBOX")
    
    # Load environment and authenticate
    load_dotenv()
    
    client_id = os.getenv('ZOHO_CLIENT_ID')
    client_secret = os.getenv('ZOHO_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("❌ Error: Missing credentials")
        return False
    
    print("\n🔑 Authenticating...")
    auth = ZohoAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=os.getenv('ZOHO_REDIRECT_URI', 'http://localhost:8080/callback'),
        scope=os.getenv('ZOHO_SCOPE', 'ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL'),
        token_file_path=os.getenv('TOKEN_FILE_PATH', '.zoho_tokens.json')
    )
    
    token = auth.get_valid_access_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✓ Authenticated successfully")
    
    headers = auth.get_headers()
    api_domain = auth.get_api_domain()
    
    # ========================================================================
    # 1. APPROVALS MODULE DETAILS
    # ========================================================================
    print_section("1. APPROVALS MODULE", "─")
    
    approvals_url = f"{api_domain}/crm/v2/Approvals"
    data, error = make_request(approvals_url, headers)
    
    if data:
        approvals = data.get('data', [])
        print(f"\n📊 Total Approvals: {len(approvals)}")
        
        if approvals:
            print("\nRecent Approvals:")
            for idx, approval in enumerate(approvals[:10], 1):
                print(f"\n{idx}. ID: {approval.get('id')}")
                print(f"   Status: {approval.get('$approval_state', 'N/A')}")
                print(f"   Module: {approval.get('$se_module', 'N/A')}")
                print(f"   Record: {approval.get('$record_id', 'N/A')}")
                print(f"   Submitted: {approval.get('$submitted_time', 'N/A')}")
        else:
            print("\n📝 No approval records found")
            print("   This is expected if no workflow approvals are configured")
    else:
        print(f"\n⚠️  Could not fetch approvals: {error}")
    
    # ========================================================================
    # 2. WORKFLOW RULES
    # ========================================================================
    print_section("2. WORKFLOW RULES", "─")
    
    workflows_url = f"{api_domain}/crm/v2/settings/workflow_rules"
    data, error = make_request(workflows_url, headers)
    
    if data:
        workflows = data.get('workflow_rules', [])
        print(f"\n📊 Total Workflow Rules: {len(workflows)}")
        
        if workflows:
            active_workflows = [w for w in workflows if w.get('state') == 'active']
            inactive_workflows = [w for w in workflows if w.get('state') != 'active']
            
            print(f"   Active: {len(active_workflows)}")
            print(f"   Inactive: {len(inactive_workflows)}")
            
            print("\n🔄 Active Workflows:")
            for idx, wf in enumerate(active_workflows[:10], 1):
                print(f"\n{idx}. {wf.get('name', 'Unnamed')}")
                print(f"   ID: {wf.get('id')}")
                print(f"   Module: {wf.get('module', {}).get('api_name', 'N/A')}")
                print(f"   State: {wf.get('state', 'N/A')}")
                print(f"   Trigger: {wf.get('condition', {}).get('criteria', 'N/A')}")
        else:
            print("\n📝 No workflow rules configured")
    else:
        print(f"\n⚠️  Could not fetch workflows: {error}")
    
    # ========================================================================
    # 3. BLUEPRINTS
    # ========================================================================
    print_section("3. BLUEPRINTS (Process Management)", "─")
    
    # Load modules to check blueprint support
    with open('zoho_modules_full.json', 'r') as f:
        modules_data = json.load(f)
        modules = modules_data['modules']
    
    blueprint_supported = [m for m in modules if m.get('isBlueprintSupported')]
    print(f"\n📊 Modules Supporting Blueprints: {len(blueprint_supported)}")
    
    print("\n📋 Blueprint-Enabled Modules:")
    for m in blueprint_supported[:20]:
        print(f"   • {m['module_name']} (API: {m['api_name']})")
    
    # Try to get blueprint details for a specific module
    print("\n🔍 Checking Blueprint Configuration...")
    for module in ['Leads', 'Deals', 'Contacts']:
        blueprint_url = f"{api_domain}/crm/v2/settings/blueprints?module={module}"
        data, error = make_request(blueprint_url, headers)
        
        if data and 'blueprints' in data and data['blueprints']:
            blueprints = data['blueprints']
            print(f"\n✓ {module} has {len(blueprints)} blueprint(s):")
            for bp in blueprints:
                print(f"   - {bp.get('blueprint_name', 'Unnamed')}")
                print(f"     Status: {bp.get('status', 'N/A')}")
    
    # ========================================================================
    # 4. AUTOMATION ACTIONS
    # ========================================================================
    print_section("4. AUTOMATION & ACTIONS", "─")
    
    actions_url = f"{api_domain}/crm/v2/settings/actions"
    data, error = make_request(actions_url, headers)
    
    if data:
        actions = data.get('actions', [])
        print(f"\n📊 Total Automation Actions: {len(actions)}")
        
        if actions:
            for idx, action in enumerate(actions[:10], 1):
                print(f"\n{idx}. {action.get('name', 'Unnamed')}")
                print(f"   ID: {action.get('id')}")
                print(f"   Type: {action.get('type', 'N/A')}")
                print(f"   Status: {action.get('status', 'N/A')}")
        else:
            print("\n📝 No automation actions configured")
    else:
        print(f"\n⚠️  Could not fetch actions: {error}")
    
    # ========================================================================
    # 5. CUSTOM VIEWS/FILTERS
    # ========================================================================
    print_section("5. CUSTOM VIEWS & FILTERS", "─")
    
    # Check custom views for key modules
    for module in ['Leads', 'Deals', 'Contacts', 'Accounts']:
        views_url = f"{api_domain}/crm/v2/settings/custom_views?module={module}"
        data, error = make_request(views_url, headers)
        
        if data and 'custom_views' in data:
            views = data['custom_views']
            print(f"\n📋 {module}: {len(views)} custom view(s)")
            for view in views[:3]:
                print(f"   • {view.get('name')} (Default: {view.get('default', False)})")
    
    # ========================================================================
    # 6. ROLES & PROFILES
    # ========================================================================
    print_section("6. ROLES & PROFILES", "─")
    
    roles_url = f"{api_domain}/crm/v2/settings/roles"
    data, error = make_request(roles_url, headers)
    
    if data:
        roles = data.get('roles', [])
        print(f"\n📊 Total Roles: {len(roles)}")
        
        for role in roles:
            print(f"   • {role.get('name')} (ID: {role.get('id')})")
    
    profiles_url = f"{api_domain}/crm/v2/settings/profiles"
    data, error = make_request(profiles_url, headers)
    
    if data:
        profiles = data.get('profiles', [])
        print(f"\n📊 Total Profiles: {len(profiles)}")
        
        for profile in profiles:
            print(f"   • {profile.get('name')} (ID: {profile.get('id')})")
    
    # ========================================================================
    # 7. FIELD DEPENDENCIES
    # ========================================================================
    print_section("7. FIELD DEPENDENCIES & VALIDATION", "─")
    
    print("\n🔍 Checking field dependencies for key modules...")
    for module in ['Leads', 'Deals']:
        fields_url = f"{api_domain}/crm/v2/settings/fields?module={module}"
        data, error = make_request(fields_url, headers)
        
        if data and 'fields' in data:
            fields = data['fields']
            required_fields = [f for f in fields if f.get('required')]
            lookup_fields = [f for f in fields if f.get('data_type') == 'lookup']
            
            print(f"\n📋 {module}:")
            print(f"   Required Fields: {len(required_fields)}")
            print(f"   Lookup Fields: {len(lookup_fields)}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_section("OPERATIONS APP SUMMARY")
    
    print("\n✅ AVAILABLE OPERATIONS FEATURES:")
    print("   • Approvals Module: For workflow approvals")
    print("   • Workflow Rules: Automation based on conditions")
    print("   • Blueprints: Process management and state transitions")
    print("   • Custom Views: Filtered data views")
    print("   • Roles & Profiles: Access control")
    print("   • Field Dependencies: Dynamic field behavior")
    
    print("\n📊 OPERATIONS CAPABILITIES:")
    print("   • Configure approval workflows")
    print("   • Create automation rules")
    print("   • Design business process blueprints")
    print("   • Manage user roles and permissions")
    print("   • Set up field validations")
    
    print("\n💡 TO ACCESS MORE OPERATIONS FEATURES:")
    print("   • Zoho Analytics: For advanced reporting and dashboards")
    print("   • Zoho Flow: For cross-app workflow automation")
    print("   • Zoho Creator: For custom business applications")
    
    print("\n" + "="*80 + "\n")
    
    # Save detailed report
    report_file = "zoho_operations_report.json"
    report_data = {
        "generated_at": datetime.now().isoformat(),
        "environment": "sandbox",
        "api_domain": api_domain,
        "approvals_checked": True,
        "workflows_checked": True,
        "blueprints_checked": True
    }
    
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    print(f"💾 Detailed report saved to: {report_file}\n")
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
