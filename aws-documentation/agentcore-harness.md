# AgentCore Harness — CloudFormation Reference

Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-harness.html
Saved: June 2026

---

## CFN Resource: `AWS::BedrockAgentCore::Harness`

A managed agent loop that wraps a model, tools, skills, and memory into a single
invokable endpoint without requiring a custom container. The Harness provisions an
AgentCore Runtime internally and exposes it under the Harness ARN.

### Properties

| Property | Type | Required | Update | Notes |
|---|---|---|---|---|
| `HarnessName` | String | **Yes** | **Replacement** | Pattern: `^[a-zA-Z][a-zA-Z0-9_]{0,39}$` |
| `ExecutionRoleArn` | String | **Yes** | No interruption | IAM role the harness assumes at runtime |
| `Model` | HarnessModelConfiguration | **Yes** | No interruption | Model used by the agent loop |
| `AllowedTools` | Array of String | No | No interruption | 1–64 items; restrict which tools can be called |
| `AuthorizerConfiguration` | AuthorizerConfiguration | No | No interruption | Inbound auth (JWT) |
| `Environment` | HarnessEnvironmentProvider | No | No interruption | Compute environment (AgentCore Runtime) |
| `EnvironmentArtifact` | HarnessEnvironmentArtifact | No | No interruption | Container image for custom environments |
| `EnvironmentVariables` | Object of String | No | No interruption | Passed into the runtime environment |
| `MaxIterations` | Integer | No | No interruption | Max agent loop iterations per invocation |
| `MaxTokens` | Integer | No | No interruption | Max total output tokens per invocation |
| `Memory` | HarnessMemoryConfiguration | No | No interruption | AgentCore Memory (short + long term) |
| `Skills` | Array of HarnessSkill | No | No interruption | Code skills loaded from S3 or Git |
| `SystemPrompt` | Array of HarnessSystemContentBlock | No | No interruption | System prompt blocks |
| `Tags` | Array of Tag | No | No interruption | Max 50 tags; Key/Value objects |
| `TimeoutSeconds` | Integer | No | No interruption | Max duration per invocation |
| `Tools` | Array of HarnessTool | No | No interruption | Tools available to the agent |
| `Truncation` | HarnessTruncationConfiguration | No | No interruption | Context truncation strategy |

### Return Values

`Ref` → HarnessId.

`Fn::GetAtt`:

| Attribute | Description |
|---|---|
| `Arn` | Full ARN of the harness |
| `HarnessId` | Unique short ID |
| `Status` | `CREATING \| ACTIVE \| FAILED \| DELETING` |
| `CreatedAt` | ISO-8601 creation timestamp |
| `UpdatedAt` | ISO-8601 last-update timestamp |
| `Environment.AgentCoreRuntimeEnvironment.AgentRuntimeArn` | ARN of the underlying Runtime |
| `Environment.AgentCoreRuntimeEnvironment.AgentRuntimeId` | ID of the underlying Runtime |
| `Environment.AgentCoreRuntimeEnvironment.AgentRuntimeName` | Name of the underlying Runtime |

---

## Property Types

### `HarnessModelConfiguration` (Union — pick exactly one)

| Property | Type | Notes |
|---|---|---|
| `BedrockModelConfig` | HarnessBedrockModelConfig | Bedrock converse/responses API |
| `GeminiModelConfig` | HarnessGeminiModelConfig | Google Gemini |
| `LiteLlmModelConfig` | HarnessLiteLlmModelConfig | LiteLLM proxy |
| `OpenAiModelConfig` | HarnessOpenAiModelConfig | OpenAI-compatible endpoint |

### `HarnessBedrockModelConfig`

| Property | Type | Required | Notes |
|---|---|---|---|
| `ModelId` | String | **Yes** | Bedrock model ID, e.g. `global.anthropic.claude-sonnet-4-6` |
| `ApiFormat` | String | No | `converse_stream \| responses \| chat_completions` |
| `MaxTokens` | Integer (min 1) | No | Per-call token limit |
| `Temperature` | Number (0–2) | No | |
| `TopP` | Number (0–1) | No | |
| `AdditionalParams` | Object | No | Free-form key/value passed to the model API |

### `HarnessEnvironmentProvider` (Union)

| Property | Type | Notes |
|---|---|---|
| `AgentCoreRuntimeEnvironment` | HarnessAgentCoreRuntimeEnvironment | Use existing or auto-create Runtime |

### `HarnessAgentCoreRuntimeEnvironment`

