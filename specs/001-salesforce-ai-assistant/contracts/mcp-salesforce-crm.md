# MCP Tool Contracts: salesforce-crm Server

**Server Label**: `salesforce-crm`
**Transport**: stdio (notebooks) / SSE (hosted)
**Entry Point**: `mcp_servers/salesforce_crm/server.py`

---

## Tool: `get_account`

**Description**: Retrieve account details by Salesforce ID or account name.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "account_id": {
      "type": "string",
      "description": "Salesforce Account ID (18-char). If provided, exact lookup."
    },
    "account_name": {
      "type": "string",
      "description": "Account name for fuzzy search. Used when account_id is not provided."
    }
  },
  "oneOf": [
    { "required": ["account_id"] },
    { "required": ["account_name"] }
  ]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "account": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "name": { "type": "string" },
        "industry": { "type": "string", "nullable": true },
        "type": { "type": "string", "nullable": true },
        "annual_revenue": { "type": "number", "nullable": true },
        "billing_city": { "type": "string", "nullable": true },
        "billing_state": { "type": "string", "nullable": true },
        "owner_name": { "type": "string", "nullable": true },
        "description": { "type": "string", "nullable": true }
      },
      "required": ["id", "name"]
    },
    "match_count": {
      "type": "integer",
      "description": "Number of matching accounts (>1 triggers disambiguation)"
    },
    "matches": {
      "type": "array",
      "description": "If multiple matches, list of {id, name} for disambiguation",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "string" },
          "name": { "type": "string" }
        }
      }
    }
  }
}
```

### Behavior

- If `account_id` provided: exact lookup by ID. Returns 404 error if not found.
- If `account_name` provided: SOQL `LIKE '%{name}%'` query, limit 5.
  - 1 match: returns full account details.
  - >1 matches: returns `matches` array for disambiguation; `account` is null.
  - 0 matches: returns error message "No accounts found matching '{name}'".

---

## Tool: `search_accounts`

**Description**: Search accounts by name, industry, or owner with pagination.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search term for account name (LIKE match)"
    },
    "industry": {
      "type": "string",
      "description": "Filter by industry picklist value",
      "nullable": true
    },
    "owner_id": {
      "type": "string",
      "description": "Filter by account owner's Salesforce User ID",
      "nullable": true
    },
    "limit": {
      "type": "integer",
      "description": "Maximum results to return",
      "default": 25,
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": ["query"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "accounts": {
      "type": "array",
      "items": { "$ref": "#/definitions/AccountSummary" }
    },
    "total_count": { "type": "integer" },
    "has_more": { "type": "boolean" }
  }
}
```

---

## Tool: `get_contacts_for_account`

**Description**: List contacts for a given account, including opportunity contact roles.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "account_id": {
      "type": "string",
      "description": "Salesforce Account ID"
    },
    "limit": {
      "type": "integer",
      "default": 25,
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": ["account_id"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "contacts": {
      "type": "array",
      "items": { "$ref": "#/definitions/ContactSummary" }
    },
    "total_count": { "type": "integer" }
  }
}
```

---

## Tool: `get_opportunities`

**Description**: List open opportunities with filters for owner, stage, and date range.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "owner_id": {
      "type": "string",
      "description": "Filter by opportunity owner User ID",
      "nullable": true
    },
    "account_id": {
      "type": "string",
      "description": "Filter by account ID",
      "nullable": true
    },
    "stage": {
      "type": "string",
      "description": "Filter by stage name",
      "nullable": true
    },
    "close_date_from": {
      "type": "string",
      "format": "date",
      "description": "Close date range start (YYYY-MM-DD)",
      "nullable": true
    },
    "close_date_to": {
      "type": "string",
      "format": "date",
      "description": "Close date range end (YYYY-MM-DD)",
      "nullable": true
    },
    "include_closed": {
      "type": "boolean",
      "default": false,
      "description": "Include closed deals"
    },
    "limit": {
      "type": "integer",
      "default": 25,
      "minimum": 1,
      "maximum": 50
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "opportunities": {
      "type": "array",
      "items": { "$ref": "#/definitions/OpportunitySummary" }
    },
    "total_count": { "type": "integer" },
    "total_value": { "type": "number" }
  }
}
```

---

## Tool: `get_pipeline_summary`

**Description**: Aggregate pipeline by owner and stage with risk flags applied per `risk_thresholds.yaml`.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "manager_id": {
      "type": "string",
      "description": "Manager User ID — summarize pipeline for all direct reports",
      "nullable": true
    },
    "owner_id": {
      "type": "string",
      "description": "Specific owner User ID — summarize one rep's pipeline",
      "nullable": true
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "total_deals": { "type": "integer" },
    "total_value": { "type": "number" },
    "by_stage": {
      "type": "object",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "count": { "type": "integer" },
          "value": { "type": "number" }
        }
      }
    },
    "at_risk_deals": {
      "type": "array",
      "items": { "$ref": "#/definitions/OpportunitySummary" },
      "description": "Deals matching risk thresholds"
    },
    "owner_breakdown": {
      "type": "object",
      "description": "Per-owner stats (when manager_id used)",
      "additionalProperties": {
        "type": "object",
        "properties": {
          "owner_name": { "type": "string" },
          "deal_count": { "type": "integer" },
          "total_value": { "type": "number" },
          "at_risk_count": { "type": "integer" }
        }
      }
    }
  }
}
```

---

## Tool: `get_case`

**Description**: Retrieve case details by Salesforce Case ID or case number, including recent comments.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "description": "Salesforce Case ID (18-char)"
    },
    "case_number": {
      "type": "string",
      "description": "Case number (e.g., '00012345'). Used when case_id not provided."
    }
  },
  "oneOf": [
    { "required": ["case_id"] },
    { "required": ["case_number"] }
  ]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "case": { "$ref": "#/definitions/CaseSummary" }
  }
}
```

