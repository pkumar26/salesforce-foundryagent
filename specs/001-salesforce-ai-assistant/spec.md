# Feature Specification: Salesforce AI Assistant

**Feature Branch**: `001-salesforce-ai-assistant`
**Created**: 2026-02-16
**Status**: Draft
**Input**: User description: "Build an end-to-end AI assistant using Microsoft Agent Framework that orchestrates domain agents via MCP servers and integrates with Salesforce as the primary CRM system. The assistant will be used by sales and service users in Microsoft Teams and (optionally) embedded in Salesforce."

## Clarifications

### Session 2026-02-16

- Q: What is the expected user scale for the AI assistant at GA? → A: Small (< 50 concurrent users, < 500 total licensed users). This is a demo-first deployment with a path to production scale later.
- Q: How should deal-risk thresholds be configured? → A: Config file or environment variables managed by an admin/developer (no admin UI in this phase).
- Q: How should the AI assistant authenticate to Salesforce on behalf of users? → A: Per-user delegated OAuth — each user authenticates individually, and all Salesforce queries run with that user's permissions.
- Q: What defines a conversation session boundary? → A: A single Microsoft Teams chat thread. Context persists within the thread; starting a new thread begins a fresh session.
- Q: Should the Salesforce-embedded experience be included in the initial demo scope? → A: No. Teams only for initial demo; Salesforce-embedded deferred to a future phase.

## Problem Statement & Business Value

### Problem Statement

Sales and service teams spend a disproportionate amount of time on manual, repetitive information-gathering tasks inside Salesforce: preparing for customer meetings, reviewing pipeline health, triaging incoming cases, and searching knowledge bases for answers. These tasks require navigating multiple Salesforce objects, cross-referencing data, and synthesizing insights — work that is time-consuming, error-prone, and pulls skilled staff away from high-value customer interactions.

### Business Value

An AI assistant embedded in the daily workflow (Microsoft Teams, and optionally within Salesforce) can dramatically reduce time-to-insight and time-to-action by:

- **Accelerating meeting preparation**: Automatically assembling account briefs, recent activity, and open opportunity context so AEs walk into meetings informed.
- **Improving pipeline visibility**: Surfacing at-risk deals with supporting evidence so sales managers can intervene early.
- **Reducing case resolution time**: Triaging new cases, proposing responses, and recommending knowledge articles so service agents resolve issues faster.
- **Standardizing quality**: Ensuring every interaction is grounded in current CRM data rather than memory or outdated notes.

### In-Scope Capabilities

- **Sales AI Assistant**: Account briefings, opportunity summaries, deal-risk analysis, next-best-action recommendations, meeting preparation.
- **Service AI Assistant**: Case triage and prioritization, response drafting, knowledge article recommendation, case escalation support.
- **Shared Capabilities**: Natural-language CRM queries, activity timeline summaries, multi-turn conversational interactions, orchestration across domain agents.
- **Salesforce Data Interactions**: Read access to Accounts, Contacts, Leads, Opportunities, Cases, Knowledge Articles, Tasks, Events, and related objects.
- **Write-Back to Salesforce**: Case creation, case updates, lead status changes, task/activity logging.
- **Delivery Channel**: Microsoft Teams (primary and sole channel for initial demo phase).
- **Orchestration**: The system must support an Orchestrator Agent that coordinates multiple domain-specific agents (Sales Agent, Service Agent) via MCP servers.

### Out-of-Scope Capabilities

- Salesforce CPQ, Billing, or Commerce Cloud integration.
- Custom Salesforce Lightning component development (UI is Teams-first).
- Real-time voice/telephony integration.
- Salesforce Marketing Cloud or Pardot workflows.
- AI model fine-tuning (prompt engineering and RAG only for this phase).
- Data migration from legacy CRM systems.
- Custom mobile app development.
- Salesforce Einstein Analytics or Tableau CRM integration.
- Forecast submission or quota management automation.
- Salesforce-embedded assistant experience (deferred to a future phase; Teams is the sole channel for initial demo).

## User Personas

### Persona 1: Account Executive (AE)

