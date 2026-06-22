# AgentCore Runtime — Reference

Sources: AWS CloudFormation Template Reference + AgentCore Developer Guide (June 2026).

---

## CFN Resource: `AWS::BedrockAgentCore::Runtime`

### Properties

| Property | Type | Required | Update | Notes |
|---|---|---|---|---|
| `AgentRuntimeArtifact` | [AgentRuntimeArtifact](#agentruntimeartifact) | **Yes** | No interruption | Container or code configuration |
| `AgentRuntimeName` | String | **Yes** | **Replacement** | Pattern: `[a-zA-Z][a-zA-Z0-9_]{0,47}` |
| `NetworkConfiguration` | [NetworkConfiguration](#networkconfiguration) | **Yes** | No interruption | PUBLIC or VPC mode |
| `RoleArn` | String | **Yes** | No interruption | Pattern: `arn:aws(-[^:]+)?:iam::([0-9]{12})?:role/.+` |
| `AuthorizerConfiguration` | AuthorizerConfiguration | No | No interruption | Inbound auth (JWT) |
| `Description` | String | No | No interruption | 1–1200 chars |
| `EnvironmentVariables` | Object of String | No | No interruption | Key pattern: `^[a-zA-Z_][a-zA-Z0-9_]*$`; max 2048 |
| `FilesystemConfigurations` | Array of FilesystemConfiguration | No | No interruption | 0–5 items |
| `LifecycleConfiguration` | LifecycleConfiguration | No | No interruption | |
| `ProtocolConfiguration` | String | No | No interruption | `MCP \| HTTP \| A2A \| AGUI` |
| `RequestHeaderConfiguration` | RequestHeaderConfiguration | No | No interruption | Headers passed through to the container |
| `Tags` | Object of String | No | No interruption | Key/value pattern: `^[a-zA-Z0-9\s._:/=+@-]*$` |

### Return Values

`Ref` → AgentRuntime ARN.

`Fn::GetAtt`:

| Attribute | Description |
|---|---|
| `AgentRuntimeArn` | Full ARN of the runtime |
| `AgentRuntimeId` | Unique short identifier |
| `AgentRuntimeVersion` | Version number (increments on each update) |
| `CreatedAt` | ISO-8601 creation timestamp |
| `LastUpdatedAt` | ISO-8601 last-update timestamp |
| `FailureReason` | Set when Status is FAILED |
| `Status` | `CREATING \| ACTIVE \| FAILED \| DELETING` |

---

## Sub-property Types

### `AgentRuntimeArtifact`

Choose exactly one of `ContainerConfiguration` or `CodeConfiguration`.

| Property | Type | Notes |
|---|---|---|
| `ContainerConfiguration` | [ContainerConfiguration](#containerconfiguration) | Use for container (ECR) deployments |
| `CodeConfiguration` | CodeConfiguration | Source code location + execution settings |

### `ContainerConfiguration`

| Property | Type | Required | Notes |
|---|---|---|---|
| `ContainerUri` | String | **Yes** | Must include tag or digest: `<acct>.dkr.ecr.<region>.amazonaws.com/<repo>:<tag>` — bare repo URI is rejected |

Pattern: `^\d{12}\.dkr\.ecr\.([a-z0-9-]+)\.amazonaws\.com/((?:[a-z0-9]+(?:[._-][a-z0-9]+)*/)*[a-z0-9]+(?:[._-][a-z0-9]+)*)([:@]\S+)$`

### `NetworkConfiguration`

| Property | Type | Required | Notes |
|---|---|---|---|
| `NetworkMode` | String | **Yes** | `PUBLIC \| VPC` |
| `NetworkModeConfig` | [VpcConfig](#vpcconfig) | No | Required when `NetworkMode: VPC` |

### `VpcConfig` (NetworkModeConfig)

| Property | Type | Required | Constraints |
|---|---|---|---|
| `Subnets` | Array of String | **Yes** | 1–16 subnet IDs |
| `SecurityGroups` | Array of String | **Yes** | 1–16 security group IDs |

---

## Versioning

- Creating the Runtime creates V1 automatically.
- Every configuration update (container image, protocol, network) creates a new **immutable version**.
- A `DEFAULT` endpoint is created automatically and always points to the latest version — no downtime on updates.
- Custom endpoints (dev/test/prod) can be created via `CreateAgentRuntimeEndpoint`.

---

## VPC Mode — Required PrivateLink Endpoints

When `NetworkMode: VPC`, the runtime ENIs are in private subnets with no internet access.
All AWS service traffic must route through VPC endpoints:

| Service | Endpoint type | Purpose |
|---|---|---|
| `ecr.api` | Interface | ECR control-plane API |
| `ecr.dkr` | Interface | Docker image pull |
| `bedrock-runtime` | Interface | Model invocation |
| `bedrock-agentcore` | Interface | Runtime control plane |
| `logs` | Interface | CloudWatch Logs |
| `xray` | Interface | X-Ray traces |
| `monitoring` | Interface | CloudWatch metrics (optional) |
| `s3` | Gateway | ECR layer storage (free, no ENI) |

Each interface endpoint needs a security group allowing inbound TCP 443 from the runtime security group.
See `agentcore-runtime/cloudformation/03-vpc-endpoints/` for a full CFN example.

---

## IAM — Execution Role

The role AgentCore assumes to run the agent container. Trust principal is `bedrock-agentcore.amazonaws.com`.

### Trust Policy

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "Service": "bedrock-agentcore.amazonaws.com" },
    "Action": "sts:AssumeRole",
    "Condition": {
      "StringEquals": { "aws:SourceAccount": "123456789012" },
      "ArnLike": { "aws:SourceArn": "arn:aws:bedrock-agentcore:us-east-1:123456789012:*" }
    }
  }]
}
```

### Permission Statements

```json
[
  {
    "Sid": "ECRImageAccess",
    "Effect": "Allow",
    "Action": ["ecr:BatchGetImage", "ecr:GetDownloadUrlForLayer"],
    "Resource": ["arn:aws:ecr:us-east-1:123456789012:repository/*"]
  },
  {
    "Sid": "ECRTokenAccess",
    "Effect": "Allow",
    "Action": ["ecr:GetAuthorizationToken"],
    "Resource": "*"
  },
  {
    "Effect": "Allow",
    "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents",
               "logs:DescribeLogGroups", "logs:DescribeLogStreams"],
    "Resource": ["arn:aws:logs:us-east-1:123456789012:log-group:/aws/bedrock-agentcore/*"]
  },
  {
    "Effect": "Allow",
    "Action": ["xray:PutTraceSegments", "xray:PutTelemetryRecords",
               "xray:GetSamplingRules", "xray:GetSamplingTargets"],
    "Resource": "*"
  },
  {
    "Effect": "Allow",
    "Action": "cloudwatch:PutMetricData",
    "Resource": "*",
    "Condition": { "StringEquals": { "cloudwatch:namespace": "bedrock-agentcore" } }
  },
  {
    "Sid": "WorkloadIdentity",
    "Effect": "Allow",
    "Action": ["bedrock-agentcore:GetWorkloadAccessToken",
               "bedrock-agentcore:GetWorkloadAccessTokenForJWT",
               "bedrock-agentcore:GetWorkloadAccessTokenForUserId"],
    "Resource": [
      "arn:aws:bedrock-agentcore:us-east-1:123456789012:workload-identity-directory/default",
      "arn:aws:bedrock-agentcore:us-east-1:123456789012:workload-identity-directory/default/workload-identity/*"
    ]
  },
  {
    "Sid": "BedrockModelInvocation",
    "Effect": "Allow",
    "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
    "Resource": ["arn:aws:bedrock:*::foundation-model/*",
                 "arn:aws:bedrock:us-east-1:123456789012:*"]
  }
]
```

**Notes:**
- `cloudwatch:PutMetricData` is intentionally `Resource: "*"` — that is the documented form, gated by the namespace condition.
- The WorkloadIdentity statement is needed only if the agent uses AgentCore Identity to get outbound tokens.
- The resource name prefix `bedrock-agentcore-*` is intentional — several AWS managed/CLI policies scope permissions to that prefix.

---

## Service Contract

### Container Requirements

- **Platform**: ARM64 (AWS Graviton) — only ARM64 images are accepted.
- **Listen on**: `0.0.0.0:8080` (HTTP protocol).
- Must serve `POST /invocations` and `GET /ping`.

### Protocol Ports and Mount Paths

| Protocol | Port | Mount path |
|---|---|---|
| `HTTP` | 8080 | `/invocations` (HTTP), `/ws` (WebSocket) |
| `MCP` | 8000 | `/mcp` |
| `A2A` | 9000 | `/` (root) |
| `AGUI` | 8080 | `/invocations` (SSE), `/ws` (WebSocket) |

### `POST /invocations`

Primary agent interaction endpoint. JSON input; JSON or SSE output.

```
Request:  Content-Type: application/json
          { "prompt": "What is the weather today?" }

