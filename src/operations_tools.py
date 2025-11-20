"""
Operations Apps MCP Tools
Tools to interact with Operations-related modules in Zoho CRM
"""

from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)

class OperationsTools:
    """MCP tools for Operations Apps functionality."""
    
    def __init__(self, multi_app_handler):
        """
        Initialize Operations Tools.
        
        Args:
            multi_app_handler: ZohoMultiApp instance
        """
        self.api = multi_app_handler
        
        # Operations-related custom modules from your CRM
        self.ops_modules = {
            'buildings': 'Buildings',
            'facilitators': 'Facilitators',
            'item_types': 'Item_Types',
            'enquiries': 'Enquiries',
            'schedule': 'Schudule',
            'move_types': 'Move_Types',
            'gifts': 'Gifts',
            'sms_campaigns': 'SMS_Campaigns',
            'blocked_numbers': 'Blocked_Numbers',
            'sms_logs': 'SMS_Campaign_Logs'
        }
    
    # ========================================================================
    # BUILDINGS OPERATIONS
    # ========================================================================
    
    def get_buildings(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """
        Get all buildings/locations.
        
        Args:
            page: Page number
            per_page: Records per page
            
        Returns:
            List of buildings
        """
        return self.api.crm_get_records('Buildings', page, per_page)
    
    def create_building(self, building_data: Dict) -> Dict[str, Any]:
        """
        Create a new building/location.
        
        Args:
            building_data: Building information
            
        Returns:
            Created building record
        """
        return self.api.crm_create_record('Buildings', building_data)
    
    def get_building_by_id(self, building_id: str) -> Dict[str, Any]:
        """Get specific building by ID."""
        return self.api.make_request('crm', f'Buildings/{building_id}')
    
    # ========================================================================
    # FACILITATORS OPERATIONS
    # ========================================================================
    
    def get_facilitators(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """
        Get all facilitators/staff members.
        
        Args:
            page: Page number
            per_page: Records per page
            
        Returns:
            List of facilitators
        """
        return self.api.crm_get_records('Facilitators', page, per_page)
    
    def create_facilitator(self, facilitator_data: Dict) -> Dict[str, Any]:
        """
        Create a new facilitator.
        
        Args:
            facilitator_data: Facilitator information
            
        Returns:
            Created facilitator record
        """
        return self.api.crm_create_record('Facilitators', facilitator_data)
    
    def get_facilitator_by_id(self, facilitator_id: str) -> Dict[str, Any]:
        """Get specific facilitator by ID."""
        return self.api.make_request('crm', f'Facilitators/{facilitator_id}')
    
    def link_facilitator_to_building(self, facilitator_id: str, building_id: str) -> Dict[str, Any]:
        """
        Link a facilitator to a building.
        Uses the Facilitators_X_Buildings linking module.
        
        Args:
            facilitator_id: ID of facilitator
            building_id: ID of building
            
        Returns:
            Link record
        """
        link_data = {
            'Facilitator': facilitator_id,
            'Building': building_id
        }
        return self.api.crm_create_record('Facilitators_X_Buildings', link_data)
    
    # ========================================================================
    # ENQUIRIES OPERATIONS
    # ========================================================================
    
    def get_enquiries(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """
        Get all enquiries.
        
        Args:
            page: Page number
            per_page: Records per page
            
        Returns:
            List of enquiries
        """
        return self.api.crm_get_records('Enquiries', page, per_page)
    
    def create_enquiry(self, enquiry_data: Dict) -> Dict[str, Any]:
        """
        Create a new enquiry.
        
        Args:
            enquiry_data: Enquiry information
            
        Returns:
            Created enquiry record
        """
        return self.api.crm_create_record('Enquiries', enquiry_data)
    
    def get_enquiry_by_id(self, enquiry_id: str) -> Dict[str, Any]:
        """Get specific enquiry by ID."""
        return self.api.make_request('crm', f'Enquiries/{enquiry_id}')
    
    def update_enquiry_status(self, enquiry_id: str, status: str) -> Dict[str, Any]:
        """
        Update enquiry status.
        
        Args:
            enquiry_id: ID of enquiry
            status: New status
            
        Returns:
            Updated enquiry
        """
        update_data = {'Status': status}
        return self.api.make_request('crm', f'Enquiries/{enquiry_id}', method='PUT', data={'data': [update_data]})
    
    # ========================================================================
    # SCHEDULE/BOOKINGS OPERATIONS
    # ========================================================================
    
    def get_schedules(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """
        Get all schedules/bookings.
        
        Args:
            page: Page number
            per_page: Records per page
            
        Returns:
            List of schedules
        """
        return self.api.crm_get_records('Schudule', page, per_page)
    
    def create_schedule(self, schedule_data: Dict) -> Dict[str, Any]:
        """
        Create a new schedule/booking.
        
        Args:
            schedule_data: Schedule information
            
        Returns:
            Created schedule record
        """
        return self.api.crm_create_record('Schudule', schedule_data)
    
    def get_schedule_by_id(self, schedule_id: str) -> Dict[str, Any]:
        """Get specific schedule by ID."""
        return self.api.make_request('crm', f'Schudule/{schedule_id}')
    
    # ========================================================================
    # ITEM TYPES & INVENTORY
    # ========================================================================
    
    def get_item_types(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """
        Get all item types.
        
        Args:
            page: Page number
            per_page: Records per page
            
        Returns:
            List of item types
        """
        return self.api.crm_get_records('Item_Types', page, per_page)
    
    def create_item_type(self, item_type_data: Dict) -> Dict[str, Any]:
        """
        Create a new item type.
        
        Args:
            item_type_data: Item type information
            
        Returns:
            Created item type record
        """
        return self.api.crm_create_record('Item_Types', item_type_data)
    
    # ========================================================================
    # MOVE TYPES OPERATIONS
    # ========================================================================
    
    def get_move_types(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get all move types."""
        return self.api.crm_get_records('Move_Types', page, per_page)
    
    def create_move_type(self, move_type_data: Dict) -> Dict[str, Any]:
        """Create a new move type."""
        return self.api.crm_create_record('Move_Types', move_type_data)
    
    # ========================================================================
    # GIFTS/PROMOTIONS OPERATIONS
    # ========================================================================
    
    def get_gifts(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get all gifts/promotions."""
        return self.api.crm_get_records('Gifts', page, per_page)
    
    def create_gift(self, gift_data: Dict) -> Dict[str, Any]:
        """Create a new gift/promotion."""
        return self.api.crm_create_record('Gifts', gift_data)
    
    # ========================================================================
    # SMS CAMPAIGN OPERATIONS
    # ========================================================================
    
    def get_sms_campaigns(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get all SMS campaigns."""
        return self.api.crm_get_records('SMS_Campaigns', page, per_page)
    
    def create_sms_campaign(self, campaign_data: Dict) -> Dict[str, Any]:
        """Create a new SMS campaign."""
        return self.api.crm_create_record('SMS_Campaigns', campaign_data)
    
    def get_sms_campaign_logs(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get SMS campaign logs."""
        return self.api.crm_get_records('SMS_Campaign_Logs', page, per_page)
    
    def get_blocked_numbers(self, page: int = 1, per_page: int = 200) -> Dict[str, Any]:
        """Get all blocked numbers."""
        return self.api.crm_get_records('Blocked_Numbers', page, per_page)
    
    def block_number(self, number_data: Dict) -> Dict[str, Any]:
        """Add a number to blocked list."""
        return self.api.crm_create_record('Blocked_Numbers', number_data)
    
    # ========================================================================
    # REPORTING & ANALYTICS
    # ========================================================================
    
    def get_operations_summary(self) -> Dict[str, Any]:
        """
        Get summary of all operations modules.
        
        Returns:
            Summary with counts for each module
        """
        summary = {
            'status': 'success',
            'data': {}
        }
        
        for key, module in self.ops_modules.items():
            try:
                result = self.api.crm_get_records(module, 1, 1)
                if result['status'] == 'success':
                    # Get count from info field
                    info = result.get('data', {}).get('info', {})
                    count = info.get('count', 0)
                    summary['data'][key] = {
                        'module': module,
                        'count': count,
                        'status': 'active'
                    }
            except Exception as e:
                summary['data'][key] = {
                    'module': module,
                    'status': 'error',
                    'error': str(e)
                }
        
        return summary
    
    def search_across_operations(self, search_term: str, modules: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Search across operations modules.
        
        Args:
            search_term: Term to search for
            modules: List of module keys to search in (if None, searches all)
            
        Returns:
            Search results from all modules
        """
        if modules is None:
            modules = list(self.ops_modules.keys())
        
        results = {
            'status': 'success',
            'search_term': search_term,
            'results': {}
        }
        
        for module_key in modules:
            if module_key not in self.ops_modules:
                continue
            
            module = self.ops_modules[module_key]
            try:
                # Use CRM search API with criteria
                criteria = f"((Name:contains:{search_term}))"
                search_result = self.api.make_request(
                    'crm',
                    f'{module}/search',
                    params={'criteria': criteria}
                )
                
                if search_result['status'] == 'success':
                    results['results'][module_key] = search_result['data'].get('data', [])
            except Exception as e:
                results['results'][module_key] = {'error': str(e)}
        
        return results
    
    # ========================================================================
    # WORKFLOW & APPROVALS
    # ========================================================================
    
    def get_pending_approvals(self) -> Dict[str, Any]:
        """Get all pending approvals for operations."""
        return self.api.make_request('crm', 'Approvals', params={'status': 'pending'})
    
    def approve_record(self, approval_id: str, notes: str = "") -> Dict[str, Any]:
        """
        Approve a pending approval.
        
        Args:
            approval_id: ID of approval
            notes: Approval notes
            
        Returns:
            Approval result
        """
        approval_data = {
            'approval_state': 'approved',
            'notes': notes
        }
        return self.api.make_request('crm', f'Approvals/{approval_id}', method='PUT', data={'data': [approval_data]})
    
    def reject_record(self, approval_id: str, reason: str) -> Dict[str, Any]:
        """
        Reject a pending approval.
        
        Args:
            approval_id: ID of approval
            reason: Rejection reason
            
        Returns:
            Rejection result
        """
        rejection_data = {
            'approval_state': 'rejected',
            'notes': reason
        }
        return self.api.make_request('crm', f'Approvals/{approval_id}', method='PUT', data={'data': [rejection_data]})
