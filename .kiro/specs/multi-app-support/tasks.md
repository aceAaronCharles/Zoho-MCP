# Implementation Plan

- [x] 1. Set up core infrastructure for multi-app support
  - Create app registry system to track and validate enabled Zoho apps
  - Create API router for dynamic endpoint routing across all Zoho services
  - Update server initialization to use new registry and router
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 1.1 Create app registry module (`src/app_registry.py`)
  - Define `ZohoAppConfig` dataclass with name, api_path, required_scopes, enabled, api_version, and category fields
  - Define `APP_CONFIGS` dictionary with all 40+ Zoho app configurations
  - Implement `AppRegistry` class with initialization from OAuth scope string
  - Implement `get_app_config()` method to retrieve specific app configuration
  - Implement `list_enabled_apps()` method to return all enabled applications
  - Implement `is_app_enabled()` method to check if specific app is enabled
  - Implement scope parsing logic to determine which apps are enabled
  - _Requirements: 1.1, 11.1, 11.4_

- [x] 1.2 Create API router module (`src/api_router.py`)
  - Implement `APIRouter` class with auth and registry dependencies
  - Implement `make_request()` method with app_name, endpoint, method, data, params, and additional_path parameters
  - Implement `_build_url()` method to construct complete API URLs for any Zoho app
  - Implement `_handle_response()` method to standardize response format across all apps
  - Add support for app-specific URL patterns (e.g., organization_id for Books/Inventory)
  - Implement error handling for disabled apps, authentication failures, and API errors
  - _Requirements: 1.3, 1.4, 10.1, 10.2, 10.3, 10.4, 10.5_

- [x] 1.3 Update main server file (`src/server.py`)
  - Add global variables for `app_registry` and `api_router`
  - Create `init_system()` function to initialize auth, registry, and router
  - Replace `make_api_request()` function with calls to `api_router.make_request()`
  - Update all existing CRM tools to use new router while maintaining backward compatibility
  - Add logging for enabled apps on server startup
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 1.4 Add system management tool
  - Implement `list_enabled_apps()` MCP tool to show all currently enabled Zoho applications
  - Return app name, category, API version, and enabled status for each app
  - _Requirements: 1.2, 11.2_

- [x] 1.5 Write unit tests for core infrastructure
  - Test app registry correctly identifies enabled apps from scope strings
  - Test API router builds correct URLs for different app types
  - Test error handling returns standardized responses
  - Test backward compatibility with existing CRM functionality
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Implement Zoho Books support
  - Create Books tools module with core financial operations
  - Implement tools for invoices, customers, vendors, bills, and expenses
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2.1 Create Books tools module (`src/apps/books_tools.py`)
  - Create `register_books_tools()` function that checks if Books is enabled
  - Implement `books_get_invoices()` tool with organization_id, page, and per_page parameters
  - Implement `books_get_invoice_by_id()` tool to retrieve specific invoice details
  - Implement `books_create_invoice()` tool with invoice data and organization_id
  - Implement `books_update_invoice()` tool with invoice_id and update data
  - Implement `books_get_customers()` tool to retrieve customer list
  - Implement `books_get_vendors()` tool to retrieve vendor list
  - Implement `books_get_bills()` tool to retrieve bills with pagination
  - Implement `books_get_expenses()` tool to retrieve expense records
  - All tools should use `api_router.make_request()` with app_name="Books"
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 2.2 Register Books tools in main server
  - Import `register_books_tools` in `src/server.py`
  - Call registration function after router initialization
  - _Requirements: 2.1_

