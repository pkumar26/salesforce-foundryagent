# Salesforce Setup Quickstart for New Users

A step-by-step guide to get your Salesforce credentials configured for the **Salesforce AI Assistant** project. By the end of this guide, you will have all five environment variables populated in your `.env` file.

---

## Table of Contents

1. [Get a Salesforce Org](#1-get-a-salesforce-org)
2. [Find Your Instance URL (`SF_INSTANCE_URL`)](#2-find-your-instance-url)
3. [Create a Connected App (`SF_CONSUMER_KEY` + `SF_CONSUMER_SECRET`)](#3-create-a-connected-app)
4. [Configure Security Policies](#4-configure-security-policies)
5. [Set Permissions for the Integration User](#5-set-permissions-for-the-integration-user)
6. [Get an Access Token (`SF_ACCESS_TOKEN`)](#6-get-an-access-token)
7. [Configure Your `.env` File](#7-configure-your-env-file)
8. [Verify the Connection](#8-verify-the-connection)
9. [Token Refresh & Expiry](#9-token-refresh--expiry)
10. [IP Allowlisting (Production)](#10-ip-allowlisting-production)
11. [Troubleshooting](#11-troubleshooting)
12. [Appendix: Required Object & Field Permissions](#appendix-required-object--field-permissions)

---

## 1. Get a Salesforce Org

If you don't already have a Salesforce org, sign up for a **free Developer Edition**:

1. Go to **<https://developer.salesforce.com/signup>**
2. Fill in the form (use your work email)
3. Check your inbox and verify the email
4. Set your password at the link provided

> **Tip**: Developer Edition orgs include API access and sample data — perfect for local development and testing.

---

## 2. Find Your Instance URL

The `SF_INSTANCE_URL` is your Salesforce domain — the base URL you see when logged in.

### How to find it

**Option A — From the browser address bar:**

After logging in, your URL will look like one of these:

| Org Type | Example URL |
|----------|-------------|
| Developer Edition | `https://yourname-dev-ed.develop.my.salesforce.com` |
| Sandbox | `https://mycompany--sandbox.sandbox.my.salesforce.com` |
| Production | `https://mycompany.my.salesforce.com` |

Copy everything up to `.salesforce.com` (no trailing slash).

**Option B — From Setup:**

1. Click the **gear icon** → **Setup**
2. In the Quick Find box, search for **My Domain**
3. Your domain is shown under **My Domain Name**

**Option C — Using Salesforce CLI:**

```bash
sf org display --target-org my-org --json | grep instanceUrl
```

### Set it in `.env`

```dotenv
SF_INSTANCE_URL=https://yourname-dev-ed.develop.my.salesforce.com
```

---

## 3. Create a Connected App

A **Connected App** gives you the `SF_CONSUMER_KEY` and `SF_CONSUMER_SECRET` needed for OAuth authentication.

### Step-by-step

1. Log in to Salesforce → click **gear icon** → **Setup**
2. In the Quick Find box, search for **App Manager**
3. Click **New Connected App** (top-right)

4. Fill in the **Basic Information**:
   - **Connected App Name**: `AI Assistant Agent`
   - **API Name**: `AI_Assistant_Agent` (auto-fills)
   - **Contact Email**: your email address

5. Under **API (Enable OAuth Settings)**:
   - ✅ **Enable OAuth Settings**
   - **Callback URL**: `https://localhost:8443/callback`
   - Add these **Selected OAuth Scopes**:
     - `Access and manage your data (api)`
     - `Perform requests on your behalf at any time (refresh_token, offline_access)`
     - `Access unique user identifiers (openid)`
   - ✅ **Require Secret for Web Server Flow**
   - ✅ **Require Secret for Refresh Token Flow**

6. Click **Save**

7. ⏳ **Wait 2–10 minutes** — Salesforce needs time to activate the Connected App

8. Go back to **App Manager** → find `AI Assistant Agent` → click the dropdown arrow on the right → **View**

9. Copy the credentials:
   - **Consumer Key** → this is your `SF_CONSUMER_KEY`
   - **Consumer Secret** → click **Click to reveal** → this is your `SF_CONSUMER_SECRET`

### Set them in `.env`

```dotenv
SF_CONSUMER_KEY=3MVG9rZjd7MXFdLh...your_full_key_here
SF_CONSUMER_SECRET=E11E79925017125B...your_full_secret_here
```

### Set the Callback URL

For local development, use:

```dotenv
SF_CALLBACK_URL=https://localhost:8443/callback
```

> This must **exactly match** the Callback URL configured in your Connected App.

---

## 4. Configure Security Policies

After creating the Connected App, configure its security policies:

1. Navigate to **Setup → App Manager** → find `AI Assistant Agent` → click the dropdown → **Manage**
2. Set **IP Relaxation**:
   - **Development**: `Relax IP restrictions`
   - **Production**: `Enforce IP restrictions` (with an IP allowlist — see [Section 10](#10-ip-allowlisting-production))
3. Set **Refresh Token Policy**: `Refresh token is valid until revoked`
4. Set **Session Policies**: Configure timeout appropriate for your security requirements (e.g., 2 hours for dev, 30 minutes for prod)

---

## 5. Set Permissions for the Integration User

The user whose token you'll use needs read access to all objects the AI Assistant queries.

### Create a Permission Set

1. **Setup** → search **Permission Sets** → click **New**
2. **Label**: `AI Assistant User`
3. Click **Save**

4. Click **Object Settings** and configure:

   | Object | Read | Create | Edit |
   |--------|------|--------|------|
   | Account | ✅ | — | — |
   | Contact | ✅ | — | — |
   | Opportunity | ✅ | — | — |
   | Case | ✅ | ✅ | ✅ |
   | CaseComment | ✅ | ✅ | — |
   | Task | ✅ | ✅ | — |
   | Event | ✅ | — | — |
   | User | ✅ | — | — |
   | Lead | ✅ | — | ✅ |
   | Knowledge Article | ✅ | — | — |

5. **Connected App Access**: Add the `AI Assistant Agent` Connected App
6. **Assign** the Permission Set to the user(s) who will run the assistant

### Enable Salesforce Knowledge (if using KB tools)

1. **Setup** → search **Knowledge Settings**
2. ✅ **Enable Salesforce Knowledge**
3. Create/publish at least one article for testing
4. Grant `ViewAllKnowledge` permission or article-type-level access

---

## 6. Get an Access Token

The `SF_ACCESS_TOKEN` is used for local development and demo mode instead of going through the full OAuth flow.

> **⚠️ Security Note**: Access tokens expire (typically after 2 hours). For production deployments, use the full OAuth flow with `SF_CONSUMER_KEY` / `SF_CONSUMER_SECRET` instead.

### Method A: Salesforce CLI (Recommended)

```bash
# Install the Salesforce CLI (if not already installed)
brew install sf          # macOS
# or: npm install -g @salesforce/cli

# Log in to your org (opens a browser)
sf org login web --alias my-org --instance-url https://yourname-dev-ed.develop.my.salesforce.com

# Display the org info (includes access token)
sf org display --target-org my-org --json
```

In the JSON output, look for:

```json
{
  "result": {
    "accessToken": "00DXX000000XXXXX!AQEAQ...",
    "instanceUrl": "https://yourname-dev-ed.develop.my.salesforce.com",
    ...
  }
}
```

Copy the `accessToken` value.

### Method B: Developer Console (Quick & dirty)

1. Log in to Salesforce
2. Click your **avatar** (top-right) → **Developer Console**
3. Go to **Debug** → **Open Execute Anonymous Window**
4. Paste and run:
   ```apex
   System.debug(UserInfo.getSessionId());
   ```
5. Open the debug log → find the `DEBUG|00DXX...` line → that's your token

### Method C: cURL (Username-Password OAuth)

```bash
curl -X POST "https://YOUR_INSTANCE.my.salesforce.com/services/oauth2/token" \
  -d "grant_type=password" \
  -d "client_id=YOUR_CONSUMER_KEY" \
  -d "client_secret=YOUR_CONSUMER_SECRET" \
  -d "username=YOUR_SALESFORCE_USERNAME" \
  -d "password=YOUR_PASSWORD_PLUS_SECURITY_TOKEN"
```

> **Password + Security Token**: Salesforce requires your password concatenated with your security token (e.g., `MyPassword123XYZTOKEN`). To reset your security token: **Setup** → **Reset My Security Token**.

The response:

```json
{
  "access_token": "00DXX000000XXXXX!AQEAQ...",
  "instance_url": "https://yourname-dev-ed.develop.my.salesforce.com",
  "token_type": "Bearer"
}
```

### Set it in `.env`

```dotenv
SF_ACCESS_TOKEN=00DXX000000XXXXX!AQEAQ...your_full_token_here
```

---

## 7. Configure Your `.env` File

After collecting all values, your Salesforce section in `.env` should look like this:

```dotenv
# -----------------------------------------------------------------------------
# Salesforce OAuth (Connected App)
# -----------------------------------------------------------------------------
SF_CONSUMER_KEY=3MVG9rZjd7MXFdLh...
SF_CONSUMER_SECRET=E11E7992501712...
SF_INSTANCE_URL=https://yourname-dev-ed.develop.my.salesforce.com
SF_CALLBACK_URL=https://localhost:8443/callback

# -----------------------------------------------------------------------------
# Salesforce Direct Token (Development/Demo Only)
# -----------------------------------------------------------------------------
SF_ACCESS_TOKEN=00DXX000000XXXXX!AQEAQ...
```

### Quick checklist

- [ ] `SF_INSTANCE_URL` starts with `https://` and has no trailing slash
- [ ] `SF_CONSUMER_KEY` is the full key (usually starts with `3MVG9`)
- [ ] `SF_CONSUMER_SECRET` is the revealed secret (64-char hex string)
- [ ] `SF_CALLBACK_URL` matches exactly what's in the Connected App
- [ ] `SF_ACCESS_TOKEN` is a fresh token (not expired)

---

## 8. Verify the Connection

### Quick verification with Python

```bash
source .venv/bin/activate
python -c "
from simple_salesforce import Salesforce
import os
from dotenv import load_dotenv

load_dotenv()
sf = Salesforce(
    instance_url=os.getenv('SF_INSTANCE_URL'),
    session_id=os.getenv('SF_ACCESS_TOKEN'),
    version='62.0'
)
result = sf.query('SELECT Id, Name FROM Account LIMIT 3')
print(f'✅ Connected! Found {result[\"totalSize\"]} accounts:')
for r in result['records']:
    print(f'   - {r[\"Name\"]}')
"
```

### Verify with Salesforce CLI

```bash
sf data query --query "SELECT Id, Name FROM Account LIMIT 3" --target-org my-org
```

### Run project contract tests

```bash
source .venv/bin/activate
pytest tests/contract/ -v
```

---

## 9. Token Refresh & Expiry

| Token Type | Lifetime | Refresh Strategy |
|-----------|----------|-----------------|
| `SF_ACCESS_TOKEN` (Session ID) | ~2 hours | Re-run `sf org display` to get a new one |
| `SF_ACCESS_TOKEN` (OAuth access token) | ~2 hours | Use refresh token flow (automatic in production) |
| Refresh Token | Until revoked | Stored and used by the OAuth flow in `shared/auth.py` |

### Refreshing an expired token

```bash
# Quickest way — re-auth and get a new token
sf org login web --alias my-org --instance-url $SF_INSTANCE_URL
sf org display --target-org my-org --json | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data['result']['accessToken'])
"
```

Then update `SF_ACCESS_TOKEN` in your `.env` file.

> **Production note**: When deployed to Azure, the application uses the full OAuth 2.0 Authorization Code flow via `SF_CONSUMER_KEY` and `SF_CONSUMER_SECRET` — tokens are refreshed automatically. See `shared/auth.py`.

---

## 10. IP Allowlisting (Production)

For production deployments, restrict API access to known IP ranges:

1. Navigate to **Setup → Network Access**
2. Add trusted IP ranges for your Azure deployment:
   - Azure AI Foundry outbound IPs
   - MCP server hosting IPs (App Service or Container Apps)
3. Or use **Connected App IP Restrictions** for per-app control (configured in [Section 4](#4-configure-security-policies))

> **Tip**: To find your Azure outbound IPs, check the Azure Portal under your App Service → **Properties** → **Outbound IP Addresses**, or for Container Apps, check the environment's static IP.

---

## 11. Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| `INVALID_SESSION_ID` | Token expired or malformed | Re-run `sf org display` and update `SF_ACCESS_TOKEN` |
| `INSUFFICIENT_ACCESS_OR_READONLY` | Missing object/field permissions | Check Permission Set assignments (Step 5) |
| `INVALID_CLIENT_ID` | Wrong Consumer Key | Verify `SF_CONSUMER_KEY` in Connected App → View |
| `INVALID_CLIENT_CREDENTIALS` | Wrong Consumer Secret | Re-copy `SF_CONSUMER_SECRET` (click "Reveal") |
| `RATE_LIMIT_EXCEEDED` | Too many API calls | Wait and retry; check API usage in Setup → Company Information |
| `redirect_uri_mismatch` | Callback URL doesn't match | Ensure `SF_CALLBACK_URL` exactly matches the Connected App |
| `Knowledge not enabled` | Salesforce Knowledge not turned on | Setup → Knowledge Settings → Enable |
| `UNABLE_TO_LOCK_ROW` | Concurrent data modification | Retry the operation |
| Connection timeout | Network/firewall issue | Check VPN, proxy, or IP allowlist settings |

### Common gotchas

- **Connected App activation delay**: After creating a Connected App, wait **2–10 minutes** before using the credentials.
- **Security Token in password**: For username-password OAuth, append your security token to your password (e.g., `password123TOKEN`).
- **Sandbox URLs**: Sandbox instances use `--sandbox.sandbox.my.salesforce.com`, not the production domain.
- **API version**: This project uses Salesforce API **v62.0**. Ensure your org supports it (Spring '25+).
- **IP restrictions**: If you get `INVALID_IP_RANGE` errors, check your Connected App IP Relaxation setting ([Section 4](#4-configure-security-policies)) and Network Access allowlist ([Section 10](#10-ip-allowlisting-production)).

---

## Appendix: Required Object & Field Permissions

These are the Salesforce objects and fields accessed by the MCP tools. Your integration user must have read access to all of them.

### Account
`Id`, `Name`, `Industry`, `BillingCity`, `BillingState`, `Website`, `OwnerId`, `Owner.Name`, `AnnualRevenue`, `NumberOfEmployees`, `Description`

### Contact
`Id`, `FirstName`, `LastName`, `Title`, `Email`, `Phone`, `AccountId`

### Opportunity
`Id`, `Name`, `Amount`, `StageName`, `CloseDate`, `Probability`, `OwnerId`, `Owner.Name`, `AccountId`, `Account.Name`, `LastActivityDate`, `IsClosed`

### Case
`Id`, `CaseNumber`, `Subject`, `Description`, `Status`, `Priority`, `Type`, `CreatedDate`, `OwnerId`, `Owner.Name`, `AccountId`, `Account.Name`

### Task / Event
`Id`, `Subject`, `Status`, `Priority`, `ActivityDate`, `OwnerId`, `WhatId`, `WhoId`

### Lead
`Id`, `FirstName`, `LastName`, `Company`, `Status`, `Email`, `Phone`, `OwnerId`

### User
`Id`, `Name`, `Email`, `IsActive`, `Profile.Name`

### Knowledge Article (KnowledgeArticleVersion)
`Id`, `Title`, `Summary`, `UrlName`, `LastPublishedDate`, `ArticleType`, `PublishStatus`, `Language`, `IsLatestVersion`, `ArticleBody`

---

## Summary of Environment Variables

| Variable | Required | Where to Get It | Example |
|----------|----------|-----------------|---------|
| `SF_CONSUMER_KEY` | For OAuth | Connected App → View → Consumer Key | `3MVG9rZjd7MXFdLh...` |
| `SF_CONSUMER_SECRET` | For OAuth | Connected App → View → Consumer Secret | `E11E799250171...` |
| `SF_INSTANCE_URL` | ✅ Yes | Browser URL bar or Setup → My Domain | `https://mycompany.my.salesforce.com` |
| `SF_CALLBACK_URL` | For OAuth | Must match Connected App config | `https://localhost:8443/callback` |
| `SF_ACCESS_TOKEN` | For dev/demo | `sf org display --json` or Developer Console | `00DXX000000XXXXX!AQEAQ...` |
