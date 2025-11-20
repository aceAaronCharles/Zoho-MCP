#!/usr/bin/env python3
"""Test Operations Apps MCP Tools"""

import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from zoho_auth import ZohoAuth
from zoho_multi_app import ZohoMultiApp
from operations_tools import OperationsTools

def main():
    load_dotenv()
    
    print('\n' + '='*80)
    print('  OPERATIONS APPS - MCP TOOLS TEST')
    print('='*80)
    
    # Authenticate
    print('\n🔑 Authenticating...')
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
    
    print("✓ Authenticated successfully\n")
    
    # Initialize Operations Tools
    multi_app = ZohoMultiApp(auth, auth.get_api_domain())
    ops = OperationsTools(multi_app)
    
    print('='*80)
    print('  OPERATIONS MODULES SUMMARY')
    print('='*80)
    
    # Get operations summary
    summary = ops.get_operations_summary()
    
    if summary['status'] == 'success':
        print('\n📊 Operations Modules Status:\n')
        for key, info in summary['data'].items():
            module = info.get('module')
            count = info.get('count', 'N/A')
            status = info.get('status')
            
            if status == 'active':
                print(f'✓ {module.ljust(25)} {count} records')
            else:
                print(f'✗ {module.ljust(25)} {status}')
    
    print('\n' + '='*80)
    print('  AVAILABLE OPERATIONS TOOLS')
    print('='*80)
    
    tools_list = [
        ('Buildings Management', [
            'get_buildings()',
            'create_building(data)',
            'get_building_by_id(id)',
        ]),
        ('Facilitators Management', [
            'get_facilitators()',
            'create_facilitator(data)',
            'link_facilitator_to_building(fac_id, building_id)',
        ]),
        ('Enquiries Management', [
            'get_enquiries()',
            'create_enquiry(data)',
            'update_enquiry_status(id, status)',
        ]),
        ('Schedule/Bookings', [
            'get_schedules()',
            'create_schedule(data)',
            'get_schedule_by_id(id)',
        ]),
        ('SMS Campaigns', [
            'get_sms_campaigns()',
            'create_sms_campaign(data)',
            'get_sms_campaign_logs()',
            'block_number(number_data)',
        ]),
        ('Item Types & Inventory', [
            'get_item_types()',
            'create_item_type(data)',
        ]),
        ('Move Types', [
            'get_move_types()',
            'create_move_type(data)',
        ]),
        ('Gifts/Promotions', [
            'get_gifts()',
            'create_gift(data)',
        ]),
        ('Reporting & Search', [
            'get_operations_summary()',
            'search_across_operations(term, modules)',
        ]),
        ('Approvals & Workflow', [
            'get_pending_approvals()',
            'approve_record(id, notes)',
            'reject_record(id, reason)',
        ]),
    ]
    
    for category, tools in tools_list:
        print(f'\n📦 {category}:')
        for tool in tools:
            print(f'   • {tool}')
    
    # Test a few operations
    print('\n' + '='*80)
    print('  TESTING OPERATIONS ACCESS')
    print('='*80)
    
    # Test Buildings
    print('\n1. Testing Buildings access...')
    buildings = ops.get_buildings(page=1, per_page=5)
    if buildings['status'] == 'success':
        data = buildings.get('data', {}).get('data', [])
        print(f'   ✓ Found {len(data)} buildings (showing sample)')
        for building in data[:3]:
            print(f'     • {building.get("Name", "Unnamed")} (ID: {building.get("id")})')
    else:
        print(f'   ✗ {buildings.get("message")}')
    
    # Test Facilitators
    print('\n2. Testing Facilitators access...')
    facilitators = ops.get_facilitators(page=1, per_page=5)
    if facilitators['status'] == 'success':
        data = facilitators.get('data', {}).get('data', [])
        print(f'   ✓ Found {len(data)} facilitators (showing sample)')
        for fac in data[:3]:
            print(f'     • {fac.get("Name", "Unnamed")} (ID: {fac.get("id")})')
    else:
        print(f'   ✗ {facilitators.get("message")}')
    
    # Test Enquiries
    print('\n3. Testing Enquiries access...')
    enquiries = ops.get_enquiries(page=1, per_page=5)
    if enquiries['status'] == 'success':
        data = enquiries.get('data', {}).get('data', [])
        print(f'   ✓ Found {len(data)} enquiries (showing sample)')
        for enq in data[:3]:
            print(f'     • {enq.get("Name", "Unnamed")} (ID: {enq.get("id")})')
    else:
        print(f'   ✗ {enquiries.get("message")}')
    
    print('\n' + '='*80)
    print('✅ OPERATIONS TOOLS READY TO USE!')
    print('='*80)
    print('\n💡 You can now use these tools to:')
    print('   • Manage buildings, facilitators, and schedules')
    print('   • Track enquiries and bookings')
    print('   • Run SMS campaigns')
    print('   • Handle approvals and workflows')
    print('   • Generate reports across all operations')
    print('\n' + '='*80 + '\n')

if __name__ == '__main__':
    main()
