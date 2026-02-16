<!--
  Sync Impact Report
  ==================
  Version change: N/A → 1.0.0 (initial ratification)
  Modified principles: None (initial creation)
  Added sections:
    - Core Principles (5 principles)
    - Project Overview
    - Scope
    - Stakeholders & Governance (detailed)
    - Architecture & Integration Approach
    - Data Governance & Security
    - Environments & DevOps
    - Key Milestones & Timeline
    - Risk Register
    - Budget & Resource Allocation
    - Communication Plan
    - Success Metrics & KPIs
    - Assumptions, Constraints & Dependencies
    - Approval & Sign-off
    - Governance
  Removed sections: None (initial creation)
  Templates requiring updates:
    - .specify/templates/plan-template.md ✅ reviewed — no update needed
    - .specify/templates/spec-template.md ✅ reviewed — no update needed
    - .specify/templates/tasks-template.md ✅ reviewed — no update needed
  Follow-up TODOs: None
-->

# Salesforce × Azure AI Foundry Agent Integration Constitution

## Core Principles

### I. Integration-First Architecture

All capabilities MUST be designed as integration-ready
components from inception. Every module — whether an Azure AI
Foundry Agent tool, a Salesforce automation, or a middleware
service — MUST expose well-defined interfaces (REST APIs,
Platform Events, or SDK contracts) and operate as a composable
building block. No component may be built as a standalone silo;
cross-platform data flow between Salesforce CRM and Azure AI
Foundry MUST be a first-class design constraint.

**Non-negotiable rules:**

- Every agent tool MUST declare its input/output schema and
  Salesforce object dependencies before implementation begins.
- All Salesforce connectivity MUST use OAuth 2.0
  (Authorization Code or Client Credentials flow) via
  Connected Apps; hard-coded credentials are prohibited.
- Data flow direction (read, write, bidirectional) MUST be
  documented per Salesforce object in the integration manifest.
- Azure API Management or direct REST MUST be the primary
  integration channel; MuleSoft is an approved optional
  middleware when organizational standards require it.

### II. Security & Compliance by Default

Security, privacy, and regulatory compliance MUST be embedded
into every design decision — not bolted on after the fact.
All data traversing the integration boundary between
Salesforce and Azure MUST be classified, encrypted, and
access-controlled before any feature reaches production.

**Non-negotiable rules:**

- All data MUST be classified (Public, Internal, Confidential,
  Restricted) before integration development begins.
- PII and PHI MUST be masked or tokenized when transferred
  outside the originating system unless explicit consent and
  a lawful basis are documented.
- Encryption MUST be enforced: TLS 1.2+ in transit, AES-256
  at rest (Azure Key Vault for secrets, Salesforce Shield for
  platform encryption).
- Salesforce field-level security and Azure RBAC MUST follow
  least-privilege principles; service accounts MUST be scoped
  to the minimum permissions required.
- Compliance with GDPR, SOC 2 Type II, and HIPAA (when
  healthcare data is involved) MUST be validated before
  any GA deployment.
- Salesforce API rate limits (daily and concurrent) MUST be
  monitored and enforced via throttling policies in Azure API
  Management.

### III. AI-Responsible & Human-in-the-Loop

AI-powered automation MUST augment — not replace — human
judgment for high-stakes decisions. Every AI Foundry Agent
action that creates, updates, or deletes CRM records MUST
include an auditable decision trail and, where configured, a
human-approval gate.

**Non-negotiable rules:**

- AI Agent responses MUST cite their knowledge source
  (Salesforce Knowledge article ID, CRM record reference, or
  external document) so users can verify accuracy.
- Case creation and lead qualification actions MUST log the
  agent's reasoning (tool calls, retrieved context,
  confidence signals) to an audit store.
- The AI Agent MUST be able to accommodate user questions
  directly and MUST also be capable of working with an
  Orchestrator Agent for multi-step workflows.
- Model drift monitoring MUST be implemented; retraining or
  prompt-revision thresholds MUST be defined before Pilot.
- Hallucination guardrails (content filtering, grounding
  checks via Azure AI Content Safety) MUST be enabled in
  all environments.

### IV. Iterative Delivery & Phased Rollout

The project MUST follow a phased delivery model — Discovery,
POC, MVP, Pilot, GA — with explicit go/no-go gates between
phases. Each phase MUST produce demonstrable business value
and MUST NOT proceed without stakeholder sign-off.