**Role**: Manages a portfolio of accounts and opportunities through the sales cycle.
**Jobs-to-be-Done**: Prepare for customer meetings, track deal progress, identify at-risk opportunities, determine next best actions, update CRM records efficiently.
**Pain Points**: Spends 30-45 minutes per meeting prep manually reviewing Salesforce records; misses signals in large pipelines; forgets to log activities.

### Persona 2: Sales Manager

**Role**: Oversees a team of AEs and is accountable for pipeline health and revenue targets.
**Jobs-to-be-Done**: Review team pipeline, identify coaching opportunities, forecast accurately, spot systemic risks across deals, prepare for leadership reviews.
**Pain Points**: Pipeline reviews require assembling data from multiple reports; relies on AE self-reporting which may be incomplete; at-risk deals surface too late.

### Persona 3: Customer Service Representative (CSR)

**Role**: Handles inbound customer cases across channels (email, chat, phone follow-up).
**Jobs-to-be-Done**: Triage incoming cases quickly, find relevant knowledge articles, draft responses, escalate complex issues appropriately, maintain case quality.
**Pain Points**: Manually searches knowledge base; spends time on repetitive Tier-1 questions; inconsistent triage quality across the team.

### Persona 4: Support Manager

**Role**: Manages the service team, monitors case queues, and ensures SLA compliance.
**Jobs-to-be-Done**: Monitor case backlog and aging, identify patterns in incoming issues, ensure equitable workload distribution, report on service KPIs.
**Pain Points**: Queue monitoring requires constant dashboard checking; trends are identified after they become problems; case reassignment is reactive.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Meeting Preparation Assistant (Priority: P1)

As an Account Executive, I want to ask the AI assistant to prepare me for my next customer meeting so that I walk in with a complete, up-to-date briefing without manually reviewing Salesforce.

**Why this priority**: Meeting preparation is the highest-frequency, highest-impact use case for AEs. It delivers immediate, tangible time savings (30-45 min per meeting) and improves meeting outcomes. This is the most compelling proof of value for sales adoption.

**Independent Test**: Can be fully tested by asking the assistant "Prepare me for my meeting with [Account Name]" and verifying the briefing includes account overview, key contacts, open opportunities, recent activities, and recommended talking points.

**Acceptance Scenarios**:

1. **Given** an AE has an upcoming meeting with a customer account that exists in Salesforce, **When** the AE asks "Prepare me for my meeting with Acme Corp," **Then** the assistant returns a briefing that includes: account summary (industry, tier, revenue), key contacts and their roles, open opportunities with stage and close date, recent activities (last 30 days), and suggested talking points based on deal stage and recent interactions.

2. **Given** an AE asks for meeting prep for an account with no recent activity in Salesforce, **When** the assistant retrieves the account data, **Then** the briefing explicitly flags "No activity recorded in the last 30 days" and recommends re-engagement actions.

3. **Given** an AE asks for meeting prep but provides an account name that matches multiple Salesforce records, **When** the assistant searches, **Then** it presents the top matches with distinguishing details (e.g., location, owner) and asks the AE to confirm which account.

4. **Given** the AE's Salesforce permissions restrict access to certain fields on the Account or Opportunity, **When** the assistant retrieves data, **Then** it only surfaces data the AE is authorized to see and does not expose restricted information.

---

### User Story 2 — Pipeline Summary & Risk Flagging (Priority: P1)

As a Sales Manager, I want a summarized view of my team's pipeline with at-risk deals flagged and supporting reasons so that I can prioritize coaching and intervention without manually assembling reports.

**Why this priority**: Pipeline visibility is the core job of a sales manager and directly impacts revenue outcomes. This use case demonstrates AI value to leadership and produces easily shareable, high-impact output.

**Independent Test**: Can be fully tested by asking "Summarize my team's open pipeline and flag deals at risk" and verifying the response includes deal list, risk indicators, and recommended actions.

**Acceptance Scenarios**:

1. **Given** a Sales Manager oversees a team with open opportunities in Salesforce, **When** the manager asks "Show me my team's pipeline and flag at-risk deals," **Then** the assistant returns a summary grouped by AE showing: total pipeline value, deal count, stage distribution, and a list of at-risk deals with reasons (e.g., stalled in stage > 30 days, close date in the past, no recent activity, key contact disengaged).

