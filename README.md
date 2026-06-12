# aws-bedrock-agentcore-cfn

Production CloudFormation for deploying [Strands](https://strandsagents.com/)
agents to **Amazon Bedrock AgentCore Runtime**, organized as 4 layered stacks
deployed in sequence.

| Layer | Stack | Purpose |
|-------|-------|---------|
| 1 | `cloudformation/01-iam-foundation.yaml` | IAM roles (runtime execution, CodeBuild, CodePipeline) |
| 2 | `cloudformation/02-network.yaml` | VPC, private subnets, PrivateLink endpoints |
| 3 | `cloudformation/03-cicd.yaml` | CodeCommit, ECR, CodeBuild, CodePipeline |
| 4 | `cloudformation/04-agentcore-runtime.yaml` | `AWS::BedrockAgentCore::Runtime` (VPC mode) |

The agent lives at the repo root (`app.py`, `requirements.txt`, `Dockerfile`) and is
built into an ARM64 image by the pipeline. Stacks pass values to each other via
**explicit parameters** (`params/<env>/*.json`).

- **Deploy:** see [DEPLOY.md](DEPLOY.md).
- **Architecture & conventions for contributors:** see [CLAUDE.md](CLAUDE.md).
- **Saved AWS reference docs:** `aws-documentation/`.
