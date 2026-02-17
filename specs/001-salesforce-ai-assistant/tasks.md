# Tasks: Salesforce AI Assistant

**Input**: Design documents from `/specs/001-salesforce-ai-assistant/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included to align with the CI pipeline (`ci.yml`) which runs
unit and contract tests on every PR.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- Single project layout with MCP servers under `mcp_servers/`, shared code under `shared/`, notebooks under `notebooks/`
- Infrastructure as Code under `infra/bicep/`
- CI/CD under `.github/workflows/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization, skeleton repo, and dev-environment IaC

- [x] T001 Create project root structure with `pyproject.toml`, `requirements.txt`, `requirements-dev.txt`, and `.gitignore`
- [x] T001a [P] Document data classification for all Salesforce objects and integration data per constitution Principle II: classify each data element as Public, Internal, Confidential, or Restricted in `docs/data-classification.md`
- [x] T002 [P] Create `.env.example` with all required environment variables documented in plan.md
- [x] T003 [P] Create `config/risk_thresholds.yaml` with configurable deal-risk signal thresholds per plan.md
- [x] T004 [P] Create `scripts/bootstrap_env.sh` to set up venv, install deps, and copy `.env.example` to `.env`
- [x] T005 [P] Create `infra/bicep/modules/storage.bicep` per contracts/bicep-modules.md Storage module contract
- [x] T006 [P] Create `infra/bicep/modules/keyvault.bicep` per contracts/bicep-modules.md Key Vault module contract
- [x] T007 [P] Create `infra/bicep/modules/app-insights.bicep` per contracts/bicep-modules.md App Insights module contract
- [x] T008 Create `infra/bicep/main.bicep` orchestrator with foundation modules (storage, keyvault, app-insights) per plan.md main.bicep design
- [x] T009 Create `infra/bicep/env/dev.bicepparam` with dev environment values per plan.md parameterization section
- [x] T010 [P] Create `.github/workflows/ci.yml` with Python lint, type check, unit tests, and Bicep validate per plan.md CI workflow

**Checkpoint**: Skeleton repo exists, dev IaC validates, CI pipeline runs

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core shared modules that ALL user stories depend on — MCP servers cannot be built without these

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T011 Implement `shared/config.py` with environment loader, `.env` parsing via python-dotenv, config validation, and `McpConfig` dataclass with `transport`, `crm_url`, `kb_url`, and `hosting_mode` fields (populated from `MCP_TRANSPORT`, `MCP_CRM_URL`, `MCP_KB_URL`, `HOSTING_MODE` env vars)
- [x] T012 [P] Implement `shared/models.py` with all Pydantic response models from data-model.md: AccountSummary, ContactSummary, OpportunitySummary, PipelineSummary, CaseSummary, KnowledgeArticle, ActivitySummary, LeadSummary, TeamMember
- [x] T012a [P] Write unit tests `tests/unit/test_models.py` for all Pydantic response models from data-model.md
- [x] T013 [P] Implement `shared/auth.py` with OAuth 2.0 flow helpers and token refresh logic per research.md Section 4
- [x] T014 Implement `shared/salesforce_client.py` with simple-salesforce wrapper, per-user auth, SOQL query helper, and API rate tracking per research.md Section 5
- [x] T014a [P] Write unit tests `tests/unit/test_salesforce_client.py` for SF client wrapper, auth error handling, and rate tracking
- [x] T015 [P] Create `mcp_servers/salesforce_crm/__init__.py` and `mcp_servers/salesforce_crm/server.py` with FastMCP server skeleton (empty tool registrations)
- [x] T016 [P] Create `mcp_servers/salesforce_knowledge/__init__.py` and `mcp_servers/salesforce_knowledge/server.py` with FastMCP server skeleton
- [x] T017 [P] Author `agents/sales/system_prompt.md` with Sales Agent instructions, grounding constraints, and citation requirements
- [x] T018 [P] Author `agents/service/system_prompt.md` with Service Agent instructions, triage guidelines, and KB citation requirements
- [x] T019 [P] Create `infra/bicep/modules/ai-foundry.bicep` per contracts/bicep-modules.md AI Foundry module contract (Hub + Project)
- [x] T020 [P] Create `infra/bicep/modules/openai.bicep` per contracts/bicep-modules.md OpenAI module contract (account + GPT-4o deployment)
- [x] T021 [P] Create `infra/bicep/modules/ai-search.bicep` per contracts/bicep-modules.md AI Search module contract
- [x] T022 Update `infra/bicep/main.bicep` to add ai-foundry, openai, and ai-search modules with dependency wiring per plan.md Module Dependency Graph
- [x] T023 [P] Create `infra/bicep/env/test.bicepparam` with test environment values per plan.md parameterization section (includes `hostingMode` = `'appService'` or `'aca'`, `appServiceSkuName`, `acrSku` parameters)
- [x] T024 [P] Create `infra/bicep/env/prod.bicepparam` with prod environment values per plan.md parameterization section (includes `hostingMode` = `'appService'` or `'aca'`, `appServiceSkuName`, `acrSku` parameters, premium Key Vault HSM, ZRS storage)
- [x] T025 Create `.github/workflows/deploy-infra.yml` with OIDC auth, Bicep lint, what-if validation, and progressive deployment (dev → test → prod) per plan.md deploy-infra.yml design
- [x] T025a [P] Design and implement Knowledge Article sync pipeline: incremental indexing from Salesforce KnowledgeArticleVersion to Azure AI Search index (scheduled or event-driven) — required for RAG-based response grounding in US3/US4

