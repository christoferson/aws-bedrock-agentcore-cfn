# CLAUDE.md

Reference examples and CloudFormation templates for **Amazon Bedrock AgentCore**.

## Repository layout

```
agentcore-quickstart/   4-layer production stack (IAM, Network, CI/CD, Runtime)
agentcore-runtime/      CloudFormation tutorial examples (01–04) for AgentCore Runtime
agentcore-gateway/      CloudFormation templates for AgentCore Gateway
agentcore-identity/     CloudFormation templates for AgentCore Identity
aws-documentation/      Saved AWS docs — READ THESE before changing any template
```

Each folder has its own `CLAUDE.md` (or `README.md`) with folder-specific guidance.

## Universal rules (apply everywhere)

### AWS documentation
If you need current AWS behavior or CFN property details, **fetch the doc and
save it into `aws-documentation/`**, then cite it in template comments. Never
change a template to contradict a saved doc without fetching an updated source.

### Cross-stack parameter convention
All stacks pass values between layers via **explicit parameters** only.
- Each stack has `Outputs:` — the operator reads them and passes them as
  `Parameters:` to the next stack.
- **Never** use `Fn::ImportValue`, `Export`, or SSM Parameter Store lookups
  between stacks.
- When a value flows from one layer to another, add an `Output` to the producer
  and a matching `Parameter` to the consumer.

### Naming
`ApplicationName` defaults to `bedrock-agentcore`. Several AWS managed policies
scope permissions to this prefix — keep it unless you also update IAM ARNs.

### cfn-lint false positives
`AWS::BedrockAgentCore::*` types post-date cfn-lint's bundled spec.
`E3001` (unsupported type) and `E1010` (invalid GetAtt) on those resources are
false positives. Lint with `--ignore-checks E3001 E1010` for affected templates.
