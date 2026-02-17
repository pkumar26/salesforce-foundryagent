# Data Model: Salesforce AI Assistant

**Date**: 2026-02-16 | **Phase**: 1 (Design & Contracts)
**Source**: Feature spec FR-001 through FR-020 and Salesforce Data Interactions table

---

## 1. Salesforce Object Model

The AI assistant interacts with 12 Salesforce standard objects. This section documents each entity, relevant fields, relationships, validation rules, and access direction.

### 1.1 Account

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | All account tools |
| Name | String(255) | Account name | `get_account`, `search_accounts` |
| Industry | Picklist | Industry classification | `search_accounts` filter |
| Type | Picklist | Customer/Partner/Prospect | `get_account` display |
| AnnualRevenue | Currency | Annual revenue | `get_account` display, risk analysis |
| BillingCity | String | Billing city | `get_account` display |
| BillingState | String | Billing state | `get_account` display |
| OwnerId | Reference(User) | Account owner | `search_accounts` filter |
| Owner.Name | String | Owner name (relationship) | `get_account` display |
| Description | TextArea | Account description | `get_account` display |

**Relationships**:
- Parent of: Contact (1:N via AccountId), Opportunity (1:N via AccountId), Case (1:N via AccountId)
- Referenced by: Task.WhatId, Event.WhatId

**Access**: Read-only

---

### 1.2 Contact

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | All contact tools |
| Name | String | Full name (FirstName + LastName) | `get_contacts_for_account` |
| Title | String(128) | Job title | Display |
| Email | Email | Email address | Display |
| Phone | Phone | Phone number | Display |
| AccountId | Reference(Account) | Parent account | Filter |
| LastActivityDate | Date | Date of last activity | Sorting |

**Relationships**:
- Child of: Account (via AccountId)
- Related to: OpportunityContactRole (via ContactId)
- Referenced by: Task.WhoId, Event.WhoId

**Access**: Read-only

---

### 1.3 Lead

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | All lead tools |
| Name | String | Full name | `get_leads` display |
| Company | String(255) | Company name | `get_leads` display |
| Status | Picklist | Lead status (e.g., Open, Working, Qualified) | `get_leads` filter, `update_lead_status` |
| LeadSource | Picklist | Source channel | `get_leads` filter |
| Email | Email | Email address | Display |
| OwnerId | Reference(User) | Lead owner | Filter |
| CreatedDate | DateTime | Creation timestamp | Sorting |

**Validation Rules**:
- Status transitions: Only forward transitions allowed (Open → Working → Qualified/Unqualified)
- `update_lead_status` must validate target status is a valid forward transition

**Access**: Read + Write (Status updates via `update_lead_status`)

---

### 1.4 Opportunity

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | All opportunity tools |
| Name | String(120) | Deal name | Display |
| Amount | Currency | Deal amount | Pipeline aggregation, risk analysis |
| StageName | Picklist | Current stage | Pipeline grouping, risk analysis |
| CloseDate | Date | Expected close date | Risk flagging (overdue detection) |
| Probability | Percent | Win probability | Risk analysis |
| IsClosed | Boolean | Whether deal is closed | Filter (exclude closed) |
| OwnerId | Reference(User) | Deal owner | Pipeline scoping |
| Owner.Name | String | Owner name (relationship) | Display |
| AccountId | Reference(Account) | Related account | Display |
| Account.Name | String | Account name (relationship) | Display |
| LastActivityDate | Date | Date of last activity | Risk flagging (inactivity detection) |
| CreatedDate | DateTime | Creation timestamp | Risk analysis (aging) |

**Relationships**:
- Child of: Account (via AccountId)
- Parent of: OpportunityContactRole (1:N), OpportunityLineItem (1:N)
- Referenced by: Task.WhatId, Event.WhatId

**Risk Analysis Fields** (used by `get_pipeline_summary`):
- `CloseDate < TODAY` → overdue flag
- `LastActivityDate` older than threshold → stale flag
- `StageName` unchanged for > N days → stuck flag
- Thresholds defined in `config/risk_thresholds.yaml`

**Access**: Read-only

---

### 1.5 Case

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | All case tools |
| CaseNumber | String | Auto-generated case number | `get_case` lookup |
| Subject | String(255) | Case subject | Display, triage |
| Description | TextArea | Full case description | Triage analysis |
| Status | Picklist | Case status | Filter, `update_case` |
| Priority | Picklist | Priority level (High/Medium/Low) | Triage, `update_case` |
| Type | Picklist | Case category/type | Triage, `update_case` |
| CreatedDate | DateTime | Creation timestamp | Sorting, SLA tracking |
| OwnerId | Reference(User) | Case owner | Filter |
| Owner.Name | String | Owner name (relationship) | Display |
| AccountId | Reference(Account) | Related account | Display |
| Account.Name | String | Account name (relationship) | Display |

**Relationships**:
- Child of: Account (via AccountId)
- Parent of: CaseComment (1:N)