- [x] 2.3 Write tests for Books tools
  - Test Books tools are only registered when Books scope is present
  - Test invoice retrieval with valid organization_id
  - Test customer and vendor listing
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Implement Zoho Projects support
  - Create Projects tools module with project management operations
  - Implement tools for portals, projects, tasks, milestones, and timesheets
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3.1 Create Projects tools module (`src/apps/projects_tools.py`)
  - Create `register_projects_tools()` function that checks if Projects is enabled
  - Implement `projects_get_portals()` tool to list all portals
  - Implement `projects_get_projects()` tool with portal_id and pagination
  - Implement `projects_get_project_by_id()` tool for specific project details
  - Implement `projects_get_tasks()` tool with project_id and filtering options
  - Implement `projects_create_task()` tool with task data
  - Implement `projects_update_task()` tool with task_id and update data
  - Implement `projects_get_milestones()` tool to retrieve project milestones
  - Implement `projects_get_timesheets()` tool for time tracking data
  - All tools should use `api_router.make_request()` with app_name="Projects"
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 3.2 Register Projects tools in main server
  - Import `register_projects_tools` in `src/server.py`
  - Call registration function after router initialization
  - _Requirements: 3.1_

- [x] 3.3 Write tests for Projects tools
  - Test Projects tools are only registered when Projects scope is present
  - Test portal and project listing
  - Test task creation and updates
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Implement Zoho Desk support
  - Create Desk tools module with customer support operations
  - Implement tools for tickets, contacts, and ticket management
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4.1 Create Desk tools module (`src/apps/desk_tools.py`)
  - Create `register_desk_tools()` function that checks if Desk is enabled
  - Implement `desk_get_tickets()` tool with status filtering and pagination
  - Implement `desk_get_ticket_by_id()` tool for specific ticket details including comments
  - Implement `desk_create_ticket()` tool with ticket data
  - Implement `desk_update_ticket()` tool with ticket_id and update data
  - Implement `desk_add_comment()` tool to add comments to tickets
  - Implement `desk_get_contacts()` tool to retrieve support contacts
  - All tools should use `api_router.make_request()` with app_name="Desk"
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 4.2 Register Desk tools in main server
  - Import `register_desk_tools` in `src/server.py`
  - Call registration function after router initialization
  - _Requirements: 4.1_

- [x] 4.3 Write tests for Desk tools
  - Test Desk tools are only registered when Desk scope is present
  - Test ticket retrieval with status filtering
  - Test ticket creation and updates
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [x] 5. Implement Zoho People support
  - Create People tools module with HR operations
  - Implement tools for employees, attendance, and leave management
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5.1 Create People tools module (`src/apps/people_tools.py`)
  - Create `register_people_tools()` function that checks if People is enabled
  - Implement `people_get_employees()` tool to retrieve employee records
  - Implement `people_get_employee_by_id()` tool for specific employee details
  - Implement `people_get_attendance()` tool with employee_id and date range
  - Implement `people_get_leave_requests()` tool to retrieve leave applications
  - Implement `people_get_forms()` tool to access custom forms data
  - All tools should use `api_router.make_request()` with app_name="People"
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 5.2 Register People tools in main server
  - Import `register_people_tools` in `src/server.py`
  - Call registration function after router initialization
  - _Requirements: 5.1_

- [x] 5.3 Write tests for People tools
  - Test People tools are only registered when People scope is present
  - Test employee retrieval
  - Test attendance and leave data access
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 6. Implement Zoho Recruit support
  - Create Recruit tools module with recruitment operations
  - Implement tools for candidates, job openings, and recruitment workflow
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6.1 Create Recruit tools module (`src/apps/recruit_tools.py`)
  - Create `register_recruit_tools()` function that checks if Recruit is enabled
  - Implement `recruit_get_candidates()` tool with pagination and filtering
  - Implement `recruit_get_candidate_by_id()` tool for specific candidate details
  - Implement `recruit_search_candidates()` tool with search criteria
  - Implement `recruit_get_job_openings()` tool to retrieve job postings
  - Implement `recruit_update_candidate_status()` tool to change candidate status
  - Implement `recruit_add_note()` tool to add notes to candidate records
  - All tools should use `api_router.make_request()` with app_name="Recruit"
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 6.2 Register Recruit tools in main server
  - Import `register_recruit_tools` in `src/server.py`
  - Call registration function after router initialization
  - _Requirements: 6.1_

