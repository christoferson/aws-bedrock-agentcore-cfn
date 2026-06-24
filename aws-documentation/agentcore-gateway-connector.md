# AgentCore Gateway — Connector Targets Reference

Sources: AWS CloudFormation Template Reference + AgentCore Developer Guide (June 2026).

---

## Overview

Connector targets provide pre-built integrations with AWS services and third-party tools.
They use the `TargetConfiguration.Mcp.Connector` path in the CFN resource and the
`mcp.connector` key in the SDK/CLI.

Two available connectors (as of June 2026):
- `web-search` — Amazon-operated web search index
- `bedrock-knowledge-bases` — Amazon Bedrock Managed Knowledge Bases

Connector targets support only `GATEWAY_IAM_ROLE` as the credential provider type.

---

## CFN: `ConnectorTargetConfiguration`

Under `TargetConfiguration.Mcp.Connector`:

```yaml
TargetConfiguration:
  Mcp:
    Connector:
      Source:                   # required
        ConnectorId: String     # e.g. "web-search" or "bedrock-knowledge-bases"
      Configurations:           # optional; per-tool configuration
        - Name: String          # tool name within the connector
          ParameterValues: ...  # tool-specific parameters (JSON object)
      Enabled:                  # optional; list of tool names to enable (default: all)
        - String
```

| Property | Type | Required | Update | Notes |
|---|---|---|---|---|
| `Source` | ConnectorSource | **Yes** | No interruption | Identifies which connector to use |
| `Configurations` | Array of ConnectorConfiguration | No | No interruption | Per-tool parameter values |
| `Enabled` | Array of String | No | No interruption | 1–50 items; filter which tools are exposed |

### `ConnectorSource`

| Property | Type | Required | Notes |
|---|---|---|---|
| `ConnectorId` | String | **Yes** | `web-search` or `bedrock-knowledge-bases` |

---

## Web Search Connector (`connectorId: "web-search"`)

### What it is

A fully managed, Amazon-operated web search index. Tens of billions of documents,
continuously refreshed. Queries stay within AWS — no third-party search engine.
Returns semantic snippets optimized for model context windows.

**Region**: `us-east-1` only (as of June 2026).  
**Pricing**: $7 per 1,000 queries (~$0.007/query).

### Tool

One tool: `WebSearch`

### CFN Configuration (minimal)

```yaml
GatewayTarget:
  Type: AWS::BedrockAgentCore::GatewayTarget
  Properties:
    GatewayIdentifier: !GetAtt Gateway.GatewayIdentifier
    Name: web-search-tool
    TargetConfiguration:
      Mcp:
        Connector:
          Source:
            ConnectorId: web-search
          Configurations:
            - Name: WebSearch
              ParameterValues: {}
    CredentialProviderConfigurations:
      - CredentialProviderType: GATEWAY_IAM_ROLE
```

### Domain Filtering (optional)

Restrict which domains can be returned. Enforced server-side; hidden from the LLM.

```yaml
Configurations:
  - Name: WebSearch
    ParameterValues:
      domainFilter:
        exclude:
          - blocked-website-1.com
          - blocked-website-2.com
```

### IAM — Gateway Service Role Permissions

Add to the role passed as `RoleArn` when creating the Gateway:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "InvokeGateway",
      "Effect": "Allow",
      "Action": "bedrock-agentcore:InvokeGateway",
      "Resource": "arn:aws:bedrock-agentcore:<REGION>:<ACCOUNT_ID>:gateway/*"
    },
    {
      "Sid": "InvokeWebSearch",
      "Effect": "Allow",
      "Action": "bedrock-agentcore:InvokeWebSearch",
      "Resource": "arn:aws:bedrock-agentcore:<REGION>:aws:tool/web-search.v1"
    }
  ]
}
```

**Note**: The Resource account segment for `InvokeWebSearch` is `aws` (AWS-owned tool), not your account ID.

### Response Format

MCP `tools/call` envelope → `content[].text` → serialized JSON:

```json
{
  "publishedDate": "04:43AM, Wednesday, June 17 2026, PDT",
  "text": "Snippet text optimized for LLM context...",
  "title": "Page title",
  "url": "https://example.com/page"
}
```

Knowledge graph responses (entity queries): `title` and `url` are `null`; `text` contains structured key-value facts.

### SDK (boto3)

```python
import boto3

gateway_client = boto3.client("bedrock-agentcore-control", region_name="us-east-1")

gateway_client.create_gateway_target(
    name="web-search-tool",
    gatewayIdentifier="<GATEWAY_ID>",
    targetConfiguration={
        "mcp": {
            "connector": {
                "source": {"connectorId": "web-search"},
                "configurations": [{"name": "WebSearch", "parameterValues": {}}],
            }
        }
    },
    credentialProviderConfigurations=[
        {"credentialProviderType": "GATEWAY_IAM_ROLE"}
    ],
)
```

---

## Knowledge Bases Connector (`connectorId: "bedrock-knowledge-bases"`)

### Tools

Two tools:
- `AgenticRetrieveStream` — multi-step streaming agentic retrieval across multiple KBs
- `Retrieve` — single hybrid search against one KB

### CFN Configuration

```yaml
Configurations:
  - Name: AgenticRetrieveStream
    ParameterValues:
      retrievers:
        - description: "Product documentation"
          configuration:
            knowledgeBase:
              knowledgeBaseId: "<KB_ID>"
      agenticRetrieveConfiguration:  # required (can be {} for service-managed defaults)
        foundationModelType: MANAGED
        rerankingModelType: MANAGED
  - Name: Retrieve
    ParameterValues:
      knowledgeBaseId: "<KB_ID>"  # required
```

### IAM — Gateway Service Role Permissions

```json
{
  "Statement": [
    { "Action": "bedrock:GetKnowledgeBase", "Resource": "arn:aws:bedrock:<REGION>:<ACCOUNT_ID>:knowledge-base/<KB_ID>" },
    { "Action": "bedrock:Retrieve",          "Resource": "arn:aws:bedrock:<REGION>:<ACCOUNT_ID>:knowledge-base/<KB_ID>" },
    { "Action": "bedrock:AgenticRetrieveStream", "Resource": "*" }
  ]
}
```

---

## IAM — Caller Permissions (inbound, AWS_IAM gateways)

The application or agent invoking the gateway needs:

```json
{
  "Action": "bedrock-agentcore:InvokeGateway",
  "Resource": "arn:aws:bedrock-agentcore:<REGION>:<ACCOUNT_ID>:gateway/<GATEWAY_ID>"
}
```