**State Transitions** (for `update_case`):
- New → Working → Escalated → Closed
- Any status → Closed (close path always available)
- Closed → Reopened (if business rule allows)

**Access**: Read + Write (`create_case`, `update_case`)

---

### 1.6 CaseComment

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | Display |
| ParentId | Reference(Case) | Parent case | Subquery filter |
| CommentBody | TextArea | Comment text | Display |
| IsPublished | Boolean | Visible to customer? | Filter |
| CreatedDate | DateTime | Creation timestamp | Sorting |

**Relationships**:
- Child of: Case (via ParentId, subquery)

**Access**: Read (via Case subquery) + Write (via `update_case` comment parameter)

---

### 1.7 KnowledgeArticleVersion

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Article version ID | `get_article_by_id` |
| KnowledgeArticleId | ID | Master article ID | Linking |
| Title | String(255) | Article title | Search results display |
| Summary | TextArea | Article summary | Search results display |
| UrlName | String | URL-safe article name | Link generation |
| ArticleBody | RichText | Full article content | `get_article_by_id` |
| PublishStatus | Picklist | Online/Draft/Archived | Filter (Online only) |
| Language | Picklist | Article language | Filter (en_US) |
| LastPublishedDate | DateTime | Last publish timestamp | Sorting |
| ArticleType | String | Article type/category | Display |

**Access**: Read-only (via SOQL structured search or SOSL full-text search)

**Search Strategy**:
- Structured search: SOQL `WHERE Title LIKE '%keyword%'`
- Full-text search: SOSL `FIND {keyword} RETURNING KnowledgeArticleVersion(...)`
- SOSL preferred for relevance-ranked results

---

### 1.8 Task

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | Display |
| Subject | String(255) | Task subject | Display |
| Status | Picklist | Task status | Display |
| ActivityDate | Date | Due date | Display, sorting |
| WhoId | Reference(Contact/Lead) | Related person | Filter |
| WhatId | Reference(Account/Opportunity) | Related object | Filter |
| OwnerId | Reference(User) | Task owner | Filter |
| Description | TextArea | Task description | Display |
| CreatedDate | DateTime | Creation timestamp | Filter, sorting |

**Access**: Read + Write (`get_recent_activities`, `create_task`)

---

### 1.9 Event

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | Display |
| Subject | String(255) | Event subject | Display |
| StartDateTime | DateTime | Event start | Sorting, display |
| EndDateTime | DateTime | Event end | Display |
| WhoId | Reference(Contact/Lead) | Related person | Filter |
| WhatId | Reference(Account/Opportunity) | Related object | Filter |
| Location | String(255) | Event location | Display |
| Description | TextArea | Event description | Display |
| OwnerId | Reference(User) | Event owner | Filter |

**Access**: Read-only

---

### 1.10 User

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | All ownership filters |
| Name | String | Full name | Display |
| ManagerId | Reference(User) | Manager user | `get_team_members` hierarchy query |
| IsActive | Boolean | Active user flag | Filter |
| Profile.Name | String | Profile name (relationship) | Display |

**Access**: Read-only

---

### 1.11 OpportunityContactRole

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | N/A |
| ContactId | Reference(Contact) | Related contact | Join |
| OpportunityId | Reference(Opportunity) | Related opportunity | Join |
| Role | Picklist | Role (Decision Maker, etc.) | Display |
| IsPrimary | Boolean | Primary contact flag | Sorting |

**Access**: Read-only (via Contact subquery)

---

### 1.12 OpportunityLineItem

| Field | Type | Description | Used By |
|-------|------|-------------|---------|
| Id | ID | Salesforce record ID | N/A |
| OpportunityId | Reference(Opportunity) | Parent opportunity | Subquery |
| Product2.Name | String | Product name (relationship) | Display |
| Quantity | Double | Units | Display |
| TotalPrice | Currency | Line total | Display |

**Access**: Read-only (via Opportunity subquery)

---

## 2. Pydantic Models (`shared/models.py`)

These models are used by MCP tool handlers for structured responses.

