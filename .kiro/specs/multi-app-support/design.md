# Design Document

## Overview

This design transforms the existing Zoho CRM MCP Server into a **comprehensive Zoho Ecosystem MCP Server** that supports 40+ Zoho applications through a unified architecture. The solution introduces an app registry system, dynamic API routing, and app-specific tool modules while maintaining backward compatibility with existing CRM functionality.

### Supported Zoho Apps (40+)

**Sales & Marketing (6 apps)**
- CRM, SalesIQ, Campaigns, Social, Forms, Survey

**Finance & Commerce (6 apps)**
- Books, Invoice, Expense, Inventory, Subscriptions, Commerce

**Customer Service (2 apps)**
- Desk, Assist

**HR & Recruitment (2 apps)**
- People, Recruit

**Project Management (4 apps)**
- Projects, Sprints, BugTracker, Connect

**Collaboration (2 apps)**
- Cliq, Meeting

**Email & Storage (2 apps)**
- Mail, WorkDrive

**Productivity (3 apps)**
- Writer, Sheet, Show

**Analytics (1 app)**
- Analytics

**Developer Platform (3 apps)**
- Creator, Flow, Catalyst

**Operations & Field Service (3 apps)**
- Fleet, FSM (Field Service Management), Bookings

**Legal & Compliance (2 apps)**
- Sign, Contracts

**IoT (1 app)**
- IoT

The design leverages the existing OAuth infrastructure (which already supports multi-app scopes) and adds a flexible routing layer that directs API requests to the appropriate Zoho service endpoint based on the target application.

## Architecture

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Assistant (Claude, etc.)               │
└────────────────────────┬────────────────────────────────────┘
                         │ MCP Protocol
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCP Server (FastMCP)                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │           Tool Registry & Dispatcher                  │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ▼               ▼               ▼
┌────────────────┐ ┌────────────┐ ┌────────────┐
│  App Registry  │ │ API Router │ │ Auth Layer │
└────────┬───────┘ └─────┬──────┘ └─────┬──────┘
         │               │              │
         │               │              │ (Shared OAuth)
         │               ▼              ▼
         │      ┌──────────────────────────┐
         │      │   ZohoAuth (Existing)    │
         │      └──────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────┐
│                    App-Specific Modules                      │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │   CRM    │ │  Books   │ │ Projects │ │   Desk   │       │
│  │  Tools   │ │  Tools   │ │  Tools   │ │  Tools   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │  People  │ │ Recruit  │ │Inventory │ │Analytics │       │
│  │  Tools   │ │  Tools   │ │  Tools   │ │  Tools   │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
│  ┌──────────┐                                                │
│  │ Creator  │                                                │
│  │  Tools   │                                                │
│  └──────────┘                                                │
└─────────────────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                  Zoho API Endpoints                          │
│  /crm/v2/  /books/v3/  /projects/v3/  /desk/v1/  etc.       │
└─────────────────────────────────────────────────────────────┘
```

### Key Architectural Decisions

1. **Modular App Structure**: Each Zoho app gets its own module with dedicated tools
2. **Shared Authentication**: Single OAuth token works across all apps (already configured)
3. **Dynamic Routing**: API router determines correct endpoint based on app name
4. **Backward Compatibility**: Existing CRM tools remain unchanged
5. **Lazy Loading**: App modules only load if their scopes are present
6. **Unified Error Handling**: Consistent error responses across all apps

## Components and Interfaces

### 1. App Registry (`src/app_registry.py`)

**Purpose**: Central registry that tracks available Zoho apps, their API configurations, and enabled status.

**Interface**:
```python
class ZohoAppConfig:
    """Configuration for a Zoho application."""
    name: str                    # e.g., "CRM", "Books"
    api_path: str               # e.g., "/crm/v2", "/books/v3"
    required_scopes: List[str]  # e.g., ["ZohoCRM.modules.ALL"]
    enabled: bool               # Determined by scope presence
    api_version: str            # e.g., "v2", "v3"

class AppRegistry:
    """Registry of available Zoho applications."""
    
    def __init__(self, scope_string: str):
        """Initialize registry based on OAuth scopes."""
        pass
    
    def get_app_config(self, app_name: str) -> Optional[ZohoAppConfig]:
        """Get configuration for a specific app."""
        pass
    
    def list_enabled_apps(self) -> List[ZohoAppConfig]:
        """List all enabled applications."""
        pass
    
    def is_app_enabled(self, app_name: str) -> bool:
        """Check if an app is enabled."""
        pass