**Non-negotiable rules:**

- No phase transition without documented acceptance criteria
  met and steering committee approval.
- POC scope MUST be limited to a single use case (e.g.,
  automated case triage) to validate integration feasibility.
- MVP MUST cover all three primary use cases (case triage,
  lead qualification, customer Q&A) at production-quality
  for a limited user group.
- Pilot MUST run in production with real users for a minimum
  of 4 weeks before GA consideration.
- Rollback procedures MUST be tested and documented before
  each phase promotion.

### V. Operational Excellence & Observability

Every deployed component MUST be observable, measurable, and
maintainable. Monitoring infrastructure is not optional — it
is a prerequisite for any production deployment.

**Non-negotiable rules:**

- All Azure resources MUST emit structured logs and metrics
  to Azure Monitor / Application Insights.
- Salesforce integration events MUST be captured via Platform
  Event monitoring and surfaced in unified dashboards.
- End-to-end latency for agent interactions MUST be tracked;
  P95 response time MUST stay below defined SLA thresholds.
- Alerting MUST be configured for: API rate-limit proximity
  (>80% daily quota), agent error rates (>2%), and
  authentication failures.
- Incident runbooks MUST exist for every production service
  before GA deployment.

## Project Overview

**Project Title:** Salesforce × Azure AI Foundry Agent
Integration

**Purpose:** This project delivers an enterprise-grade
integration between Microsoft Azure AI Foundry Agents and
Salesforce CRM to automate customer-facing and internal
workflows using AI. By connecting Foundry Agents to live
Salesforce data — Accounts, Contacts, Cases, Leads,
Opportunities, and Knowledge Articles — the solution enables
intelligent case triage, automated lead qualification, and
real-time customer Q&A grounded in organizational knowledge.

**Business Problem:** Customer service and sales teams spend
significant time on repetitive, low-complexity tasks: routing
cases, qualifying inbound leads, and answering recurring
questions. These manual processes slow response times, increase
operational cost, and degrade customer satisfaction. This
project solves that by deploying AI agents that read from and
write to Salesforce, providing contextual, accurate, and
auditable automation.

**Industry Applicability:** The solution is designed to be
industry-agnostic with proven applicability in Financial
Services (account-based insights, regulatory-compliant case
handling), Healthcare (patient inquiry triage, PHI-aware
workflows), and Retail (order-related case routing, product
knowledge Q&A).

**Primary Use Cases:**

1. **Automated Case Triage** — AI Agent reads incoming Case
   details, enriches them with Account/Contact context, and
   assigns priority, category, and queue routing.
2. **Lead Qualification** — AI Agent evaluates Lead fields
   against Ideal Customer Profile rules, scores the lead,
   and updates Salesforce with qualification status and
   recommended next actions.
3. **Customer Q&A from Knowledge Base** — AI Agent performs
   RAG (Retrieval-Augmented Generation) over Salesforce
   Knowledge Articles to answer customer and agent questions
   with cited, grounded responses.

## Vision & Objectives

**Strategic Vision:** Become the organization's reference
architecture for AI-augmented CRM operations, proving that
Azure AI Foundry Agents integrated with Salesforce can reduce
manual effort by 40%+, improve first-response time by 60%+,
and increase customer satisfaction (CSAT) by 15%+ within 12
months of GA.

**Measurable Objectives:**

| # | Objective | Target | Timeframe |
|---|-----------|--------|-----------|
| O1 | Case triage automation rate | ≥ 70% of Tier-1 cases auto-triaged | 6 months post-GA |
| O2 | Lead qualification throughput | 3× increase vs. manual baseline | 6 months post-GA |
| O3 | Average first-response time | ≤ 2 minutes for AI-handled queries | At GA |
| O4 | Customer satisfaction (CSAT) | +15% improvement over baseline | 12 months post-GA |
| O5 | Agent accuracy (grounded answers) | ≥ 92% factual accuracy rate | At GA |
| O6 | Operational cost reduction | 25% reduction in Tier-1 support cost | 12 months post-GA |

**Key Success Criteria:**

- All three primary use cases operational in production.
- Integration sustains Salesforce API limits without throttle
  incidents for 30 consecutive days.
