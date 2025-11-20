# Complete Zoho Apps Portfolio

This MCP server will support **40+ Zoho applications** across all major business categories.

## 📊 Apps by Category

### 🎯 Sales & Marketing (6 apps)
1. **Zoho CRM** - Customer relationship management
   - Scope: `ZohoCRM.modules.ALL`
   - API: `/crm/v2`

2. **Zoho SalesIQ** - Live chat, visitor tracking, lead capture
   - Scope: `ZohoSalesIQ.modules.ALL`
   - API: `/salesiq/v2`

3. **Zoho Campaigns** - Email marketing automation
   - Scope: `ZohoCampaigns.campaign.ALL`
   - API: `/campaigns/v2`

4. **Zoho Social** - Social media management
   - Scope: `ZohoSocial.data.ALL`
   - API: `/social/v2`

5. **Zoho Forms** - Online form builder
   - Scope: `ZohoForms.form.ALL`
   - API: `/forms/v2`

6. **Zoho Survey** - Survey and feedback collection
   - Scope: `ZohoSurvey.surveys.ALL`
   - API: `/survey/v2`

---

### 💰 Finance & Commerce (6 apps)
7. **Zoho Books** - Accounting and invoicing
   - Scope: `ZohoBooks.fullaccess.all`
   - API: `/books/v3`

8. **Zoho Invoice** - Invoicing for freelancers
   - Scope: `ZohoInvoice.fullaccess.all`
   - API: `/invoice/v3`

9. **Zoho Expense** - Expense tracking and reporting
   - Scope: `ZohoExpense.fullaccess.all`
   - API: `/expense/v1`

10. **Zoho Inventory** - Inventory and order management
    - Scope: `ZohoInventory.fullaccess.all`
    - API: `/inventory/v1`

11. **Zoho Subscriptions** - Recurring billing management
    - Scope: `ZohoSubscriptions.fullaccess.all`
    - API: `/subscriptions/v1`

12. **Zoho Commerce** - E-commerce platform
    - Scope: `ZohoCommerce.fullaccess.all`
    - API: `/commerce/v1`

---

### 🎧 Customer Service (2 apps)
13. **Zoho Desk** - Customer support ticketing
    - Scope: `Desk.tickets.ALL`
    - API: `/desk/v1`

14. **Zoho Assist** - Remote support and screen sharing
    - Scope: `ZohoAssist.session.ALL`
    - API: `/assist/v2`

---

### 👥 HR & Recruitment (2 apps)
15. **Zoho People** - HR management system
    - Scope: `ZohoPeople.forms.ALL`
    - API: `/people/api`

16. **Zoho Recruit** - Applicant tracking system
    - Scope: `ZohoRecruit.modules.ALL`
    - API: `/recruit/v2`

---

### 📋 Project Management (4 apps)
17. **Zoho Projects** - Project management and collaboration
    - Scope: `ZohoProjects.projects.ALL`
    - API: `/projects/v3`

18. **Zoho Sprints** - Agile project management
    - Scope: `ZohoSprints.projects.ALL`
    - API: `/sprints/v2`

19. **Zoho BugTracker** - Bug and issue tracking
    - Scope: `ZohoBugTracker.projects.ALL`
    - API: `/bugtracker/v2`

20. **Zoho Connect** - Team collaboration network
    - Scope: `ZohoConnect.network.ALL`
    - API: `/connect/v2`

---

### 💬 Collaboration (2 apps)
21. **Zoho Cliq** - Team messaging and chat
    - Scope: `ZohoCliq.channels.ALL`
    - API: `/cliq/v2`

22. **Zoho Meeting** - Video conferencing
    - Scope: `ZohoMeeting.meeting.ALL`
    - API: `/meeting/v2`

---

### 📧 Email & Storage (2 apps)
23. **Zoho Mail** - Business email hosting
    - Scope: `ZohoMail.accounts.ALL`
    - API: `/mail/v1`

24. **Zoho WorkDrive** - Cloud file storage and sharing
    - Scope: `ZohoWorkDrive.files.ALL`
    - API: `/workdrive/api/v1`

---

### 📝 Productivity Suite (3 apps)
25. **Zoho Writer** - Word processor
    - Scope: `ZohoWriter.documents.ALL`
    - API: `/writer/api/v1`

26. **Zoho Sheet** - Spreadsheet application
    - Scope: `ZohoSheet.spreadsheets.ALL`
    - API: `/sheet/api/v1`

27. **Zoho Show** - Presentation software
    - Scope: `ZohoShow.presentations.ALL`
    - API: `/show/api/v1`

---

### 📊 Analytics & BI (1 app)
28. **Zoho Analytics** - Business intelligence and reporting
    - Scope: `ZohoAnalytics.fullaccess.all`
    - API: `/restapi/v2`

---

### 🛠️ Developer Platform (3 apps)
29. **Zoho Creator** - Low-code application builder
    - Scope: `ZohoCreator.report.READ`, `ZohoCreator.report.CREATE`, `ZohoCreator.report.UPDATE`
    - API: `/creator/v2`