```

**App Configurations**:
```python
APP_CONFIGS = {
    # Sales & Marketing
    "CRM": {
        "api_path": "/crm/v2",
        "required_scopes": ["ZohoCRM.modules.ALL"],
        "api_version": "v2",
        "category": "Sales"
    },
    "SalesIQ": {
        "api_path": "/salesiq/v2",
        "required_scopes": ["ZohoSalesIQ.modules.ALL"],
        "api_version": "v2",
        "category": "Sales"
    },
    "Campaigns": {
        "api_path": "/campaigns/v2",
        "required_scopes": ["ZohoCampaigns.campaign.ALL"],
        "api_version": "v2",
        "category": "Marketing"
    },
    "Social": {
        "api_path": "/social/v2",
        "required_scopes": ["ZohoSocial.data.ALL"],
        "api_version": "v2",
        "category": "Marketing"
    },
    "Forms": {
        "api_path": "/forms/v2",
        "required_scopes": ["ZohoForms.form.ALL"],
        "api_version": "v2",
        "category": "Marketing"
    },
    "Survey": {
        "api_path": "/survey/v2",
        "required_scopes": ["ZohoSurvey.surveys.ALL"],
        "api_version": "v2",
        "category": "Marketing"
    },
    
    # Finance & Commerce
    "Books": {
        "api_path": "/books/v3",
        "required_scopes": ["ZohoBooks.fullaccess.all"],
        "api_version": "v3",
        "category": "Finance"
    },
    "Invoice": {
        "api_path": "/invoice/v3",
        "required_scopes": ["ZohoInvoice.fullaccess.all"],
        "api_version": "v3",
        "category": "Finance"
    },
    "Expense": {
        "api_path": "/expense/v1",
        "required_scopes": ["ZohoExpense.fullaccess.all"],
        "api_version": "v1",
        "category": "Finance"
    },
    "Inventory": {
        "api_path": "/inventory/v1",
        "required_scopes": ["ZohoInventory.fullaccess.all"],
        "api_version": "v1",
        "category": "Finance"
    },
    "Subscriptions": {
        "api_path": "/subscriptions/v1",
        "required_scopes": ["ZohoSubscriptions.fullaccess.all"],
        "api_version": "v1",
        "category": "Finance"
    },
    "Commerce": {
        "api_path": "/commerce/v1",
        "required_scopes": ["ZohoCommerce.fullaccess.all"],
        "api_version": "v1",
        "category": "Commerce"
    },
    
    # Customer Service
    "Desk": {
        "api_path": "/desk/v1",
        "required_scopes": ["Desk.tickets.ALL"],
        "api_version": "v1",
        "category": "Service"
    },
    "Assist": {
        "api_path": "/assist/v2",
        "required_scopes": ["ZohoAssist.session.ALL"],
        "api_version": "v2",
        "category": "Service"
    },
    
    # HR & Recruitment
    "People": {
        "api_path": "/people/api",
        "required_scopes": ["ZohoPeople.forms.ALL"],
        "api_version": "api",
        "category": "HR"
    },
    "Recruit": {
        "api_path": "/recruit/v2",
        "required_scopes": ["ZohoRecruit.modules.ALL"],
        "api_version": "v2",
        "category": "HR"
    },
    
    # Project Management & Collaboration
    "Projects": {
        "api_path": "/projects/v3",
        "required_scopes": ["ZohoProjects.projects.ALL"],
        "api_version": "v3",
        "category": "Projects"
    },
    "Sprints": {
        "api_path": "/sprints/v2",
        "required_scopes": ["ZohoSprints.projects.ALL"],
        "api_version": "v2",
        "category": "Projects"
    },
    "BugTracker": {
        "api_path": "/bugtracker/v2",
        "required_scopes": ["ZohoBugTracker.projects.ALL"],
        "api_version": "v2",
        "category": "Projects"
    },
    "Connect": {
        "api_path": "/connect/v2",
        "required_scopes": ["ZohoConnect.network.ALL"],
        "api_version": "v2",
        "category": "Collaboration"
    },
    "Cliq": {
        "api_path": "/cliq/v2",
        "required_scopes": ["ZohoCliq.channels.ALL"],
        "api_version": "v2",
        "category": "Collaboration"
    },
    "Meeting": {
        "api_path": "/meeting/v2",
        "required_scopes": ["ZohoMeeting.meeting.ALL"],
        "api_version": "v2",
        "category": "Collaboration"
    },
    
    # Email & Productivity
    "Mail": {
        "api_path": "/mail/v1",
        "required_scopes": ["ZohoMail.accounts.ALL"],
        "api_version": "v1",
        "category": "Email"
    },
    "WorkDrive": {
        "api_path": "/workdrive/api/v1",
        "required_scopes": ["ZohoWorkDrive.files.ALL"],
        "api_version": "v1",
        "category": "Storage"
    },
    "Writer": {
        "api_path": "/writer/api/v1",
        "required_scopes": ["ZohoWriter.documents.ALL"],
        "api_version": "v1",
        "category": "Productivity"
    },
    "Sheet": {
        "api_path": "/sheet/api/v1",
        "required_scopes": ["ZohoSheet.spreadsheets.ALL"],
        "api_version": "v1",
        "category": "Productivity"
    },
    "Show": {
        "api_path": "/show/api/v1",
        "required_scopes": ["ZohoShow.presentations.ALL"],
        "api_version": "v1",
        "category": "Productivity"
    },
    
    # Analytics & BI
    "Analytics": {
        "api_path": "/restapi/v2",
        "required_scopes": ["ZohoAnalytics.fullaccess.all"],
        "api_version": "v2",
        "category": "Analytics"
    },
    
    # Developer & Custom Apps
    "Creator": {
        "api_path": "/creator/v2",
        "required_scopes": ["ZohoCreator.report.READ"],
        "api_version": "v2",
        "category": "Developer"
    },
    "Flow": {
        "api_path": "/flow/v1",
        "required_scopes": ["ZohoFlow.flows.ALL"],
        "api_version": "v1",
        "category": "Developer"
    },
    "Catalyst": {
        "api_path": "/catalyst/v2",
        "required_scopes": ["ZohoCatalyst.projects.ALL"],
        "api_version": "v2",
        "category": "Developer"
    },
    
    # Operations & Field Service
    "Fleet": {
        "api_path": "/fleet/v1",
        "required_scopes": ["ZohoFleet.modules.ALL"],
        "api_version": "v1",
        "category": "Operations"
    },
    "FSM": {
        "api_path": "/fsm/v1",
        "required_scopes": ["ZohoFSM.modules.ALL"],
        "api_version": "v1",
        "category": "Operations"
    },
    
    # Legal & Compliance
    "Sign": {
        "api_path": "/sign/v1",
        "required_scopes": ["ZohoSign.documents.ALL"],
        "api_version": "v1",
        "category": "Legal"
    },
    "Contracts": {
        "api_path": "/contracts/v1",
        "required_scopes": ["ZohoContracts.contracts.ALL"],
        "api_version": "v1",
        "category": "Legal"
    },
    
    # IoT & Specialized
    "IoT": {
        "api_path": "/iot/v1",
        "required_scopes": ["ZohoIoT.devices.ALL"],
        "api_version": "v1",
        "category": "IoT"
    },
    "Bookings": {
        "api_path": "/bookings/v1",
        "required_scopes": ["ZohoBookings.bookings.ALL"],
        "api_version": "v1",
        "category": "Operations"
    }
}
```

### 2. API Router (`src/api_router.py`)

**Purpose**: Routes API requests to the correct Zoho application endpoint.

**Interface**:
```python
class APIRouter:
    """Routes API requests to appropriate Zoho app endpoints."""
    
    def __init__(self, auth: ZohoAuth, registry: AppRegistry):
        """Initialize router with auth and app registry."""
        pass
    
    def make_request(
        self,
        app_name: str,
        endpoint: str,
        method: str = 'GET',
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        additional_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make authenticated API request to any Zoho app.
        
        Args:
            app_name: Name of the Zoho app (e.g., "CRM", "Books")
            endpoint: API endpoint path (e.g., "Leads", "invoices")
            method: HTTP method
            data: Request body data
            params: Query parameters
            additional_path: Additional path segments (e.g., organization_id for Books)
        
        Returns:
            Standardized response dictionary
        """
        pass
    
    def _build_url(
        self,
        app_config: ZohoAppConfig,
        endpoint: str,
        additional_path: Optional[str]
    ) -> str:
        """Build complete API URL."""
        pass
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Standardize response format across all apps."""
        pass
```

### 3. Updated Server (`src/server.py`)

**Changes**:
- Replace hardcoded `make_api_request()` with `APIRouter`
- Initialize `AppRegistry` on startup
- Add new tool: `list_enabled_apps()`
- Keep existing CRM tools unchanged (backward compatibility)
- Add app-specific tool modules

**New Global Initialization**:
```python
# Global instances
auth: Optional[ZohoAuth] = None
app_registry: Optional[AppRegistry] = None
api_router: Optional[APIRouter] = None

def init_system():
    """Initialize authentication, registry, and router."""
    global auth, app_registry, api_router
    
    # Initialize auth (existing)
    auth = ZohoAuth(...)
    
    # Initialize app registry
    scope = os.getenv('ZOHO_SCOPE', '')
    app_registry = AppRegistry(scope)
    
    # Initialize API router
    api_router = APIRouter(auth, app_registry)
    
    logger.info(f"Enabled apps: {[app.name for app in app_registry.list_enabled_apps()]}")
```

### 4. App-Specific Tool Modules

Each Zoho app gets its own module with dedicated tools. Structure:

```
src/
├── apps/
│   ├── __init__.py
│   ├── crm_tools.py       # Existing CRM tools (refactored)
│   ├── books_tools.py     # Zoho Books tools
│   ├── projects_tools.py  # Zoho Projects tools
│   ├── desk_tools.py      # Zoho Desk tools
│   ├── people_tools.py    # Zoho People tools
│   ├── recruit_tools.py   # Zoho Recruit tools
│   ├── inventory_tools.py # Zoho Inventory tools
│   ├── analytics_tools.py # Zoho Analytics tools
│   ├── creator_tools.py   # Zoho Creator tools
│   ├── salesiq_tools.py   # Zoho SalesIQ tools
│   └── fleet_tools.py     # Zoho Fleet tools
```

**Example: Books Tools** (`src/apps/books_tools.py`):
```python
from typing import Dict, Any
from functools import wraps

def register_books_tools(mcp, api_router, app_registry):
    """Register Zoho Books tools with MCP server."""
    
    if not app_registry.is_app_enabled("Books"):
        return  # Skip if Books not enabled
    
    @mcp.tool()
    def books_get_invoices(
        ctx,
        organization_id: str,
        page: int = 1,
        per_page: int = 200
    ) -> Dict[str, Any]:
        """Get invoices from Zoho Books."""
        params = {'page': page, 'per_page': per_page}
        return api_router.make_request(
            app_name="Books",
            endpoint="invoices",
            method="GET",
            params=params,
            additional_path=f"organization/{organization_id}"
        )
    
    @mcp.tool()
    def books_get_customers(
        ctx,
        organization_id: str
    ) -> Dict[str, Any]:
        """Get customers from Zoho Books."""
        return api_router.make_request(
            app_name="Books",
            endpoint="contacts",
            method="GET",
            additional_path=f"organization/{organization_id}"
        )
    
    # Additional Books tools...
```

## Data Models

### Standardized Response Format

All API responses follow this structure:

```python
{
    "status": "success" | "error",
    "status_code": int,
    "app": str,  # e.g., "CRM", "Books"
    "data": Any,  # App-specific data
    "message": Optional[str],  # Error message if applicable
    "error": Optional[Any]  # Detailed error info
}
```

### App Configuration Model

```python
@dataclass
class ZohoAppConfig:
    name: str
    api_path: str
    required_scopes: List[str]
    enabled: bool
    api_version: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "api_path": self.api_path,
            "enabled": self.enabled,
            "api_version": self.api_version
        }
