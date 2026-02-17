# MCP Tool Contracts: salesforce-knowledge Server

**Server Label**: `salesforce-knowledge`
**Transport**: stdio (notebooks) / SSE (hosted)
**Entry Point**: `mcp_servers/salesforce_knowledge/server.py`

---

## Tool: `search_articles`

**Description**: Search Salesforce Knowledge Articles by keyword with relevance ranking. Uses SOSL for full-text search when available, falls back to SOQL LIKE queries.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "query": {
      "type": "string",
      "description": "Search keywords (natural language or specific terms)"
    },
    "language": {
      "type": "string",
      "default": "en_US",
      "description": "Article language filter"
    },
    "limit": {
      "type": "integer",
      "default": 10,
      "minimum": 1,
      "maximum": 25
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
    "articles": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "string",
            "description": "Knowledge Article Version ID"
          },
          "title": { "type": "string" },
          "summary": {
            "type": "string",
            "nullable": true,
            "description": "Article summary/excerpt"
          },
          "url_name": {
            "type": "string",
            "nullable": true,
            "description": "URL-safe article identifier"
          },
          "last_published": {
            "type": "string",
            "format": "date-time",
            "nullable": true
          },
          "article_type": {
            "type": "string",
            "nullable": true
          }
        },
        "required": ["id", "title"]
      }
    },
    "total_count": { "type": "integer" },
    "search_method": {
      "type": "string",
      "enum": ["sosl", "soql"],
      "description": "Search method used"
    }
  }
}
```

### Behavior

- **Primary**: Use SOSL (`FIND {query} RETURNING KnowledgeArticleVersion(...)`) for relevance-ranked results.
- **Fallback**: If SOSL fails or is unavailable, use SOQL `WHERE Title LIKE '%{query}%'`.
- Only returns articles with `PublishStatus = 'Online'`.
- Results include title and summary only (not full body — use `get_article_by_id` for that).

---

## Tool: `get_article_by_id`

**Description**: Retrieve the full content of a Knowledge Article by its version ID.

### Input Schema

```json
{
  "type": "object",
  "properties": {
    "article_id": {
      "type": "string",
      "description": "Knowledge Article Version ID"
    }
  },
  "required": ["article_id"]
}
```

### Output Schema

```json
{
  "type": "object",
  "properties": {
    "article": {
      "type": "object",
      "properties": {
        "id": { "type": "string" },
        "title": { "type": "string" },
        "summary": {
          "type": "string",
          "nullable": true
        },
        "body": {
          "type": "string",
          "description": "Full article content (HTML or plain text, stripped of tags)"
        },
        "url_name": {
          "type": "string",
          "nullable": true
        },
        "last_published": {
          "type": "string",
          "format": "date-time",
          "nullable": true
        },
        "article_type": {
          "type": "string",
          "nullable": true
        }
      },
      "required": ["id", "title", "body"]
    }
  }
}
```

### Behavior

- Retrieves the full article content including the `ArticleBody` field.
- HTML content is stripped to plain text for agent consumption.
- Returns 404 error if article not found or not published.

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
            "AUTH_ERROR",
            "KNOWLEDGE_DISABLED"
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

### Special Error: `KNOWLEDGE_DISABLED`

Returned when the Salesforce org does not have Knowledge enabled or the user's profile lacks `ViewAllKnowledge` permission. The agent should inform the user that Salesforce Knowledge must be enabled by an admin.
