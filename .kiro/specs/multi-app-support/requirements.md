# Requirements Document

## Introduction

This feature extends the existing Zoho CRM MCP Server to support multiple Zoho applications beyond CRM, including Books, Projects, Desk, People, Recruit, Inventory, Analytics, and Creator. The system will provide a unified MCP interface that allows AI assistants to interact with all configured Zoho apps through a single server, leveraging the already-configured OAuth scopes.

## Glossary

- **MCP Server**: The Model Context Protocol server that provides tools for AI assistants to interact with Zoho services
- **Zoho App**: Any application within the Zoho ecosystem (CRM, Books, Projects, Desk, etc.)
- **API Endpoint**: The base URL path for a specific Zoho application's API
- **Tool**: An MCP function that AI assistants can invoke to perform operations
- **OAuth Scope**: Permission grants that define what Zoho resources the application can access
- **API Domain**: The base URL for Zoho API requests (e.g., https://www.zohoapis.com or https://sandbox.zohoapis.com)

## Requirements

### Requirement 1

**User Story:** As a developer using the MCP server, I want to access multiple Zoho applications through a single server, so that I can manage all my Zoho data from one integration point.

#### Acceptance Criteria

1. WHEN the MCP server initializes, THE MCP Server SHALL load all configured Zoho app scopes from environment variables
2. WHEN an AI assistant requests available apps, THE MCP Server SHALL return a list of all Zoho applications the user has access to based on OAuth scopes
3. WHEN making API requests, THE MCP Server SHALL dynamically route requests to the correct Zoho application endpoint based on the app parameter
4. WHEN a tool is invoked for a specific Zoho app, THE MCP Server SHALL use the appropriate API version and endpoint structure for that app
5. WHEN authentication tokens are managed, THE MCP Server SHALL use a single OAuth token that works across all configured Zoho applications

### Requirement 2

**User Story:** As a user managing financial data, I want to access Zoho Books through the MCP server, so that I can query invoices, bills, customers, and other accounting records via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho Books scope is configured, THE MCP Server SHALL provide tools for accessing Books API endpoints
2. THE MCP Server SHALL support retrieving invoices from Zoho Books with pagination and filtering
3. THE MCP Server SHALL support retrieving customers and vendors from Zoho Books
4. THE MCP Server SHALL support creating and updating invoices in Zoho Books
5. THE MCP Server SHALL support retrieving bills and expenses from Zoho Books

### Requirement 3

**User Story:** As a project manager, I want to access Zoho Projects through the MCP server, so that I can query project data, tasks, and timesheets via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho Projects scope is configured, THE MCP Server SHALL provide tools for accessing Projects API endpoints
2. THE MCP Server SHALL support retrieving all portals and projects from Zoho Projects
3. THE MCP Server SHALL support retrieving tasks from specific projects with filtering
4. THE MCP Server SHALL support creating and updating tasks in Zoho Projects
5. THE MCP Server SHALL support retrieving project timesheets and milestones

### Requirement 4

**User Story:** As a support team member, I want to access Zoho Desk through the MCP server, so that I can query and manage support tickets via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho Desk scope is configured, THE MCP Server SHALL provide tools for accessing Desk API endpoints
2. THE MCP Server SHALL support retrieving tickets from Zoho Desk with status filtering
3. THE MCP Server SHALL support retrieving ticket details including comments and attachments
4. THE MCP Server SHALL support creating new tickets in Zoho Desk
5. THE MCP Server SHALL support updating ticket status and adding comments

### Requirement 5

**User Story:** As an HR manager, I want to access Zoho People through the MCP server, so that I can query employee data and attendance records via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho People scope is configured, THE MCP Server SHALL provide tools for accessing People API endpoints
2. THE MCP Server SHALL support retrieving employee records from Zoho People
3. THE MCP Server SHALL support retrieving attendance data for employees
4. THE MCP Server SHALL support retrieving leave requests and approvals
5. THE MCP Server SHALL support accessing custom forms data from Zoho People

### Requirement 6

**User Story:** As a recruiter, I want to access Zoho Recruit through the MCP server, so that I can query candidate data and job postings via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho Recruit scope is configured, THE MCP Server SHALL provide tools for accessing Recruit API endpoints
2. THE MCP Server SHALL support retrieving candidate records from Zoho Recruit
3. THE MCP Server SHALL support retrieving job openings and their details
4. THE MCP Server SHALL support searching candidates by criteria
5. THE MCP Server SHALL support updating candidate status and adding notes

### Requirement 7

**User Story:** As an inventory manager, I want to access Zoho Inventory through the MCP server, so that I can query stock levels and orders via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho Inventory scope is configured, THE MCP Server SHALL provide tools for accessing Inventory API endpoints
2. THE MCP Server SHALL support retrieving items and their stock levels from Zoho Inventory
3. THE MCP Server SHALL support retrieving sales orders and purchase orders
4. THE MCP Server SHALL support retrieving warehouse information
5. THE MCP Server SHALL support creating and updating inventory items

### Requirement 8

**User Story:** As a data analyst, I want to access Zoho Analytics through the MCP server, so that I can query reports and dashboards via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho Analytics scope is configured, THE MCP Server SHALL provide tools for accessing Analytics API endpoints
2. THE MCP Server SHALL support retrieving available workspaces from Zoho Analytics
3. THE MCP Server SHALL support retrieving reports and their data
4. THE MCP Server SHALL support executing custom SQL queries on Analytics data
5. THE MCP Server SHALL support retrieving dashboard information

### Requirement 9

**User Story:** As a business user, I want to access Zoho Creator applications through the MCP server, so that I can query custom application data via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho Creator scope is configured, THE MCP Server SHALL provide tools for accessing Creator API endpoints
2. THE MCP Server SHALL support retrieving available Creator applications
3. THE MCP Server SHALL support retrieving forms and their metadata
4. THE MCP Server SHALL support retrieving records from Creator reports
5. THE MCP Server SHALL support creating and updating records in Creator applications

### Requirement 9A

**User Story:** As a sales or support team member, I want to access Zoho SalesIQ through the MCP server, so that I can query visitor data, chat transcripts, and lead tracking information via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho SalesIQ scope is configured, THE MCP Server SHALL provide tools for accessing SalesIQ API endpoints
2. THE MCP Server SHALL support retrieving visitor information and tracking data
3. THE MCP Server SHALL support retrieving chat conversations and transcripts
4. THE MCP Server SHALL support retrieving leads captured through SalesIQ
5. THE MCP Server SHALL support retrieving operator and department information

### Requirement 9B

**User Story:** As a fleet manager, I want to access Zoho Fleet through the MCP server, so that I can query vehicle data, trip information, and driver details via AI assistants.

#### Acceptance Criteria

1. WHEN Zoho Fleet scope is configured, THE MCP Server SHALL provide tools for accessing Fleet API endpoints
2. THE MCP Server SHALL support retrieving vehicle information and status
3. THE MCP Server SHALL support retrieving trip data and routes
4. THE MCP Server SHALL support retrieving driver information and assignments
5. THE MCP Server SHALL support retrieving maintenance records and fuel logs

### Requirement 10

**User Story:** As a developer, I want comprehensive error handling across all Zoho apps, so that I can understand and resolve issues when API calls fail.

#### Acceptance Criteria

1. WHEN an API call fails for any Zoho app, THE MCP Server SHALL return a structured error response with status code and message
2. WHEN an unsupported Zoho app is requested, THE MCP Server SHALL return a clear error indicating the app is not configured
3. WHEN rate limits are exceeded, THE MCP Server SHALL return a specific rate limit error with retry information
4. WHEN authentication fails, THE MCP Server SHALL return an authentication error with guidance for re-authentication
5. THE MCP Server SHALL log all errors with sufficient detail for debugging while protecting sensitive information

### Requirement 11

**User Story:** As a system administrator, I want to configure which Zoho apps are enabled, so that I can control access and reduce complexity for specific use cases.

#### Acceptance Criteria

1. THE MCP Server SHALL read OAuth scopes from environment variables to determine enabled apps
2. THE MCP Server SHALL provide a tool to list all currently enabled Zoho applications
3. WHEN a tool is invoked for a disabled app, THE MCP Server SHALL return an error indicating the app is not enabled
4. THE MCP Server SHALL validate that required scopes are present before exposing app-specific tools
5. THE MCP Server SHALL support both production and sandbox API domains for all apps
