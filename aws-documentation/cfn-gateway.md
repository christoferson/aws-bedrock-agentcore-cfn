# AWS::BedrockAgentCore::Gateway — CloudFormation Reference

Consolidated reference for the `AWS::BedrockAgentCore::Gateway` resource and all its
nested property types. Sourced from the AWS CloudFormation Template Reference (June 2026).

---

## Overview

Amazon Bedrock AgentCore Gateway provides a unified connectivity layer between agents
and the tools/resources they need to interact with. The gateway manages authentication,
protocol translation (MCP), interceptors, and optional policy enforcement.

---

## Resource: `AWS::BedrockAgentCore::Gateway`

### YAML Syntax

```yaml
Type: AWS::BedrockAgentCore::Gateway
Properties:
  AuthorizerConfiguration:
    AuthorizerConfiguration          # optional
  AuthorizerType: String             # required
  Description: String                # optional
  ExceptionLevel: String             # optional
  InterceptorConfigurations:
    - GatewayInterceptorConfiguration  # optional, 1–2 items
  KmsKeyArn: String                  # optional
  Name: String                       # required
  PolicyEngineConfiguration:
    GatewayPolicyEngineConfiguration # optional
  ProtocolConfiguration:
    GatewayProtocolConfiguration     # optional
  ProtocolType: String               # optional
  RoleArn: String                    # required
  Tags:                              # optional
    Key: Value
```