**Checkpoint**: Foundation ready — shared modules importable, both MCP server skeletons startable, all Bicep modules validate, CI/CD pipelines operational. User story implementation can now begin.

---

## Phase 3: User Story 1 — Meeting Preparation Assistant (Priority: P1) 🎯 MVP

**Goal**: AEs ask "Prepare me for my meeting with [Account]" and get a complete briefing with account overview, contacts, opportunities, activities, and talking points.

**Independent Test**: Ask the assistant "Prepare me for my meeting with Acme Corp" — verify briefing includes account summary, key contacts, open opportunities, recent activities, and recommended talking points.

### Implementation for User Story 1

- [x] T026 [P] [US1] Implement `mcp_servers/salesforce_crm/tools/accounts.py` with `get_account` and `search_accounts` per contracts/mcp-salesforce-crm.md
- [x] T027 [P] [US1] Implement `mcp_servers/salesforce_crm/tools/contacts.py` with `get_contacts_for_account` per contracts/mcp-salesforce-crm.md
- [x] T028 [P] [US1] Implement `mcp_servers/salesforce_crm/tools/opportunities.py` with `get_opportunities` and `get_pipeline_summary` per contracts/mcp-salesforce-crm.md
- [x] T029 [P] [US1] Implement `mcp_servers/salesforce_crm/tools/activities.py` with `get_recent_activities` and `create_task` per contracts/mcp-salesforce-crm.md
- [x] T030 [US1] Register account, contact, opportunity, and activity tools in `mcp_servers/salesforce_crm/server.py`
- [x] T030a Write contract tests `tests/contract/test_crm_tools.py` for all 13 CRM MCP tools against mock Salesforce responses
- [x] T031 [US1] Implement `notebooks/02_sales_account_briefing.ipynb` with all 8 cells per plan.md Notebook 2 design (env setup → MCP connection → Sales Agent → briefing query → follow-up → cleanup)

**Checkpoint**: User Story 1 fully functional — AEs can get meeting briefings grounded in live Salesforce data via notebook

---

## Phase 4: User Story 2 — Pipeline Summary & Risk Flagging (Priority: P1)

**Goal**: Sales Managers ask for a team pipeline summary and get deals grouped by AE with at-risk deals flagged and reasons provided.

**Independent Test**: Ask "Show me my team's pipeline and flag at-risk deals" — verify response includes deal list by owner, risk indicators (stalled stage, overdue close, no activity), and recommended actions.

### Implementation for User Story 2

