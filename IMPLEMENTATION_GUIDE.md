# Quote Preview Implementation Guide

## Overview
This solution creates an **editable** quote preview that combines Deal data with Move_Types content in the Quotes module, without requiring Zoho Writer.

---

## Implementation Steps

### Step 1: Add Custom Field to Quotes Module

1. Go to **Setup** (⚙️ icon) > **Customization** > **Modules and Fields**
2. Select **Quotes** module
3. Click **New Field** and create:
   - **Field Label**: `Quote Preview` (or `Quotation Content`)
   - **Field Type**: `Multi Line` with **Rich Text Editor**
   - **API Name**: `Quote_Preview`
   - Click **Save**

4. Drag the new field to your Quote layout where users should edit it

---

### Step 2: Identify the Move_Types Connection

You need to determine how Move_Types connects to Quotes/Deals:

**Check in your CRM:**
- Does the **Deal** have a lookup field to Move_Types?
- Does the **Quote** have a lookup field to Move_Types?
- What is the API name of that field?

**Once you know the field name, update line 30 or 33 in the workflow script accordingly.**

---

### Step 3: Create the Workflow Rule

1. Go to **Setup** > **Automation** > **Workflow Rules**
2. Click **Create Rule**
3. Configure:
   - **Module**: Quotes
   - **Rule Name**: `Auto-Generate Quote Preview`
   - **Description**: `Automatically generates editable quote preview from Deal and Move_Types data`

4. **When**: Choose one of these triggers:
   - ✅ **On Create** - Generates preview when Quote is first created
   - ✅ **On Create or Edit** - Regenerates whenever Quote is updated
   - ✅ **On Field Update** - Only when specific fields change (e.g., Deal_Name field)

5. **Condition**: (Optional) Add condition if needed, e.g.:
   ```
   Deal_Name is not empty
   ```

6. Click **Next**

---

### Step 4: Add the Custom Function Action

1. Under **Instant Actions**, click **Custom Function**
2. Click **New Function**
3. **Function Name**: `GenerateQuotePreview`
4. **Copy the entire code from `quote_preview_workflow.deluge`** into the function editor
5. **IMPORTANT**: Update line 30 with your actual Move_Types lookup field name:
   ```deluge
   moveTypeId = dealInfo.get("YOUR_ACTUAL_FIELD_NAME_HERE");
   ```
   OR if Move_Types is connected to Quote (line 33):
   ```deluge
   moveTypeId = quote.get("YOUR_ACTUAL_FIELD_NAME_HERE");
   ```

6. Click **Save** and **Associate** the function with the workflow
7. **Save** the workflow rule

---

### Step 5: Test the Implementation

1. **Create a new Quote** or **edit an existing Quote** linked to a Deal
2. Check if the `Quote_Preview` field is automatically populated with:
   - Deal information table (Deal Name, Origin, Destination)
   - Quote Main Body content
   - Quote Bottom Body content

3. **Try editing** the content in the Quote_Preview field - it should be fully editable!

---

## How It Works

```
┌─────────────┐
│   Deal      │ (Source: Deal_Name, Origin_Town, etc.)
└──────┬──────┘
       │
       │ Related to
       ▼
┌─────────────┐
│   Quote     │ ◄── Workflow triggers here
└──────┬──────┘
       │
       │ Fetches data from
       ▼
┌─────────────┐
│ Move_Types  │ (Source: Quote_Main_Body, Quote_Bottom_Body)
└──────┬──────┘
       │
       │ Combines all data
       ▼
┌─────────────────────────────┐
│  Quote_Preview Field        │ ← User can edit this!
│  (Rich-Text, Editable)      │
└─────────────────────────────┘
```

---

## Customization Options

### Add More Deal Fields to the Table

In the workflow script, add more rows to the table:

```deluge
quotationHTML = quotationHTML + "<tr>";
quotationHTML = quotationHTML + "<td style='padding: 12px; border: 1px solid #ddd; font-weight: bold;'>Contact Person:</td>";
quotationHTML = quotationHTML + "<td style='padding: 12px; border: 1px solid #ddd;'>" + ifnull(dealInfo.get("Contact_Name"), "") + "</td>";
quotationHTML = quotationHTML + "</tr>";
```

### Change Table Styling

Modify the style attributes in the HTML generation section (lines 60-93):
- Colors: Change `#2c3e50`, `#f8f9fa`, etc.
- Padding: Adjust `padding: 12px`
- Borders: Modify `border: 1px solid #ddd`

### Add Company Logo

Add at the top of the HTML (after line 60):

```deluge
quotationHTML = quotationHTML + "<div style='text-align: center; margin-bottom: 20px;'>";
quotationHTML = quotationHTML + "<img src='YOUR_LOGO_URL' style='max-width: 200px;' />";
quotationHTML = quotationHTML + "</div>";
```

---

## Troubleshooting

### Preview Not Generating?

1. Check workflow execution logs: **Setup** > **Automation** > **Workflow Rules** > View logs
2. Verify the Move_Types field name is correct (line 30/33)
3. Ensure the Quote is actually related to a Deal
4. Check field permissions - make sure workflow has access to all fields

### Preview Not Editable?

1. Verify `Quote_Preview` field type is **Rich Text Editor**
2. Check field-level security: **Setup** > **Security Control** > **Field Permissions**
3. Ensure user profile has edit permission for this field

### Deal Fields Showing Empty?

1. Verify API names match exactly (case-sensitive):
   - `Origin_Town`, `Destination_Town`, `Origin_Street`, `Destination_Street`
2. Check if Deal actually has data in these fields
3. Test with `info` statements to debug:
   ```deluge
   info "Origin Town: " + originTown;
   ```

---

## Next Steps

1. ✅ Implement the custom field
2. ✅ Set up the workflow
3. ✅ Test with sample data
4. 📧 Configure email templates to use `${Quotes.Quote_Preview}` for sending quotes
5. 📄 Add a custom button to convert Quote_Preview to PDF if needed

---

## Questions?

- What is the API name of the field connecting Move_Types to Deals/Quotes?
- Do you want to add more fields to the preview?
- Should the workflow regenerate on every edit, or only on creation?