Response: Content-Type: application/json
          { "response": "...", "status": "success" }

  or SSE: Content-Type: text/event-stream
          data: {"event": "partial ..."}
          data: {"event": "final ..."}
```

### `GET /ping`

Health check. Returns HTTP 200 with:
```json
{ "status": "<status_value>", "time_of_last_update": <unix_timestamp> }
```

| Status | Meaning |
|---|---|
| `Healthy` | Ready for new work |
| `HealthyBusy` | Operational but busy with async tasks (keeps session alive) |

### Sessions

- Each session runs in an isolated microVM; max lifetime 8 hours; terminated after 15 min idle.
- Session state is ephemeral — use AgentCore Memory for durability.
- Logs: CloudWatch `/aws/bedrock-agentcore/runtimes/<agent-id>-DEFAULT`.

### SDK Invocation (boto3)

```python
import json, uuid, boto3

client = boto3.client("bedrock-agentcore")
resp = client.invoke_agent_runtime(
    agentRuntimeArn="<arn>",
    runtimeSessionId=str(uuid.uuid4()),
    payload=json.dumps({"prompt": "Tell me a joke"}).encode(),
    qualifier="DEFAULT",
)
chunks = [c.decode("utf-8") for c in resp.get("response", [])]
print(json.loads("".join(chunks)))
```

Caller needs `bedrock-agentcore:InvokeAgentRuntime`. OAuth-authenticated agents must call the HTTPS endpoint directly (SDK does not support OAuth inbound auth).

---

## cfn-lint

`E3001` (unsupported type) and `E1010` (invalid GetAtt) on `AWS::BedrockAgentCore::Runtime` are **false positives** — cfn-lint's bundled spec predates this resource type. Suppress with:

```bash
cfn-lint 04-agentcore-runtime.yaml --ignore-checks E3001 E1010
```