- Compliance audit passed for applicable regulations before GA.
- Positive NPS from pilot user cohort (score ≥ 40).

## Scope

### In-Scope

**Salesforce Objects / Entities:**

- Account, Contact, Lead, Opportunity
- Case (including Case Comments, Case Teams)
- Knowledge Articles (KnowledgeArticleVersion)
- Task, Event (for activity tracking)
- Custom objects as identified during Discovery

**Azure AI Foundry Agent Capabilities:**

- RAG over Salesforce Knowledge Articles (Azure AI Search
  as vector store, Salesforce as source of truth)
- CRM record lookup (Account, Contact, Case, Lead)
- Case creation and update via Salesforce REST API
- Lead scoring and qualification update
- Multi-turn conversational interactions
- Orchestrator Agent integration for complex workflows

**Integration Channels:**

- Azure API Management (primary API gateway)
- Direct Salesforce REST API (Connected App + OAuth 2.0)
- MuleSoft Anypoint (optional, when enterprise iPaaS is
  mandated)
- Azure Service Bus (event-driven patterns)
- Salesforce Platform Events (real-time CRM event capture)

**Deployment Targets:**

- Microsoft Teams (agent-as-a-channel)
- Web chat widget (customer-facing)
- Internal agent desktop (service console integration)

### Out-of-Scope

- Salesforce CPQ or Billing integrations
- Custom Salesforce Lightning component development
- Real-time voice/telephony integration (Phase 2+)
- Salesforce Marketing Cloud or Pardot integration
- Azure AI Foundry Agent fine-tuning (prompt engineering
  and RAG only in Phase 1)
- Data migration from legacy CRM systems
- Custom mobile app development

## Stakeholders & Governance

### Roles & Responsibilities

| Role | Responsibility | Decision Authority |
|------|---------------|-------------------|
| **Executive Sponsor** | Strategic alignment, budget approval, escalation resolution | Final authority on scope changes > 10% budget impact |
| **Product Owner** | Backlog prioritization, acceptance criteria, UAT sign-off | Feature prioritization and trade-off decisions |
| **Technical Lead** | Architecture decisions, integration design, code review | Technical approach and tooling selections |
| **Salesforce Admin** | Salesforce configuration, Connected App setup, field-level security | Salesforce platform changes and permissions |
| **Azure / AI Engineer** | Foundry Agent development, Azure resource provisioning, RAG pipeline | AI model configuration, prompt engineering |
| **Integration Engineer** | API design, middleware configuration, data mapping | Integration pattern and error-handling design |
| **QA Lead** | Test strategy, test execution, defect management | Release readiness recommendation |
| **Security / Compliance Officer** | Security review, compliance validation, data classification | Compliance gate approval (blocking) |
| **DevOps Engineer** | CI/CD pipelines, environment management, deployment automation | Infrastructure and deployment process |
| **Change Manager** | Training, communication, adoption tracking | Organizational readiness assessment |

### Steering Committee

- **Cadence:** Biweekly (weekly during Pilot and GA phases)
- **Members:** Executive Sponsor, Product Owner, Technical
  Lead, Security Officer, Change Manager
- **Quorum:** 3 of 5 members required for decisions

### Escalation Path

1. Team-level resolution (Technical Lead) — 24-hour SLA
2. Product Owner arbitration — 48-hour SLA
3. Steering Committee — next scheduled meeting or emergency
   session within 72 hours
4. Executive Sponsor — final escalation within 5 business days

### Decision-Making Authority

- **Technical decisions** (tooling, patterns): Technical Lead
  with peer review
- **Scope changes ≤ 10% budget**: Product Owner approval
- **Scope changes > 10% budget**: Steering Committee vote
  (majority)
- **Security / compliance exceptions**: Security Officer
  approval (no delegation)
- **Go/no-go phase gates**: Steering Committee unanimous

## Architecture & Integration Approach

### Azure AI Foundry Agent Design

**Agent Structure:**

- **Primary Agent:** Customer-facing conversational agent
  handling case triage, lead qualification, and knowledge Q&A
- **Orchestrator Agent:** Coordinates multi-step workflows
  spanning multiple tools and Salesforce operations
- **Tools:** Salesforce Record Lookup, Case Creator, Lead
  Qualifier, Knowledge Search (RAG)