2. **Given** a Sales Manager asks about a specific AE's deals, **When** the manager says "What's the status of Sarah's pipeline?", **Then** the assistant filters to that AE's opportunities and provides the same risk-flagged summary.

3. **Given** no deals meet the at-risk criteria, **When** the manager requests a pipeline review, **Then** the assistant confirms "No deals currently flagged as at-risk" and still provides the pipeline summary.

---

### User Story 3 — Case Triage & Response Assistance (Priority: P1)

As a Customer Service Representative, I want the AI assistant to triage new cases, propose draft responses, and suggest relevant knowledge articles so that I can resolve customer issues faster and more consistently.

**Why this priority**: Case triage is the highest-volume, highest-frequency service activity. Automating initial triage and response drafting directly reduces mean time to resolution (MTTR) and improves service consistency — the primary goals of the Service AI Assistant.

**Independent Test**: Can be fully tested by presenting the assistant with a new case description and verifying it returns a priority recommendation, a draft response, and relevant knowledge article links.

**Acceptance Scenarios**:

1. **Given** a new case is created in Salesforce with a subject and description, **When** the CSR asks "Triage this case and suggest a response," **Then** the assistant returns: recommended priority (High/Medium/Low) with justification, suggested case category, a draft response using relevant knowledge article content, and links to the source knowledge articles.

2. **Given** a case description matches multiple knowledge articles, **When** the assistant searches, **Then** it ranks articles by relevance and presents the top 3 with brief summaries of why each is relevant.

3. **Given** a case requires information not available in the knowledge base, **When** the assistant cannot find relevant articles, **Then** it states "No matching knowledge articles found," still proposes a best-effort response based on case context, and recommends escalation to a subject-matter expert.

4. **Given** the CSR wants to update the case in Salesforce with the AI's recommendation, **When** the CSR confirms "Apply this triage," **Then** the assistant updates the case priority, category, and adds the draft response as an internal comment — requiring explicit CSR confirmation before any write-back occurs.

---

### User Story 4 — Natural-Language CRM Query (Priority: P2)

As any sales or service user, I want to ask the AI assistant questions about my Salesforce data in natural language so that I can get answers without building reports or navigating the Salesforce UI.

**Why this priority**: Natural-language querying is a foundational capability that enhances all other use cases. While not a standalone business outcome, it enables ad-hoc data access that users currently cannot get without report-building skills.

**Independent Test**: Can be fully tested by asking natural-language questions like "How many open cases are assigned to me?" or "What's the total pipeline value for Q2?" and verifying accurate answers grounded in Salesforce data.

**Acceptance Scenarios**:

1. **Given** a user asks "How many open opportunities do I have closing this quarter?", **When** the assistant queries Salesforce, **Then** it returns the count and a brief list with deal names, amounts, and close dates.

2. **Given** a user asks a question that spans multiple Salesforce objects (e.g., "Show me all open cases for accounts I own"), **When** the assistant processes the query, **Then** it correctly resolves the cross-object relationship and returns accurate results.

3. **Given** a user asks a question the assistant cannot confidently answer from available data, **When** the query is ambiguous or underspecified, **Then** the assistant asks a clarifying follow-up question rather than guessing.

---

### User Story 5 — Next Best Action Recommendations (Priority: P2)

As an Account Executive, I want the AI assistant to recommend next best actions for my deals so that I focus my effort where it will have the most impact.

**Why this priority**: Next best actions build on the data retrieval capabilities of P1 stories and add a layer of intelligence. This is high-value but depends on meeting prep and pipeline analysis being functional first.

**Independent Test**: Can be fully tested by asking "What should I focus on today?" and verifying the response includes prioritized action recommendations with supporting reasoning from Salesforce data.

**Acceptance Scenarios**:

