# Quick Setup Checklist ✅

## Your Configuration:
- **Deal Lookup Field**: `Service_Type` (connects Deal → Move_Types)
- **Move_Types Fields**: `Quote_Main_Body`, `Quote_Bottom_Body`
- **Deal Fields**: `Deal_Name`, `Origin_Town`, `Destination_Town`, `Origin_Street`, `Destination_Street`

---

## Setup Steps (15 minutes)

### ☐ Step 1: Add Custom Field to Quotes Module (3 min)
1. Go to **Setup** > **Customization** > **Modules and Fields** > **Quotes**
2. Click **New Field**
3. Select **Multi Line** field type
4. Enable **Rich Text Editor** ✓
5. **Field Label**: `Quote Preview`
6. **API Name**: `Quote_Preview`
7. Click **Save**
8. Drag field to your Quote layout

---

### ☐ Step 2: Create Workflow Rule (5 min)
1. Go to **Setup** > **Automation** > **Workflow Rules**
2. Click **Create Rule**
3. **Module**: Quotes
4. **Rule Name**: `Auto-Generate Quote Preview`
5. **Description**: `Generates editable quote preview from Deal and Move_Types`
6. **Execute**: Choose your preferred trigger:
   - ✅ **On Create** (recommended)
   - ⚠️ **On Create or Edit** (regenerates every time)
   - 📌 **On Field Update** → Select `Deal_Name` field
7. **Condition**: Leave blank or add: `Deal_Name is not null`
8. Click **Next**

---

### ☐ Step 3: Add Custom Function (5 min)
1. Under **Instant Actions**, click **+ Custom Function**
2. Click **New Function**
3. **Function Name**: `GenerateQuotePreview`
4. **Display Name**: `Generate Quote Preview`
5. Copy the **ENTIRE content** from `FINAL_quote_preview_workflow.deluge`
6. Paste into the function editor
7. Click **Save**
8. The function should automatically associate with your workflow
9. Click **Save** on the workflow

---

### ☐ Step 4: Test It! (2 min)
1. Open or create a **Quote** that's linked to a **Deal**
2. Make sure the Deal has:
   - A `Service_Type` selected (Move_Types record)
   - Deal_Name, Origin_Town, Destination_Town filled in
3. Make sure the Move_Types record has content in:
   - Quote_Main_Body
   - Quote_Bottom_Body
4. Save the Quote
5. Check the `Quote_Preview` field - it should auto-populate! 🎉
6. **Try editing** the preview content - you should be able to change it freely

---

## Expected Result:

Your Quote_Preview field should show:

```
┌─────────────────────────────────────────┐
│     Quotation Details                   │
├─────────────────────────────────────────┤
│ Deal Name:           [Deal_Name]        │
│ Origin Location:     [Street], [Town]   │
│ Destination Location: [Street], [Town]  │
└─────────────────────────────────────────┘

Quote Details
[Content from Quote_Main_Body]

─────────────────────────────────
[Content from Quote_Bottom_Body]
```

**And it's fully editable!** ✏️

---

## Troubleshooting

### ❌ Preview not generating?
- Check **Setup** > **Automation** > **Workflow Rules** > [Your Rule] > View Logs
- Verify the Quote is actually linked to a Deal
- Verify the Deal has Service_Type filled in

### ❌ Deal data showing empty?
- Confirm Deal fields are named exactly: `Origin_Town`, `Destination_Town`, `Origin_Street`, `Destination_Street`
- Check if Deal actually has data in these fields

### ❌ Move_Types content not showing?
- Verify Move_Types record has content in `Quote_Main_Body` and `Quote_Bottom_Body`
- Check if Deal's `Service_Type` field is populated

### ❌ Can't edit the preview?
- Ensure `Quote_Preview` field type is **Multi Line with Rich Text Editor**
- Check field permissions: **Setup** > **Security Control** > **Field Permissions**

---

## Next Steps

### 📧 Send Quotes via Email
In your email templates, use the merge field:
```
${Quotes.Quote_Preview}
```

### 🔄 Add More Fields
Edit the workflow function to add more Deal fields to the table (see IMPLEMENTATION_GUIDE.md)

### 🎨 Customize Styling
Modify the HTML/CSS in lines 65-98 of the workflow script

### 📄 PDF Export
Add a button to convert Quote_Preview to PDF using Zoho CRM's built-in PDF generation

---

## Support Files
- **FINAL_quote_preview_workflow.deluge** - Ready-to-use script (configured for Service_Type)
- **IMPLEMENTATION_GUIDE.md** - Detailed documentation with customization options

---

## ✅ Done!
Once tested successfully, your users can:
1. Create/edit Quotes
2. Preview auto-generated quotation content
3. Edit any part of the preview before sending
4. Send professional quotes without Zoho Writer complexity