```

## Error Handling

### Error Categories

1. **Authentication Errors**: Token invalid/expired
2. **Authorization Errors**: Insufficient scopes
3. **App Not Enabled**: Requested app not configured
4. **API Errors**: Zoho API returned error
5. **Network Errors**: Timeout, connection issues
6. **Validation Errors**: Invalid parameters

### Error Response Structure

```python
{
    "status": "error",
    "error_type": "authentication" | "authorization" | "app_disabled" | "api_error" | "network" | "validation",
    "status_code": int,
    "message": str,  # Human-readable message
    "details": Optional[Dict],  # Additional error context
    "retry_after": Optional[int]  # For rate limit errors
}
```

### Error Handling Flow

```python
def _handle_error(self, error_type: str, details: Any) -> Dict[str, Any]:
    """Centralized error handling."""
    
    error_messages = {
        "app_disabled": "The requested Zoho app is not enabled. Check your OAuth scopes.",
        "authentication": "Authentication failed. Please re-authenticate.",
        "authorization": "Insufficient permissions for this operation.",
        "rate_limit": "Rate limit exceeded. Please retry after {retry_after} seconds.",
        "network": "Network error occurred. Please check your connection.",
        "api_error": "Zoho API returned an error: {message}"
    }
    
    return {
        "status": "error",
        "error_type": error_type,
        "message": error_messages.get(error_type, "Unknown error"),
        "details": details
    }