| Property | Type | Required | Notes |
|---|---|---|---|
| `AgentRuntimeArn` | String | No | Point to an existing Runtime ARN |
| `AgentRuntimeId` | String | No | Point to an existing Runtime ID |
| `AgentRuntimeName` | String | No | Reference by name |
| `NetworkConfiguration` | NetworkConfiguration | No | PUBLIC or VPC |
| `FilesystemConfigurations` | Array (0–5) | No | EFS/S3 mounts |
| `LifecycleConfiguration` | LifecycleConfiguration | No | Idle timeout, max lifetime |

### `NetworkConfiguration`

| Property | Type | Required | Notes |
|---|---|---|---|
| `NetworkMode` | String | **Yes** | `PUBLIC \| VPC` |
| `NetworkModeConfig` | VpcConfig | No | Required when `NetworkMode: VPC` |

### `HarnessEnvironmentArtifact` (Union)

| Property | Type | Notes |
|---|---|---|
| `ContainerConfiguration` | ContainerConfiguration | Custom container image |

### `ContainerConfiguration`

| Property | Type | Required | Notes |
|---|---|---|---|
| `ContainerUri` | String | **Yes** | ECR URI with tag/digest; also accepts `public.ecr.aws/...` |

### `HarnessTool`

| Property | Type | Required | Notes |
|---|---|---|---|
| `Type` | String | **Yes** | `remote_mcp \| agentcore_browser \| agentcore_gateway \| inline_function \| agentcore_code_interpreter` |
| `Name` | String | No | Pattern: `^[a-zA-Z0-9_-]+$`; 1–64 chars |
| `Config` | HarnessToolConfiguration | No | Type-specific config |

### `HarnessToolConfiguration` (Union — match the `Type` field)

| Property | Type | Notes |
|---|---|---|
| `AgentCoreGateway` | HarnessAgentCoreGatewayConfig | Connect to an AgentCore Gateway |
| `AgentCoreBrowser` | HarnessAgentCoreBrowserConfig | Managed browser |
| `AgentCoreCodeInterpreter` | HarnessAgentCoreCodeInterpreterConfig | Code execution sandbox |
| `InlineFunction` | HarnessInlineFunctionConfig | Python function defined in template |
| `RemoteMcp` | HarnessRemoteMcpConfig | External MCP server |

### `HarnessAgentCoreGatewayConfig`

| Property | Type | Required | Notes |
|---|---|---|---|
| `GatewayArn` | String | **Yes** | Full Gateway ARN |
| `OutboundAuth` | HarnessGatewayOutboundAuth | No | Auth the harness uses to call the gateway |

### `HarnessInlineFunctionConfig`

| Property | Type | Required | Notes |
|---|---|---|---|
| `Description` | String (1–4096) | **Yes** | Describes what the function does (used as tool description) |
| `InputSchema` | Json | **Yes** | JSON Schema for the function's input parameters |

### `HarnessSkill`

| Property | Type | Notes |
|---|---|---|
| `Path` | String (min 1) | Path within the source to the skill entrypoint |
| `S3` | HarnessSkillS3Source | Load skill code from S3 |
| `Git` | HarnessSkillGitSource | Load skill code from a Git repo |

### `HarnessSkillS3Source`

| Property | Type | Required | Notes |
|---|---|---|---|
| `Uri` | String | **Yes** | Pattern: `^s3://`; min 5 chars |

### `HarnessSkillGitSource`

| Property | Type | Required | Notes |
|---|---|---|---|
| `Url` | String | **Yes** | Pattern: `^https://` |
| `Path` | String | No | Subdirectory within the repo |
| `Auth` | HarnessSkillGitAuth | No | Git credentials |

### `HarnessSystemContentBlock`

| Property | Type | Required | Notes |
|---|---|---|---|
| `Text` | String (min 1) | **Yes** | One block of system prompt text |

### `HarnessMemoryConfiguration`

| Property | Type | Notes |
|---|---|---|
| `AgentCoreMemoryConfiguration` | HarnessAgentCoreMemoryConfiguration | Connect to an AgentCore Memory instance |

### `HarnessAgentCoreMemoryConfiguration`

| Property | Type | Required | Notes |
|---|---|---|---|
| `Arn` | String | **Yes** | ARN of an existing AgentCore Memory resource |
| `ActorId` | String | No | Identity scope for memory operations |
| `MessagesCount` | Integer | No | Number of recent messages to load from memory |
| `RetrievalConfig` | Object | No | Free-form retrieval settings |

### `HarnessTruncationConfiguration`

