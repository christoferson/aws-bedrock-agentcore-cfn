# AWS::Lambda::Function — CloudFormation Reference

Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html
Saved: June 2026

---

## Properties

| Property | Type | Required | Update |
|---|---|---|---|
| `Architectures` | Array of String (`x86_64 \| arm64`) | No | No interruption |
| `Code` | Code | **Yes** | No interruption |
| `CodeSigningConfigArn` | String | No | No interruption |
| `DeadLetterConfig` | DeadLetterConfig | No | No interruption |
| `Description` | String (max 256) | No | No interruption |
| `Environment` | Environment | No | No interruption |
| `EphemeralStorage` | EphemeralStorage | No | No interruption |
| `FileSystemConfigs` | Array of FileSystemConfig (max 1) | No | No interruption |
| `FunctionName` | String | No | **Replacement** |
| `Handler` | String (max 128) | No | No interruption |
| `ImageConfig` | ImageConfig | No | No interruption |
| `KmsKeyArn` | String | No | No interruption |
| `Layers` | Array of String | No | No interruption |
| `LoggingConfig` | LoggingConfig | No | No interruption |
| `MemorySize` | Integer (128–32768 MB) | No | No interruption |
| `PackageType` | String (`Image \| Zip`) | No | **Replacement** |
| `RecursiveLoop` | String (`Allow \| Terminate`) | No | No interruption |
| `ReservedConcurrentExecutions` | Integer (min 0) | No | No interruption |
| `Role` | String (IAM role ARN) | **Yes** | No interruption |
| `Runtime` | String | No | No interruption |
| `RuntimeManagementConfig` | RuntimeManagementConfig | No | No interruption |
| `SnapStart` | SnapStart | No | No interruption |
| `Tags` | **Array of Tag** | No | No interruption |
| `Timeout` | Integer (1–900 seconds) | No | No interruption |
| `TracingConfig` | TracingConfig | No | No interruption |
| `VpcConfig` | VpcConfig | No | No interruption |

---

## Tags — correct syntax

`Tags` is **Array of Tag** (Key/Value objects), NOT a flat string map.

```yaml
Tags:
  - Key: Application
    Value: my-app
  - Key: Environment
    Value: dev
```

This differs from resources like `AWS::BedrockAgentCore::Gateway` where `Tags` is `Object of String` (flat map):

```yaml
Tags:
  Application: my-app
  Environment: dev
```

---

## Return Values

`Ref` → function name.

`Fn::GetAtt`:
- `Arn` — function ARN

---

## Code (ZipFile for inline Python/Node.js)

```yaml
Code:
  ZipFile: |
    def handler(event, context):
        return {"statusCode": 200}
```

ZipFile only works for Python and Node.js runtimes. For other runtimes use S3Bucket/S3Key.

---

## Environment Variables

```yaml
Environment:
  Variables:
    MY_VAR: value
    OTHER_VAR: !Ref SomeResource
```

Note: `AWS_REGION` is a reserved environment variable name in Lambda — use a different name (e.g. `AWS_REGION_NAME`) to pass the region as a custom variable.