- **Knowledge Sources:** Azure AI Search index populated from
  Salesforce Knowledge Articles (incremental sync via
  scheduled pipeline or Platform Events)
- **Actions:** Create Case, Update Lead Status, Log Activity,
  Escalate to Human Agent

**Model Configuration:**

- Foundation model via Azure OpenAI Service (GPT-4o or latest
  recommended model)
- System prompts with role-specific instructions and
  grounding constraints
- Azure AI Content Safety enabled for all agent responses

### Salesforce Connectivity

- **Authentication:** OAuth 2.0 Client Credentials flow for
  server-to-server; Authorization Code flow for user-context
  operations
- **Connected App:** Dedicated Connected App per environment
  with IP restrictions and certificate-based authentication
- **APIs:** Salesforce REST API v60.0+ (primary), Composite
  API for batch operations, Streaming API / Platform Events
  for real-time notifications
- **Rate Limit Management:** Azure API Management policies
  enforce per-minute and daily call budgets aligned with
  Salesforce org limits

### Data Flow

| Flow | Direction | Source → Target | Frequency |
|------|-----------|----------------|-----------|
| Knowledge Article sync | Salesforce → Azure | SF Knowledge → AI Search | Incremental (15-min or event-driven) |
| Case creation | Azure → Salesforce | AI Agent → SF Case object | Real-time (per interaction) |
| Lead qualification update | Azure → Salesforce | AI Agent → SF Lead object | Real-time (per interaction) |
| CRM record lookup | Salesforce → Azure | SF Account/Contact/Case → Agent context | Real-time (per query) |
| Activity logging | Azure → Salesforce | Agent audit trail → SF Task/Event | Near real-time (batched) |
| Agent analytics | Azure → Azure | Agent telemetry → Application Insights | Continuous |

### Middleware & Event Patterns

- **Azure API Management:** Central gateway for all
  Salesforce API calls; enforces authentication, throttling,
  logging, and retry policies
- **Azure Service Bus:** Asynchronous message broker for
  decoupled event processing (e.g., case creation
  confirmation, lead score distribution)
- **Salesforce Platform Events:** Real-time event channel for
  CRM state changes that trigger agent actions (e.g., new
  Case created, Lead status change)
- **MuleSoft Anypoint (optional):** Enterprise iPaaS layer
  when organizational standards require centralized
  integration management

## Data Governance & Security

### Data Classification

| Data Category | Classification | Examples |
|--------------|---------------|----------|
| Customer PII | Confidential | Name, Email, Phone, Address |
| Health Information (PHI) | Restricted | Medical records, diagnoses (Healthcare vertical) |
| Financial Data | Confidential | Account balances, transaction history (FinServ vertical) |
| Case Content | Internal | Case descriptions, agent notes |
| Knowledge Articles | Internal / Public | Published KB content |
| Agent Telemetry | Internal | Interaction logs, performance metrics |

### Security Controls

- **Encryption in Transit:** TLS 1.2+ enforced on all API
  calls between Azure and Salesforce
- **Encryption at Rest:** Azure Key Vault for secrets and
  certificates; Salesforce Shield Platform Encryption for
  sensitive fields; AES-256 standard
- **Identity & Access:**
  - Azure: Entra ID (AAD) + RBAC with custom roles per
    environment; Managed Identities for service-to-service
  - Salesforce: Permission Sets, Profiles, field-level
    security; Connected App with scoped OAuth permissions
- **API Security:** Azure API Management subscription keys +
  OAuth token validation; Salesforce Connected App IP
  restrictions
- **Secrets Management:** Azure Key Vault (no secrets in
  code, config, or pipelines); rotation policy ≤ 90 days
- **Consent Management:** Explicit consent tracking for
  AI-processed data; opt-out mechanism per GDPR Article 22

### Compliance Requirements

| Standard | Applicability | Validation |
|----------|--------------|------------|
| GDPR | All deployments with EU data subjects | DPA in place, DPIA completed before Pilot |
| SOC 2 Type II | All production deployments | Annual audit; controls mapped to integration |
| HIPAA | Healthcare vertical deployments | BAA with Azure and Salesforce; PHI handling validated |
| PCI DSS | FinServ vertical (if payment data) | Scoped assessment; cardholder data excluded from AI |

## Environments & DevOps

### Environment Strategy