| Property | Type | Required | Notes |
|---|---|---|---|
| `Strategy` | String | **Yes** | `sliding_window \| summarization \| none` |
| `Config` | HarnessTruncationStrategyConfiguration | No | Strategy-specific parameters |

### `HarnessTruncationStrategyConfiguration`

| Property | Type | Notes |
|---|---|---|
| `SlidingWindow` | HarnessSlidingWindowConfiguration | Keep the N most recent messages |
| `Summarization` | HarnessSummarizationConfiguration | Summarize older context |

---

## Type Hierarchy

```
AWS::BedrockAgentCore::Harness
├── Model: HarnessModelConfiguration (Union)
│   ├── BedrockModelConfig: HarnessBedrockModelConfig
│   ├── GeminiModelConfig
│   ├── LiteLlmModelConfig
│   └── OpenAiModelConfig
├── Environment: HarnessEnvironmentProvider (Union)
│   └── AgentCoreRuntimeEnvironment: HarnessAgentCoreRuntimeEnvironment
│       └── NetworkConfiguration: NetworkConfiguration
│           └── NetworkModeConfig: VpcConfig
├── EnvironmentArtifact: HarnessEnvironmentArtifact (Union)
│   └── ContainerConfiguration: ContainerConfiguration
├── Tools[]: HarnessTool
│   └── Config: HarnessToolConfiguration (Union)
│       ├── AgentCoreGateway: HarnessAgentCoreGatewayConfig
│       ├── AgentCoreBrowser
│       ├── AgentCoreCodeInterpreter
│       ├── InlineFunction: HarnessInlineFunctionConfig
│       └── RemoteMcp
├── Skills[]: HarnessSkill
│   ├── S3: HarnessSkillS3Source
│   └── Git: HarnessSkillGitSource
│       └── Auth: HarnessSkillGitAuth
├── SystemPrompt[]: HarnessSystemContentBlock
├── Memory: HarnessMemoryConfiguration
│   └── AgentCoreMemoryConfiguration: HarnessAgentCoreMemoryConfiguration
└── Truncation: HarnessTruncationConfiguration
    └── Config: HarnessTruncationStrategyConfiguration
        ├── SlidingWindow: HarnessSlidingWindowConfiguration
        └── Summarization: HarnessSummarizationConfiguration
```

---

## Key Concepts

- **No container required**: Unlike `AWS::BedrockAgentCore::Runtime`, the Harness manages the agent loop itself. You only supply a model, tools, and optionally a system prompt.
- **HarnessName forces replacement**: like `AgentRuntimeName` on Runtime.
- **Tags**: `Array of Tag` (Key/Value objects) — same as `AWS::Lambda::Function`, NOT the flat map used by Gateway/Runtime.
- **Tool type must match Config**: `Type: agentcore_gateway` → `Config.AgentCoreGateway`; `Type: inline_function` → `Config.InlineFunction`, etc.
- **cfn-lint**: `E3001` and `E1010` on `AWS::BedrockAgentCore::Harness` are false positives — suppress with `--ignore-checks E3001 E1010`.

---

## Execution Role — Required IAM Permissions

Source: https://docs.aws.amazon.com/service-authorization/latest/reference/list_amazonbedrockagentcore.html
Verified: June 2026

The Harness execution role needs permissions in four categories:

### 1. Bedrock model inference
```json
{ "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
  "Resource": ["arn:aws:bedrock:*::foundation-model/*", "arn:aws:bedrock:<region>:<account>:*"] }
```

### 2. CloudWatch Logs / X-Ray / Metrics
Standard observability permissions scoped to `/aws/bedrock-agentcore/*` and namespace `bedrock-agentcore`.

### 3. Gateway invocation (if tools are wired)
```json
{ "Action": "bedrock-agentcore:InvokeGateway",
  "Resource": "arn:aws:bedrock-agentcore:<region>:<account>:gateway/*" }
```

### 4. Session event store — **required at runtime even without explicit Memory config**
The Harness calls these to read/write session history. `ListEvents` was the reported missing permission.
All four actions require the `memory` resource ARN.

| Action | Access Level | Notes |
|---|---|---|
| `bedrock-agentcore:CreateEvent` | Write | Condition keys: `sessionId`, `actorId` |
| `bedrock-agentcore:GetEvent` | Read | Condition keys: `sessionId`, `actorId` |
| `bedrock-agentcore:ListEvents` | List | Condition keys: `sessionId`, `actorId` |
| `bedrock-agentcore:DeleteEvent` | Write | Condition keys: `sessionId`, `actorId` |