1. **Given** an AE has multiple open opportunities at various stages, **When** the AE asks "What should I do next for my top deals?", **Then** the assistant returns a prioritized list of recommended actions (e.g., "Schedule follow-up with decision maker at Acme — no contact in 14 days," "Send proposal to Contoso — deal at Negotiation stage for 20 days") with supporting context from Salesforce.

2. **Given** an AE has a deal with an overdue close date, **When** the assistant analyzes the opportunity, **Then** it flags the overdue deal and recommends specific re-engagement steps, such as reaching out to the last active contact.

---

### User Story 6 — Case Queue Monitoring for Support Managers (Priority: P3)

As a Support Manager, I want a summarized view of my team's case queue with aging and SLA compliance indicators so that I can proactively manage workload and escalations.

**Why this priority**: Queue monitoring is important for operational efficiency but is lower-frequency than individual case handling (P1). It builds on the case data retrieval capabilities already established.

**Independent Test**: Can be fully tested by asking "Show me the case queue status for my team" and verifying the response includes case counts by status, aging distribution, and SLA compliance indicators.

**Acceptance Scenarios**:

1. **Given** a Support Manager oversees a team with open cases, **When** the manager asks "What does my team's case queue look like?", **Then** the assistant returns: total open cases, breakdown by priority and status, cases approaching SLA breach (within 2 hours), cases already breached, and cases unassigned or requiring reassignment.

2. **Given** the manager asks "Are there any patterns in today's new cases?", **When** the assistant analyzes recent cases, **Then** it identifies common themes (e.g., "12 new cases mention 'login issues' — possible system incident") and recommends whether to escalate as a known issue.

---

### User Story 7 — Orchestrator-Coordinated Multi-Domain Workflow (Priority: P3)

As a user working across sales and service contexts, I want the AI assistant to coordinate between the Sales Agent and Service Agent seamlessly so that I can handle cross-functional requests in a single conversation without switching tools.

**Why this priority**: Orchestration is architecturally important but delivers incremental user value on top of the individual domain agents. Users must have working Sales and Service agents (P1/P2) before orchestration adds meaningful value.

**Independent Test**: Can be fully tested by asking a cross-domain question like "Show me open opportunities for accounts that also have escalated cases" and verifying the response combines data from both sales and service domains.

**Acceptance Scenarios**:

1. **Given** a user asks "Which of my accounts have both open deals and open support cases?", **When** the Orchestrator Agent coordinates the Sales Agent and Service Agent, **Then** the user receives a unified response listing the accounts with relevant deal and case details from both domains.

2. **Given** a user starts with a service question ("What are the top cases today?") and follows up with a sales question ("And what deals do those same accounts have?"), **When** the assistant processes the multi-turn conversation, **Then** it maintains context and correctly links the service data to the sales query without asking the user to repeat information.

---

### Edge Cases

- What happens when the user's Salesforce session token is expired or their Connected App permissions are revoked? The assistant must inform the user about the authentication issue and provide guidance on re-authorizing, without exposing technical error details.
- What happens when Salesforce API rate limits are exceeded during a busy period? The assistant must gracefully inform the user that data retrieval is temporarily delayed and offer to retry, rather than failing silently.
- How does the system handle large result sets (e.g., "Show me all cases from the last year")? The assistant must set reasonable boundaries (e.g., return top 50 with option to narrow), not attempt to retrieve unbounded data.
- What happens when a user asks the assistant to perform a Salesforce write-back (e.g., update a case) but the user lacks the required Salesforce permission? The assistant must return a clear access-denied message and not attempt the operation.
- How does the system handle stale or conflicting data if Salesforce records were updated between query and action? The system must re-validate before write-back and inform the user of any changes detected since their last query.
- What happens when the assistant cannot determine user identity or Salesforce user mapping? The assistant must not proceed with data retrieval and must prompt the user to verify their identity mapping.

## Feature Breakdown

### Sales AI Assistant