- [x] 6.3 Write tests for Recruit tools
  - Test Recruit tools are only registered when Recruit scope is present
  - Test candidate retrieval and search
  - Test job opening listing
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 7. Implement Zoho Inventory support
  - Create Inventory tools module with stock management operations
  - Implement tools for items, orders, and warehouse management
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7.1 Create Inventory tools module (`src/apps/inventory_tools.py`)
  - Create `register_inventory_tools()` function that checks if Inventory is enabled
  - Implement `inventory_get_items()` tool with organization_id and pagination
  - Implement `inventory_get_item_by_id()` tool for specific item with stock levels
  - Implement `inventory_create_item()` tool with item data
  - Implement `inventory_update_item()` tool with item_id and update data
  - Implement `inventory_get_sales_orders()` tool to retrieve sales orders
  - Implement `inventory_get_purchase_orders()` tool to retrieve purchase orders
  - Implement `inventory_get_warehouses()` tool to retrieve warehouse information
  - All tools should use `api_router.make_request()` with app_name="Inventory"
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 7.2 Register Inventory tools in main server
  - Import `register_inventory_tools` in `src/server.py`
  - Call registration function after router initialization
  - _Requirements: 7.1_

- [x] 7.3 Write tests for Inventory tools
  - Test Inventory tools are only registered when Inventory scope is present
  - Test item retrieval with stock levels
  - Test order management
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5_

- [x] 8. Implement Zoho Analytics support
  - Create Analytics tools module with business intelligence operations
  - Implement tools for workspaces, reports, and data queries
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 8.1 Create Analytics tools module (`src/apps/analytics_tools.py`)
  - Create `register_analytics_tools()` function that checks if Analytics is enabled
  - Implement `analytics_get_workspaces()` tool to list available workspaces
  - Implement `analytics_get_reports()` tool with workspace_id to list reports
  - Implement `analytics_get_report_data()` tool to retrieve report data
  - Implement `analytics_execute_sql()` tool to run custom SQL queries on Analytics data
  - Implement `analytics_get_dashboards()` tool to retrieve dashboard information
  - All tools should use `api_router.make_request()` with app_name="Analytics"
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 8.2 Register Analytics tools in main server
  - Import `register_analytics_tools` in `src/server.py`
  - Call registration function after router initialization
  - _Requirements: 8.1_

- [x] 8.3 Write tests for Analytics tools
  - Test Analytics tools are only registered when Analytics scope is present
  - Test workspace and report listing
  - Test data retrieval
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [x] 9. Implement Zoho Creator support
  - Create Creator tools module with custom application operations
  - Implement tools for applications, forms, and records
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 9.1 Create Creator tools module (`src/apps/creator_tools.py`)
  - Create `register_creator_tools()` function that checks if Creator is enabled
  - Implement `creator_get_applications()` tool to list available Creator apps
  - Implement `creator_get_forms()` tool with application_name to list forms
  - Implement `creator_get_form_metadata()` tool to retrieve form field information
  - Implement `creator_get_records()` tool to retrieve records from Creator reports
  - Implement `creator_create_record()` tool with application_name, form_name, and record data
  - Implement `creator_update_record()` tool with record_id and update data
  - All tools should use `api_router.make_request()` with app_name="Creator"
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [x] 9.2 Register Creator tools in main server
  - Import `register_creator_tools` in `src/server.py`
  - Call registration function after router initialization
  - _Requirements: 9.1_

- [x] 9.3 Write tests for Creator tools
  - Test Creator tools are only registered when Creator scope is present
  - Test application and form listing
  - Test record operations
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5_

- [ ] 10. Implement additional Zoho apps support (Sales & Marketing)
  - Create tools modules for SalesIQ, Campaigns, Social, Forms, and Survey
  - Implement core operations for each app
  - _Requirements: 9A.1, 9A.2, 9A.3, 9A.4, 9A.5_