### Properties

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `AuthorizerConfiguration` | [AuthorizerConfiguration](#authorizerconfiguration) | No | — | No interruption |
| `AuthorizerType` | String | **Yes** | `CUSTOM_JWT \| AWS_IAM \| NONE \| AUTHENTICATE_ONLY` | No interruption |
| `Description` | String | No | Min: 1, Max: 200 | No interruption |
| `ExceptionLevel` | String | No | `DEBUG` | No interruption |
| `InterceptorConfigurations` | Array of [GatewayInterceptorConfiguration](#gatewayinterceptorconfiguration) | No | Min: 1, Max: 2 items | No interruption |
| `KmsKeyArn` | String | No | Pattern: `^arn:[a-z0-9-]{1,20}:kms:[a-zA-Z0-9-]*:[0-9]{12}:key/[a-zA-Z0-9-]{36}$`; Min: 1, Max: 2048 | No interruption |
| `Name` | String | **Yes** | Pattern: `^([0-9a-zA-Z][-]?){1,100}$` | No interruption |
| `PolicyEngineConfiguration` | [GatewayPolicyEngineConfiguration](#gatewaypolicyengineconfiguration) | No | — | No interruption |
| `ProtocolConfiguration` | [GatewayProtocolConfiguration](#gatewayprotocolconfiguration) | No | — | No interruption |
| `ProtocolType` | String | No | — | No interruption |
| `RoleArn` | String | **Yes** | Pattern: `^arn:[a-z0-9-]{1,20}:iam::([0-9]{12})?:role/.+$`; Min: 1, Max: 2048 | No interruption |
| `Tags` | Object of String | No | Key/value pattern: `^[a-zA-Z0-9\s._:/=+@-]*$`; Max value length: 256 | No interruption |

**Property notes:**

- **`AuthorizerType`** — Controls how inbound requests are authenticated. Use `CUSTOM_JWT`
  when providing a `CustomJWTAuthorizer` under `AuthorizerConfiguration`. `AWS_IAM` uses
  SigV4 signing. `NONE` disables auth. `AUTHENTICATE_ONLY` validates identity without
  authorization enforcement.
- **`ExceptionLevel`** — When set to `DEBUG`, detailed exception information is included
  in error responses (useful during development; avoid in production).
- **`KmsKeyArn`** — Customer-managed KMS key used to encrypt gateway data at rest.
- **`Name`** — Must start with an alphanumeric character; hyphens allowed but not
  consecutively at the end. Max 100 characters.
- **`ProtocolType`** — Paired with `ProtocolConfiguration`; currently only MCP is
  documented (see `GatewayProtocolConfiguration`).
- **`RoleArn`** — The gateway assumes this IAM role to access downstream AWS services
  (e.g., invoke Lambda targets, access secrets).

### Return Values

#### `Ref`

Returns the gateway identifier, e.g. `my-gateway-a1b2c3d4e5`.

#### `Fn::GetAtt`

| Attribute | Description |
|---|---|
| `CreatedAt` | ISO 8601 timestamp when the gateway was created. |
| `GatewayArn` | Full ARN of the gateway resource. |
| `GatewayIdentifier` | Unique short identifier for the gateway. |
| `GatewayUrl` | HTTPS endpoint URL clients use to invoke the gateway. |
| `Status` | Current lifecycle status of the gateway. |
| `StatusReasons` | List of reasons explaining the current status (useful when status is not `ACTIVE`). |
| `UpdatedAt` | ISO 8601 timestamp of the last update. |

---

## Property Types

---

### `AuthorizerConfiguration`

Wraps the specific authorizer configuration. Currently only `CustomJWTAuthorizer` is
supported as a nested type.

```yaml
AuthorizerConfiguration:
  CustomJWTAuthorizer:
    CustomJWTAuthorizerConfiguration
```

| Property | Type | Required | Update Behavior |
|---|---|---|---|
| `CustomJWTAuthorizer` | [CustomJWTAuthorizerConfiguration](#customjwtauthorizerconfiguration) | **Yes** | No interruption |

---

### `CustomJWTAuthorizerConfiguration`

Configuration for inbound JWT-based authorization. The gateway validates the `Authorization`
bearer token against the OIDC discovery endpoint and the specified constraints.

```yaml
CustomJWTAuthorizer:
  AllowedAudience:
    - String
  AllowedClients:
    - String
  AllowedScopes:
    - String
  CustomClaims:
    - CustomClaimValidationType
  DiscoveryUrl: String
```

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `AllowedAudience` | Array of String | No | Min: 1 item | No interruption |
| `AllowedClients` | Array of String | No | Min: 1 item | No interruption |
| `AllowedScopes` | Array of String | No | Min: 1 item | No interruption |
| `CustomClaims` | Array of [CustomClaimValidationType](#customclaimvalidationtype) | No | Min: 1 item | No interruption |
| `DiscoveryUrl` | String | **Yes** | Pattern: `^.+/\.well-known/openid-configuration$` | No interruption |

**Property notes:**

- **`DiscoveryUrl`** — Must be the OIDC `/.well-known/openid-configuration` URL for
  the identity provider (e.g. `https://cognito-idp.us-east-1.amazonaws.com/<pool-id>/.well-known/openid-configuration`).
  Used to fetch the public keys for JWT signature validation.
- **`AllowedAudience`** — JWT `aud` claim must match one of these values.
- **`AllowedClients`** — JWT `client_id` (or `azp`) claim must match one of these values.
- **`AllowedScopes`** — JWT `scope` claim must include at least one of these values.
- **`CustomClaims`** — Additional claim checks beyond standard OIDC fields.

---

### `CustomClaimValidationType`

Defines a rule for validating a single custom JWT claim field.

```yaml
- AuthorizingClaimMatchValue:
    AuthorizingClaimMatchValueType
  InboundTokenClaimName: String
  InboundTokenClaimValueType: String
```

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `AuthorizingClaimMatchValue` | [AuthorizingClaimMatchValueType](#authorizingclaimmatchvaluetype) | **Yes** | — | No interruption |
| `InboundTokenClaimName` | String | **Yes** | Pattern: `[A-Za-z0-9_.-:]+` | No interruption |
| `InboundTokenClaimValueType` | String | **Yes** | `STRING \| STRING_ARRAY` | No interruption |

**Property notes:**

- **`InboundTokenClaimName`** — Name of the JWT claim field to inspect (e.g. `tenant_id`,
  `custom:role`).
- **`InboundTokenClaimValueType`** — Use `STRING` when the claim holds a single string;
  use `STRING_ARRAY` when the claim holds a JSON array of strings.

---

### `AuthorizingClaimMatchValueType`

Specifies what to compare the claim value against and how.

```yaml
ClaimMatchOperator: String
ClaimMatchValue:
  ClaimMatchValueType
```

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `ClaimMatchOperator` | String | **Yes** | `EQUALS \| CONTAINS \| CONTAINS_ANY` | No interruption |
| `ClaimMatchValue` | [ClaimMatchValueType](#claimmatchvaluetype) | **Yes** | — | No interruption |

**Operator semantics:**

| Operator | Meaning |
|---|---|
| `EQUALS` | Claim value exactly equals `MatchValueString`. |
| `CONTAINS` | Claim value (a `STRING_ARRAY`) contains `MatchValueString` as an element. |
| `CONTAINS_ANY` | Claim value (a `STRING_ARRAY`) contains at least one element from `MatchValueStringList`. |

---

### `ClaimMatchValueType`

Holds the literal value(s) used in the match comparison. Populate only the field that
matches the operator in use.

```yaml
MatchValueString: String            # use with EQUALS or CONTAINS
MatchValueStringList:               # use with CONTAINS_ANY
  - String
```

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `MatchValueString` | String | No | Pattern: `[A-Za-z0-9_.-]+` | No interruption |
| `MatchValueStringList` | Array of String | No | Min: 1, Max: 255 items | No interruption |

---

### `GatewayInterceptorConfiguration`

Configures a single interceptor that runs custom code at specified points during a
gateway invocation. Up to 2 interceptors per gateway are supported.

```yaml
- InputConfiguration:
    InterceptorInputConfiguration    # optional
  InterceptionPoints:
    - String                         # required, 1–2 items
  Interceptor:
    InterceptorConfiguration         # required
```

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `InputConfiguration` | [InterceptorInputConfiguration](#interceptorinputconfiguration) | No | — | No interruption |
| `InterceptionPoints` | Array of String | **Yes** | Min: 1, Max: 2 items | No interruption |
| `Interceptor` | [InterceptorConfiguration](#interceptorconfiguration) | **Yes** | — | No interruption |

**Property notes:**

- **`InterceptionPoints`** — The lifecycle points at which to call the interceptor.
  Allowed values (not explicitly enumerated in docs but implied): `REQUEST` (before the
  target is called) and `RESPONSE` (after the target responds).

---

### `InterceptorInputConfiguration`

Controls what data is forwarded to the interceptor Lambda function.

```yaml
PassRequestHeaders: Boolean
```

| Property | Type | Required | Update Behavior |
|---|---|---|---|
| `PassRequestHeaders` | Boolean | **Yes** | No interruption |

**Property notes:**

- **`PassRequestHeaders`** — When `true`, the original HTTP request headers are included
  in the event payload sent to the interceptor Lambda. Useful when the interceptor needs
  to inspect auth headers or custom metadata.

---

### `InterceptorConfiguration`

Selects the interceptor backend. Currently only Lambda is supported.

```yaml
Lambda:
  LambdaInterceptorConfiguration
```

| Property | Type | Required | Update Behavior |
|---|---|---|---|
| `Lambda` | [LambdaInterceptorConfiguration](#lambdainterceptorconfiguration) | **Yes** | No interruption |

---

### `LambdaInterceptorConfiguration`

Identifies the Lambda function to invoke as the interceptor.

```yaml
Arn: String
```

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `Arn` | String | **Yes** | Pattern: `^arn:[a-z0-9-]{1,20}:lambda:([a-z]{2}(-gov)?-[a-z]+-\d{1}):(\d{12}):function:([a-zA-Z0-9-_.]+)(:(\$LATEST|[a-zA-Z0-9-_]+))?$`; Min: 1, Max: 170 | No interruption |

**Property notes:**

- **`Arn`** — Supports both unversioned (`function:name`) and versioned/aliased
  (`function:name:alias` or `function:name:$LATEST`) ARNs.

---

### `GatewayPolicyEngineConfiguration`

Associates a Cedar-based policy engine with the gateway. The policy engine evaluates
every agent tool call against defined authorization policies.

```yaml
Arn: String
Mode: String
```

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `Arn` | String | **Yes** | Pattern: `^arn:[a-z0-9-]{1,20}:bedrock-agentcore:[a-z0-9-]+:[0-9]{12}:policy-engine/[a-zA-Z][a-zA-Z0-9-_]{0,99}-[a-zA-Z0-9_]{10}$`; Min: 1, Max: 170 | No interruption |
| `Mode` | String | **Yes** | `LOG_ONLY \| ENFORCE` | No interruption |

**Mode semantics:**

| Mode | Behavior |
|---|---|
| `LOG_ONLY` | Evaluates policies and traces allow/deny decisions in logs, but never blocks requests. Use this to validate policies before enforcement. |
| `ENFORCE` | Evaluates policies and enforces decisions — denied tool calls are blocked. Test in `LOG_ONLY` first to avoid accidental production denials. |

---

### `GatewayProtocolConfiguration`

Selects the communication protocol used by the gateway. Currently only MCP is supported.

```yaml
Mcp:
  MCPGatewayConfiguration
```

| Property | Type | Required | Update Behavior |
|---|---|---|---|
| `Mcp` | [MCPGatewayConfiguration](#mcpgatewayconfiguration) | **Yes** | No interruption |

---

### `MCPGatewayConfiguration`

Configures the Model Context Protocol (MCP) behaviour of the gateway — the protocol
that enables agents to discover and call tools through a standardised interface.

```yaml
Instructions: String                 # optional
SearchType: String                   # optional
SessionConfiguration:
  SessionConfiguration               # optional
StreamingConfiguration:
  StreamingConfiguration             # optional
SupportedVersions:                   # optional
  - String
```

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `Instructions` | String | No | Min: 1, Max: 2048 | No interruption |
| `SearchType` | String | No | `SEMANTIC` | No interruption |
| `SessionConfiguration` | [SessionConfiguration](#sessionconfiguration) | No | — | No interruption |
| `StreamingConfiguration` | [StreamingConfiguration](#streamingconfiguration) | No | — | No interruption |
| `SupportedVersions` | Array of String | No | — | No interruption |

**Property notes:**

- **`Instructions`** — Human-readable guidance injected into the MCP `initialize` response,
  telling agents how to interact with this gateway's tools.
- **`SearchType`** — When set to `SEMANTIC`, the gateway uses semantic (embedding-based)
  search to surface relevant tools to the agent rather than returning the full tool list.
- **`SupportedVersions`** — List of MCP spec version strings the gateway accepts
  (e.g. `["2024-11-05"]`).

---

### `SessionConfiguration`

Controls MCP session lifetime. Sessions allow stateful multi-turn interactions; after
the timeout an expired session returns an error.

```yaml
SessionTimeoutInSeconds: Integer
```

| Property | Type | Required | Constraints | Update Behavior |
|---|---|---|---|---|
| `SessionTimeoutInSeconds` | Integer | No | Min: 900 (15 min), Max: 28800 (8 hr), Default: 3600 (1 hr) | No interruption |

---

### `StreamingConfiguration`

Toggles Server-Sent Events (SSE) streaming for MCP gateway responses.

```yaml
EnableResponseStreaming: Boolean
```

| Property | Type | Required | Update Behavior |
|---|---|---|---|
| `EnableResponseStreaming` | Boolean | No | No interruption |

**Property notes:**

- **`EnableResponseStreaming`** — When `true`, the gateway streams partial results back
  to the client as they become available instead of waiting for a complete response.
  Recommended for long-running tool calls.

---

## Type Hierarchy

```
AWS::BedrockAgentCore::Gateway
├── AuthorizerConfiguration
│   └── CustomJWTAuthorizer: CustomJWTAuthorizerConfiguration
│       └── CustomClaims[]: CustomClaimValidationType
│           └── AuthorizingClaimMatchValue: AuthorizingClaimMatchValueType
│               └── ClaimMatchValue: ClaimMatchValueType
├── InterceptorConfigurations[]: GatewayInterceptorConfiguration
│   ├── InputConfiguration: InterceptorInputConfiguration
│   └── Interceptor: InterceptorConfiguration
│       └── Lambda: LambdaInterceptorConfiguration
├── PolicyEngineConfiguration: GatewayPolicyEngineConfiguration
└── ProtocolConfiguration: GatewayProtocolConfiguration
    └── Mcp: MCPGatewayConfiguration
        ├── SessionConfiguration: SessionConfiguration
        └── StreamingConfiguration: StreamingConfiguration
```

---

## Minimal Example (MCP + JWT Auth)

```yaml
MyGateway:
  Type: AWS::BedrockAgentCore::Gateway
  Properties:
    Name: bedrock-agentcore-my-gateway
    RoleArn: !GetAtt GatewayExecutionRole.Arn
    AuthorizerType: CUSTOM_JWT
    AuthorizerConfiguration:
      CustomJWTAuthorizer:
        DiscoveryUrl: https://cognito-idp.us-east-1.amazonaws.com/us-east-1_XXXXX/.well-known/openid-configuration
        AllowedAudience:
          - my-client-id
        AllowedScopes:
          - gateway/invoke
    ProtocolType: MCP
    ProtocolConfiguration:
      Mcp:
        Instructions: "Use the available tools to answer user questions."
        SearchType: SEMANTIC
        SessionConfiguration:
          SessionTimeoutInSeconds: 3600
        StreamingConfiguration:
          EnableResponseStreaming: true
    Description: MCP gateway for Strands agent tools
    Tags:
      Environment: dev
      Application: bedrock-agentcore-myapp
```

---

## Notes and Caveats

- **cfn-lint false positives** — cfn-lint's bundled spec may not yet include
  `AWS::BedrockAgentCore::Gateway`. Suppress `E3001` and `E1010` with
  `--ignore-checks E3001 E1010` until the spec is updated.
- **All updates are non-disruptive** — every property supports `No interruption`
  updates; no property forces replacement.
- **Policy engine prerequisite** — The `PolicyEngineConfiguration.Arn` must reference
  an existing `AWS::BedrockAgentCore::PolicyEngine` resource (or one created outside
  CloudFormation). The policy engine must be in `ACTIVE` status before the gateway is
  created.
- **Interceptor Lambda permissions** — The gateway's `RoleArn` must have
  `lambda:InvokeFunction` permission on any Lambda ARN listed in
  `LambdaInterceptorConfiguration.Arn`.
- **MCP session storage** — AgentCore manages session state internally; no external
  DynamoDB or cache is required.