```json
{ "Action": ["bedrock-agentcore:CreateEvent", "bedrock-agentcore:GetEvent",
             "bedrock-agentcore:ListEvents", "bedrock-agentcore:DeleteEvent"],
  "Resource": "arn:aws:bedrock-agentcore:<region>:<account>:memory/*" }
```

### 5. Long-term memory records (needed only when `Memory` is configured in the Harness)
```json
{ "Action": ["bedrock-agentcore:BatchCreateMemoryRecords", "bedrock-agentcore:BatchUpdateMemoryRecords",
             "bedrock-agentcore:BatchDeleteMemoryRecords", "bedrock-agentcore:GetMemoryRecord",
             "bedrock-agentcore:ListMemoryRecords", "bedrock-agentcore:DeleteMemoryRecord",
             "bedrock-agentcore:ListActors", "bedrock-agentcore:ListMemoryExtractionJobs",
             "bedrock-agentcore:GetMemory"],
  "Resource": "arn:aws:bedrock-agentcore:<region>:<account>:memory/*" }

---

## Memory — `AWS::BedrockAgentCore::Memory`

Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/aws-resource-bedrockagentcore-memory.html
Saved: June 2026

### Properties

| Property | Type | Required | Update | Notes |
|---|---|---|---|---|
| `Name` | String | **Yes** | Replacement | Pattern: `^[a-zA-Z][a-zA-Z0-9_]{0,47}$` |
| `EventExpiryDuration` | Integer | **Yes** | No interruption | Days; min 3, max 365. Applied per event at write time — does not backfill existing events. |
| `Description` | String | No | No interruption | |
| `EncryptionKeyArn` | String | No | Replacement | Customer-managed KMS key ARN |
| `MemoryExecutionRoleArn` | String | No | No interruption | IAM role for memory operations |
| `MemoryStrategies` | Array of MemoryStrategy | No | No interruption | Long-term extraction strategies |
| `IndexedKeys` | Array of IndexedKey | No | No interruption | 1–10; only indexed keys usable in metadata filters |
| `StreamDeliveryResources` | StreamDeliveryResources | No | No interruption | Stream memory records to external targets |
| `Tags` | Object of String | No | No interruption | Flat map (same as Gateway/Runtime, not Array of Tag) |

### Return Values

`Ref` → Memory ARN (e.g. `arn:aws:bedrock-agentcore:us-east-1:123456789012:memory/MyMemory-a1b2c3d4e5`)

`Fn::GetAtt`: `MemoryArn`, `MemoryId`, `Status`, `CreatedAt`, `UpdatedAt`, `FailureReason`

### MemoryStrategy (Union — include one or more sub-keys)

| Sub-key | Required fields | NamespaceTemplates default |
|---|---|---|
| `SemanticMemoryStrategy` | `Name` | `/facts/{actorId}/` |
| `SummaryMemoryStrategy` | `Name` | `/summary/{actorId}/{sessionId}/` |
| `UserPreferenceMemoryStrategy` | `Name` | `/users/{actorId}/preferences/` |
| `EpisodicMemoryStrategy` | `Name` | `/episodes/{actorId}/` |
| `CustomMemoryStrategy` | `Name` | User-defined |

`NamespaceTemplates` is optional — omit to use the default path.
`{actorId}` and `{sessionId}` are template variables filled at runtime from the invocation parameters.

### Wiring Memory to a Harness

```yaml
Memory:
  AgentCoreMemoryConfiguration:
    Arn: !GetAtt Memory.MemoryArn   # ARN of the AWS::BedrockAgentCore::Memory resource
    MessagesCount: 20               # recent short-term messages to load per invocation (optional)
    ActorId: default                # default actor scope; callers can override at invoke time (optional)
```

### Key Behaviours (from dev guide)

- **Short-term memory**: raw events (messages, tool calls) per session. Gives continuity across turns without the caller passing history.
- **Long-term memory**: extracted from events via strategies; retrieved via semantic search and injected into context on each invocation automatically.
- **actorId scoping**: each actor gets isolated short-term and long-term memory. Pass `actorId` at invoke time per user.
- **Managed vs BYO**: omitting `Memory` on the Harness auto-provisions managed memory with defaults. BYO (`agentCoreMemoryConfiguration`) is needed for shared memory across harnesses, custom KMS, or custom namespaces.
- **Retrieval defaults**: `topK=10`, `relevanceScore=0.2`. Override by setting `retrievalConfig` in the BYO config.
- **Deletion**: `DeleteHarness` cascade-deletes managed memory by default. Pass `deleteManagedMemory=false` to detach instead.