- [x] T032 [P] [US2] Implement `mcp_servers/salesforce_crm/tools/users.py` with `get_team_members` per contracts/mcp-salesforce-crm.md
- [x] T033 [US2] Add pipeline risk-analysis logic to `mcp_servers/salesforce_crm/tools/opportunities.py` using thresholds from `config/risk_thresholds.yaml`
- [x] T034 [US2] Register user tools in `mcp_servers/salesforce_crm/server.py`
- [x] T035 [US2] Implement `notebooks/01_sales_pipeline_summary.ipynb` with all 9 cells per plan.md Notebook 1 design (env setup → MCP connection → Sales Agent → pipeline query → risk flags → AE-specific follow-up → cleanup)

**Checkpoint**: User Stories 1 AND 2 both work independently — meeting prep and pipeline analysis functional

---

## Phase 5: User Story 3 — Case Triage & Response Assistance (Priority: P1)

**Goal**: CSRs present a case to the assistant and get priority recommendation, category, draft response grounded in KB articles, and source citations.

**Independent Test**: Present case #12345 and ask "Triage this case and suggest a response" — verify priority, category, draft response, and KB article citations returned. Confirm write-back requires explicit CSR approval.

### Implementation for User Story 3

- [x] T036 [P] [US3] Implement `mcp_servers/salesforce_crm/tools/cases.py` with `get_case`, `create_case`, and `update_case` per contracts/mcp-salesforce-crm.md
- [x] T037 [P] [US3] Implement `mcp_servers/salesforce_knowledge/tools/articles.py` with `search_articles` (SOSL + SOQL fallback) and `get_article_by_id` per contracts/mcp-salesforce-knowledge.md
- [x] T038 [US3] Register case tools in `mcp_servers/salesforce_crm/server.py` and knowledge tools in `mcp_servers/salesforce_knowledge/server.py`
- [x] T038a Write contract tests `tests/contract/test_knowledge_tools.py` for search_articles and get_article_by_id against mock Salesforce responses
- [x] T039 [US3] Implement write-back confirmation protocol in `shared/salesforce_client.py` — all write operations (create_case, update_case) require explicit user confirmation before execution
- [x] T039a [P] [US3] Implement idempotent write guards for `create_case` and `create_task` in `shared/salesforce_client.py` — use check-before-write (query by external reference or subject+account+timestamp dedup window) to prevent duplicate records on retry, per spec.md NFR-reliability
- [x] T040 [US3] Implement `notebooks/03_service_case_triage.ipynb` with all 9 cells per plan.md Notebook 3 design (env setup → dual MCP connections → Service Agent → triage query → display results → user confirms write-back → verify update → cleanup)

**Checkpoint**: User Stories 1, 2, AND 3 all work independently — Sales and Service core scenarios operational

---

## Phase 6: User Story 4 — Natural-Language CRM Query (Priority: P2)

**Goal**: Any user asks natural-language questions about Salesforce data and gets accurate, scoped answers without building reports.

**Independent Test**: Ask "How many open opportunities do I have closing this quarter?" and verify accurate count with deal list. Ask an ambiguous question and verify the assistant asks a clarifying follow-up.

### Implementation for User Story 4

- [x] T041 [US4] Implement `notebooks/04_service_kb_assistant.ipynb` with all 8 cells per plan.md Notebook 4 design (env setup → MCP connection → Service Agent → KB query → follow-up → cleanup)
- [x] T042 [US4] Add disambiguation logic to MCP server responses — when queries match multiple records or are ambiguous, return distinguishing details and prompt for clarification via `search_accounts` multi-match handling

**Checkpoint**: User Stories 1–4 all work independently — ad-hoc CRM querying and KB search functional

---

## Phase 7: User Story 5 — Next Best Action Recommendations (Priority: P2)

**Goal**: AEs ask "What should I focus on today?" and get prioritized action recommendations with supporting reasoning from Salesforce data.

**Independent Test**: Ask "What should I do next for my top deals?" — verify prioritized recommendations with supporting context (e.g., "Schedule follow-up with decision maker at Acme — no contact in 14 days").

### Implementation for User Story 5