| Capability | Description | Salesforce Interactions |
|-----------|-------------|----------------------|
| **Meeting Preparation** | Assembles account briefings with contacts, deals, and recent activity | Read: Account, Contact, Opportunity, Task, Event |
| **Pipeline Summary** | Summarizes open pipeline by rep, stage, and value | Read: Opportunity, User (team members) |
| **Deal Risk Analysis** | Flags at-risk deals using activity recency, stage duration, and close date signals | Read: Opportunity, Task, Event, OpportunityContactRole |
| **Next Best Action** | Recommends prioritized actions per deal based on stage, activity gaps, and deal signals | Read: Opportunity, Task, Event, Contact |
| **Activity Logging** | Logs agent-recommended activities as Tasks in Salesforce upon user confirmation | Write: Task |

### Service AI Assistant

| Capability | Description | Salesforce Interactions |
|-----------|-------------|----------------------|
| **Case Triage** | Classifies case priority and category from case subject and description | Read: Case; Write: Case (priority, category) |
| **Response Drafting** | Proposes draft responses grounded in knowledge article content | Read: Case, KnowledgeArticleVersion |
| **Knowledge Article Recommendation** | Ranks and surfaces relevant articles for a given case | Read: KnowledgeArticleVersion, Case |
| **Case Escalation Support** | Recommends escalation when case complexity exceeds Tier-1 scope | Read: Case, CaseComment; Write: Case (escalation flag) |
| **Queue Monitoring** | Provides team-level queue status, aging, and SLA compliance | Read: Case, User (team members), BusinessHours |

### Shared Capabilities

| Capability | Description | Salesforce Interactions |
|-----------|-------------|----------------------|
| **Natural-Language CRM Query** | Answers ad-hoc questions about Salesforce data in conversational language | Read: Multiple objects as needed |
| **Activity Timeline** | Summarizes recent activities for any Account, Contact, or Opportunity | Read: Task, Event, CaseComment, EmailMessage |
| **Multi-Turn Conversation** | Maintains context across follow-up questions within a session | N/A (session management) |
| **Orchestrator Coordination** | Routes requests to the appropriate domain agent (Sales or Service) and merges results for cross-domain queries | N/A (agent routing) |
| **Write-Back with Confirmation** | All Salesforce record modifications require explicit user confirmation before execution | Write: Case, Lead, Task (gated by confirmation) |

## Salesforce Data Interactions

### Data Domains & Operations

| Salesforce Object | Read | Write | Purpose |
|------------------|------|-------|---------|
| **Account** | Yes | No | Account context for briefings, relationship mapping |
| **Contact** | Yes | No | Key people, roles, engagement history |
| **Lead** | Yes | Yes (status update) | Lead qualification, status changes |
| **Opportunity** | Yes | No | Pipeline analysis, deal risk, meeting prep |
| **OpportunityContactRole** | Yes | No | Decision-maker identification |
| **Case** | Yes | Yes (create, update priority/category/status) | Case triage, response drafting, queue monitoring |
| **CaseComment** | Yes | Yes (add internal comment) | Response drafting, activity context |
| **KnowledgeArticleVersion** | Yes | No | RAG source for case response and customer Q&A |
| **Task** | Yes | Yes (create) | Activity logging, activity timeline |
| **Event** | Yes | No | Activity timeline, meeting context |
| **User** | Yes | No | Team membership, case/opportunity ownership |
| **BusinessHours** | Yes | No | SLA calculation for queue monitoring |

### Data Access Principles

- All reads MUST respect the requesting user's Salesforce field-level security and sharing rules — the AI assistant should never surface data the user could not see in Salesforce directly.
- All writes MUST require explicit user confirmation before execution ("Apply this triage?" → user confirms → write-back proceeds).
- Large data retrievals MUST be bounded (reasonable limits per query) to avoid Salesforce API rate-limit exhaustion.
- Data freshness expectations: all reads reflect current Salesforce state at time of query (no caching beyond a single conversation turn unless explicitly stated).
- The assistant MUST cite which Salesforce records or Knowledge Articles it used to formulate any answer, enabling the user to verify accuracy.

## Non-Functional Requirements (Business Perspective)

### Reliability

- The assistant must be available during business hours with a target availability of ≥ 99.5% uptime, consistent with other business-critical collaboration tools.
- If Salesforce is temporarily unreachable, the assistant must inform the user clearly rather than returning incomplete or inaccurate information.
- Write-back operations must be idempotent where possible — if a user confirms a case update and the connection drops, retrying should not create duplicate records.

