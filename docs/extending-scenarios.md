# Extending Scenarios

This guide explains how to add new MCP tools, agents, and notebooks to the Salesforce AI Assistant project.

## Adding a New MCP Tool

### Step 1: Define the Tool Contract

Add input/output JSON schemas to the appropriate contract file:
- Sales tools → `specs/.../contracts/mcp-salesforce-crm.md`
- Knowledge tools → `specs/.../contracts/mcp-salesforce-knowledge.md`

### Step 2: Create the Pydantic Model (if needed)

Add a response model to `shared/models.py`:

```python
class MyNewModel(BaseModel):
    """Description of the model."""
    id: str
    name: str
    # ... fields matching your contract
```

### Step 3: Implement the Tool

Create a new file in the appropriate tools directory:

```python
# mcp_servers/salesforce_crm/tools/my_tool.py

from __future__ import annotations
from typing import Any
from mcp_servers.salesforce_crm.server import _get_sf_client, mcp
from shared.models import MyNewModel
from shared.salesforce_client import SalesforceClientError

@mcp.tool()
def my_new_tool(param1: str, param2: int = 10) -> dict[str, Any]:
    """Tool description for the LLM to understand when to use this tool.

    Args:
        param1: Description of param1.
        param2: Description of param2 (default: 10).
    """
    try:
        sf = _get_sf_client()
        soql = f"SELECT Id, Name FROM MyObject WHERE Field = '{param1}' LIMIT {param2}"
        records = sf.query(soql)
        results = [MyNewModel(**r).model_dump() for r in records]
        return {"results": results, "total_count": len(results)}
    except SalesforceClientError as e:
        return e.to_error_response()
```

### Step 4: Register the Tool

Add the import to the `_register_tools()` function in `server.py`:

```python
def _register_tools() -> None:
    import mcp_servers.salesforce_crm.tools.my_tool  # noqa: F401
```

### Step 5: Write Contract Tests

```python
# tests/contract/test_my_tool.py
from unittest.mock import MagicMock, patch

def test_my_new_tool_returns_results():
    mock_client = MagicMock()
    with patch("mcp_servers.salesforce_crm.server._get_sf_client", return_value=mock_client):
        mock_client.query.return_value = [{"Id": "001ABC", "Name": "Test"}]
        from mcp_servers.salesforce_crm.tools.my_tool import my_new_tool
        result = my_new_tool(param1="test")
        assert "results" in result
        assert result["total_count"] == 1
```

## Adding a Write-Back Tool

For tools that create or modify Salesforce data:

```python
from shared.salesforce_client import WriteBackConfirmationRequired

@mcp.tool()
def update_my_record(record_id: str, new_value: str, confirmed: bool = False) -> dict[str, Any]:
    """Update a record. Requires user confirmation."""
    try:
        sf = _get_sf_client()
        sf.update_record("MyObject", record_id, {"Field": new_value}, confirmed=confirmed)
        return {"success": True, "message": "Updated successfully."}
    except WriteBackConfirmationRequired:
        return {
            "success": False,
            "message": f"Please confirm: Update record {record_id}? Call again with confirmed=true."
        }
    except SalesforceClientError as e:
        return e.to_error_response()
```

## Adding a New Agent Persona

1. Create a system prompt: `agents/<persona>/system_prompt.md`
2. Include:
   - Core capabilities
   - Grounding rules
   - Write-back protocol
   - Response format guidelines
   - Constraints

3. Use in a notebook:
   ```python
   prompt_path = Path("../agents/<persona>/system_prompt.md")
   system_prompt = prompt_path.read_text(encoding="utf-8")
   agent = project_client.agents.create_agent(
       model="gpt-4o",
       name="My New Agent",
       instructions=system_prompt,
       toolset=[mcp_connection],
   )
   ```

## Adding a New Notebook

Follow the established pattern:

1. **Cell 1**: Markdown — title, user story, persona
2. **Cell 2**: Code — environment + auth setup
3. **Cell 3**: Code — MCP connection(s)
4. **Cell 4**: Code — Create agent with system prompt
5. **Cell 5+**: Code — User queries and agent interactions
6. **Last Cell**: Code — Cleanup (delete agent, thread)

## Adding a New Salesforce Object

1. Check FLS permissions in your Permission Set
2. Add required fields to the SOQL query constants
3. Create a Pydantic model in `shared/models.py`
4. Implement the tool with proper error handling
5. Add contract tests
6. Update documentation

## Adding Azure Infrastructure

1. Create a new Bicep module in `infra/bicep/modules/`
2. Follow the parameter/output conventions from existing modules
3. Add the module to `main.bicep` (conditional if needed)
4. Update `.bicepparam` files for each environment
5. Test with `az bicep build` and `az deployment sub what-if`
