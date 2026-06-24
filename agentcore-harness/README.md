# agentcore-harness

CloudFormation templates for **AWS::BedrockAgentCore::Harness** — a managed agent
loop that wires a Bedrock model, tools, and system prompt into an invokable endpoint
without requiring a custom container or CI/CD pipeline.

Reference doc: [../../aws-documentation/agentcore-harness.md](../../aws-documentation/agentcore-harness.md)

## How Harness differs from Runtime

| | Harness | Runtime |
|---|---|---|
| Agent loop | Managed by service | Your container code |
| Container | Not required | Required (ARM64, ECR) |
| CI/CD | Not required | Required |
| Tools | Declared in CFN | Wired in agent code |
| Model | Declared in CFN | Configured in agent code |

Use **Harness** when you want the service to run the agent loop.
Use **Runtime** when you need full control over the container and framework.

## Stacks (deploy in order)

| # | Template | Creates |
|---|----------|---------|
| 1 | `01-iam.yaml` | HarnessExecutionRole |
| 2 | `02-harness.yaml` | `AWS::BedrockAgentCore::Harness` (optionally wired to a Gateway) |
| 99 | `99-client.yaml` | Lambda test client |

## Deploy

### 1. IAM
```bash
aws cloudformation deploy \
  --template-file cloudformation/01-iam.yaml \
  --stack-name harness-iam \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides ApplicationName=coreagent Environment=dev
```

### 2. Harness (standalone, no gateway)
```bash
ROLE_ARN=$(aws cloudformation describe-stacks --stack-name harness-iam \
  --query "Stacks[0].Outputs[?OutputKey=='HarnessExecutionRoleArn'].OutputValue" --output text)

aws cloudformation deploy \
  --template-file cloudformation/02-harness.yaml \
  --stack-name harness \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ApplicationName=coreagent \
    Environment=dev \
    HarnessExecutionRoleArn="$ROLE_ARN"
```

### 2b. Harness wired to an existing Gateway
```bash
aws cloudformation deploy \
  --template-file cloudformation/02-harness.yaml \
  --stack-name harness \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    ApplicationName=coreagent \
    Environment=dev \
    HarnessExecutionRoleArn="$ROLE_ARN" \
    GatewayArn="arn:aws:bedrock-agentcore:us-east-1:123456789012:gateway/my-gateway-abc123"
```

### 3. Client Lambda
```bash
HARNESS_ARN=$(aws cloudformation describe-stacks --stack-name harness \
  --query "Stacks[0].Outputs[?OutputKey=='HarnessArn'].OutputValue" --output text)

aws cloudformation deploy \
  --template-file cloudformation/99-client.yaml \
  --stack-name harness-client \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides \
    ApplicationName=coreagent \
    Environment=dev \
    HarnessArn="$HARNESS_ARN"
```

## Invoke

From the Lambda console, open `coreagent-dev-harness-client` and test with:
```json
{ "prompt": "What is the capital of France?" }
```

Or via CLI:
```bash
HARNESS_ARN=$(aws cloudformation describe-stacks --stack-name harness \
  --query "Stacks[0].Outputs[?OutputKey=='HarnessArn'].OutputValue" --output text)

./scripts/invoke.sh "$HARNESS_ARN" "What is the capital of France?"
```

## Teardown
```bash
for stack in harness-client harness harness-iam; do
  aws cloudformation delete-stack --stack-name $stack
  aws cloudformation wait stack-delete-complete --stack-name $stack
done
```

## Lint
```bash
cfn-lint cloudformation/01-iam.yaml cloudformation/99-client.yaml
# Harness resource type post-dates cfn-lint bundled spec — suppress false positives:
cfn-lint cloudformation/02-harness.yaml --ignore-checks E3001 E1010
```
