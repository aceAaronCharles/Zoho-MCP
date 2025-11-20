#!/usr/bin/env python3
"""Get Operations App Report from Zoho Creator"""

import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from zoho_auth import ZohoAuth
import requests
import json

def main():
    load_dotenv()
    
    # Authenticate
    auth = ZohoAuth(
        client_id=os.getenv('ZOHO_CLIENT_ID'),
        client_secret=os.getenv('ZOHO_CLIENT_SECRET'),
        redirect_uri=os.getenv('ZOHO_REDIRECT_URI'),
        scope=os.getenv('ZOHO_SCOPE'),
        token_file_path='.zoho_tokens.json'
    )
    
    token = auth.get_valid_access_token()
    if not token:
        print("❌ Authentication failed")
        return
    
    headers = auth.get_headers()
    creator_base = 'https://creator.zoho.com/api/v2'
    account = 'taylorsolutions'
    
    print('\n' + '='*80)
    print('  ZOHO CREATOR OPERATIONS APP - FULL REPORT')
    print('='*80)
    print(f'Account: {account}')
    print(f'API Base: {creator_base}\n')
    
    # Get all applications
    print('🔍 Fetching Creator applications...')
    apps_url = f'{creator_base}/{account}/applications'
    
    try:
        response = requests.get(apps_url, headers=headers, timeout=30)
        print(f'Response Status: {response.status_code}')
        
        if response.status_code == 200:
            data = response.json()
            apps = data.get('applications', [])
            print(f'✓ Found {len(apps)} Creator Applications\n')
            
            # Find Operations App
            ops_app = None
            print('Applications:')
            for idx, app in enumerate(apps, 1):
                name = app.get('application_name', 'Unnamed')
                link = app.get('link_name', '')
                print(f'  {idx}. {name} ({link})')
                
                if 'operation' in name.lower():
                    ops_app = app
                    print(f'      ⭐ THIS IS THE OPERATIONS APP!')
            
            if ops_app:
                print('\n' + '='*80)
                print(f'  OPERATIONS APP DETAILS')
                print('='*80)
                
                app_name = ops_app.get('application_name')
                app_link = ops_app.get('link_name')
                
                print(f'\nName: {app_name}')
                print(f'Link: {app_link}')
                print(f'Type: {ops_app.get("type")}')
                print(f'Created: {ops_app.get("date_created")}')
                print(f'Owner: {ops_app.get("owner_name")}')
                
                # Get Forms
                print('\n' + '─'*80)
                print('FORMS:')
                print('─'*80)
                
                forms_url = f'{creator_base}/{account}/{app_link}/forms'
                forms_resp = requests.get(forms_url, headers=headers, timeout=30)
                
                if forms_resp.status_code == 200:
                    forms = forms_resp.json().get('forms', [])
                    print(f'Total Forms: {len(forms)}\n')
                    
                    for i, form in enumerate(forms, 1):
                        print(f'{i}. {form.get("display_name")}')
                        print(f'   Link: {form.get("link_name")}')
                        print(f'   Type: {form.get("type")}\n')
                else:
                    print(f'Could not fetch forms: {forms_resp.status_code}')
                
                # Get Reports
                print('─'*80)
                print('REPORTS:')
                print('─'*80)
                
                reports_url = f'{creator_base}/{account}/{app_link}/reports'
                reports_resp = requests.get(reports_url, headers=headers, timeout=30)
                
                if reports_resp.status_code == 200:
                    reports = reports_resp.json().get('reports', [])
                    print(f'Total Reports: {len(reports)}\n')
                    
                    for i, report in enumerate(reports, 1):
                        print(f'{i}. {report.get("display_name")}')
                        print(f'   Link: {report.get("link_name")}')
                        print(f'   Type: {report.get("type")}\n')
                else:
                    print(f'Could not fetch reports: {reports_resp.status_code}')
                
                # Summary
                print('='*80)
                print('✅ REPORT COMPLETE')
                print(f'🔗 Access at: https://creator.zoho.com/{account}/{app_link}')
                print('='*80 + '\n')
                
                # Save to file
                report_data = {
                    'application': ops_app,
                    'account': account,
                    'url': f'https://creator.zoho.com/{account}/{app_link}'
                }
                
                with open('operations_app_details.json', 'w') as f:
                    json.dump(report_data, f, indent=2)
                
                print('💾 Saved to: operations_app_details.json\n')
            else:
                print('\n⚠️  No Operations App found')
                print('Available apps listed above')
        else:
            print(f'❌ Error: {response.status_code}')
            print(f'Response: {response.text[:500]}')
            
    except Exception as e:
        print(f'❌ Error: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