- [ ] 10.1 Create SalesIQ tools module (`src/apps/salesiq_tools.py`)
  - Implement `salesiq_get_visitors()` tool to retrieve visitor tracking data
  - Implement `salesiq_get_chats()` tool to retrieve chat conversations
  - Implement `salesiq_get_chat_transcript()` tool for specific chat details
  - Implement `salesiq_get_leads()` tool to retrieve leads captured through SalesIQ
  - Implement `salesiq_get_operators()` tool to retrieve operator information
  - _Requirements: 9A.1, 9A.2, 9A.3, 9A.4, 9A.5_

- [ ] 10.2 Create Campaigns tools module (`src/apps/campaigns_tools.py`)
  - Implement `campaigns_get_campaigns()` tool to list email campaigns
  - Implement `campaigns_get_campaign_by_id()` tool for campaign details
  - Implement `campaigns_get_mailing_lists()` tool to retrieve mailing lists
  - Implement `campaigns_get_subscribers()` tool with list_id
  - _Requirements: Requirements for marketing automation_

- [ ] 10.3 Create Social tools module (`src/apps/social_tools.py`)
  - Implement `social_get_posts()` tool to retrieve social media posts
  - Implement `social_get_channels()` tool to list connected social channels
  - Implement `social_get_analytics()` tool for social media metrics
  - _Requirements: Requirements for social media management_

- [ ] 10.4 Create Forms tools module (`src/apps/forms_tools.py`)
  - Implement `forms_get_forms()` tool to list all forms
  - Implement `forms_get_form_by_id()` tool for form details
  - Implement `forms_get_submissions()` tool to retrieve form submissions
  - _Requirements: Requirements for form management_

- [ ] 10.5 Create Survey tools module (`src/apps/survey_tools.py`)
  - Implement `survey_get_surveys()` tool to list surveys
  - Implement `survey_get_responses()` tool to retrieve survey responses
  - _Requirements: Requirements for survey management_

- [ ] 10.6 Register all Sales & Marketing tools in main server
  - Import and register all new tool modules
  - _Requirements: 9A.1_

- [ ] 11. Implement Finance & Commerce apps support
  - Create tools modules for Invoice, Expense, Subscriptions, and Commerce
  - Implement core financial operations for each app
  - _Requirements: Requirements for finance apps_

- [ ] 11.1 Create Invoice tools module (`src/apps/invoice_tools.py`)
  - Implement invoice management tools similar to Books but for freelancers
  - _Requirements: Requirements for invoicing_

- [ ] 11.2 Create Expense tools module (`src/apps/expense_tools.py`)
  - Implement expense tracking and reporting tools
  - _Requirements: Requirements for expense management_

- [ ] 11.3 Create Subscriptions tools module (`src/apps/subscriptions_tools.py`)
  - Implement recurring billing and subscription management tools
  - _Requirements: Requirements for subscription management_

- [ ] 11.4 Create Commerce tools module (`src/apps/commerce_tools.py`)
  - Implement e-commerce store management tools
  - _Requirements: Requirements for e-commerce_

- [ ] 11.5 Register all Finance & Commerce tools in main server
  - Import and register all new tool modules
  - _Requirements: Requirements for finance apps_

- [ ] 12. Implement Operations apps support (Fleet, FSM, Bookings)
  - Create tools modules for Fleet, Field Service Management, and Bookings
  - Implement operational management tools
  - _Requirements: 9B.1, 9B.2, 9B.3, 9B.4, 9B.5_

- [ ] 12.1 Create Fleet tools module (`src/apps/fleet_tools.py`)
  - Implement `fleet_get_vehicles()` tool to retrieve vehicle information
  - Implement `fleet_get_vehicle_by_id()` tool for specific vehicle details
  - Implement `fleet_get_trips()` tool to retrieve trip data and routes
  - Implement `fleet_get_drivers()` tool to retrieve driver information
  - Implement `fleet_get_maintenance_records()` tool for vehicle maintenance
  - Implement `fleet_get_fuel_logs()` tool for fuel consumption data
  - _Requirements: 9B.1, 9B.2, 9B.3, 9B.4, 9B.5_

