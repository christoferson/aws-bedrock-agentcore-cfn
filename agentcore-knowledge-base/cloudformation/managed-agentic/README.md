# Managed KB — Agentic Retrieval variant

Harness → AgentCore Gateway → **managed** Bedrock Knowledge Base(s), using the
`AgenticRetrieveStream` tool.

This is one of two sibling variants. See `../managed-retrieve/` for the cheaper,
harness-controlled alternative. **Deploy one, not both** — they use the same
resource names and would clash.

## What this variant does

The gateway exposes a **single tool** spanning **both** KBs:

```
kb-retrieval___AgenticRetrieveStream
```

When the harness calls it, a Bedrock-managed LLM runs its own agent loop inside the
tool call: plans a strategy, decides which KB(s) to query, does multi-hop retrieval,
re-ranks, and returns a synthesized, citation-backed answer.

## When to choose this variant

| Choose managed-agentic when… | Choose managed-retrieve when… |
|---|---|
| The caller wants a finished, cited answer in one shot | The caller (harness) will reason over raw passages itself |
| Questions are broad / multi-part / span both KBs | Questions map cleanly to one KB |
| You want built-in planning + re-ranking | You want lowest cost and latency |
| Extra token/latency cost is acceptable | You want retrieval control in the harness |

> **Note on cost:** because the harness is *already* an agent, this runs an
> agent-inside-an-agent — a second reasoning LLM per tool call. If cost matters and
> your harness can orchestrate retrieval, prefer `managed-retrieve`.

## Stacks

| Stack | Creates | Consumes |
|---|---|---|
| `01-iam.yaml` | KB role (S3 read) + Gateway role (Retrieve + **AgenticRetrieveStream** + GetKnowledgeBase) | — |
| `02-kb-products.yaml` | S3 bucket + managed KB + data source | `KnowledgeBaseRoleArn` |
| `03-kb-suppliers.yaml` | S3 bucket + managed KB + data source | `KnowledgeBaseRoleArn` |
| `04-gateway.yaml` | Gateway + 1 target (AgenticRetrieveStream, both KBs) | `GatewayRoleArn`, both `KnowledgeBaseId`s |
| `05-harness.yaml` | Harness role + Harness | `GatewayArn` |

`02` and `03` can deploy in parallel. Everything else is sequential.

## Deploy

```bash
APP=coreagent ENV=dev

aws cloudformation deploy --template-file 01-iam.yaml \
  --stack-name $APP-$ENV-mkb-iam --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides ApplicationName=$APP Environment=$ENV

# read KnowledgeBaseRoleArn / GatewayRoleArn from stack 01 outputs, then:
aws cloudformation deploy --template-file 02-kb-products.yaml \
  --stack-name $APP-$ENV-mkb-products \
  --parameter-overrides ApplicationName=$APP Environment=$ENV KnowledgeBaseRoleArn=<arn>
aws cloudformation deploy --template-file 03-kb-suppliers.yaml \
  --stack-name $APP-$ENV-mkb-suppliers \
  --parameter-overrides ApplicationName=$APP Environment=$ENV KnowledgeBaseRoleArn=<arn>

# read KnowledgeBaseId from stacks 02 & 03, GatewayRoleArn from 01, then:
aws cloudformation deploy --template-file 04-gateway.yaml \
  --stack-name $APP-$ENV-mkb-gateway \
  --parameter-overrides ApplicationName=$APP Environment=$ENV \
    GatewayRoleArn=<arn> ProductsKnowledgeBaseId=<id> SuppliersKnowledgeBaseId=<id>

# read GatewayArn from stack 04, then:
aws cloudformation deploy --template-file 05-harness.yaml \
  --stack-name $APP-$ENV-mkb-harness --capabilities CAPABILITY_NAMED_IAM \
  --parameter-overrides ApplicationName=$APP Environment=$ENV GatewayArn=<arn>
```

After stacks 02/03, upload documents to the S3 buckets and run
`start-ingestion-job` (see the header comments in those templates).

## Lint

`AWS::Bedrock::*` and `AWS::BedrockAgentCore::*` post-date cfn-lint's bundled spec,
so `E3001` and `E1010` on those resources are false positives:

```bash
cfn-lint *.yaml --ignore-checks E3001 E1010
```