### Response Quality

- All responses referencing Salesforce data must be grounded in actual CRM records, not generated from model knowledge alone.
- Every factual claim must be attributable to a specific Salesforce record or Knowledge Article.
- The assistant must never fabricate Salesforce data (e.g., inventing opportunity amounts, contact names, or case details that do not exist in the org).

### Latency Expectations

- Simple queries ("How many open cases do I have?") should return within 5 seconds (P95).
- Complex queries (pipeline summary, meeting preparation) should return within 15 seconds (P95).
- Users should see a progress indicator or interim acknowledgment for any query taking more than 3 seconds. For notebook-based demos, this is satisfied by streaming output or a print statement indicating the query is in progress; for Teams, the bot typing indicator serves this purpose.

### Scale

- Initial deployment targets < 50 concurrent users and < 500 total licensed users (demo-first).
- Architecture should support a clear upgrade path to production scale without redesign.

### Security & Privacy

- Access to Salesforce data must be scoped to each user's existing Salesforce permissions — no privilege escalation through the AI layer.
- The system must use per-user delegated OAuth so that all Salesforce queries execute under the authenticated user's identity, natively enforcing sharing rules and field-level security.
- PII accessed from Salesforce (names, emails, phone numbers) must not be stored or logged outside the authorized systems.
- Conversation logs containing customer data must follow the organization's data retention policies.
- The assistant must not expose raw Salesforce record IDs, internal field names, or system metadata to end users in responses.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST allow users to request an account meeting briefing by providing an account name or identifier, and return a structured summary including account overview, key contacts, open opportunities, recent activities, and suggested talking points.
- **FR-002**: The system MUST allow sales managers to request a pipeline summary for their team, returning deals grouped by owner with stage, value, close date, and risk indicators.
- **FR-003**: The system MUST flag at-risk deals based on observable signals: stage duration exceeding configurable thresholds, close date in the past, no logged activity within a configurable window, and absence of an identified decision-maker contact.
- **FR-004**: The system MUST triage incoming cases by analyzing case subject and description, assigning a recommended priority (High/Medium/Low) and category, and proposing a draft response grounded in knowledge base content.
- **FR-005**: The system MUST search Salesforce Knowledge Articles by relevance to a case or user question and return ranked results with article title, summary, and a citation link.
- **FR-006**: The system MUST support natural-language queries against Salesforce data, interpreting user intent and returning accurate, scoped results across supported objects.
- **FR-007**: The system MUST require explicit user confirmation before executing any write-back operation to Salesforce (case creation, case update, lead status change, task creation).
- **FR-008**: The system MUST respect Salesforce field-level security and sharing rules for each authenticated user — no data surfaced that the user cannot see in Salesforce natively.
- **FR-009**: The system MUST support multi-turn conversations, maintaining context within a Microsoft Teams chat thread so follow-up questions reference prior results without requiring the user to repeat information. A new thread constitutes a new session with no prior context.
- **FR-010**: The system MUST support orchestration across domain agents (Sales Agent and Service Agent) so that cross-domain queries produce unified results in a single conversation.
- **FR-011**: The system MUST cite the specific Salesforce records or Knowledge Articles used to generate any response, enabling users to verify accuracy.
- **FR-012**: The system MUST deliver the assistant experience within Microsoft Teams as the primary channel.
- **FR-013**: The system MUST handle ambiguous queries by asking clarifying follow-up questions rather than making assumptions that could return incorrect results.
- **FR-014**: The system MUST provide clear, non-technical error messages when Salesforce connectivity fails, permissions are insufficient, or API limits are reached.
- **FR-015**: The system MUST bound large data retrievals to a reasonable result set (e.g., top 50 records) and offer users the ability to narrow their query, preventing API quota exhaustion.
- **FR-016**: The system MUST log all AI-initiated Salesforce write-back actions with the user who confirmed them, the timestamp, and the data written, for audit purposes.
- **FR-017**: The system MUST support configurable risk-signal thresholds (e.g., stage duration, inactivity window) via a config file or environment variables managed by an admin or developer, so that organizations can adapt deal-risk criteria to their sales process without code changes.
- **FR-018**: The system MUST generate next-best-action recommendations for AEs based on deal stage, activity gaps, close date proximity, and contact engagement signals.
- **FR-019**: The system MUST support queue-level monitoring for support managers, including case counts by status, aging distribution, and SLA compliance indicators.
- **FR-020**: The system MUST be usable entirely through the Microsoft Agent Framework with MCP as the primary integration mechanism for Salesforce and other backend data sources.
- **FR-021**: The system MUST support configurable hosting of runtime components (MCP servers, API backends) via a `hostingMode` parameter with values `'none'` (notebooks only), `'appService'` (Azure App Service), or `'aca'` (Azure Container Apps). The hosting choice MUST be selectable per environment without code changes. Existing App Service support is preserved; ACA is additive.