- [ ] 12.2 Create FSM tools module (`src/apps/fsm_tools.py`)
  - Implement field service management and work order tools
  - _Requirements: Requirements for field service_

- [ ] 12.3 Create Bookings tools module (`src/apps/bookings_tools.py`)
  - Implement appointment scheduling and booking management tools
  - _Requirements: Requirements for bookings_

- [ ] 12.4 Register all Operations tools in main server
  - Import and register all new tool modules
  - _Requirements: 9B.1_

- [ ] 13. Implement remaining specialized apps
  - Create tools modules for remaining apps (Collaboration, Productivity, Legal, IoT, etc.)
  - Implement specialized operations for each category
  - _Requirements: Requirements for specialized apps_

- [ ] 13.1 Create Collaboration tools (Connect, Cliq, Meeting, Assist)
  - Implement team collaboration and communication tools
  - _Requirements: Requirements for collaboration_

- [ ] 13.2 Create Productivity tools (Mail, WorkDrive, Writer, Sheet, Show)
  - Implement document and file management tools
  - _Requirements: Requirements for productivity_

- [ ] 13.3 Create Project Management tools (Sprints, BugTracker)
  - Implement agile and bug tracking tools
  - _Requirements: Requirements for project management_

- [ ] 13.4 Create Developer tools (Flow, Catalyst)
  - Implement workflow automation and serverless platform tools
  - _Requirements: Requirements for developer platform_

- [ ] 13.5 Create Legal tools (Sign, Contracts)
  - Implement e-signature and contract management tools
  - _Requirements: Requirements for legal_

- [ ] 13.6 Create IoT tools
  - Implement IoT device management tools
  - _Requirements: Requirements for IoT_

- [ ] 13.7 Register all specialized tools in main server
  - Import and register all remaining tool modules
  - _Requirements: Requirements for specialized apps_

- [-] 14. Update documentation and configuration
  - Update README with multi-app capabilities
  - Create comprehensive usage guide
  - Update environment configuration examples
  - _Requirements: All requirements_

- [x] 14.1 Update README.md
  - Replace "Zoho CRM MCP Server" with "Zoho Ecosystem MCP Server"
  - Add section listing all 40+ supported apps by category
  - Update quick start guide with multi-app scope examples
  - Add examples for different app categories
  - Update feature list to reflect multi-app support
  - _Requirements: All requirements_

- [ ] 14.2 Create comprehensive multi-app guide
  - Create `MULTI_APP_GUIDE.md` with detailed usage for each app category
  - Include scope configuration for each app
  - Provide code examples for common operations in each app
  - Add troubleshooting section for multi-app scenarios
  - _Requirements: All requirements_

- [ ] 14.3 Update .env.example
  - Add comprehensive scope string with all 40+ apps
  - Add comments explaining each app category
  - Provide examples for common app combinations
  - _Requirements: 11.1, 11.5_

- [ ] 14.4 Create app-specific documentation
  - Create individual markdown files for each major app with detailed tool documentation
  - Include API endpoint references and common use cases
  - _Requirements: All requirements_

- [ ] 15. Final integration testing and validation
  - Test multi-app authentication flow
  - Validate all app tools work correctly
  - Test error handling across different apps
  - Verify backward compatibility
  - _Requirements: All requirements_

- [ ] 15.1 Integration testing
  - Test authentication with multi-app scopes
  - Test simultaneous requests to different apps
  - Test app registry correctly identifies enabled apps
  - Test error handling for disabled apps
  - Test rate limiting across multiple apps
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 10.1, 10.2, 10.3, 10.4, 10.5_

- [ ] 15.2 Backward compatibility testing
  - Verify all existing CRM tools still work
  - Test with existing .env configurations
  - Ensure token storage format unchanged
  - _Requirements: All requirements_

- [ ] 15.3 Performance testing
  - Test response times for different apps
  - Verify connection pooling works correctly
  - Test with high request volumes
  - _Requirements: Performance requirements_