```

## Testing Strategy

### Unit Tests

**Test Files**:
- `tests/test_app_registry.py` - App registry functionality
- `tests/test_api_router.py` - API routing logic
- `tests/test_books_tools.py` - Books-specific tools
- `tests/test_projects_tools.py` - Projects-specific tools
- (etc. for each app)

**Key Test Cases**:
1. App registry correctly identifies enabled apps from scopes
2. API router builds correct URLs for each app
3. Error handling returns standardized responses
4. Tools validate parameters correctly
5. Backward compatibility with existing CRM tools

### Integration Tests

**Test Scenarios**:
1. Authenticate and list enabled apps
2. Make requests to multiple apps in sequence
3. Handle app-not-enabled errors gracefully
4. Token refresh works across all apps
5. Rate limiting is respected

### Manual Testing Checklist

- [ ] Authenticate with multi-app scopes
- [ ] List enabled apps shows correct apps
- [ ] CRM tools still work (backward compatibility)
- [ ] Books tools retrieve invoices successfully
- [ ] Projects tools retrieve projects successfully
- [ ] Desk tools retrieve tickets successfully
- [ ] Error messages are clear and actionable
- [ ] Sandbox vs production domains work correctly

## Implementation Phases

### Phase 1: Core Infrastructure
- Create `app_registry.py` with app configurations
- Create `api_router.py` with dynamic routing
- Update `server.py` to use new router
- Add `list_enabled_apps()` tool
- Ensure backward compatibility with CRM

### Phase 2: Books & Projects Support
- Implement `books_tools.py` with core operations
- Implement `projects_tools.py` with core operations
- Test multi-app requests
- Document Books and Projects tools

### Phase 3: Desk & People Support
- Implement `desk_tools.py` with ticket management
- Implement `people_tools.py` with HR operations
- Test support and HR workflows

### Phase 4: Recruit, Inventory & Analytics
- Implement `recruit_tools.py` with candidate management
- Implement `inventory_tools.py` with stock operations
- Implement `analytics_tools.py` with reporting
- Test data retrieval across apps

### Phase 5: Creator, SalesIQ & Polish
- Implement `creator_tools.py` with custom app access
- Implement `salesiq_tools.py` with visitor tracking and chat tools
- Comprehensive error handling review
- Performance optimization
- Documentation updates
- Final integration testing

## Security Considerations

1. **Scope Validation**: Only expose tools for apps with valid scopes
2. **Token Security**: Existing token storage remains secure
3. **Input Validation**: Validate all user inputs before API calls
4. **Error Messages**: Don't expose sensitive data in errors
5. **Logging**: Log operations without exposing credentials
6. **Rate Limiting**: Respect Zoho's rate limits per app

## Performance Considerations

1. **Lazy Loading**: Only load app modules if enabled
2. **Connection Pooling**: Reuse HTTP connections
3. **Caching**: Cache app configurations (not data)
4. **Timeout Management**: Appropriate timeouts per app
5. **Batch Operations**: Support bulk operations where available

## Backward Compatibility

**Guarantees**:
- All existing CRM tools work unchanged
- Existing `.env` configurations still valid
- Token storage format unchanged
- MCP server name can remain "ZohoCRM" or change to "ZohoMultiApp"

**Migration Path**:
- Users can add new scopes to `.env`
- Restart server to enable new apps
- No code changes required for existing integrations

## Documentation Updates

**Files to Update**:
- `README.md` - Add multi-app capabilities
- `QUICK_SETUP.md` - Update scope configuration
- Create `MULTI_APP_GUIDE.md` - Comprehensive guide for all apps
- Update tool documentation with app-specific examples

## Open Questions

1. Should we rename the server from "ZohoCRM" to "ZohoMultiApp"?
2. Do we need organization_id caching for Books/Inventory?
3. Should we support custom app configurations via config file?
4. Do we need tool name prefixes (e.g., `books_get_invoices` vs `get_invoices`)?

## Success Criteria

- ✅ Support for 40+ Zoho apps across all major categories (Sales, Marketing, Finance, Service, HR, Projects, Collaboration, Analytics, Developer, Operations, Legal, IoT)
- ✅ Existing CRM functionality unchanged
- ✅ Clear error messages for disabled apps
- ✅ Single OAuth token works across all apps
- ✅ Comprehensive documentation for each app
- ✅ Unit test coverage > 80%
- ✅ Integration tests pass for all enabled apps