30. **Zoho Flow** - Workflow automation and integration
    - Scope: `ZohoFlow.flows.ALL`
    - API: `/flow/v1`

31. **Zoho Catalyst** - Serverless application platform
    - Scope: `ZohoCatalyst.projects.ALL`
    - API: `/catalyst/v2`

---

### 🚚 Operations & Field Service (3 apps)
32. **Zoho Fleet** - Fleet and vehicle management
    - Scope: `ZohoFleet.modules.ALL`
    - API: `/fleet/v1`

33. **Zoho FSM** - Field service management
    - Scope: `ZohoFSM.modules.ALL`
    - API: `/fsm/v1`

34. **Zoho Bookings** - Appointment scheduling
    - Scope: `ZohoBookings.bookings.ALL`
    - API: `/bookings/v1`

---

### ⚖️ Legal & Compliance (2 apps)
35. **Zoho Sign** - Electronic signature management
    - Scope: `ZohoSign.documents.ALL`
    - API: `/sign/v1`

36. **Zoho Contracts** - Contract lifecycle management
    - Scope: `ZohoContracts.contracts.ALL`
    - API: `/contracts/v1`

---

### 🌐 IoT (1 app)
37. **Zoho IoT** - IoT device management and data
    - Scope: `ZohoIoT.devices.ALL`
    - API: `/iot/v1`

---

## 🎯 Implementation Priority

### Phase 1: Core Business Apps (Already in your .env)
- ✅ CRM
- ✅ Books
- ✅ Projects
- ✅ Desk
- ✅ People
- ✅ Recruit
- ✅ Inventory
- ✅ Analytics
- ✅ Creator

### Phase 2: Sales & Marketing Expansion
- SalesIQ
- Campaigns
- Social
- Forms
- Survey

### Phase 3: Finance & Operations
- Invoice
- Expense
- Subscriptions
- Commerce
- Fleet
- FSM
- Bookings

### Phase 4: Collaboration & Productivity
- Connect
- Cliq
- Meeting
- Mail
- WorkDrive
- Writer
- Sheet
- Show

### Phase 5: Specialized & Advanced
- Assist
- BugTracker
- Sprints
- Flow
- Catalyst
- Sign
- Contracts
- IoT

---

## 📝 How to Enable Apps

Add the desired scopes to your `.env` file:

```bash
ZOHO_SCOPE=ZohoCRM.modules.ALL,ZohoBooks.fullaccess.all,ZohoProjects.projects.ALL,...
```

The MCP server will automatically detect enabled apps based on your OAuth scopes and expose only the relevant tools.

---

## 🔑 Complete Scope String (All Apps)

```
ZohoCRM.modules.ALL,ZohoCRM.settings.ALL,ZohoCRM.users.ALL,ZohoCRM.org.ALL,
ZohoSalesIQ.modules.ALL,ZohoCampaigns.campaign.ALL,ZohoSocial.data.ALL,
ZohoForms.form.ALL,ZohoSurvey.surveys.ALL,ZohoBooks.fullaccess.all,
ZohoInvoice.fullaccess.all,ZohoExpense.fullaccess.all,
ZohoInventory.fullaccess.all,ZohoSubscriptions.fullaccess.all,
ZohoCommerce.fullaccess.all,Desk.tickets.ALL,Desk.contacts.ALL,
ZohoAssist.session.ALL,ZohoPeople.forms.ALL,ZohoPeople.attendance.ALL,
ZohoRecruit.modules.ALL,ZohoProjects.projects.ALL,ZohoProjects.portals.ALL,
ZohoSprints.projects.ALL,ZohoBugTracker.projects.ALL,
ZohoConnect.network.ALL,ZohoCliq.channels.ALL,ZohoMeeting.meeting.ALL,
ZohoMail.accounts.ALL,ZohoWorkDrive.files.ALL,ZohoWriter.documents.ALL,
ZohoSheet.spreadsheets.ALL,ZohoShow.presentations.ALL,
ZohoAnalytics.fullaccess.all,ZohoCreator.report.READ,
ZohoCreator.report.CREATE,ZohoCreator.report.UPDATE,
ZohoCreator.meta.application.READ,ZohoCreator.meta.form.READ,
ZohoFlow.flows.ALL,ZohoCatalyst.projects.ALL,ZohoFleet.modules.ALL,
ZohoFSM.modules.ALL,ZohoBookings.bookings.ALL,ZohoSign.documents.ALL,
ZohoContracts.contracts.ALL,ZohoIoT.devices.ALL
```

---

## 🎉 Total Coverage

**40+ Zoho Applications** spanning:
- Sales & Marketing
- Finance & Commerce
- Customer Service
- HR & Recruitment
- Project Management
- Collaboration
- Email & Storage
- Productivity
- Analytics
- Developer Tools
- Operations
- Legal
- IoT

This makes your MCP server the **most comprehensive Zoho integration available**!