- [x] T043 [US5] Enhance Sales Agent system prompt in `agents/sales/system_prompt.md` with next-best-action reasoning instructions — incorporate deal stage, activity gaps, close date proximity, and contact engagement signals
- [x] T044 [US5] Add activity-gap and contact-engagement analysis helpers to `mcp_servers/salesforce_crm/tools/opportunities.py` for NBA support

**Checkpoint**: User Stories 1–5 all work — AEs can get proactive action recommendations

---

## Phase 8: User Story 6 — Case Queue Monitoring (Priority: P3)

**Goal**: Support Managers ask for queue status and get case counts by status, aging distribution, and SLA compliance indicators.

**Independent Test**: Ask "Show me the case queue status for my team" — verify case counts, aging, and SLA indicators returned.

### Implementation for User Story 6

- [x] T045 [US6] Add queue-level aggregation queries to `mcp_servers/salesforce_crm/tools/cases.py` — case counts by status/priority, aging buckets, SLA breach detection using BusinessHours
- [x] T046 [US6] Enhance Service Agent system prompt in `agents/service/system_prompt.md` with queue monitoring and pattern-detection instructions

**Checkpoint**: User Stories 1–6 all work — Support Managers can monitor queues

---

## Phase 9: User Story 7 — Orchestrator-Coordinated Multi-Domain Workflow (Priority: P3)

**Goal**: Users ask cross-domain questions (spanning sales and service) and get unified results from both agents in a single conversation.

**Independent Test**: Ask "Which of my accounts have both open deals and open support cases?" — verify unified response with deal and case details from both domains.

### Implementation for User Story 7

- [x] T047 [US7] Implement orchestrator agent configuration in `notebooks/05_orchestrator_multi_domain.ipynb`: create an Orchestrator Agent with both Sales Agent and Service Agent as sub-agents via MCP toolset. The Orchestrator uses `azure-ai-projects` Agent API with a combined `McpToolConnection` that includes both `salesforce-crm` and `salesforce-knowledge` MCP servers. System prompt instructs the Orchestrator to route sales-domain questions to Sales Agent tools and service-domain questions to Service Agent tools.
- [x] T048 [US7] Implement cross-domain context linking — ensure Orchestrator maintains context when user pivots from service to sales questions within the same thread by leveraging the Foundry Agent thread state. Validate with test: "What are the top cases today?" followed by "And what deals do those same accounts have?"
- [x] T048a Write integration tests `tests/integration/test_agent_e2e.py` covering multi-turn conversation and cross-domain orchestration

**Checkpoint**: All 7 user stories functional — full feature scope delivered

---

## Phase 10: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, hardening, observability, security, and production readiness

