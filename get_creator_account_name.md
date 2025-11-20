# How to Find Your Zoho Creator Account Name

## Method 1: Via Zoho Creator Web Interface

1. **Log in to Zoho Creator:**
   - Go to: https://creator.zoho.com
   - Or from CRM: Click Setup → Developer Hub → Zoho Creator

2. **Find your account name in the URL:**
   - Once logged in, look at the browser URL
   - Format: `https://creator.zoho.com/[YOUR_ACCOUNT_NAME]/`
   - Example: `https://creator.zoho.com/joela123/` → account name is `joela123`

3. **Alternative - Check any existing app:**
   - Open any Creator app you have
   - URL format: `https://creator.zoho.com/[ACCOUNT_NAME]/[APP_NAME]`
   - The part after `creator.zoho.com/` and before the app name is your account name

## Method 2: Via API Console

1. Go to: https://api-console.zoho.com
2. Check your registered apps
3. The Creator account is usually associated with your primary email prefix

## Method 3: Common Patterns

Your account name is usually one of:
- Your email username (part before @)
- Your company name (lowercase, no spaces)
- A custom username you set up

## Once You Have the Account Name:

Run this command:
```bash
python3 report_creator_operations_app.py --account YOUR_ACCOUNT_NAME
```

Or update the .env file:
```bash
# Add this line to .env
ZOHO_CREATOR_ACCOUNT=your_account_name_here
```

## Need Help?

If you can't find your account name:
1. Log in to https://creator.zoho.com
2. Take a screenshot of the URL
3. Or let me know what you see in the URL after logging in
