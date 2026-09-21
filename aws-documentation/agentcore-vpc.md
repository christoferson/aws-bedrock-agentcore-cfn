# AgentCore VPC Configuration

Sources:
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-vpc.html
- https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/vpc-interface-endpoints.html
Saved: June 2026

---

## VPC endpoint service names

### AgentCore PrivateLink endpoints

| Endpoint | Service name | Covers |
|---|---|---|
| Data plane | `com.amazonaws.{region}.bedrock-agentcore` | Runtime invoke, Memory events, Built-in Tools, Identity |
| Control plane | `com.amazonaws.{region}.bedrock-agentcore-control` | Runtime/Memory create/update/delete |
| Gateway | `com.amazonaws.{region}.bedrock-agentcore.gateway` | Gateway data plane |

### Supporting endpoints

| Service | Service name | Type | Purpose |
|---|---|---|---|
| Bedrock runtime | `com.amazonaws.{region}.bedrock-runtime` | Interface | Model inference |
| ECR DKR | `com.amazonaws.{region}.ecr.dkr` | Interface | Container image pulls |
| ECR API | `com.amazonaws.{region}.ecr.api` | Interface | ECR API calls |
| S3 | `com.amazonaws.{region}.s3` | **Gateway** | ECR image layer storage |
| CloudWatch Logs | `com.amazonaws.{region}.logs` | Interface | Log delivery |
| X-Ray | `com.amazonaws.{region}.xray` | Interface | Distributed tracing |
| CloudWatch Metrics | `com.amazonaws.{region}.monitoring` | Interface | PutMetricData |
| STS | `com.amazonaws.{region}.sts` | Interface | GetServiceBearerToken (ECR Public auth) |

---

## ECR Public gap — NAT Gateway always required

ECR Public (`public.ecr.aws`) does **not** support VPC interface endpoints.
The Harness pulls its managed container from ECR Public on session start.
Even with full VPC endpoint coverage, a NAT Gateway with an Internet Gateway is still required.

---

## Architecture for private harness

```
Private subnets (Harness ENIs)
  │
  ├─ HTTPS to VPC endpoint ENIs → bedrock-agentcore (data plane)
  │                              → bedrock-agentcore.gateway  ← REQUIRED for agentcore_gateway tools
  │                              → bedrock-agentcore-control
  │                              → bedrock-runtime, ecr.dkr, ecr.api, logs, xray, monitoring, sts
  └─ HTTPS to NAT GW → Internet → ECR Public (public.ecr.aws)
```

- VPC must have `EnableDnsSupport: true` and `EnableDnsHostnames: true`.
- Interface endpoints: `PrivateDnsEnabled: true` on all three AgentCore endpoints.
- S3 Gateway endpoint: associated with the private route table (free; eliminates NAT charges for ECR layer pulls).

---

## Security groups

**Endpoint security group** (applied to interface endpoint ENIs):
- Inbound: TCP 443 from VPC CIDR

**Harness security group** (applied to Runtime ENIs):
- Outbound: TCP 443 to `0.0.0.0/0` (covers both VPC endpoint ENIs via DNS and NAT for ECR Public)
- No inbound rules required

---

## VPC Endpoint CFN snippet

```yaml
# Interface endpoint example
BedrockAgentCoreEndpoint:
  Type: AWS::EC2::VPCEndpoint
  Properties:
    VpcId: !Ref Vpc
    ServiceName: !Sub "com.amazonaws.${AWS::Region}.bedrock-agentcore"
    VpcEndpointType: Interface
    SubnetIds: [!Ref PrivateSubnet1, !Ref PrivateSubnet2]
    SecurityGroupIds: [!Ref EndpointSecurityGroup]
    PrivateDnsEnabled: true

# S3 Gateway endpoint
S3Endpoint:
  Type: AWS::EC2::VPCEndpoint
  Properties:
    VpcId: !Ref Vpc
    ServiceName: !Sub "com.amazonaws.${AWS::Region}.s3"
    VpcEndpointType: Gateway
    RouteTableIds: [!Ref PrivateRouteTable]
```
