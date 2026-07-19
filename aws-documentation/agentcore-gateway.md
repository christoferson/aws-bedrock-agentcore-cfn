# AgentCore Gateway — Reference

Sources: AWS CloudFormation Template Reference (June 2026).

---

## CFN Resource: `AWS::BedrockAgentCore::Gateway`

### Properties

| Property | Type | Required | Update | Notes |
|---|---|---|---|---|
| `Name` | String | **Yes** | No interruption | Pattern: `^([0-9a-zA-Z][-]?){1,100}$` |
| `RoleArn` | String | **Yes** | No interruption | Pattern: `^arn:[a-z0-9-]{1,20}:iam::([0-9]{12})?:role/.+$`; 1–2048 chars |
| `AuthorizerType` | String | **Yes** | No interruption | `CUSTOM_JWT \| AWS_IAM \| NONE \| AUTHENTICATE_ONLY` |
| `AuthorizerConfiguration` | [AuthorizerConfiguration](#authorizerconfiguration) | No | No interruption | Required when `AuthorizerType: CUSTOM_JWT` |
| `Description` | String | No | No interruption | 1–200 chars |
| `ExceptionLevel` | String | No | No interruption | `DEBUG` — include details in error responses (dev only) |
| `InterceptorConfigurations` | Array of [GatewayInterceptorConfiguration](#gatewayinterceptorconfiguration) | No | No interruption | 1–2 items; max one REQUEST + one RESPONSE |
| `KmsKeyArn` | String | No | No interruption | CMK for data at rest; pattern: `^arn:[a-z0-9-]{1,20}:kms:...` |
| `PolicyEngineConfiguration` | [GatewayPolicyEngineConfiguration](#gatewaypolicyengineconfiguration) | No | No interruption | Cedar policy engine (must exist before gateway) |
| `ProtocolConfiguration` | [GatewayProtocolConfiguration](#gatewayprotocolconfiguration) | No | No interruption | MCP protocol settings |
| `ProtocolType` | String | No | No interruption | Currently `MCP` |
| `Tags` | Object of String | No | No interruption | Key/value pattern: `^[a-zA-Z0-9\s._:/=+@-]*$` |

**All properties support `No interruption` updates — no property forces replacement.**

### Return Values

`Ref` → `GatewayIdentifier` (short ID, e.g. `my-gateway-a1b2c3d4e5`).

`Fn::GetAtt`:

| Attribute | Description |
|---|---|
| `GatewayArn` | Full ARN |
| `GatewayIdentifier` | Short unique identifier (used as `GatewayTarget.GatewayIdentifier`) |
| `GatewayUrl` | HTTPS endpoint URL clients invoke |
| `Status` | `CREATING \| ACTIVE \| FAILED \| DELETING` |
| `StatusReasons` | List of reasons for current status |
| `CreatedAt` | ISO-8601 creation timestamp |
| `UpdatedAt` | ISO-8601 last-update timestamp |

---

## CFN Resource: `AWS::BedrockAgentCore::GatewayTarget`

A GatewayTarget binds a backend to a gateway and declares the tools it exposes.
Multiple targets attach to one gateway; each contributes tools to the shared MCP namespace.

### Properties

| Property | Type | Required | Update | Notes |
|---|---|---|---|---|
| `Name` | String | **Yes** | No interruption | Pattern: `^([0-9a-zA-Z][-]?){1,100}$` |
| `TargetConfiguration` | [TargetConfiguration](#targetconfiguration) | **Yes** | No interruption | Backend type + tool schema |
| `GatewayIdentifier` | String | No | **Replacement** | From `Fn::GetAtt Gateway.GatewayIdentifier` (not the ARN) |
| `Description` | String | No | No interruption | 1–200 chars |
| `CredentialProviderConfigurations` | Array of [CredentialProviderConfiguration](#credentialproviderconfiguration) | No | No interruption | Max 1 item — outbound auth to the backend |
| `MetadataConfiguration` | [MetadataConfiguration](#metadataconfiguration) | No | No interruption | Header/param forwarding |
| `PrivateEndpoint` | PrivateEndpoint | No | No interruption | Private connectivity |

### Return Values

`Ref` → `<gatewayIdentifier>|<targetId>`.

`Fn::GetAtt`:

| Attribute | Description |
|---|---|
| `TargetId` | Unique short ID of the target |
| `GatewayArn` | ARN of the parent gateway |
| `Status` | `CREATING \| ACTIVE \| FAILED \| DELETING` |
| `StatusReasons` | List of reasons for current status |
| `CreatedAt` | ISO-8601 creation timestamp |
| `UpdatedAt` | ISO-8601 last-update timestamp |
| `LastSynchronizedAt` | Timestamp of last target sync |
| `ProtocolType` | Protocol type of the target |

---

## Property Types

### `AuthorizerConfiguration`

```yaml
AuthorizerConfiguration:
  CustomJWTAuthorizer:
    DiscoveryUrl: String      # required; must end in /.well-known/openid-configuration
    AllowedAudience: [String] # JWT aud claim
    AllowedClients: [String]  # JWT client_id / azp claim
    AllowedScopes: [String]   # JWT scope claim
    CustomClaims:
      - InboundTokenClaimName: String       # e.g. tenant_id
        InboundTokenClaimValueType: String  # STRING | STRING_ARRAY
        AuthorizingClaimMatchValue:
          ClaimMatchOperator: String        # EQUALS | CONTAINS | CONTAINS_ANY
          ClaimMatchValue:
            MatchValueString: String        # use with EQUALS or CONTAINS
            MatchValueStringList: [String]  # use with CONTAINS_ANY
```

**Operator semantics:**

| Operator | Claim value type | Matches when |
|---|---|---|
| `EQUALS` | `STRING` | Claim exactly equals `MatchValueString` |
| `CONTAINS` | `STRING_ARRAY` | Array contains `MatchValueString` as an element |
| `CONTAINS_ANY` | `STRING_ARRAY` | Array contains at least one item from `MatchValueStringList` |

---

### `GatewayInterceptorConfiguration`

Up to 2 interceptors per gateway (one `REQUEST`, one `RESPONSE`).

```yaml
InterceptorConfigurations:
  - InterceptionPoints: [REQUEST]   # or [RESPONSE] or [REQUEST, RESPONSE]
    InputConfiguration:
      PassRequestHeaders: true      # forward original request headers to the Lambda
    Interceptor:
      Lambda:
        Arn: String                 # Lambda function ARN (versioned/aliased supported)
```

**Dual-permission requirement for interceptor Lambda** (same as target Lambda):
1. GatewayRole IAM policy: `lambda:InvokeFunction` on the Lambda ARN.
2. `AWS::Lambda::Permission` with `Principal: bedrock-agentcore.amazonaws.com`.

---

### `GatewayPolicyEngineConfiguration`

```yaml
PolicyEngineConfiguration:
  Arn: String    # ARN of an existing AWS::BedrockAgentCore::PolicyEngine
  Mode: String   # LOG_ONLY | ENFORCE
```

| Mode | Behavior |
|---|---|
| `LOG_ONLY` | Evaluates Cedar policies; logs decisions; never blocks. Use to validate before enforcement. |
| `ENFORCE` | Evaluates and enforces — denied tool calls are blocked. Test in `LOG_ONLY` first. |

GatewayRole needs `bedrock-agentcore:IsAuthorized` to use the policy engine.

---

### `GatewayProtocolConfiguration`

```yaml
ProtocolConfiguration:
  Mcp:
    Instructions: String                    # injected into MCP initialize response; max 2048
    SearchType: SEMANTIC                    # embedding-based tool search (omit for full list)
    SupportedVersions: [String]             # MCP spec versions, e.g. ["2024-11-05"]
    SessionConfiguration:
      SessionTimeoutInSeconds: Integer      # 900–28800; default 3600
    StreamingConfiguration:
      EnableResponseStreaming: Boolean      # SSE streaming for long-running tool calls
```

---

### `TargetConfiguration`

Populate exactly one of `Http` or `Mcp`.

```yaml
TargetConfiguration:
  Mcp:
    Lambda:                    # Lambda target
      LambdaArn: String
      ToolSchema:
        InlinePayload:         # tool schema embedded in template
          - Name: String
            Description: String
            InputSchema:
              Type: string|number|object|array|boolean|integer
              Properties:
                fieldName:
                  Type: String
                  Description: String
              Required: [String]
              Items:           # for array types
                Type: String
            OutputSchema:      # optional
              Type: String
        S3:                    # tool schema in S3
          ...
    ApiGateway: ...
    McpServer: ...
    OpenApiSchema: ...
    SmithyModel: ...
  Http:
    ...
```

**Lambda invocation contract (aggregated mode — the only mode):**

Gateway handles `tools/list` itself from the registered schema. The Lambda is only called for tool execution.

```python
# event = flat map of tool arguments directly (no MCP envelope)
# { "keywords": "wireless headphones", "category": "electronics" }

def lambda_handler(event, context):
    # Tool name is in context.client_context.custom, not in event
    # Format: "${target_name}___${tool_name}" (triple underscore)
    original = context.client_context.custom['bedrockAgentCoreToolName']
    tool_name = original[original.index("___") + 3:]   # strip target prefix

    # Other metadata available:
    # context.client_context.custom['bedrockAgentCoreMessageVersion']
    # context.client_context.custom['bedrockAgentCoreAwsRequestId']
    # context.client_context.custom['bedrockAgentCoreMcpMessageId']
    # context.client_context.custom['bedrockAgentCoreGatewayId']
    # context.client_context.custom['bedrockAgentCoreTargetId']

    # event is the arguments dict — access properties directly
    result = do_something(event.get("location", ""))
    return {"content": [{"type": "text", "text": result}], "isError": False}
```

Source: https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-add-target-lambda.html

---

### `CredentialProviderConfiguration`

Outbound auth — how the gateway authenticates to the backend target. Independent of inbound `AuthorizerType`.

```yaml
CredentialProviderConfigurations:
  - CredentialProviderType: String    # required
    CredentialProvider: ...           # only needed for OAUTH and API_KEY
```

| Type | How the gateway authenticates to the backend |
|---|---|
| `GATEWAY_IAM_ROLE` | Uses the gateway's execution role + SigV4. Best for Lambda/API GW in same account. |
| `OAUTH` | Obtains an OAuth 2.0 access token; sends as Bearer header. |
| `API_KEY` | Static API key from Secrets Manager; sends in a header. |
| `CALLER_IAM_CREDENTIALS` | Forwards the caller's AWS credentials to the backend. |
| `JWT_PASSTHROUGH` | Forwards the inbound JWT unchanged as the Authorization header. |

---

### `MetadataConfiguration`

```yaml
MetadataConfiguration:
  AllowedRequestHeaders: [String]    # headers forwarded from caller → target
  AllowedResponseHeaders: [String]   # headers forwarded from target → caller
  AllowedQueryParameters: [String]   # query params forwarded through
```

---

## Dual-Permission Requirement for Lambda Targets

Both are required — either alone results in `403 / AccessDeniedException`:

```yaml
# 1. IAM policy on GatewayRole
- Effect: Allow
  Action: lambda:InvokeFunction
  Resource: !GetAtt ToolLambda.Arn

# 2. Lambda resource-based policy
Type: AWS::Lambda::Permission
Properties:
  FunctionName: !GetAtt ToolLambda.Arn
  Action: lambda:InvokeFunction
  Principal: bedrock-agentcore.amazonaws.com
  SourceAccount: !Ref AWS::AccountId
```

---

## Type Hierarchy

```
AWS::BedrockAgentCore::Gateway
├── AuthorizerConfiguration
│   └── CustomJWTAuthorizer: CustomJWTAuthorizerConfiguration
│       └── CustomClaims[]: CustomClaimValidationType
│           └── AuthorizingClaimMatchValue: AuthorizingClaimMatchValueType
│               └── ClaimMatchValue: ClaimMatchValueType
├── InterceptorConfigurations[]: GatewayInterceptorConfiguration (max 2)
│   ├── InputConfiguration: InterceptorInputConfiguration
│   └── Interceptor: InterceptorConfiguration
│       └── Lambda: LambdaInterceptorConfiguration
├── PolicyEngineConfiguration: GatewayPolicyEngineConfiguration
└── ProtocolConfiguration: GatewayProtocolConfiguration
    └── Mcp: MCPGatewayConfiguration
        ├── SessionConfiguration
        └── StreamingConfiguration

AWS::BedrockAgentCore::GatewayTarget
├── TargetConfiguration
│   ├── Http: HttpTargetConfiguration
│   └── Mcp: McpTargetConfiguration
│       ├── Lambda: McpLambdaTargetConfiguration
│       │   └── ToolSchema
│       │       ├── InlinePayload[]: ToolDefinition
│       │       │   ├── InputSchema: SchemaDefinition (recursive)
│       │       │   └── OutputSchema: SchemaDefinition (recursive)
│       │       └── S3: S3Configuration
│       ├── ApiGateway, McpServer, OpenApiSchema, SmithyModel
├── CredentialProviderConfigurations[] (max 1)
└── MetadataConfiguration
```

---

## KMS Key Policy (Customer-Managed Key)

When using a CMK (`KmsKeyArn`), the key policy needs four statements:

```json
[
  { "Sid": "DescribeKey",    "Action": "kms:DescribeKey",      "Principal": {"AWS": "<GatewayRoleArn>"} },
  { "Sid": "DecryptKey",     "Action": "kms:Decrypt",          "Principal": {"AWS": "<GatewayRoleArn>"},
    "Condition": { "StringEquals": {
      "kms:ViaService": "bedrock-agentcore.<region>.amazonaws.com",
      "kms:EncryptionContext:aws:bedrock-agentcore-gateway:arn": "<GatewayArn>"
    }}
  },
  { "Sid": "CreateGrant",    "Action": "kms:CreateGrant",      "Principal": {"AWS": "<GatewayRoleArn>"},
    "Condition": { "Bool": { "kms:GrantIsForAWSResource": "true" } }
  },
  { "Sid": "CloudWatchLogs", "Action": ["kms:GenerateDataKey", "kms:Decrypt"],
    "Principal": {"Service": "logs.<region>.amazonaws.com"},
    "Condition": { "ArnLike": { "kms:EncryptionContext:aws:logs:arn": "arn:aws:logs:<region>:<acct>:*" } }
  }
]
```
