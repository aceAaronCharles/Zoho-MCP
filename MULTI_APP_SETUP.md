# Zoho Multi-Application MCP Server Configuration

## Overview
This guide will help you configure the MCP server to access multiple Zoho applications beyond just CRM, including:
- Zoho CRM
- Zoho Books (Accounting)
- Zoho Projects
- Zoho Desk
- Zoho People
- Zoho Recruit
- Zoho Inventory
- Zoho Creator
- And more...

## Step 1: Update Your Zoho OAuth Application

### 1.1 Go to Zoho Developer Console
Visit: https://api-console.zoho.com/

### 1.2 Edit Your Existing Application or Create New One
- Click on your application or create a new "Server-based Application"
- Make sure **Authorized Redirect URIs** includes: `http://localhost:8080/callback`

### 1.3 Configure Scopes for Multiple Applications
You need to add scopes for each Zoho application you want to access:

#### CRM Scopes:
```
ZohoCRM.modules.ALL
ZohoCRM.settings.ALL
ZohoCRM.users.ALL
ZohoCRM.org.ALL
```

#### Books (Accounting) Scopes:
```
ZohoBooks.fullaccess.all
```

#### Projects Scopes:
```
ZohoProjects.projects.ALL
ZohoProjects.portals.ALL
ZohoProjects.timesheets.ALL
```

#### Desk (Support) Scopes:
```
Desk.tickets.ALL
Desk.contacts.ALL
Desk.tasks.ALL
Desk.settings.ALL
```

#### People (HR) Scopes:
```
ZohoPeople.forms.ALL
ZohoPeople.attendance.ALL
ZohoPeople.leave.ALL
```

#### Recruit Scopes:
```
ZohoRecruit.modules.ALL
ZohoRecruit.settings.ALL
```

#### Inventory Scopes:
```
ZohoInventory.fullaccess.all
```

#### Creator Scopes:
```
ZohoCreator.form.CREATE
ZohoCreator.report.CREATE
ZohoCreator.report.READ
ZohoCreator.report.UPDATE
ZohoCreator.report.DELETE
```

#### Operations/Analytics Scopes:
```
ZohoAnalytics.fullaccess.all
ZohoOperations.fullaccess.all
```

## Step 2: Update Your .env File

Edit your `.env` file with the comprehensive scopes:

```bash
# Zoho OAuth Configuration
ZOHO_CLIENT_ID=your_client_id_here
ZOHO_CLIENT_SECRET=your_client_secret_here
ZOHO_REDIRECT_URI=http://localhost:8080/callback

# Comprehensive Scopes for Multiple Applications
ZOHO_SCOPE=ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL,ZohoBooks.fullaccess.all,ZohoProjects.projects.ALL,ZohoProjects.portals.ALL,Desk.tickets.ALL,Desk.contacts.ALL,ZohoPeople.forms.ALL,ZohoPeople.attendance.ALL,ZohoRecruit.modules.ALL,ZohoInventory.fullaccess.all,ZohoAnalytics.fullaccess.all,ZohoCreator.report.READ,ZohoCreator.report.CREATE

# API Domains (change if using different data center)
ZOHO_API_DOMAIN=https://www.zohoapis.com
# For EU: https://www.zohoapis.eu
# For India: https://www.zohoapis.in
# For Australia: https://www.zohoapis.com.au
# For Sandbox: https://sandbox.zohoapis.com

ZOHO_ACCOUNTS_DOMAIN=https://accounts.zoho.com
# For EU: https://accounts.zoho.eu
# For India: https://accounts.zoho.in
# For Australia: https://accounts.zoho.com.au

# Token Storage
TOKEN_FILE_PATH=.zoho_tokens.json

# Server Configuration
MCP_SERVER_NAME=ZohoMultiApp
MCP_SERVER_VERSION=1.0.0

# Logging
LOG_LEVEL=INFO
LOG_FILE_PATH=logs/zoho_multi_app.log

# Rate Limiting & Timeout
RATE_LIMIT=100
REQUEST_TIMEOUT=30
```

## Step 3: Common Zoho Operations App Modules

The "Operations" in Zoho typically refers to:

### Zoho Analytics (formerly Zoho Reports)
- Workspace management
- Report generation
- Dashboard creation
- Data visualization

### Zoho Flow
- Workflow automation
- App integrations
- Trigger management

### Zoho Creator
- Custom application builder
- Forms and reports
- Business process automation

## Step 4: API Endpoints for Different Products

### CRM:
```
https://www.zohoapis.com/crm/v2/
```

### Books:
```
https://books.zoho.com/api/v3/
```

### Projects:
```
https://projectsapi.zoho.com/restapi/
```

### Desk:
```
https://desk.zoho.com/api/v1/
```

### Analytics:
```
https://analyticsapi.zoho.com/restapi/v2/
```

### People:
```
https://people.zoho.com/people/api/
```

### Inventory:
```
https://inventory.zoho.com/api/v1/
```

## Step 5: Re-authenticate

After updating your scopes:

1. Delete the old token file:
   ```bash
   rm .zoho_tokens.json
   ```

2. Run the test connection again:
   ```bash
   python3 test_connection.py
   ```

3. When the browser opens, you'll see ALL the permissions you're requesting
4. Accept all permissions
5. The new tokens will be saved with expanded access

## Step 6: Verify Access

After authentication, you can verify which applications you have access to by checking the scopes in your token file:

```bash
cat .zoho_tokens.json | python3 -m json.tool
```

Look for the `scope` field to confirm all requested scopes were granted.

## Notes

- Not all scopes may be available depending on your Zoho subscription plan
- Some applications require separate subscriptions
- The Operations app features are spread across Analytics, Flow, and Creator
- Always test with the minimum required scopes first, then expand as needed