| Environment | Purpose | Salesforce Org | Azure Subscription |
|-------------|---------|---------------|-------------------|
| **Dev** | Feature development & unit testing | Developer Sandbox | Dev resource group |
| **QA** | Integration & regression testing | Partial Copy Sandbox | QA resource group |
| **UAT** | User acceptance testing & demo | Full Copy Sandbox | UAT resource group |
| **Prod** | Live production workloads | Production Org | Prod resource group |

### Salesforce Sandbox Strategy

- Developer Sandboxes for individual feature branches
- Partial Copy Sandbox (QA) refreshed monthly from Production
- Full Copy Sandbox (UAT) refreshed before each release cycle
- Change Sets or Salesforce CLI (sf) for metadata deployment

### CI/CD Pipelines

- **Azure DevOps / GitHub Actions:** Primary CI/CD platform
- **Infrastructure as Code:** Bicep / Terraform for Azure
  resources; Salesforce CLI + metadata API for CRM config
- **Pipeline Stages:** Build → Unit Test → SAST Scan →
  Deploy to QA → Integration Test → Deploy to UAT →
  UAT Sign-off → Deploy to Prod
- **Deployment Cadence:** Biweekly sprint releases; hotfix
  path for critical issues (same-day)
- **Feature Flags:** Azure App Configuration for gradual
  rollout and kill-switch capabilities

### Azure Resource Management

- Separate resource groups per environment
- Azure Policy for tagging, naming, and region enforcement
- Cost Management alerts at 80% and 100% budget thresholds
- Managed Identity for all service-to-service authentication

## Key Milestones & Timeline

| Phase | Milestone | Duration | Key Deliverables | Dependencies |
|-------|-----------|----------|-----------------|-------------|
| **Phase 0: Discovery** | Requirements validated, architecture approved | 4 weeks | Integration manifest, data flow diagrams, security assessment | Salesforce org access, Azure subscription provisioned |
| **Phase 1: POC** | Single use case (case triage) working end-to-end | 6 weeks | Working agent with case triage, Connected App configured, RAG pipeline operational | Discovery sign-off, Salesforce sandbox available |
| **Phase 2: MVP** | All 3 use cases functional in QA | 10 weeks | Case triage + lead qualification + knowledge Q&A, API Management policies, monitoring dashboard | POC sign-off, QA sandbox refreshed |
| **Phase 3: Pilot** | Limited production deployment | 6 weeks | Production deployment for pilot user group (50-100 users), incident runbooks, training materials | MVP sign-off, UAT passed, compliance audit |
| **Phase 4: GA** | Full production rollout | 4 weeks | Organization-wide rollout, SLA enforcement, operational handover | Pilot success criteria met, steering committee approval |
| **Post-GA** | Optimization & expansion | Ongoing | Performance tuning, additional use cases, new Salesforce objects | GA hypercare complete |

**Total estimated timeline: 30 weeks (Discovery through GA)**

## Risk Register

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| R01 | Salesforce API daily rate limits exceeded | Medium | High | Implement caching layer, batch operations via Composite API, monitor quota via APIM policies, request limit increase if needed |
| R02 | Data sync conflicts between Salesforce and Azure AI Search | Medium | Medium | Implement conflict resolution strategy (Salesforce as source of truth), add reconciliation job, use Platform Events for near-real-time sync |
| R03 | AI model drift reducing answer accuracy | Medium | High | Establish accuracy benchmarking pipeline, automated regression tests against golden QA set, monthly evaluation reviews |
| R04 | Salesforce tri-annual release breaking integrations | High | Medium | Subscribe to Salesforce release previews, test in Preview Sandbox before each release, maintain API version pinning strategy |
| R05 | OAuth token expiration causing silent failures | Low | High | Implement proactive token refresh, monitor token lifecycle via APIM, alert on authentication failures |
| R06 | PHI/PII data leakage through AI agent responses | Low | Critical | Azure AI Content Safety filters, output validation rules, field-level security in Salesforce, DLP policies, regular penetration testing |
| R07 | MuleSoft dependency creating delivery bottleneck | Medium | Medium | Design MuleSoft as optional layer; ensure direct REST fallback path is always functional |
| R08 | Organizational resistance to AI-driven automation | Medium | High | Early stakeholder engagement, transparent pilot metrics, human-in-the-loop for high-stakes actions, champion network |
| R09 | Azure AI Foundry service availability issues | Low | High | Multi-region deployment readiness, circuit-breaker patterns in APIM, graceful degradation to manual workflows |
| R10 | Knowledge Article staleness leading to inaccurate answers | Medium | Medium | Automated freshness checks, article last-modified tracking, agent response includes article date, feedback loop for content gaps |

