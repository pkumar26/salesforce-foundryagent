# Data Classification: Salesforce AI Assistant

**Date**: 2026-02-16
**Principle**: Constitution Principle II — Security & Compliance by Default

This document classifies all data elements handled by the Salesforce AI Assistant
per the organization's data classification policy.

## Classification Levels

| Level | Description | Handling Requirements |
|-------|-------------|----------------------|
| **Public** | Non-sensitive, publicly available | Standard controls |
| **Internal** | Business data, not for external sharing | Access-controlled, TLS in transit |
| **Confidential** | Sensitive business data, PII | Encrypted at rest and in transit, audit logging, least-privilege access |
| **Restricted** | Highly sensitive, regulatory impact | Encrypted (HSM), strict RBAC, comprehensive audit, retention policies |

---

## Salesforce Object Classifications

### Account

| Field | Classification | Rationale |
|-------|---------------|-----------|
| Id | Internal | System identifier |
| Name | Internal | Business entity name |
| Industry | Internal | Business categorization |
| Type | Internal | Account classification |
| AnnualRevenue | Confidential | Financial data |
| BillingCity, BillingState | Internal | Business address |
| OwnerId, Owner.Name | Internal | Internal user reference |
| Description | Internal | Business notes |

### Contact

| Field | Classification | Rationale |
|-------|---------------|-----------|
| Id | Internal | System identifier |
| Name | Confidential | Personal Identifiable Information (PII) |
| Title | Internal | Job role |
| Email | Confidential | PII — personal email address |
| Phone | Confidential | PII — personal phone number |
| AccountId | Internal | System reference |

### Lead

| Field | Classification | Rationale |
|-------|---------------|-----------|
| Id | Internal | System identifier |
| Name | Confidential | PII |
| Company | Internal | Business entity |
| Status | Internal | Lead lifecycle |
| Email | Confidential | PII |
| LeadSource | Internal | Marketing channel |

### Opportunity

| Field | Classification | Rationale |
|-------|---------------|-----------|
| Id | Internal | System identifier |
| Name | Internal | Deal name |
| Amount | Confidential | Financial data — deal value |
| StageName | Internal | Sales process stage |
| CloseDate | Internal | Business timeline |
| Probability | Internal | Sales forecast |
| OwnerId, Owner.Name | Internal | Internal user reference |

### Case

| Field | Classification | Rationale |
|-------|---------------|-----------|
| Id | Internal | System identifier |
| CaseNumber | Internal | System reference |
| Subject | Internal | Case summary |
| Description | Confidential | May contain customer-specific issues, PII |
| Status, Priority, Type | Internal | Workflow metadata |
| OwnerId, Owner.Name | Internal | Internal user reference |

### CaseComment

| Field | Classification | Rationale |
|-------|---------------|-----------|
| CommentBody | Confidential | May contain customer-specific details, PII |
| IsPublished | Internal | Visibility flag |

### KnowledgeArticleVersion

| Field | Classification | Rationale |
|-------|---------------|-----------|
| Id, Title, Summary | Internal | Published knowledge content |
| ArticleBody | Internal | Published content (Online status only) |
| UrlName | Public | URL-safe identifier |

### Task / Event

| Field | Classification | Rationale |
|-------|---------------|-----------|
| Id, Subject | Internal | Activity metadata |
| Description | Confidential | May contain customer-specific details |
| WhoId, WhatId | Internal | System references |
| OwnerId | Internal | Internal user reference |

### User

| Field | Classification | Rationale |
|-------|---------------|-----------|
| Id, Name | Internal | Internal employee data |
| ManagerId | Internal | Org hierarchy |
| IsActive | Internal | Employment status |
| Profile.Name | Internal | System role |

---

## Integration Data Classifications

| Data Element | Classification | Storage Location | Handling |
|-------------|---------------|-----------------|----------|
| SF Consumer Key | Restricted | Azure Key Vault | HSM-backed in prod, @secure() in Bicep |
| SF Consumer Secret | Restricted | Azure Key Vault | HSM-backed in prod, @secure() in Bicep |
| SF Access Token | Restricted | In-memory only | Never persisted, passed via env vars (stdio) |
| SF Refresh Token | Restricted | Azure Key Vault | Encrypted at rest |
| SF Instance URL | Internal | .env / Key Vault | Non-secret but scoped |
| Azure AI Endpoint | Internal | .env / Bicep outputs | Non-secret infrastructure |
| App Insights Conn String | Internal | .env / Bicep outputs | Instrumentation only |

---

## Data Flow Controls

1. **No caching**: Salesforce data is never cached by the AI assistant. Every request queries Salesforce in real-time.
2. **No persistence**: PII/Confidential data is returned to the user but not stored outside Salesforce.
3. **Per-user auth**: Each user's OAuth token ensures they only access data permitted by their Salesforce profile (FLS + sharing rules).
4. **TLS 1.2+**: All data in transit uses TLS 1.2 or higher.
5. **Audit trail**: All write-back operations are logged to Application Insights with user identity, timestamp, and operation details.
6. **Token lifecycle**: Access tokens are short-lived (~2 hours). Refresh tokens are stored in Key Vault with RBAC access control.