- [x] T049 [P] Write `docs/salesforce-setup.md` with Connected App creation steps, OAuth scopes, IP allowlisting, and Permission Set configuration
- [x] T050 [P] Write `docs/azure-setup.md` with manual provisioning alternative, Bicep module reference, and per-environment guidance
- [x] T051 [P] Write `docs/extending-scenarios.md` with instructions for adding new MCP tools and notebooks
- [x] T051a [P] Write `docs/hosting-modes.md` with App Service vs ACA comparison table, cost analysis (idle/light-load monthly costs for each SKU tier), migration guide from `deployAppService` boolean to `hostingMode` enum, security parity documentation (managed identity, TLS, HTTPS, Key Vault for both), and recommendation guidance (ACA Consumption for intermittent/demo, App Service for operational simplicity) per research.md Sections 1, 9, 10
- [x] T052 Write root `README.md` with project overview, architecture diagram, quickstart pointer, and contributor guidelines
- [x] T053 [P] Add Application Insights telemetry to both MCP servers (`mcp_servers/salesforce_crm/server.py` and `mcp_servers/salesforce_knowledge/server.py`) using APPLICATIONINSIGHTS_CONNECTION_STRING from `.env`
- [x] T053a [P] Add write-back audit logging: log all AI-initiated Salesforce write-back actions (user, timestamp, operation, data written) to Application Insights custom events per FR-016
- [x] T053b [P] Configure Azure Monitor alert rules: API rate-limit proximity (>80%), MCP server error rate (>2%), and OAuth authentication failures per constitution Principle V
- [x] T053c [P] Write incident runbooks for: (1) Salesforce API rate-limit exceeded, (2) OAuth token refresh failure, (3) MCP server crash/restart, (4) Azure OpenAI service degradation — store in `docs/runbooks/`
- [x] T054 [P] Implement `mcp_servers/salesforce_crm/tools/leads.py` with `get_leads` and `update_lead_status` per contracts/mcp-salesforce-crm.md and register in `server.py`
- [x] T054a [P] Create Microsoft Teams bot registration (Azure Bot Service resource + Bicep module `infra/bicep/modules/bot-service.bicep`) and configure Foundry Agent channel binding per FR-012
- [x] T054b Test end-to-end assistant experience within a Teams chat thread, validating multi-turn conversation, write-back confirmation UX, error messages, and verify typing indicator is shown for queries exceeding 3 seconds per spec.md NFR-latency
- [x] T055 Edge-case hardening: implement rate-limit warning/exceeded handling, auth-error recovery, large-result-set bounding (top 50 with narrowing guidance), ambiguous-account disambiguation, stale-data re-validation before write-back, and user-identity/Salesforce-user-mapping failure handling (prompt user to verify identity) across all MCP tools
- [x] T055a Add output sanitisation to system prompts (`agents/sales/system_prompt.md`, `agents/service/system_prompt.md`): suppress raw Salesforce record IDs (15/18-char), internal field API names, and system metadata from user-facing responses per spec.md data-access principles and NFR-security
- [x] T056 [P] Create `infra/bicep/modules/app-service.bicep` per contracts/bicep-modules.md App Service module contract (optional hosted MCP/SSE)
- [x] T057 Update `infra/bicep/main.bicep`: replace `deployAppService` boolean with `@allowed(['none', 'appService', 'aca'])` `hostingMode` enum parameter, add conditional hosting modules (App Service when `hostingMode == 'appService'`, ACR + ACA when `hostingMode == 'aca'`), add `mcpCrmUrl`, `mcpKnowledgeUrl`, `acrLoginServer`, `hostingMode` outputs per plan.md main.bicep design
- [x] T057a [P] Create `infra/bicep/modules/container-registry.bicep` per contracts/bicep-modules.md Container Registry module contract (ACR Basic/Standard SKU, admin user disabled, outputs: `acrId`, `acrName`, `acrLoginServer`) — only deployed when `hostingMode == 'aca'`
- [x] T057b Create `infra/bicep/modules/container-apps.bicep` per contracts/bicep-modules.md Container Apps module contract (ACA Environment + 2 Container Apps for CRM & KB servers, Log Analytics integration, managed identity with `AcrPull` role on ACR, HTTPS-only ingress port 8000, liveness/readiness health probes at `/health`, Consumption workload profile, scale-to-zero with 0–3 replicas, outputs: `crmAppFqdn`, `knowledgeAppFqdn`, `crmPrincipalId`, `knowledgePrincipalId`) — only deployed when `hostingMode == 'aca'`
- [x] T057c Create `Dockerfile` in project root with multi-stage build: `base` stage (python:3.11-slim, install requirements.txt, copy shared/ and config/), `crm-server` target (copy mcp_servers/salesforce_crm/, EXPOSE 8000, CMD python -m mcp_servers.salesforce_crm.server), `knowledge-server` target (copy mcp_servers/salesforce_knowledge/, EXPOSE 8000, CMD python -m mcp_servers.salesforce_knowledge.server) per research.md Dockerfile strategy
- [x] T057d Create `scripts/deploy_app.sh` with unified deployment script: accept `<environment> [hosting-mode]` args, auto-detect `hostingMode` from `.env.azure` `HOSTING_MODE` variable, route to zip deploy for `appService` (`az webapp deploy`) or Docker build+push+update for `aca` (`docker build --target`, `az acr login`, `docker push`, `az containerapp update`), no-op for `hostingMode=none` per research.md deployment script strategy
- [x] T057e Update `.bicepparam` files (`infra/bicep/env/dev.bicepparam`, `test.bicepparam`, `prod.bicepparam`): replace `deployAppService` boolean parameter with `hostingMode` enum (`'none'` for dev, `'appService'` or `'aca'` for test/prod), add `acrSku` and `containerImageTag` parameters for ACA environments per plan.md parameterization section
- [x] T057f [P] Update CI/CD `.github/workflows/deploy-infra.yml`: add `HOSTING_MODE` workflow input with options (`appService`, `aca`), add Docker build+push job for ACA path (build both targets, push to ACR), add `deploy_app.sh` call after infra deployment per research.md CI/CD pipeline updates
- [x] T058 Create `scripts/provision_azure.sh` wrapping `az deployment sub create` with env argument, what-if preview, and output capture to `.env.azure` per plan.md provision_azure.sh design — extract `hostingMode`, `mcpCrmUrl`, `mcpKnowledgeUrl`, `acrLoginServer` from Bicep outputs and print hosting-mode-specific next steps (e.g., "Run scripts/deploy_app.sh" for ACA)
- [x] T059 Final review: run all 4 notebooks end-to-end against a real Salesforce org and verify all acceptance scenarios from spec.md
- [x] T060 Security review: validate Key Vault access policies, RBAC assignments, OIDC configuration, network rules, and `@secure()` usage across all Bicep modules
- [x] T060a [P] Create accuracy benchmarking pipeline: define golden QA set of representative queries with expected answers, run automated evaluation against agent responses, and establish prompt-revision thresholds per constitution Principle III (model drift monitoring)
- [x] T060b [P] Document rollback procedures for each deployment phase: Bicep resource rollback via `az deployment` revert, MCP server version rollback, agent prompt rollback — store in `docs/runbooks/rollback.md` per constitution Principle IV
- [x] T060c [P] Create post-pilot user satisfaction survey template and measurement plan for SC-006 (target: 90% report "makes their job easier")
- [x] T060d [P] Run performance/load testing: simulate 50 concurrent users executing representative query mix (simple + complex), validate P95 latency stays within spec thresholds (≤ 5s simple, ≤ 15s complex) per SC-008