## Budget & Resource Allocation

### Cost Categories

| Category | Description | Estimated Range |
|----------|-------------|----------------|
| **Azure AI Consumption** | Azure OpenAI tokens, AI Search, App Service, Service Bus, APIM, Monitor | $5,000 – $25,000/month (scaling with usage) |
| **Salesforce Licensing** | API call overage, Shield Platform Encryption, additional sandbox licenses | $2,000 – $10,000/month |
| **Development Effort** | Engineering team (6-8 FTEs across roles for 30-week delivery) | Per organizational rate card |
| **Integration Middleware** | Azure API Management premium tier; MuleSoft licenses (if applicable) | $3,000 – $15,000/month |
| **Training & Change Mgmt** | End-user training, documentation, champion program | $10,000 – $30,000 (one-time) |
| **Security & Compliance** | Penetration testing, SOC 2 audit support, DPIA | $15,000 – $40,000 (one-time) |
| **Contingency** | 15% buffer for scope changes and unforeseen issues | 15% of total |

### Funding Model

- Capital expenditure (CapEx) for initial build (Phases 0-4)
- Operational expenditure (OpEx) for ongoing Azure and
  Salesforce consumption post-GA
- Monthly cost review with Finance and Executive Sponsor

### Approval Thresholds

| Amount | Approver |
|--------|----------|
| ≤ $5,000 | Technical Lead |
| $5,001 – $25,000 | Product Owner |
| $25,001 – $100,000 | Executive Sponsor |
| > $100,000 | Steering Committee |

## Communication Plan

### Meeting Cadence

| Meeting | Frequency | Participants | Purpose |
|---------|-----------|-------------|---------|
| Daily Standup | Daily (15 min) | Delivery team | Progress, blockers, coordination |
| Sprint Planning | Biweekly | Delivery team + Product Owner | Sprint scope and commitments |
| Sprint Review / Demo | Biweekly | All stakeholders | Demonstrate completed work |
| Sprint Retrospective | Biweekly | Delivery team | Process improvement |
| Steering Committee | Biweekly (weekly during Pilot/GA) | SC members | Strategic decisions, risk review |
| Architecture Review | Monthly | Tech Lead, Engineers, Security | Technical governance |
| Executive Briefing | Monthly | Exec Sponsor, Product Owner | Budget, timeline, strategic alignment |

### Reporting Structure

- **Weekly Status Report:** Product Owner → Steering Committee
  (RAG status, milestone progress, risks, blockers)
- **Monthly Dashboard:** Technical Lead → Architecture Review
  (system health, API usage, agent performance metrics)
- **Phase Gate Report:** Product Owner → Steering Committee
  (acceptance criteria evidence, go/no-go recommendation)

### Tools

| Tool | Purpose |
|------|---------|
| Microsoft Teams | Daily communication, ad-hoc meetings |
| Azure DevOps / Jira | Backlog management, sprint tracking |
| Confluence / SharePoint | Documentation, decision logs, runbooks |
| Azure Monitor / Application Insights | Operational dashboards |
| Power BI | Executive reporting and KPI dashboards |

## Success Metrics & KPIs

### Quantitative Metrics

| KPI | Baseline | Target | Measurement Method |
|-----|----------|--------|-------------------|
| Case triage automation rate | 0% (manual) | ≥ 70% | SF report: auto-triaged cases / total cases |
| Lead qualification throughput | X leads/day (manual) | 3× baseline | SF report: qualified leads per day |
| Average first-response time | Y minutes (manual) | ≤ 2 minutes | Agent telemetry: time to first response |
| AI answer accuracy | N/A | ≥ 92% | Monthly evaluation against golden QA set |
| Customer satisfaction (CSAT) | Baseline survey score | +15% improvement | Post-interaction survey |
| Operational cost (Tier-1 support) | Current cost baseline | –25% reduction | Finance report: cost per case |
| System availability | N/A | ≥ 99.5% uptime | Azure Monitor: availability metric |
| API error rate | N/A | < 2% | APIM analytics: failed requests / total |
| Knowledge article coverage | N/A | ≥ 85% of FAQs covered | Content audit: mapped articles vs. top queries |

