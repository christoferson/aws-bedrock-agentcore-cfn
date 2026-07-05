# Official AWS Documentation Links

Reference links for Amazon Bedrock AgentCore CloudFormation templates in this repo.
Saved documentation snapshots are in `aws-documentation/`.

---

## CloudFormation Template Reference

| Resource | URL |
|---|---|
| `AWS::BedrockAgentCore::Harness` | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-harness.html |
| `AWS::BedrockAgentCore::Gateway` | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-gateway.html |
| `AWS::BedrockAgentCore::GatewayTarget` | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-gatewaytarget.html |
| `AWS::BedrockAgentCore::Memory` | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-memory.html |
| `AWS::Bedrock::KnowledgeBase` (MANAGED type) | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrock-knowledgebase.html |
| `AWS::S3Vectors::VectorBucket` | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-s3vectors-vectorbucket.html |

---

## AgentCore Developer Guide

### General
| Topic | URL |
|---|---|
| What is AgentCore? | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/what-is-bedrock-agentcore.html |
| Get started (CLI) | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-get-started-cli.html |
| IAM service authorization reference | https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonbedrockagentcore.html |

### Harness
| Topic | URL |
|---|---|
| Harness overview | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness.html |
| Harness security (execution role permissions) | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/harness-security.html |

### Gateway
| Topic | URL |
|---|---|
| Gateway overview | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway.html |
| Gateway quick start | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-quick-start.html |
| Core concepts | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-core-concepts.html |
| Supported targets overview | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-supported-targets.html |
| MCP targets | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-targets-mcp.html |
| **Lambda targets** (invocation contract, event/context format) | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-add-target-lambda.html |
| Tool naming (targetName___toolName) | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-tool-naming.html |
| Connector targets (web-search, knowledge-bases) | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-target-connectors.html |
| VPC egress configuration | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-vpc-egress.html |
| Fine-grained access control (Cedar policy engine) | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-fine-grained-access-control.html |

### VPC / Networking
| Topic | URL |
|---|---|
| VPC configuration for AgentCore | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html |
| **VPC interface endpoints** (3 service names: data plane, gateway, control plane) | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/vpc-interface-endpoints.html |
| Gateway VPC egress (Lambda, MCP, API GW patterns) | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/gateway-vpc-egress.html |

### Identity
| Topic | URL |
|---|---|
| Identity overview | https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/identity.html |
| `WorkloadIdentity` CFN resource | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-workloadidentity.html |
| `ApiKeyCredentialProvider` CFN resource | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-apikeycredentialprovider.html |
| `OAuth2CredentialProvider` CFN resource | https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-oauth2credentialprovider.html |

### Knowledge Base
| Topic | URL |
|---|---|
| Managed knowledge base (MANAGED type, no StorageConfiguration) | https://docs.aws.amazon.com/bedrock/latest/userguide/knowledge-base-managed.html |

---

## AWS Blog Posts

| Title | URL |
|---|---|
| **Private connectivity patterns for AgentCore Gateway targets** (VPC Lattice, VPC Link, Lambda ENI, on-prem, multi-cloud) | https://aws.amazon.com/blogs/networking-and-content-delivery/private-connectivity-patterns-for-amazon-bedrock-agentcore-gateway-targets/ |
| Connecting MCP servers to AgentCore Gateway using Authorization Code Flow | https://aws.amazon.com/blogs/machine-learning/connecting-mcp-servers-to-amazon-bedrock-agentcore-gateway-using-authorization-code-flow/ |

---

## Lambda VPC Networking

| Topic | URL |
|---|---|
| Lambda VPC networking (`AWSLambdaVPCAccessExecutionRole`) | https://docs.aws.amazon.com/lambda/latest/dg/configuration-vpc.html |
| `AWSLambdaVPCAccessExecutionRole` managed policy | https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSLambdaVPCAccessExecutionRole.html |

---

## Key facts captured from docs

- **Lambda target invocation** — one mode only (aggregated): `event` = flat args dict; tool name in `context.client_context.custom["bedrockAgentCoreToolName"]`; delimiter `___`; Gateway handles `tools/list` from registered schema.
- **Lambda in VPC** — requires `AWSLambdaVPCAccessExecutionRole` (adds `ec2:CreateNetworkInterface`, `ec2:DescribeNetworkInterfaces`, `ec2:DeleteNetworkInterface`).
- **Three AgentCore VPC endpoints** — `bedrock-agentcore` (data plane), `bedrock-agentcore.gateway` (Gateway data plane — **required** for `agentcore_gateway` tools), `bedrock-agentcore-control` (control plane). Missing the gateway endpoint causes `[Errno -2]` when Harness tries to reach a Gateway tool.
- **Gateway DNS in VPC** — `PrivateDnsEnabled: true` on the `bedrock-agentcore` data plane endpoint intercepts the whole `bedrock-agentcore.<region>.amazonaws.com` zone; Gateway URL subdomains resolve to NXDOMAIN. Fix: `PrivateDnsEnabled: false` on data plane endpoint only. The `bedrock-agentcore.gateway` endpoint uses `PrivateDnsEnabled: true` (its own separate zone, no conflict).
- **Dual Lambda permission** — both `AWS::Lambda::Permission` (Principal: bedrock-agentcore.amazonaws.com) AND IAM `lambda:InvokeFunction` on GatewayRole are required.
- **AllowedClients vs AllowedAudience** — use `AllowedClients` (matches `client_id` claim, works for both ID and access tokens); `AllowedAudience` matches `aud` claim which breaks for access tokens.
