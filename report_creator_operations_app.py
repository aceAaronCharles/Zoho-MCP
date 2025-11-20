#!/usr/bin/env python3
"""
Zoho Creator Operations App Report
Access and analyze the Operations app in Zoho Creator
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

def make_request(url, headers, method='GET', data=None):
    """Make API request with error handling."""
    try:
        if method == 'GET':
            response = requests.get(url, headers=headers, timeout=30)
        elif method == 'POST':
            response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            return response.json(), None
        else:
            return None, f"Status {response.status_code}: {response.text[:200]}"
    except Exception as e:
        return None, str(e)

def main():
    print_section("ZOHO CREATOR - OPERATIONS APP REPORT")
    print(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
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
        scope=os.getenv('ZOHO_SCOPE'),
        token_file_path=os.getenv('TOKEN_FILE_PATH', '.zoho_tokens.json')
    )
    
    token = auth.get_valid_access_token()
    if not token:
        print("❌ Authentication failed")
        return False
    
    print("✓ Authenticated successfully")
    
    headers = auth.get_headers()
    
    # Zoho Creator API base
    creator_base = "https://creator.zoho.com/api/v2"
    
    # ========================================================================
    # 1. LIST ALL CREATOR APPLICATIONS
    # ========================================================================
    print_section("1. ZOHO CREATOR APPLICATIONS", "─")
    
    # Get account name from org info first
    api_domain = auth.get_api_domain()
    org_url = f"{api_domain}/crm/v2/org"
    org_data, org_error = make_request(org_url, headers)
    
    account_name = None
    if org_data and 'org' in org_data:
        org_info = org_data['org'][0]
        # Try to derive account name from company name or email
        company = org_info.get('company_name', '').lower().replace(' ', '')
        print(f"\n🏢 Organization: {org_info.get('company_name')}")
        print(f"   Trying to access Creator apps...")
    
    # Try to list applications
    # Creator API format: https://creator.zoho.com/api/v2/{account_owner_name}/applications
    print("\n🔍 Searching for Creator applications...")
    
    # Method 1: Try common account patterns
    account_patterns = []
    if org_data and 'org' in org_data:
        org_info = org_data['org'][0]
        company = org_info.get('company_name', '').lower().replace(' ', '').replace('.', '')
        email_prefix = org_info.get('primary_email', '').split('@')[0] if org_info.get('primary_email') else None
        
        if company:
            account_patterns.append(company)
        if email_prefix:
            account_patterns.append(email_prefix)
    
    # Also check from current user
    user_url = f"{api_domain}/crm/v2/users?type=CurrentUser"
    user_data, user_error = make_request(user_url, headers)
    
    if user_data and 'users' in user_data:
        user = user_data['users'][0]
        user_email = user.get('email', '')
        user_name = user.get('name', '').lower().replace(' ', '')
        email_user = user_email.split('@')[0]
        
        account_patterns.extend([user_name, email_user])
        print(f"\n👤 Current User: {user.get('full_name')} ({user_email})")
    
    # Remove duplicates
    account_patterns = list(dict.fromkeys(account_patterns))
    
    print(f"\n🔍 Trying {len(account_patterns)} possible account patterns...")
    
    found_apps = []
    working_account = None
    
    for pattern in account_patterns[:5]:  # Try first 5 patterns
        print(f"\n   Testing account pattern: '{pattern}'...")
        apps_url = f"{creator_base}/{pattern}/applications"
        apps_data, apps_error = make_request(apps_url, headers)
        
        if apps_data and 'applications' in apps_data:
            apps = apps_data['applications']
            print(f"   ✓ Found {len(apps)} application(s)!")
            found_apps = apps
            working_account = pattern
            break
        else:
            print(f"   ✗ No access with this pattern")
    
    if not found_apps:
        print("\n⚠️  Could not automatically detect Creator account name.")
        print("\n💡 TO FIND YOUR CREATOR APPS:")
        print("   1. Log in to https://creator.zoho.com")
        print("   2. Note your account name from the URL")
        print("   3. URL format: https://creator.zoho.com/[ACCOUNT_NAME]/")
        print("   4. Provide the account name to access your apps")
        return False
    
    # ========================================================================
    # 2. ANALYZE APPLICATIONS - FIND OPERATIONS APP
    # ========================================================================
    print_section("2. CREATOR APPLICATIONS FOUND", "─")
    
    operations_app = None
    
    print(f"\n📦 Total Applications: {len(found_apps)}\n")
    
    for idx, app in enumerate(found_apps, 1):
        app_name = app.get('application_name', 'Unnamed')
        app_link_name = app.get('link_name', '')
        app_type = app.get('type', 'Unknown')
        
        print(f"{idx}. {app_name}")
        print(f"   Link Name: {app_link_name}")
        print(f"   Type: {app_type}")
        print(f"   Owner: {app.get('owner_name', 'Unknown')}")
        
        # Check if this is the Operations app
        if 'operation' in app_name.lower() or 'operations' in app_name.lower():
            operations_app = app
            print(f"   ⭐ THIS IS THE OPERATIONS APP!")
    
    if not operations_app:
        print("\n⚠️  No app named 'Operations' found.")
        print("   Please specify which app to analyze from the list above.")
        
        # Let's analyze the first app as example
        if found_apps:
            print("\n   Using first app as example...")
            operations_app = found_apps[0]
    
    # ========================================================================
    # 3. GET DETAILED INFO ABOUT OPERATIONS APP
    # ========================================================================
    if operations_app:
        print_section("3. OPERATIONS APP DETAILS", "─")
        
        app_link_name = operations_app.get('link_name')
        
        print(f"\n📱 Application: {operations_app.get('application_name')}")
        print(f"   Link Name: {app_link_name}")
        print(f"   Type: {operations_app.get('type')}")
        print(f"   Owner: {operations_app.get('owner_name')}")
        print(f"   Date Created: {operations_app.get('date_created')}")
        
        # Get forms in the application
        print_section("4. FORMS IN OPERATIONS APP", "─")
        
        forms_url = f"{creator_base}/{working_account}/{app_link_name}/forms"
        forms_data, forms_error = make_request(forms_url, headers)
        
        if forms_data and 'forms' in forms_data:
            forms = forms_data['forms']
            print(f"\n📋 Total Forms: {len(forms)}\n")
            
            for idx, form in enumerate(forms, 1):
                form_name = form.get('display_name', 'Unnamed')
                form_link = form.get('link_name', '')
                
                print(f"{idx}. {form_name}")
                print(f"   Link Name: {form_link}")
                print(f"   Type: {form.get('type', 'Unknown')}")
                
                # Get form fields
                fields_url = f"{creator_base}/{working_account}/{app_link_name}/form/{form_link}"
                fields_data, fields_error = make_request(fields_url, headers)
                
                if fields_data and 'fields' in fields_data:
                    fields = fields_data['fields']
                    print(f"   Fields: {len(fields)}")
                    
                    # Show first few fields
                    for field in fields[:5]:
                        field_label = field.get('display_label', field.get('name', 'Unknown'))
                        field_type = field.get('type', 'Unknown')
                        print(f"     • {field_label} ({field_type})")
                    
                    if len(fields) > 5:
                        print(f"     ... and {len(fields) - 5} more fields")
                
                print()
        else:
            print(f"\n⚠️  Could not fetch forms: {forms_error}")
        
        # Get reports in the application
        print_section("5. REPORTS IN OPERATIONS APP", "─")
        
        reports_url = f"{creator_base}/{working_account}/{app_link_name}/reports"
        reports_data, reports_error = make_request(reports_url, headers)
        
        if reports_data and 'reports' in reports_data:
            reports = reports_data['reports']
            print(f"\n📊 Total Reports: {len(reports)}\n")
            
            for idx, report in enumerate(reports, 1):
                report_name = report.get('display_name', 'Unnamed')
                report_link = report.get('link_name', '')
                
                print(f"{idx}. {report_name}")
                print(f"   Link Name: {report_link}")
                print(f"   Type: {report.get('type', 'Unknown')}")
                
                # Try to get report data (first few records)
                records_url = f"{creator_base}/{working_account}/{app_link_name}/report/{report_link}"
                records_params = {'max_records': 5}
                records_data, records_error = make_request(
                    f"{records_url}?max_records=5", 
                    headers
                )
                
                if records_data and 'data' in records_data:
                    record_count = len(records_data['data'])
                    print(f"   Records: {record_count} (showing sample)")
                
                print()
        else:
            print(f"\n⚠️  Could not fetch reports: {reports_error}")
        
        # Get pages/sections
        print_section("6. PAGES/SECTIONS IN OPERATIONS APP", "─")
        
        pages_url = f"{creator_base}/{working_account}/{app_link_name}/pages"
        pages_data, pages_error = make_request(pages_url, headers)
        
        if pages_data and 'pages' in pages_data:
            pages = pages_data['pages']
            print(f"\n📄 Total Pages: {len(pages)}\n")
            
            for idx, page in enumerate(pages, 1):
                print(f"{idx}. {page.get('display_name', 'Unnamed')}")
                print(f"   Link Name: {page.get('link_name')}")
                print(f"   Type: {page.get('type', 'Unknown')}")
        else:
            print(f"\n⚠️  Could not fetch pages: {pages_error}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_section("OPERATIONS APP SUMMARY")
    
    if operations_app:
        print("\n✅ OPERATIONS APP ANALYSIS COMPLETE")
        print(f"   • Application Name: {operations_app.get('application_name')}")
        print(f"   • Account: {working_account}")
        print(f"   • Forms: Available")
        print(f"   • Reports: Available")
        print(f"   • Pages: Available")
        
        print("\n🔗 ACCESS YOUR APP:")
        app_link = operations_app.get('link_name')
        print(f"   https://creator.zoho.com/{working_account}/{app_link}")
    
    print("\n💡 WHAT YOU CAN DO WITH CREATOR API:")
    print("   • Read/Write form data")
    print("   • Execute reports and get data")
    print("   • Create/update records")
    print("   • Trigger workflows")
    print("   • Access all app components")
    
    print("\n" + "="*80 + "\n")
    
    # Save report
    if operations_app:
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "account_name": working_account,
            "application": operations_app,
            "api_access": "granted"
        }
        
        report_file = "creator_operations_app_report.json"
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