### Qualitative Metrics

- Pilot user satisfaction (NPS ≥ 40)
- Agent (human) sentiment toward AI assistant (survey)
- Stakeholder confidence in AI-driven automation (SC feedback)
- Quality of AI-generated case summaries (expert review)
- Organizational readiness assessment score

## Assumptions, Constraints & Dependencies

### Assumptions

- Salesforce org is Enterprise or Unlimited Edition with
  sufficient API call entitlements.
- Azure subscription is provisioned with required resource
  providers enabled (OpenAI, AI Search, Service Bus, APIM).
- Salesforce Knowledge Base has existing published articles
  of sufficient quality for RAG grounding.
- Existing Salesforce data quality is adequate (duplicate
  management, field completeness) for AI consumption.
- Organizational change management support is available for
  user adoption and training.
- Network connectivity between Azure and Salesforce is
  established (firewall rules, IP allowlisting).

### Constraints

- Salesforce API daily call limits per edition (Enterprise:
  100,000 base + per-license allocation).
- Azure OpenAI regional availability and token rate limits.
- Salesforce tri-annual release cycle (Spring, Summer, Winter)
  may introduce breaking changes requiring regression testing.
- Data residency requirements may dictate Azure region
  selection and Salesforce data center alignment.
- MuleSoft availability is optional and subject to existing
  enterprise licensing agreements.

### Dependencies

| Dependency | Owner | Impact if Delayed |
|-----------|-------|------------------|
| Salesforce sandbox provisioning | Salesforce Admin | Blocks POC start |
| Azure subscription & resource provisioning | Cloud Operations | Blocks all development |
| Connected App configuration & OAuth setup | Salesforce Admin + Security | Blocks integration testing |
| Salesforce Knowledge article audit & enrichment | Content Team | Reduces RAG accuracy |
| Security assessment & DPIA completion | Security Officer | Blocks Pilot deployment |
| User training material development | Change Manager | Reduces Pilot adoption |
| Steering Committee availability for gate reviews | Executive Sponsor | Delays phase transitions |

## Approval & Sign-off

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Executive Sponsor | _________________ | _________________ | __________ |
| Product Owner | _________________ | _________________ | __________ |
| Technical Lead | _________________ | _________________ | __________ |
| Salesforce Admin | _________________ | _________________ | __________ |
| Azure / AI Engineer | _________________ | _________________ | __________ |
| Security / Compliance Officer | _________________ | _________________ | __________ |
| QA Lead | _________________ | _________________ | __________ |
| Change Manager | _________________ | _________________ | __________ |

By signing above, each stakeholder confirms they have reviewed
this constitution and agree to abide by its principles,
governance rules, and decision-making processes.

## Governance

This constitution is the authoritative governance document for
the Salesforce × Azure AI Foundry Agent Integration project.
It supersedes all other practices, guidelines, or ad-hoc
agreements that conflict with its principles.

**Amendment Procedure:**

1. Any stakeholder may propose an amendment by submitting a
   written change request to the Product Owner.
2. The Product Owner assesses impact and routes to the
   appropriate approval authority (see Decision-Making
   Authority above).
3. Amendments affecting Core Principles require Steering
   Committee unanimous approval.
4. All amendments MUST include: rationale, impact assessment,
   migration plan (if behavioral change), and updated version.
5. The constitution version follows semantic versioning:
   - **MAJOR:** Principle removal, redefinition, or
     backward-incompatible governance change.
   - **MINOR:** New principle or section added, material
     expansion of existing guidance.
   - **PATCH:** Clarifications, wording improvements, typo
     fixes, non-semantic refinements.

**Compliance Review:**

- All pull requests and design reviews MUST verify compliance
  with Core Principles.
- Phase gate reviews MUST include a constitution compliance
  checklist.
- Quarterly compliance audits conducted by the Security /
  Compliance Officer.
- Non-compliance findings MUST be remediated before the next
  phase gate or within 10 business days, whichever is sooner.

**Version**: 1.0.0 | **Ratified**: 2026-02-16 | **Last Amended**: 2026-02-16
