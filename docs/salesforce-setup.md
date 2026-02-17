# Salesforce Connected App Setup Guide

## Prerequisites

- Salesforce org (Developer, Sandbox, or Production)
- System Administrator profile or delegated admin permissions
- Access to Salesforce Setup

## Step 1: Create a Connected App

1. Navigate to **Setup → App Manager → New Connected App**
2. Fill in basic information:
   - **Connected App Name**: `AI Assistant Agent`
   - **API Name**: `AI_Assistant_Agent`
   - **Contact Email**: your admin email

3. Enable OAuth Settings:
   - **Enable OAuth Settings**: ✅ Checked
   - **Callback URL**: `https://localhost:8443/callback` (for development)
   - **Selected OAuth Scopes**:
     - `Access and manage your data (api)`
     - `Perform requests on your behalf at any time (refresh_token, offline_access)`
     - `Access unique user identifiers (openid)`
   - **Require Secret for Web Server Flow**: ✅ Checked
   - **Require Secret for Refresh Token Flow**: ✅ Checked

4. Click **Save** → Note the **Consumer Key** and **Consumer Secret**

## Step 2: Configure Security Policies

1. Navigate to the Connected App → **Manage**
2. Set **IP Relaxation**: `Relax IP restrictions` (for dev) or `Enforce IP restrictions` (for prod with IP allowlist)
3. Set **Refresh Token Policy**: `Refresh token is valid until revoked`
4. **Session Policies**: Set timeout appropriate for your security requirements

## Step 3: Permission Set Configuration

Create a Permission Set for AI Assistant users:

1. Navigate to **Setup → Permission Sets → New**
2. Name: `AI Assistant User`
3. Assign the following Object Permissions:

| Object | Read | Create | Edit | Delete |
|--------|------|--------|------|--------|
| Account | ✅ | ❌ | ❌ | ❌ |
| Contact | ✅ | ❌ | ❌ | ❌ |
| Opportunity | ✅ | ❌ | ❌ | ❌ |
| Case | ✅ | ✅ | ✅ | ❌ |
| CaseComment | ✅ | ✅ | ❌ | ❌ |
| Task | ✅ | ✅ | ❌ | ❌ |
| Event | ✅ | ❌ | ❌ | ❌ |
| User | ✅ | ❌ | ❌ | ❌ |
| Lead | ✅ | ❌ | ✅ | ❌ |
| KnowledgeArticleVersion | ✅ | ❌ | ❌ | ❌ |

4. **Connected App Access**: Add the Connected App to this Permission Set
5. Assign the Permission Set to all users who will use the AI Assistant

## Step 4: Field-Level Security (FLS)

Ensure the Permission Set has read access to all fields used by MCP tools:

### Account Fields
`Id, Name, Industry, BillingCity, BillingState, Website, OwnerId, Owner.Name, AnnualRevenue, NumberOfEmployees, Description`

### Contact Fields
`Id, FirstName, LastName, Title, Email, Phone, AccountId`

### Opportunity Fields
`Id, Name, Amount, StageName, CloseDate, Probability, OwnerId, Owner.Name, AccountId, Account.Name, LastActivityDate, IsClosed`

### Case Fields
`Id, CaseNumber, Subject, Description, Status, Priority, Type, CreatedDate, OwnerId, Owner.Name, AccountId, Account.Name`

### Knowledge Article Fields
`Id, Title, Summary, UrlName, LastPublishedDate, ArticleType, PublishStatus, Language, IsLatestVersion, ArticleBody`

## Step 5: IP Allowlisting (Production)

For production deployments:

1. Navigate to **Setup → Network Access**
2. Add trusted IP ranges for your Azure deployment:
   - Azure AI Foundry outbound IPs
   - MCP server hosting IPs (if App Service)
3. Or use **Connected App IP Restrictions** for per-app control

## Step 6: Knowledge Base Configuration

If using Salesforce Knowledge:

1. **Enable Knowledge**: Setup → Knowledge Settings → Enable Salesforce Knowledge
2. **Article Types**: Ensure at least one article type exists
3. **Data Categories**: Configure if using categorized search
4. **Publishing**: Publish sample articles for testing
5. **Permissions**: Grant `ViewAllKnowledge` or appropriate article-type-level permissions

## Step 7: Environment Variables

After setup, configure these environment variables:

```bash
# Salesforce OAuth Credentials
SF_CLIENT_ID=<consumer_key_from_step_1>
SF_CLIENT_SECRET=<consumer_secret_from_step_1>
SF_INSTANCE_URL=https://your-org.my.salesforce.com

# For development/testing only (use OAuth flow in production)
SF_ACCESS_TOKEN=<session_id_or_access_token>

# OAuth callback
SF_REDIRECT_URI=https://localhost:8443/callback
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `INVALID_SESSION_ID` | Refresh the access token or re-authenticate |
| `INSUFFICIENT_ACCESS` | Check Permission Set assignments and FLS |
| `RATE_LIMIT_EXCEEDED` | Reduce query frequency; consider composite API |
| `Knowledge not enabled` | Enable Knowledge in Setup → Knowledge Settings |
| `SOSL not available` | Enable full-text search or fall back to SOQL |
