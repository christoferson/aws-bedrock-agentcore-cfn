# Amazon Bedrock AgentCore Gateway — Conceptual Guide

> Source: AWS official documentation at `https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html`

---

## Table of Contents

1. [What Is AgentCore Gateway?](#1-what-is-agentcore-gateway)
2. [The Core Problem It Solves](#2-the-core-problem-it-solves)
3. [Architecture Overview](#3-architecture-overview)
4. [Key Concepts and Terminology](#4-key-concepts-and-terminology)
5. [Target Categories](#5-target-categories)
   - [5.1 MCP Targets (Aggregation Mode)](#51-mcp-targets-aggregation-mode)
   - [5.2 HTTP Targets (Passthrough Mode)](#52-http-targets-passthrough-mode)
   - [5.3 Inference Targets (Model Routing)](#53-inference-targets-model-routing)
6. [MCP Tool Types](#6-mcp-tool-types)
7. [Inbound Authentication](#7-inbound-authentication)
   - [7.1 AuthorizerType Options](#71-authorizertype-options)
   - [7.2 CUSTOM_JWT in Detail](#72-custom_jwt-in-detail)
8. [Outbound Authentication (Credential Providers)](#8-outbound-authentication-credential-providers)
9. [Interceptors](#9-interceptors)
   - [9.1 REQUEST Interceptors](#91-request-interceptors)
   - [9.2 RESPONSE Interceptors](#92-response-interceptors)
   - [9.3 Interceptor Payload Contracts](#93-interceptor-payload-contracts)
   - [9.4 Streaming and Interceptors](#94-streaming-and-interceptors)
10. [Fine-Grained Access Control](#10-fine-grained-access-control)
11. [Optional Features](#11-optional-features)
    - [11.1 MCP Sessions](#111-mcp-sessions)
    - [11.2 Response Streaming](#112-response-streaming)
    - [11.3 Semantic Tool Search](#113-semantic-tool-search)
    - [11.4 Customer-Managed KMS Encryption](#114-customer-managed-kms-encryption)
12. [Gateway Setup Workflow](#12-gateway-setup-workflow)
13. [When Do You Need AgentCore Gateway?](#13-when-do-you-need-agentcore-gateway)
14. [Use Case Examples](#14-use-case-examples)
15. [CFN Resources Quick Reference](#15-cfn-resources-quick-reference)

---

## 1. What Is AgentCore Gateway?

Amazon Bedrock AgentCore Gateway is a **fully-managed AI gateway that provides a single, secure entry point for agentic traffic** — connecting agents to tools, to other agents, and to large language models (LLMs).

Rather than serving only as an MCP tool gateway, it routes and secures *any* agentic traffic through one endpoint:

- Converts APIs, Lambda functions, and existing services into **Model Context Protocol (MCP)-compatible tools**
- Fronts other agents and HTTP services through **passthrough targets** (including Agent-to-Agent / A2A traffic)
- Routes inference requests across multiple model providers through a **unified model-based routing endpoint**
- Supports **OpenAPI, Smithy, and Lambda** as tool input types
- Provides both **comprehensive inbound authentication** (verifying the caller) and **outbound authentication** (connecting to tools) in a single managed service
- Offers **1-click integration** with popular tools: Salesforce, Slack, Jira, Asana, Zendesk

Gateway eliminates weeks of custom code development, infrastructure provisioning, and security implementation so developers can focus on building agent applications.

---

## 2. The Core Problem It Solves

Without a gateway, an agent developer must:

| Problem | Without Gateway |
|---------|----------------|
| Tool protocol integration | Write custom MCP-wrapping code for every API, Lambda, or service |
| Auth on every tool | Implement OAuth, token refresh, and credential storage per integration |
| Tool discovery | Manually manage a growing list of tool definitions in the agent prompt |
| Agent-to-agent routing | Implement custom HTTP routing and auth between agents |
| Model routing | Maintain separate endpoints per model provider; change code when switching |
| Infrastructure | Provision, scale, and monitor all gateway infrastructure |
| Inbound security | Implement JWT validation, SigV4 verification, custom auth per agent |

With Gateway, all of this is handled by the service. The developer provides: a schema (OpenAPI / Smithy / Lambda function) or an endpoint, configures inbound and outbound auth once, and agents see a unified MCP endpoint.

---

## 3. Architecture Overview

```
                             Caller (Agent / LLM Client)
                                      │
                          Authorization: Bearer <JWT>  (or SigV4)
                                      │
                                      ▼
                   ┌──────────────────────────────────────────┐
                   │         AgentCore Gateway                 │
                   │                                          │
                   │  ┌──────────────────────────────────┐   │
                   │  │  Inbound Authorizer               │   │
                   │  │  (NONE / AWS_IAM / CUSTOM_JWT /   │   │
                   │  │   AUTHENTICATE_ONLY)              │   │
                   │  └────────────────┬─────────────────┘   │
                   │                   │                      │
                   │  ┌────────────────▼─────────────────┐   │
                   │  │  REQUEST Interceptor (Lambda)     │   │
                   │  │  validate, transform, auth        │   │
                   │  └────────────────┬─────────────────┘   │
                   │                   │                      │
                   │  ┌────────────────▼─────────────────┐   │
                   │  │  Policy Engine (Cedar)            │   │
                   │  │  per-tool authorization           │   │
                   │  └────────────────┬─────────────────┘   │
                   │                   │                      │
                   └───────────────────┼──────────────────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                   │
              ┌─────▼──────┐  ┌───────▼──────┐  ┌───────▼──────┐
              │ MCP Target │  │  HTTP Target  │  │  Inference   │
              │            │  │  (Passthrough)│  │  Target      │
              │ Lambda     │  │  AgentCore    │  │  Bedrock /   │
              │ API GW     │  │  Runtime      │  │  OpenAI /    │
              │ OpenAPI    │  │  A2A service  │  │  Anthropic   │
              │ Smithy     │  │  External MCP │  └──────────────┘
              │ MCP Server │  └───────────────┘
              └─────┬──────┘
                    │
          ┌─────────▼──────────┐
          │  RESPONSE          │
          │  Interceptor       │
          │  transform, redact │
          └─────────┬──────────┘
                    │
                    ▼
               Response to caller
```

---

## 4. Key Concepts and Terminology

| Term | Definition |
|------|------------|
| **Gateway** | A single, secure access point for an agent to reach tools, other agents, and models; has an HTTPS endpoint |
| **Gateway Target** | A backend resource connected to a gateway; one of three categories: MCP, HTTP, or Inference |
| **MCP (Model Context Protocol)** | Open protocol standardizing how applications provide context to LLMs; Gateway exposes a compliant MCP server endpoint |
| **Aggregation mode** | MCP target behavior: all MCP targets behind a gateway are merged into a single virtual MCP server; callers see one unified `tools/list` |
| **Passthrough mode** | HTTP target behavior: traffic is routed directly to the target without aggregation or protocol translation |
| **Inbound auth** | Controls who can call *your* gateway (JWT Bearer, SigV4, or none) |
| **Outbound auth / Credential Provider** | Controls how the gateway authenticates *to* backend targets (IAM role, OAuth, API key, no auth) |
| **Interceptor** | Lambda function invoked at REQUEST or RESPONSE lifecycle points for custom validation, transformation, or authorization |
| **Policy Engine** | Cedar-based fine-grained per-tool-call authorization; operates in LOG_ONLY or ENFORCE mode |
| **Semantic search** | Natural-language tool discovery; agents call `x_amz_bedrock_agentcore_search` to find relevant tools from a large catalog |
| **Session** | Stateful MCP interaction; gateway issues `Mcp-Session-Id` and maintains state across requests |
| **ExceptionLevel** | Controls how much error detail is returned to callers: `DEBUG` (full detail) or omitted (generic errors for production) |

---

## 5. Target Categories

### 5.1 MCP Targets (Aggregation Mode)

MCP targets operate in **aggregation mode**: the gateway acts as a single MCP server whose capabilities are the union of all attached MCP targets. A caller sees *one* `tools/list` response combining tools from every MCP target.

MCP targets support:
- Capability synchronization (gateway discovers tools from the target)
- Semantic tool search
- Three-legged OAuth (3LO) at the target level (user consent flows)

**MCP target types:**

| Type | Description |
|------|-------------|
| **AWS Lambda** | Lambda function implements MCP `tools/list` and `tools/call`; gateway invokes and translates |
| **Amazon API Gateway REST API** | Existing REST API stage exposed as MCP tools via schema |
| **OpenAPI specification** | REST APIs described by OpenAPI spec automatically converted to MCP tools |
| **Smithy model** | AWS Smithy IDL-defined APIs converted to MCP tools; suitable for AWS service integrations |
| **Remote MCP server** | External MCP server connected directly; gateway proxies and aggregates its capabilities (tools, prompts, resources) |
| **Integration provider templates** | Pre-configured templates for popular services (Salesforce, Slack, Jira, Asana, Zendesk) |
| **Built-in connectors** | Native built-in connectors to common tools |

### 5.2 HTTP Targets (Passthrough Mode)

HTTP targets route traffic **directly** to the backend without aggregation or protocol translation. Callers address each target individually through path-based routing.

HTTP targets do **not** support:
- Capability synchronization
- Semantic tool search

HTTP targets **do** support:
- REQUEST interceptors (RESPONSE interceptor support coming)
- Credential provider attachment

**HTTP target types:**

| Type | Description |
|------|-------------|
| **AgentCore Runtime** | Routes to a containerized Strands agent running in AgentCore Runtime |
| **HTTP passthrough** | Routes to any HTTP endpoint — external agents, A2A services, external MCP servers |

### 5.3 Inference Targets (Model Routing)

Inference targets route **LLM inference traffic** across multiple model providers through a unified endpoint. The gateway selects the destination provider based on the `model` field in the request. Supported providers include Amazon Bedrock, OpenAI, and Anthropic.

This enables agents to switch models or load-balance across providers without changing their endpoint or request format.

---

## 6. MCP Tool Types

When building MCP targets, you define tools using one of the following methods:

| Method | Best for |
|--------|----------|
| **OpenAPI spec** | Existing REST APIs — gateway auto-translates MCP ↔ REST |
| **Lambda function** | Custom business logic in any language; gateway invokes and wraps |
| **Smithy model** | AWS service APIs and custom services defined in Smithy IDL |
| **Remote MCP server** | Connecting to an existing MCP server (tools + optional prompts + resources) |
| **Integration templates** | 1-click setup for Salesforce, Slack, Jira, Asana, Zendesk |
| **Built-in connectors** | Native connectors to common tools (managed by AWS) |

In CloudFormation, Lambda-based tools are defined inline via `ToolSchema` on `AWS::BedrockAgentCore::GatewayTarget`:

```yaml
GatewayTarget:
  Type: AWS::BedrockAgentCore::GatewayTarget
  Properties:
    GatewayIdentifier: !GetAtt Gateway.GatewayIdentifier
    TargetConfiguration:
      Mcp:
        Lambda:
          LambdaArn: !GetAtt ToolLambda.Arn
          ToolSchema:
            Tools:
              - ToolDefinition:
                  Name: echo
                  Description: Echoes back the input message
                  InputSchema:
                    Type: object
                    Properties:
                      - Name: message
                        Schema:
                          Type: string
                          Description: The message to echo
                    Required: [message]
```

---

## 7. Inbound Authentication

Inbound auth controls **who can call your gateway**. It is configured on the `AWS::BedrockAgentCore::Gateway` resource via `AuthorizerType` and `AuthorizerConfiguration`.

### 7.1 AuthorizerType Options

| Value | Mechanism | Use when |
|-------|-----------|----------|
| `NONE` | No auth — any caller can invoke | Dev/testing only; never production |
| `AWS_IAM` | SigV4 — caller signs request with AWS credentials | All callers are AWS-authenticated (agents on Lambda, ECS, EC2) |
| `CUSTOM_JWT` | Bearer JWT validated against an OIDC IdP | Callers present OAuth2 tokens (Cognito, Entra, custom IdP) |
| `AUTHENTICATE_ONLY` | JWT validated but no authorization decision | Identity established; authorization delegated to interceptor or target |

### 7.2 CUSTOM_JWT in Detail

When `AuthorizerType: CUSTOM_JWT`, the gateway:
1. Reads the `Authorization: Bearer <jwt>` header
2. Fetches the IdP's JWKS from `DiscoveryUrl`
3. Verifies the JWT signature, expiry, and configured claim rules
4. Accepts the request only if **all** configured checks pass

**Configuration fields:**

| Field | What it validates | Required |
|-------|------------------|----------|
| `DiscoveryUrl` | Must end in `/.well-known/openid-configuration` | Yes |
| `AllowedAudience` | `aud` claim — token was issued *for* this gateway | At least one of the four |
| `AllowedClients` | `client_id` claim — restricts which apps can call | |
| `AllowedScopes` | `scope` claim — restricts accepted permissions | |
| `CustomClaims` | Arbitrary JWT claims with match operators | |

**Custom claim operators:**

| Operator | Claim type | Meaning |
|----------|-----------|---------|
| `EQUALS` | `STRING` | Claim value must exactly match |
| `CONTAINS` | `STRING_ARRAY` | Claim array must include a specific value |
| `CONTAINS_ANY` | `STRING_ARRAY` | Claim array must overlap with an allowed list |

All configured checks are AND-ed: every rule must pass for the request to be accepted.

**Example — tenant + role check:**
```yaml
CustomClaims:
  - InboundTokenClaimName: tenant_id
    InboundTokenClaimValueType: STRING
    AuthorizingClaimMatchValue:
      ClaimMatchOperator: EQUALS
      ClaimMatchValue:
        MatchValueString: acme-corp
  - InboundTokenClaimName: roles
    InboundTokenClaimValueType: STRING_ARRAY
    AuthorizingClaimMatchValue:
      ClaimMatchOperator: CONTAINS_ANY
      ClaimMatchValue:
        MatchValueStringList: [admin, developer]
```

---

## 8. Outbound Authentication (Credential Providers)

Outbound auth controls **how the gateway authenticates to backend targets**. It is configured per `GatewayTarget` via `CredentialProviderConfigurations`.

| Type | How it works | Use when |
|------|-------------|----------|
| `GATEWAY_IAM_ROLE` | Gateway assumes its execution role to call the target (SigV4) | Target is a Lambda function or AWS service |
| `OAUTH` | Gateway retrieves an OAuth2 token from an AgentCore credential provider | Target requires OAuth Bearer tokens (3rd-party APIs) |
| `API_KEY` | Gateway injects an API key from an AgentCore credential provider | Target requires API key auth |
| `CALLER_IAM_CREDENTIALS` | Gateway forwards the caller's own IAM credentials to the target | Target should act as the original caller, not the gateway |
| `JWT_PASSTHROUGH` | Gateway forwards the caller's inbound JWT directly to the target | Target validates the same JWT the caller presented |

For `OAUTH` and `API_KEY`, an `AWS::BedrockAgentCore::OAuth2CredentialProvider` or `AWS::BedrockAgentCore::ApiKeyCredentialProvider` must be created first (see the identity guide), then referenced by ARN.

**Dual-permission requirement for Lambda targets:**

When the target is a Lambda function, *both* of the following are required:
1. **IAM policy** — `lambda:InvokeFunction` on the GatewayRole (covers Lambda invocation permission via IAM)
2. **Resource-based policy** — `AWS::Lambda::Permission` with `Principal: bedrock-agentcore.amazonaws.com` and `SourceAccount` (covers the Lambda's own trust boundary)

Either alone is insufficient.

---

## 9. Interceptors

Interceptors are **Lambda functions invoked during every gateway invocation** at specific lifecycle points. They are the primary mechanism for custom authorization, request/response transformation, and fine-grained access control.

- A gateway can have **at most one REQUEST interceptor** and **at most one RESPONSE interceptor**
- Currently only **Lambda functions** can be interceptors
- Interceptor Lambdas must be **idempotent** (the gateway may retry on failure)

**Dual-permission requirement** (same as Lambda targets):
- IAM: `lambda:InvokeFunction` in GatewayRole policy
- Resource policy: `AWS::Lambda::Permission` with `bedrock-agentcore.amazonaws.com` principal

### 9.1 REQUEST Interceptors

Execute **before** the gateway calls the target. Use cases:
- Custom authorization (examine JWT claims, call an external authz service)
- Request transformation / enrichment
- Rate limiting or quota enforcement
- Blocking requests by returning an early response (short-circuit)

**Behavior when the interceptor returns `transformedGatewayResponse`:** the gateway returns that response immediately *without* calling the target. This is how you implement request blocking or mocking.

### 9.2 RESPONSE Interceptors

Execute **after** the target responds, before the gateway sends the response to the caller. Use cases:
- Response transformation or sanitization
- Data redaction (remove PII, strip sensitive fields)
- Adding custom headers or metadata
- Logging enrichment

### 9.3 Interceptor Payload Contracts

#### MCP Target — REQUEST input:
```json
{
  "interceptorInputVersion": "1.0",
  "mcp": {
    "rawGatewayRequest": { "body": "<raw_request_body>" },
    "gatewayRequest": {
      "path": "/mcp",
      "httpMethod": "POST",
      "headers": { "Authorization": "Bearer ...", "Mcp-Session-Id": "..." },
      "body": { "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {...} }
    }
  }
}
```
> `headers` is only included when `passRequestHeaders: true`. Be careful — headers contain auth tokens.

#### MCP Target — REQUEST output (pass through or block):
```json
{
  "interceptorOutputVersion": "1.0",
  "mcp": {
    "transformedGatewayRequest": {
      "body": { "jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {...} }
    }
  }
}
```
To **block** the request, return `transformedGatewayResponse` instead (gateway short-circuits to the caller).

#### MCP Target — RESPONSE input:
Same as REQUEST input plus a `gatewayResponse` field:
```json
{
  "mcp": {
    "gatewayRequest": { ... },
    "gatewayResponse": {
      "statusCode": 200,
      "body": { "jsonrpc": "2.0", "id": 1, "result": { "tools": [...] } }
    }
  }
}
```

#### HTTP Target — REQUEST input:
```json
{
  "interceptorInputVersion": "1.0",
  "http": {
    "gatewayRequest": {
      "path": "/my-target-name/invocations",
      "httpMethod": "POST",
      "headers": { "Content-Type": "application/json" },
      "body": "<base64_encoded_body>"
    }
  }
}
```
> Key difference: uses `http` key instead of `mcp`; body is base64-encoded string, not parsed JSON.

**MCP vs HTTP interceptor payload differences:**

| Field | MCP target | HTTP target |
|-------|-----------|-------------|
| Top-level key | `mcp` | `http` |
| Body format | Parsed JSON object | Base64-encoded string |
| `rawGatewayRequest` | Included | Not included |
| Response interceptor | Supported | Not yet supported |

### 9.4 Streaming and Interceptors

When response streaming is enabled, the RESPONSE interceptor is called **multiple times per request** — once per eligible streaming event. The Lambda must check `gatewayResponse.isStreamingResponse` to distinguish streaming from non-streaming responses.

- **First event**: can override `headers`, `statusCode`, and `body`
- **Subsequent events**: can only override `body` (headers already sent to client)
- Progress notifications and log messages (`notifications/progress`, `notifications/message`) are forwarded directly — interceptor is not called for these

---

## 10. Fine-Grained Access Control

Gateway provides multiple levels of access control, from coarse-grained (gateway level) to fine-grained (parameter level).

**Access control levels:**

| Level | Scope | Mechanism |
|-------|-------|-----------|
| Gateway-level | Who can connect and authenticate | `AuthorizerType` + JWT/IAM config |
| Tool-level | Which tools a caller can invoke | REQUEST interceptor logic or Cedar policy engine |
| Operation-level | Which MCP operations are allowed (`tools/list`, `tools/call`) | REQUEST interceptor |
| Parameter-level | Which parameter values or data subsets are allowed | REQUEST interceptor |

**Implementation approaches:**

| Approach | How |
|----------|-----|
| JWT claims validation | Interceptor examines `roles`, `tenant_id`, or custom claims from the JWT |
| IAM principal matching | For IAM-authenticated gateways; match against caller's IAM ARN in Cedar policies |
| External authz service | Interceptor calls an external service (OPA, Permit.io, custom) to get allow/deny |
| Request context filtering | Interceptor rewrites parameters to limit data scope (e.g. inject user-specific filters) |

**Policy Engine (Cedar):**

The `PolicyEngineConfiguration` on a Gateway references an existing AgentCore Policy Engine and evaluates Cedar policies per tool call.

| Mode | Behavior |
|------|----------|
| `LOG_ONLY` | Evaluate policies and trace verdicts; never block — safe for initial rollout |
| `ENFORCE` | Denied tool calls return HTTP 403 — use after validating in LOG_ONLY |

**Best practices:**
- Principle of least privilege — grant users only minimum access
- Use structured JWT claims to carry user context into interceptors
- Design interceptors to **deny by default** when authorization cannot be determined (fail-safe)
- Log all authorization decisions for audit

---

## 11. Optional Features

### 11.1 MCP Sessions

Sessions enable **stateful interactions** between clients and the gateway. When enabled:
- Gateway issues a unique `Mcp-Session-Id` on `initialize`
- Client includes the session ID in all subsequent requests
- Gateway stores MCP server target session IDs and reuses them, avoiding re-initialization on each call
- Enables elicitation (target requests additional info from the client) and sampling (target requests LLM completions)

**Session configuration:**
```yaml
ProtocolConfiguration:
  Mcp:
    SessionConfiguration:
      SessionTimeoutInSeconds: 3600   # 900–28800; default 3600
```

**Session security scoping:**

| Auth method | Session scoped to |
|-------------|------------------|
| OAuth/OIDC | `sub` claim from JWT |
| AWS IAM | Principal ARN |
| No auth | None — session hijacking risk; dev/test only |

For authenticated gateways, if a different user presents another user's session ID, the gateway returns HTTP 404 (session is invisible to other users).

**Session timeout errors:**

| Scenario | HTTP status |
|----------|------------|
| Missing `Mcp-Session-Id` on session-enabled gateway | 400 Bad Request |
| Invalid or expired session | 404 Not Found |
| Different user using another's session | 404 Not Found |

### 11.2 Response Streaming

Enables real-time **Server-Sent Events (SSE)** from the gateway during tool execution. The client receives:
- Progress notifications (`notifications/progress`)
- Log messages (`notifications/message`)
- Elicitation requests (target asking the client a question)
- Sampling requests (target asking the client for an LLM completion)

Sessions must be enabled before streaming can be enabled. Required for elicitation and sampling.

```yaml
StreamingConfiguration:
  EnableResponseStreaming: true
```

### 11.3 Semantic Tool Search

When enabled, agents can find relevant tools using natural language queries instead of knowing tool names in advance. Useful as the tool catalog grows beyond what fits in a single prompt.

- Enabled by `SearchType: SEMANTIC` in `ProtocolConfiguration.Mcp`
- Agents call the `x_amz_bedrock_agentcore_search` built-in tool with a natural language description of what they need
- Gateway returns the most relevant tools from the catalog

### 11.4 Customer-Managed KMS Encryption

By default, Gateway encrypts data at rest using a service-managed AWS KMS key. You can supply your own CMK for additional control over rotation, access, and audit.

**Required KMS key policy statements:**

| Sid | Principal | Actions | Purpose |
|-----|-----------|---------|---------|
| `AllowServiceRoleDescribeKey` | Gateway service role | `kms:DescribeKey` | Key metadata lookup |
| `AllowServiceRoleDecryptKey` | Gateway service role | `kms:Decrypt`, `kms:GenerateDataKey` | Data encryption/decryption |
| `AllowServiceRoleCreateGrant` | Gateway service role | `kms:CreateGrant` | Grant-based access delegation |
| `AllowKMSDecryptionLogging` | `delivery.logs.amazonaws.com` | `kms:GenerateDataKey`, `kms:Decrypt` | CloudWatch Logs key usage audit |

All statements should use `kms:ViaService` condition scoped to `bedrock-agentcore.<region>.amazonaws.com`.

The `AllowServiceRoleDecryptKey` and `AllowServiceRoleCreateGrant` statements additionally require an encryption context condition:
```json
"kms:EncryptionContext:aws:bedrock-agentcore-gateway:arn": "arn:aws:bedrock-agentcore:...:gateway/<GatewayId>"
```

> **Warning:** If the CMK is disabled or deleted, or if the gateway loses permission to use it, access to encrypted data is permanently lost.

---

## 12. Gateway Setup Workflow

The standard setup sequence:

```
1. Define tools
   └── Choose: OpenAPI spec / Lambda schema / Smithy model / MCP server URL

2. Create Gateway (AWS::BedrockAgentCore::Gateway)
   ├── Set AuthorizerType (NONE / AWS_IAM / CUSTOM_JWT)
   ├── Configure AuthorizerConfiguration (CUSTOM_JWT: DiscoveryUrl, audiences, scopes, claims)
   ├── Optionally add InterceptorConfigurations (REQUEST / RESPONSE Lambda ARNs)
   ├── Optionally add PolicyEngineConfiguration (Cedar engine ARN + mode)
   ├── Configure ProtocolConfiguration.Mcp (sessions, streaming, semantic search)
   └── Optionally set KmsKeyArn

3. Create GatewayRole (AWS::IAM::Role)
   ├── Trust: bedrock-agentcore.amazonaws.com (with aws:SourceAccount condition)
   ├── CloudWatch Logs permissions (/aws/bedrock-agentcore/*)
   ├── lambda:InvokeFunction on interceptor + tool Lambdas
   └── bedrock-agentcore:IsAuthorized on policy engine (if used)

4. Add Targets (AWS::BedrockAgentCore::GatewayTarget)
   ├── TargetConfiguration: Mcp.Lambda / Mcp.McpServer / Http.HttpEndpoint
   ├── CredentialProviderConfigurations: GATEWAY_IAM_ROLE / OAUTH / API_KEY
   └── ToolSchema (inline for Lambda targets)

5. Add Lambda resource policies (AWS::Lambda::Permission)
   └── Principal: bedrock-agentcore.amazonaws.com + SourceAccount (for each Lambda)

6. Update agent code
   └── Connect to GatewayUrl output via MCP client
```

---

## 13. When Do You Need AgentCore Gateway?

### You need it if your agent...

| Scenario | What Gateway provides |
|----------|----------------------|
| Needs to call multiple tools / APIs | Unified MCP endpoint; single connection for all tools |
| Tools are existing REST APIs or Lambda functions | Automatic MCP wrapping via OpenAPI / Lambda / Smithy |
| Needs controlled inbound access (not open to everyone) | JWT or SigV4 inbound auth |
| Calls third-party services that require OAuth or API keys | Outbound credential provider integration |
| Must enforce per-user or per-tool authorization | Interceptors + Cedar policy engine |
| Has a growing tool catalog (>5–10 tools) | Semantic search for tool discovery |
| Needs A2A routing to other agents | HTTP passthrough target |
| Routes requests to multiple LLM providers | Inference target with model-based routing |
| Needs audit trail on all tool invocations | Gateway CloudWatch Logs |
| Operates in multi-tenant context | Custom JWT claim validation (tenant_id) + interceptors |

### You do NOT need it if...

- Your agent calls a single Lambda function directly with no auth requirements
- You are prototyping locally without any inbound security
- Your tools are already MCP-native and you control the endpoint directly (you might still benefit from the auth layer, but it is not strictly required)

---

## 14. Use Case Examples

### Simple Internal Tool — Lambda, No Auth

An internal development agent calling a Lambda that performs calculations. No auth needed.

- `AuthorizerType: NONE`
- `ExceptionLevel: DEBUG` (safe for internal)
- `CredentialProviderConfigurations: GATEWAY_IAM_ROLE`
- Template: `01-gateway-no-auth.yaml` / `01b-gateway-no-auth-lambda-target.yaml`

### External Agent Client — AWS_IAM Auth

An agent running in ECS that must call a shared tool gateway. All callers are IAM-authenticated.

- `AuthorizerType: AWS_IAM`
- Create a `GatewayCallerRole` with `bedrock-agentcore:InvokeGateway` permission scoped to the gateway ARN
- Template: `02-gateway-iam-auth.yaml`

### Multi-Tenant SaaS Agent — CUSTOM_JWT + Cognito

An agent exposed to end users who authenticate via Cognito. Each JWT carries a `tenant_id` claim that scopes tool access.

- `AuthorizerType: CUSTOM_JWT`
- `DiscoveryUrl`: Cognito pool OIDC endpoint
- `CustomClaims`: `tenant_id EQUALS <tenant>`, `roles CONTAINS_ANY [admin, user]`
- Template: `03-gateway-jwt-auth.yaml` / `04-gateway-jwt-custom-claims.yaml`

### Enterprise Agent — JWT + Request Interceptor

An enterprise agent where the gateway validates JWTs but an interceptor enforces additional RBAC logic (check department membership against a database before allowing tool calls).

- `AuthorizerType: CUSTOM_JWT`
- REQUEST interceptor Lambda: call internal authz service, return `transformedGatewayResponse` with 403 if denied
- Template: `05-gateway-jwt-interceptor.yaml`

### Regulated Environment — Full Stack (JWT + Interceptors + Policy Engine + KMS)

A healthcare or financial agent where every tool call must be policy-evaluated, data at rest encrypted, and all decisions logged.

- `AuthorizerType: CUSTOM_JWT`
- Cedar `PolicyEngineConfiguration` in `ENFORCE` mode
- REQUEST + RESPONSE interceptors for request enrichment and response redaction
- `KmsKeyArn` with `kms:ViaService` condition
- Template: `07-gateway-full.yaml`

---

## 15. CFN Resources Quick Reference

| Resource | Purpose | Key Properties |
|----------|---------|---------------|
| `AWS::BedrockAgentCore::Gateway` | The gateway itself | `AuthorizerType`, `AuthorizerConfiguration`, `InterceptorConfigurations`, `PolicyEngineConfiguration`, `ProtocolConfiguration`, `KmsKeyArn`, `ExceptionLevel` |
| `AWS::BedrockAgentCore::GatewayTarget` | A backend connected to the gateway | `GatewayIdentifier`, `TargetConfiguration` (Mcp/Http), `CredentialProviderConfigurations`, `ToolSchema` |
| `AWS::IAM::Role` (GatewayRole) | Identity assumed by the gateway service | Trust: `bedrock-agentcore.amazonaws.com`; permissions: CloudWatch Logs, `lambda:InvokeFunction`, `bedrock-agentcore:IsAuthorized` |
| `AWS::Lambda::Permission` | Resource-based policy on tool/interceptor Lambdas | `Principal: bedrock-agentcore.amazonaws.com`, `SourceAccount` |
| `AWS::KMS::Key` | CMK for gateway data encryption | Key policy: `kms:ViaService` condition + `kms:EncryptionContext` for the gateway ARN |

**GetAtt outputs to capture after deployment:**

| Resource | Output | Use |
|----------|--------|-----|
| `Gateway` | `GatewayArn` | IAM policies scoping `bedrock-agentcore:InvokeGateway` |
| `Gateway` | `GatewayIdentifier` | Required as input to `GatewayTarget.GatewayIdentifier` |
| `Gateway` | `GatewayUrl` | The MCP endpoint agents connect to |
| `Gateway` | `Status` | Monitor creation/update state |
| `GatewayTarget` | `TargetIdentifier` | Reference in policies or other resources |

**See also:**
- `agentcore-gateway/cloudformation/` — reference CFN templates (01 through 07)
- `aws-documentation/cfn-gateway.md` — Gateway CFN property-level reference
- `aws-documentation/cfn-gateway-target.md` — GatewayTarget CFN property-level reference
- `agentcore-identity/documentation/agentcore-identity-guide.md` — Identity guide (inbound JWT authorizer + credential providers)
