#!/usr/bin/env python3
"""
Test Access to All Zoho Applications
This script checks which Zoho applications you have access to
"""

import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from zoho_auth import ZohoAuth
from zoho_multi_app import ZohoMultiApp
import json

def print_header(text):
    print(f"\n{'='*80}")
    print(f"  {text}")
    print(f"{'='*80}")

def print_section(text):
    print(f"\n{'─'*80}")
    print(f"  {text}")
    print(f"{'─'*80}")

def test_app_access(multi_app, app_name, test_func, *args):
    """Test access to a specific Zoho app."""
    try:
        result = test_func(*args)
        if result['status'] == 'success':
            return True, result.get('data', {})
        else:
            return False, result.get('message', 'Unknown error')
    except Exception as e:
        return False, str(e)

def main():
    print_header("ZOHO MULTI-APPLICATION ACCESS TEST")
    
    # Load environment
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
        scope=os.getenv('ZOHO_SCOPE', 'ZohoCRM.modules.ALL'),
        token_file_path=os.getenv('TOKEN_FILE_PATH', '.zoho_tokens.json')
    )
    
    token = auth.get_valid_access_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✓ Authenticated successfully")
    
    # Initialize multi-app handler
    api_domain = auth.get_api_domain()
    multi_app = ZohoMultiApp(auth, api_domain)
    
    # Check active scopes
    print_section("ACTIVE SCOPES")
    token_file = os.getenv('TOKEN_FILE_PATH', '.zoho_tokens.json')
    if os.path.exists(token_file):
        with open(token_file, 'r') as f:
            token_data = json.load(f)
            scopes = token_data.get('scope', '').split(',')
            print(f"\n✓ Total Scopes: {len(scopes)}")
            print("\nScope List:")
            for scope in sorted(scopes):
                print(f"  • {scope}")
    
    # Test access to each Zoho application
    print_section("TESTING ACCESS TO ZOHO APPLICATIONS")
    
    apps_tested = {}
    
    # 1. CRM
    print("\n1. Testing Zoho CRM...")
    success, data = test_app_access(multi_app, 'CRM', multi_app.crm_get_modules)
    if success:
        modules_count = len(data.get('modules', []))
        print(f"   ✓ CRM Access: GRANTED ({modules_count} modules)")
        apps_tested['CRM'] = {'access': True, 'details': f'{modules_count} modules'}
    else:
        print(f"   ✗ CRM Access: DENIED ({data})")
        apps_tested['CRM'] = {'access': False, 'error': str(data)[:100]}
    
    # 2. Books
    print("\n2. Testing Zoho Books...")
    success, data = test_app_access(multi_app, 'Books', multi_app.books_get_organizations)
    if success:
        orgs = data.get('organizations', [])
        print(f"   ✓ Books Access: GRANTED ({len(orgs)} organizations)")
        apps_tested['Books'] = {'access': True, 'details': f'{len(orgs)} organizations'}
        if orgs:
            for org in orgs[:3]:
                print(f"     - {org.get('name')} (ID: {org.get('organization_id')})")
    else:
        print(f"   ✗ Books Access: DENIED ({data})")
        apps_tested['Books'] = {'access': False, 'error': str(data)[:100]}
    
    # 3. Projects
    print("\n3. Testing Zoho Projects...")
    success, data = test_app_access(multi_app, 'Projects', multi_app.projects_get_portals)
    if success:
        portals = data.get('portals', [])
        print(f"   ✓ Projects Access: GRANTED ({len(portals)} portals)")
        apps_tested['Projects'] = {'access': True, 'details': f'{len(portals)} portals'}
        if portals:
            for portal in portals[:3]:
                print(f"     - {portal.get('name')} (ID: {portal.get('id')})")
    else:
        print(f"   ✗ Projects Access: DENIED ({data})")
        apps_tested['Projects'] = {'access': False, 'error': str(data)[:100]}
    
    # 4. Desk
    print("\n4. Testing Zoho Desk...")
    # Desk requires org ID, skip for now
    print("   ⊘ Desk Access: Requires Desk Org ID (skipped)")
    apps_tested['Desk'] = {'access': 'requires_config', 'details': 'Need Desk Org ID'}
    
    # 5. Analytics
    print("\n5. Testing Zoho Analytics...")
    success, data = test_app_access(multi_app, 'Analytics', multi_app.analytics_get_workspaces)
    if success:
        workspaces = data.get('data', {}).get('workspaces', [])
        print(f"   ✓ Analytics Access: GRANTED ({len(workspaces)} workspaces)")
        apps_tested['Analytics'] = {'access': True, 'details': f'{len(workspaces)} workspaces'}
        if workspaces:
            for ws in workspaces[:3]:
                print(f"     - {ws.get('workspaceName')} (ID: {ws.get('workspaceId')})")
    else:
        print(f"   ✗ Analytics Access: DENIED ({data})")
        apps_tested['Analytics'] = {'access': False, 'error': str(data)[:100]}
    
    # 6. People
    print("\n6. Testing Zoho People...")
    success, data = test_app_access(multi_app, 'People', multi_app.people_get_employees)
    if success:
        employees = data.get('response', {}).get('result', [])
        print(f"   ✓ People Access: GRANTED ({len(employees)} employees)")
        apps_tested['People'] = {'access': True, 'details': f'{len(employees)} employees'}
    else:
        print(f"   ✗ People Access: DENIED ({data})")
        apps_tested['People'] = {'access': False, 'error': str(data)[:100]}
    
    # 7. Inventory
    print("\n7. Testing Zoho Inventory...")
    # Inventory requires org ID
    print("   ⊘ Inventory Access: Requires Organization ID (skipped)")
    apps_tested['Inventory'] = {'access': 'requires_config', 'details': 'Need Organization ID'}
    
    # 8. Recruit
    print("\n8. Testing Zoho Recruit...")
    success, data = test_app_access(multi_app, 'Recruit', multi_app.recruit_get_job_openings)
    if success:
        jobs = data.get('data', [])
        print(f"   ✓ Recruit Access: GRANTED ({len(jobs)} job openings)")
        apps_tested['Recruit'] = {'access': True, 'details': f'{len(jobs)} job openings'}
    else:
        print(f"   ✗ Recruit Access: DENIED ({data})")
        apps_tested['Recruit'] = {'access': False, 'error': str(data)[:100]}
    
    # Summary
    print_header("ACCESS SUMMARY")
    
    granted = [app for app, info in apps_tested.items() if info['access'] is True]
    denied = [app for app, info in apps_tested.items() if info['access'] is False]
    requires_config = [app for app, info in apps_tested.items() if info['access'] == 'requires_config']
    
    print(f"\n✅ GRANTED ACCESS ({len(granted)} apps):")
    for app in granted:
        details = apps_tested[app]['details']
        print(f"   ✓ {app}: {details}")
    
    if denied:
        print(f"\n❌ DENIED ACCESS ({len(denied)} apps):")
        for app in denied:
            print(f"   ✗ {app}")
            if 'error' in apps_tested[app]:
                error = apps_tested[app]['error']
                print(f"      Reason: {error}")
    
    if requires_config:
        print(f"\n⚙️  REQUIRES CONFIGURATION ({len(requires_config)} apps):")
        for app in requires_config:
            details = apps_tested[app]['details']
            print(f"   ⊘ {app}: {details}")
    
    # Recommendations
    print_header("RECOMMENDATIONS")
    
    print("\n💡 TO ENABLE MORE APPLICATIONS:")
    print("   1. Update scopes in .env file (already done)")
    print("   2. Delete .zoho_tokens.json and re-authenticate")
    print("   3. Grant permissions during OAuth flow")
    print("   4. Some apps need:")
    print("      - Zoho Books/Inventory: Organization ID")
    print("      - Zoho Desk: Desk Organization ID")
    print("      - Active subscription to the service")
    
    print("\n📝 NEXT STEPS:")
    print("   • Apps with access are ready to use")
    print("   • Check your Zoho subscriptions for denied apps")
    print("   • Configure organization IDs for Books/Inventory/Desk")
    
    # Save results
    results_file = "zoho_apps_access_report.json"
    with open(results_file, 'w') as f:
        json.dump(apps_tested, f, indent=2)
    
    print(f"\n💾 Detailed results saved to: {results_file}")
    print("\n" + "="*80 + "\n")
    
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