**Checkpoint**: Production-ready — all documentation complete, observability instrumented, security reviewed, IaC covers all environments

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion — **BLOCKS all user stories**
- **User Stories (Phases 3–9)**: All depend on Foundational phase completion
  - US1 (Phase 3): No dependencies on other stories
  - US2 (Phase 4): Shares opportunity tools with US1 but independently testable
  - US3 (Phase 5): Requires case + knowledge tools — independent of US1/US2
  - US4 (Phase 6): Builds on all prior tools — best after US1–US3 but independently testable
  - US5 (Phase 7): Builds on US1/US2 opportunity tools — depends on Phase 3 tools
  - US6 (Phase 8): Builds on US3 case tools — depends on Phase 5 tools
  - US7 (Phase 9): Requires both Sales and Service agents — depends on Phases 3 and 5
- **Polish (Phase 10)**: Depends on all desired user stories being complete
  - ACA hosting tasks (T057a–T057f, T051a) are additive — existing App Service tasks (T056, T057) remain unchanged
  - T057b (container-apps.bicep) depends on T057a (container-registry.bicep) and T007 (app-insights.bicep)
  - T057d (deploy_app.sh) depends on T057 (main.bicep hostingMode), T057c (Dockerfile)
  - T057e (.bicepparam migration) depends on T057 (main.bicep hostingMode)

### User Story Dependencies

- **US1 (P1)**: Can start after Foundational (Phase 2) — **No dependencies on other stories**
- **US2 (P1)**: Shares `opportunities.py` with US1 — can start after Phase 2 but benefits from US1 tools
- **US3 (P1)**: Can start after Foundational (Phase 2) — **No dependencies on other stories** (uses cases + knowledge, not sales tools)
- **US4 (P2)**: Uses tools from US1–US3 — start after Phase 5
- **US5 (P2)**: Extends opportunity analysis from US1/US2 — start after Phase 4
- **US6 (P3)**: Extends case analysis from US3 — start after Phase 5
- **US7 (P3)**: Requires both domain agents — start after Phases 4 and 5