```python
from pydantic import BaseModel, Field
from typing import Optional
from datetime import date, datetime

class AccountSummary(BaseModel):
    id: str = Field(description="Salesforce Account ID")
    name: str
    industry: Optional[str] = None
    type: Optional[str] = None
    annual_revenue: Optional[float] = None
    billing_city: Optional[str] = None
    billing_state: Optional[str] = None
    owner_name: Optional[str] = None

class ContactSummary(BaseModel):
    id: str = Field(description="Salesforce Contact ID")
    name: str
    title: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: Optional[str] = Field(None, description="Opportunity contact role")

class OpportunitySummary(BaseModel):
    id: str = Field(description="Salesforce Opportunity ID")
    name: str
    amount: Optional[float] = None
    stage: str
    close_date: date
    probability: Optional[float] = None
    owner_name: Optional[str] = None
    account_name: Optional[str] = None
    last_activity_date: Optional[date] = None
    risk_flags: list[str] = Field(default_factory=list, description="Risk indicators")

class PipelineSummary(BaseModel):
    total_deals: int
    total_value: float
    by_stage: dict[str, dict] = Field(description="Stage → {count, value}")
    at_risk_deals: list[OpportunitySummary]
    owner_breakdown: Optional[dict[str, dict]] = None

class CaseSummary(BaseModel):
    id: str = Field(description="Salesforce Case ID")
    case_number: str
    subject: str
    description: Optional[str] = None
    status: str
    priority: str
    type: Optional[str] = None
    created_date: datetime
    owner_name: Optional[str] = None
    account_name: Optional[str] = None
    recent_comments: list[str] = Field(default_factory=list)

class KnowledgeArticle(BaseModel):
    id: str = Field(description="Knowledge Article Version ID")
    title: str
    summary: Optional[str] = None
    url_name: Optional[str] = None
    last_published: Optional[datetime] = None
    article_type: Optional[str] = None
    body: Optional[str] = Field(None, description="Full article content (only from get_article_by_id)")

class ActivitySummary(BaseModel):
    id: str
    type: str = Field(description="'Task' or 'Event'")
    subject: str
    date: Optional[date] = None
    status: Optional[str] = None
    owner_name: Optional[str] = None

class LeadSummary(BaseModel):
    id: str = Field(description="Salesforce Lead ID")
    name: str
    company: str
    status: str
    lead_source: Optional[str] = None
    email: Optional[str] = None
    owner_name: Optional[str] = None

class TeamMember(BaseModel):
    id: str = Field(description="Salesforce User ID")
    name: str
    is_active: bool
    profile_name: Optional[str] = None
```

---

## 3. Risk Threshold Configuration

**File**: `config/risk_thresholds.yaml`

```yaml
# Deal Risk Analysis Thresholds
risk_thresholds:
  # Flag deals stuck in the same stage for this many days
  stage_stagnation_days: 30

  # Flag deals with no activity for this many days
  inactivity_days: 14

  # Flag deals past their close date
  overdue_enabled: true

  # Flag deals with probability below this threshold (%) in late stages
  low_probability_threshold: 30

  # Stages considered "late" for probability check
  late_stages:
    - "Negotiation/Review"
    - "Proposal/Price Quote"

  # Minimum deal amount to flag (ignore small deals)
  minimum_amount_for_risk: 10000
```

---

## 4. Entity Relationship Diagram

```text
                ┌──────────┐
                │   User   │
                │ (Owner)  │
                └────┬─────┘
                     │ ManagerId (self-ref)
        ┌────────────┼──────────────┐
        │            │              │
   ┌────▼────┐  ┌────▼─────┐  ┌────▼────┐
   │ Account │  │   Lead   │  │  Case   │
   └────┬────┘  └──────────┘  └────┬────┘
        │                          │
   ┌────▼──────┐             ┌─────▼──────┐
   │  Contact  │             │CaseComment │
   └────┬──────┘             └────────────┘
        │
   ┌────▼───────────────┐
   │OpportunityContact  │
   │      Role          │
   └────┬───────────────┘
        │
   ┌────▼──────────┐
   │  Opportunity  │──── OpportunityLineItem
   └───────────────┘

   Task & Event: polymorphic (WhoId → Contact/Lead, WhatId → Account/Opportunity)
   KnowledgeArticleVersion: standalone (searched by SOQL/SOSL)
```

---

## 5. Data Access Patterns Summary

| MCP Tool | Objects Accessed | Query Type | Direction |
|----------|-----------------|------------|-----------|
| `get_account` | Account | SOQL (by ID or Name) | Read |
| `search_accounts` | Account | SOQL (LIKE filter) | Read |
| `get_contacts_for_account` | Contact, OpportunityContactRole | SOQL (AccountId filter + subquery) | Read |
| `get_opportunities` | Opportunity | SOQL (owner/stage/date filters) | Read |
| `get_pipeline_summary` | Opportunity, Task, Event | SOQL (3 queries, client-side merge) | Read |
| `get_case` | Case, CaseComment | SOQL (by ID/CaseNumber + subquery) | Read |
| `create_case` | Case | REST CREATE | Write |
| `update_case` | Case, CaseComment | REST UPDATE + CREATE (comment) | Write |
| `get_recent_activities` | Task, Event | SOQL (WhatId filter, last 30 days) | Read |
| `create_task` | Task | REST CREATE | Write |
| `get_leads` | Lead | SOQL (status/owner/source filters) | Read |
| `update_lead_status` | Lead | REST UPDATE | Write |
| `get_team_members` | User | SOQL (ManagerId filter) | Read |
| `search_articles` | KnowledgeArticleVersion | SOSL (full-text) or SOQL | Read |
| `get_article_by_id` | KnowledgeArticleVersion | SOQL (by ID) | Read |
