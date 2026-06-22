# Pattern 01 — Web Search Agent

A Strands agent deployed on AgentCore Runtime that uses an AgentCore Gateway
with the built-in web search connector to answer questions with live web results.

Reference: [Introducing Web Search on Amazon Bedrock AgentCore](../../aws-blogs/introducing-web-search-agentcore.md)

## Architecture

```
Caller → AgentCore Runtime (VPC) → Agent (Strands + MCPClient)
                                      → AgentCore Gateway (AWS_IAM, MCP)
                                          → WebSearch Connector
                                              → Amazon Web Search Index
```

**Notes:**
- Web search connector is `us-east-1` only; ~$0.007/query.
- Runtime calls Gateway over HTTPS, signing with SigV4 via `mcp-proxy-for-aws`.
- All IAM permissions use wildcard gateway ARN scoped to account (avoids circular dependency).

## Stacks (deploy in order)

| # | Template | Creates |
|---|----------|---------|
| 1 | `01-iam.yaml` | ExecutionRole, GatewayRole, CodeBuildRole, CodePipelineRole |
| 2 | `02-network.yaml` | VPC, public/private subnets (2 AZ), NAT gateway, runtime SG |
| 3 | `03-ecr-cicd.yaml` | ECR repo, S3 source bucket, CodeBuild (ARM64), CodePipeline |
| 4 | `04-gateway.yaml` | Gateway (AWS_IAM) + WebSearch GatewayTarget |
| 5 | `05-runtime.yaml` | AgentCore Runtime (VPC mode) with `GATEWAY_URL` env var |

**Hard ordering constraint:** Stack 5 requires an ARM64 image in ECR. Deploy stacks
1–4 first, then push agent code (stack 3 pipeline builds the image), then deploy stack 5.

## Deploy

### 1. Deploy IAM
```bash
aws cloudformation deploy \
  --template-file cloudformation/01-iam.yaml \
  --stack-name web-search-agent-iam \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides ApplicationName=bedrock-agentcore Environment=dev
```

### 2. Deploy Network
```bash
aws cloudformation deploy \
  --template-file cloudformation/02-network.yaml \
  --stack-name web-search-agent-network \
  --parameter-overrides ApplicationName=bedrock-agentcore Environment=dev
```

### 3. Deploy ECR + CI/CD

Get outputs from stack 1:
```bash
aws cloudformation describe-stacks --stack-name web-search-agent-iam \
  --query "Stacks[0].Outputs"
```

```bash
aws cloudformation deploy \
  --template-file cloudformation/03-ecr-cicd.yaml \
  --stack-name web-search-agent-cicd \
  --parameter-overrides \
    ApplicationName=bedrock-agentcore \
    Environment=dev \
    CodeBuildRoleArn=<CodeBuildRoleArn> \
    CodePipelineRoleArn=<CodePipelineRoleArn>
```

### 4. Push agent source (triggers pipeline → builds ARM64 image)

```bash
SOURCE_BUCKET=$(aws cloudformation describe-stacks --stack-name web-search-agent-cicd \
  --query "Stacks[0].Outputs[?OutputKey=='SourceBucketName'].OutputValue" --output text)

./scripts/upload-source.sh "$SOURCE_BUCKET"
```

Wait for the pipeline to complete and note the ECR image URI:
```bash
ECR_URI=$(aws cloudformation describe-stacks --stack-name web-search-agent-cicd \
  --query "Stacks[0].Outputs[?OutputKey=='EcrRepositoryUri'].OutputValue" --output text)

IMAGE_URI="$ECR_URI:latest"
```

### 5. Deploy Gateway

Get GatewayRoleArn from stack 1:
```bash
aws cloudformation deploy \
  --template-file cloudformation/04-gateway.yaml \
  --stack-name web-search-agent-gateway \
  --parameter-overrides \
    ApplicationName=bedrock-agentcore \
    Environment=dev \
    GatewayRoleArn=<GatewayRoleArn>
```

Get GatewayUrl from stack 4:
```bash
GATEWAY_URL=$(aws cloudformation describe-stacks --stack-name web-search-agent-gateway \
  --query "Stacks[0].Outputs[?OutputKey=='GatewayUrl'].OutputValue" --output text)
```

### 6. Deploy Runtime

Get subnet/SG outputs from stack 2:
```bash
aws cloudformation deploy \
  --template-file cloudformation/05-runtime.yaml \
  --stack-name web-search-agent-runtime \
  --parameter-overrides \
    ApplicationName=bedrock-agentcore \
    Environment=dev \
    ExecutionRoleArn=<ExecutionRoleArn> \
    PrivateSubnetList=<subnet-id1,subnet-id2> \
    SecurityGroupList=<sg-id> \
    ContainerImageUri=<IMAGE_URI> \
    GatewayUrl=<GATEWAY_URL>
```

## Invoke

```bash
AGENT_ARN=$(aws cloudformation describe-stacks --stack-name web-search-agent-runtime \
  --query "Stacks[0].Outputs[?OutputKey=='AgentRuntimeArn'].OutputValue" --output text)

./scripts/invoke.sh "$AGENT_ARN" "What are the latest developments in quantum computing?"
```

## Teardown

Delete stacks in reverse order:
```bash
for stack in web-search-agent-runtime web-search-agent-gateway web-search-agent-cicd web-search-agent-network web-search-agent-iam; do
  aws cloudformation delete-stack --stack-name $stack
  aws cloudformation wait stack-delete-complete --stack-name $stack
done
```

Note: ECR images and S3 objects must be deleted manually before the stacks containing
those buckets/repos can be removed.

## Lint

```bash
cfn-lint cloudformation/01-iam.yaml cloudformation/02-network.yaml cloudformation/03-ecr-cicd.yaml
# Stacks 4 and 5 use AWS::BedrockAgentCore::* — suppress false positives:
cfn-lint cloudformation/04-gateway.yaml cloudformation/05-runtime.yaml --ignore-checks E3001 E1010
```