---

## Tool: `create_case`

**Description**: Create a new Salesforce case. **Requires user confirmation before execution.**

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "subject": {
      "type": "string",
      "description": "Case subject line"
    },
    "description": {
      "type": "string",
      "description": "Detailed case description"
    },
    "priority": {
      "type": "string",
      "enum": ["High", "Medium", "Low"],
      "default": "Medium"
    },
    "type": {
      "type": "string",
      "description": "Case type/category",
      "nullable": true
    },
    "account_id": {
      "type": "string",
      "description": "Related account ID",
      "nullable": true
    },
    "contact_id": {
      "type": "string",
      "description": "Related contact ID",
      "nullable": true
    }
  },
  "required": ["subject", "description"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "case_id": { "type": "string" },
    "case_number": { "type": "string" },
    "success": { "type": "boolean" },
    "message": { "type": "string" }
  }
}
```

### Write-Back Protocol

The agent MUST present the proposed case details to the user and wait for explicit confirmation before calling this tool. The system prompt enforces this behavior.

---

## Tool: `update_case`

**Description**: Update case fields (priority, status, type) and/or add an internal comment. **Requires user confirmation.**

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "case_id": {
      "type": "string",
      "description": "Salesforce Case ID to update"
    },
    "priority": {
      "type": "string",
      "enum": ["High", "Medium", "Low"],
      "nullable": true
    },
    "status": {
      "type": "string",
      "nullable": true
    },
    "type": {
      "type": "string",
      "nullable": true
    },
    "comment": {
      "type": "string",
      "description": "Internal comment to add to the case",
      "nullable": true
    }
  },
  "required": ["case_id"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "message": { "type": "string" },
    "updated_fields": {
      "type": "array",
      "items": { "type": "string" }
    }
  }
}
```

---

## Tool: `get_recent_activities`

**Description**: List recent tasks and events for an account, contact, or opportunity.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "related_to_id": {
      "type": "string",
      "description": "Account, Contact, or Opportunity ID"
    },
    "days": {
      "type": "integer",
      "default": 30,
      "description": "Look back N days",
      "minimum": 1,
      "maximum": 90
    },
    "limit": {
      "type": "integer",
      "default": 25,
      "minimum": 1,
      "maximum": 50
    }
  },
  "required": ["related_to_id"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "activities": {
      "type": "array",
      "items": { "$ref": "#/definitions/ActivitySummary" }
    },
    "total_count": { "type": "integer" }
  }
}
```

---

## Tool: `create_task`

**Description**: Log a new task in Salesforce. **Requires user confirmation.**

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "subject": {
      "type": "string",
      "description": "Task subject"
    },
    "description": {
      "type": "string",
      "description": "Task description",
      "nullable": true
    },
    "due_date": {
      "type": "string",
      "format": "date",
      "description": "Due date (YYYY-MM-DD)",
      "nullable": true
    },
    "related_to_id": {
      "type": "string",
      "description": "Account or Opportunity ID (WhatId)",
      "nullable": true
    },
    "who_id": {
      "type": "string",
      "description": "Contact or Lead ID (WhoId)",
      "nullable": true
    },
    "priority": {
      "type": "string",
      "enum": ["High", "Normal", "Low"],
      "default": "Normal"
    }
  },
  "required": ["subject"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "task_id": { "type": "string" },
    "success": { "type": "boolean" },
    "message": { "type": "string" }
  }
}
```

---

## Tool: `get_leads`

**Description**: List leads with filters for status, owner, and source.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "status": {
      "type": "string",
      "description": "Filter by lead status picklist value",
      "nullable": true
    },
    "owner_id": {
      "type": "string",
      "description": "Filter by lead owner User ID",
      "nullable": true
    },
    "lead_source": {
      "type": "string",
      "description": "Filter by lead source",
      "nullable": true
    },
    "limit": {
      "type": "integer",
      "default": 25,
      "minimum": 1,
      "maximum": 50
    }
  }
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "leads": {
      "type": "array",
      "items": { "$ref": "#/definitions/LeadSummary" }
    },
    "total_count": { "type": "integer" }
  }
}
```

---

## Tool: `update_lead_status`

**Description**: Update a lead's qualification status. **Requires user confirmation.**

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "lead_id": {
      "type": "string",
      "description": "Salesforce Lead ID"
    },
    "status": {
      "type": "string",
      "description": "New lead status (e.g., 'Working', 'Qualified', 'Unqualified')"
    }
  },
  "required": ["lead_id", "status"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "success": { "type": "boolean" },
    "message": { "type": "string" },
    "previous_status": { "type": "string" },
    "new_status": { "type": "string" }
  }
}
```

---

## Tool: `get_team_members`

**Description**: List active users reporting to a given manager.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "manager_id": {
      "type": "string",
      "description": "Manager's Salesforce User ID"
    }
  },
  "required": ["manager_id"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "team_members": {
      "type": "array",
      "items": { "$ref": "#/definitions/TeamMember" }
    },
    "count": { "type": "integer" }
  }
}
```

---

## Error Response Schema (all tools)

```json
{
  "type": "object",
  "properties": {
    "error": {
      "type": "object",
      "properties": {
        "code": {
          "type": "string",
          "enum": [
            "NOT_FOUND",
            "PERMISSION_DENIED",
            "RATE_LIMIT_WARNING",
            "RATE_LIMIT_EXCEEDED",
            "INVALID_INPUT",
            "SF_API_ERROR",
            "AUTH_ERROR"
          ]
        },
        "message": { "type": "string" },
        "details": { "type": "object", "nullable": true }
      },
      "required": ["code", "message"]
    }
  }
}
```