### Key Entities

- **Account**: A customer or prospect organization in Salesforce. Key attributes: name, industry, tier/segment, annual revenue, owner. Central entity linking to Contacts, Opportunities, and Cases.
- **Contact**: An individual associated with an Account. Key attributes: name, title, role, email, phone, last activity date. Used for stakeholder mapping and engagement tracking.
- **Lead**: A potential prospect not yet converted to an Account/Contact/Opportunity. Key attributes: name, company, status, lead source, score. Subject to qualification by the AI assistant.
- **Opportunity**: A potential deal associated with an Account. Key attributes: name, amount, stage, close date, owner, probability. Central to pipeline and risk analysis.
- **Case**: A customer support issue. Key attributes: subject, description, status, priority, category, owner, created date, SLA deadline. Core entity for the Service AI Assistant.
- **Knowledge Article**: A published support or product article. Key attributes: title, body content, article type, last published date, relevance tags. Used as RAG source for response grounding.
- **Task / Event**: Logged activities (calls, emails, meetings) associated with Accounts, Contacts, or Opportunities. Key attributes: subject, due date, status, associated record. Used for activity timeline and recency analysis.

## Assumptions

- The organization is on Salesforce Enterprise or Unlimited Edition with sufficient API call entitlements for the expected query volume. All Salesforce REST API calls target API version **v62.0** (pinned in `shared/salesforce_client.py`).
- Microsoft Agent Framework with MCP is the approved standard for building agentic applications; no alternative frameworks will be evaluated for this project.
- Sales and service users have active Microsoft Teams accounts and Salesforce user licenses with appropriate data access.
- Salesforce Knowledge Base has existing, published articles of sufficient quality and coverage for RAG-based response grounding (baseline: ≥ 50 published articles covering the top 20 FAQ categories).
- The Salesforce data model follows standard object schema (Account, Contact, Lead, Opportunity, Case, etc.) without heavy custom-object dependencies that would alter the described interactions.
- User identity can be mapped between Microsoft Teams (Entra ID) and Salesforce user records to enforce proper data access scoping.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Account Executives can produce a complete meeting briefing using the AI assistant in under 2 minutes, compared to a 30-45 minute manual baseline.
- **SC-002**: Sales Managers can obtain a complete team pipeline summary with risk-flagged deals in under 30 seconds, without building a custom Salesforce report.
- **SC-003**: 70% or more of Tier-1 support cases can be triaged (priority + category assigned) by the AI assistant with accuracy validated by CSRs accepting the recommendation without modification.
- **SC-004**: AI-suggested knowledge articles are rated as relevant by CSRs in at least 85% of cases where articles are recommended.
- **SC-005**: Mean time to first response (MTFR) for AI-assisted cases decreases by 50% compared to the pre-implementation baseline.
- **SC-006**: 90% of users report that the assistant "makes their job easier" in a post-pilot satisfaction survey.
- **SC-007**: Zero instances of the AI assistant surfacing Salesforce data that the requesting user does not have permission to see, validated by security audit during Pilot.
- **SC-008**: System handles up to 50 concurrent users without response degradation beyond the stated latency expectations.
- **SC-009**: All AI-initiated Salesforce write-back actions are logged with full audit trail, confirmed by compliance review.