### Within Each User Story

- Models/shared code before tool implementations
- Tool implementations before server registration
- Server registration before notebook implementation
- Core implementation before integration

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel (T002–T007, T010)
- All Foundational tasks marked [P] can run in parallel (T012–T013, T015–T021, T023–T024)
- US1 and US3 can proceed in parallel after Phase 2 (different tool files, different MCP servers)
- Tool implementations within a story marked [P] can run in parallel (e.g., T026–T029, T036–T037)
- All Polish [P] tasks can run in parallel (T049–T051a, T053–T054, T056, T057a, T057f)

---

## Parallel Example: Phases 3 + 5 (US1 + US3 in Parallel)

```bash
# Developer A: User Story 1 (Meeting Prep)
Task T026: "Implement accounts.py with get_account, search_accounts"
Task T027: "Implement contacts.py with get_contacts_for_account"
Task T028: "Implement opportunities.py with get_opportunities, get_pipeline_summary"
Task T029: "Implement activities.py with get_recent_activities, create_task"
Task T030: "Register tools in salesforce_crm server.py"
Task T031: "Implement Notebook 02 (account briefing)"

# Developer B: User Story 3 (Case Triage) — PARALLEL with Developer A
Task T036: "Implement cases.py with get_case, create_case, update_case"
Task T037: "Implement articles.py with search_articles, get_article_by_id"
Task T038: "Register tools in both server.py files"
Task T039: "Implement write-back confirmation protocol"
Task T040: "Implement Notebook 03 (case triage)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL — blocks all stories)
3. Complete Phase 3: User Story 1 (Meeting Prep)
4. **STOP and VALIDATE**: Test US1 independently — "Prepare me for my meeting with Acme Corp"
5. Deploy/demo if ready — this is the highest-impact proof of value

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add US1 (Meeting Prep) → Test independently → Demo (MVP!)
3. Add US2 (Pipeline Risk) → Test independently → Demo
4. Add US3 (Case Triage) → Test independently → Demo (Service MVP!)
5. Add US4 (NL Query) → Test independently → Demo
6. Add US5 (Next Best Action) → Test independently → Demo
7. Add US6 (Queue Monitoring) → Test independently → Demo
8. Add US7 (Orchestrator) → Test independently → Demo (Full feature!)
9. Polish → Production readiness

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: US1 (Meeting Prep) → US2 (Pipeline) → US5 (NBA)
   - Developer B: US3 (Case Triage) → US6 (Queue Monitoring)
   - Developer C: IaC (T056–T058, T057a–T057f) + Documentation (T049–T052)
3. After A+B complete: US4 (NL Query) → US7 (Orchestrator) → Polish
4. Stories complete and integrate independently

### Suggested MVP Scope

**MVP = Phase 1 + Phase 2 + Phase 3 (User Story 1 only)**
- Delivers: Account meeting briefing via notebook
- Proves: End-to-end Agent Framework → MCP → Salesforce integration
- Time estimate: ~2 weeks (Phase 1: 3 days, Phase 2: 5 days, Phase 3: 2 days)

---

## Notes

- [P] tasks = different files, no dependencies on in-progress tasks
- [Story] label maps task to specific user story for traceability
- Each user story is independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All Bicep modules follow contracts/bicep-modules.md parameter/output contracts
- All MCP tools follow contracts/mcp-salesforce-crm.md and mcp-salesforce-knowledge.md schemas
- All Bicep hosting modules follow contracts/bicep-modules.md (including new container-registry.bicep and container-apps.bicep contracts)
- ACA hosting tasks (T057a–T057f, T051a) are additive — existing App Service tasks remain unchanged; `deployAppService` boolean is migrated to `hostingMode` enum per research.md Section 2
- Risk thresholds are configurable via `config/risk_thresholds.yaml` (not hardcoded)
