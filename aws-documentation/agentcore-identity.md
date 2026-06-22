# AgentCore Identity — CloudFormation Reference

Consolidated reference for the three AgentCore identity CFN resource types.

---

## Type Hierarchy

```
AWS::BedrockAgentCore::WorkloadIdentity
  (no sub-properties)

AWS::BedrockAgentCore::ApiKeyCredentialProvider
  └── ApiKeySecretConfig → SecretReference (JsonKey, SecretId)

AWS::BedrockAgentCore::OAuth2CredentialProvider
  └── Oauth2ProviderConfigInput
        ├── CustomOauth2ProviderConfig  → CustomOauth2ProviderConfigInput
        │     ├── OauthDiscovery        → Oauth2Discovery
        │     │     ├── DiscoveryUrl    (string, pattern ^.+/\.well-known/openid-configuration$)
        │     │     └── AuthorizationServerMetadata → Oauth2AuthorizationServerMetadata
        │     │           (TokenEndpoint, AuthorizationEndpoint, Issuer)
        │     ├── ClientSecretConfig    → SecretReference
        │     └── OnBehalfOfTokenExchangeConfig → OnBehalfOfTokenExchangeConfig
        ├── GoogleOauth2ProviderConfig  → GoogleOauth2ProviderConfigInput
        │     └── ClientSecretConfig   → SecretReference
        ├── GithubOauth2ProviderConfig  → (similar, ClientId required)
        ├── AtlassianOauth2ProviderConfig
        ├── LinkedinOauth2ProviderConfig
        ├── MicrosoftOauth2ProviderConfig
        ├── SalesforceOauth2ProviderConfig
        ├── SlackOauth2ProviderConfig
        └── IncludedOauth2ProviderConfig → IncludedOauth2ProviderConfigInput
              (ClientId required; AuthorizationEndpoint, TokenEndpoint, Issuer, ClientSecret optional)
```

---

## AWS::BedrockAgentCore::WorkloadIdentity

Provides an OAuth2-based identity for agent workloads (inbound identity — identifies the agent itself).

### Properties

| Property | Type | Required | Update | Notes |
|----------|------|----------|--------|-------|
| Name | String | Yes | Replacement | Pattern: `[A-Za-z0-9_.-]+`, 3–255 chars |
| AllowedResourceOauth2ReturnUrls | List\<String\> | No | No interruption | Max 2048 chars each |
| Tags | List\<Tag\> | No | No interruption | Key/Value pairs |

### GetAtt

| Attribute | Description |
|-----------|-------------|
| WorkloadIdentityArn | ARN of the workload identity |
| CreatedTime | ISO-8601 creation timestamp |
| LastUpdatedTime | ISO-8601 last-update timestamp |

### Minimal YAML

```yaml
WorkloadIdentity:
  Type: AWS::BedrockAgentCore::WorkloadIdentity
  Properties:
    Name: my-agent-identity
```

---

## AWS::BedrockAgentCore::ApiKeyCredentialProvider

Stores an API key credential. Two secret source modes:
- **MANAGED** — AgentCore manages the secret in Secrets Manager; supply `ApiKey` inline.
- **EXTERNAL** — you own the Secrets Manager secret; supply `ApiKeySecretConfig` with `SecretId` + `JsonKey`.

### Properties

| Property | Type | Required | Update | Notes |
|----------|------|----------|--------|-------|
| Name | String | Yes | Replacement | Unique name |
| ApiKey | String | No | No interruption | Inline value; use with `ApiKeySecretSource: MANAGED` |
| ApiKeySecretConfig | SecretReference | No | No interruption | Required when `ApiKeySecretSource: EXTERNAL` |
| ApiKeySecretSource | String | No | No interruption | `MANAGED \| EXTERNAL` |
| Tags | List\<Tag\> | No | No interruption | |

### SecretReference (ApiKeySecretConfig)

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| JsonKey | String | Yes | 1–128 chars; JSON key inside the secret value |
| SecretId | String | Yes | 1–2048 chars; ARN or name of the Secrets Manager secret |

### GetAtt

| Attribute | Description |
|-----------|-------------|
| CredentialProviderArn | ARN of the credential provider |
| ApiKeySecretJsonKey | JSON key used to read the API key from the secret |
| CreatedTime | ISO-8601 creation timestamp |
| LastUpdatedTime | ISO-8601 last-update timestamp |

### Minimal YAML (MANAGED)

```yaml
ApiKeyProvider:
  Type: AWS::BedrockAgentCore::ApiKeyCredentialProvider
  Properties:
    Name: my-api-key-provider
    ApiKey: sk-my-secret-key
    ApiKeySecretSource: MANAGED
```

### Minimal YAML (EXTERNAL)

```yaml
ApiKeyProvider:
  Type: AWS::BedrockAgentCore::ApiKeyCredentialProvider
  Properties:
    Name: my-api-key-provider
    ApiKeySecretSource: EXTERNAL
    ApiKeySecretConfig:
      SecretId: arn:aws:secretsmanager:us-east-1:123456789012:secret:my-api-key
      JsonKey: apiKey
```

---

## AWS::BedrockAgentCore::OAuth2CredentialProvider

Stores OAuth2 client credentials for a specific vendor. Supports 25 vendors via `CredentialProviderVendor`.

### Properties

| Property | Type | Required | Update | Notes |
|----------|------|----------|--------|-------|
| Name | String | Yes | Replacement | Unique name |
| CredentialProviderVendor | String | Yes | Replacement | See allowed values below |
| Oauth2ProviderConfigInput | Oauth2ProviderConfigInput | No | No interruption | Vendor-specific config block |
| Tags | List\<Tag\> | No | No interruption | |

### CredentialProviderVendor — Allowed Values (25)

```
GoogleOauth2    GithubOauth2    SlackOauth2      SalesforceOauth2
MicrosoftOauth2 LinkedinOauth2  AtlassianOauth2  CustomOauth2
CognitoOauth2   HubspotOauth2   ZendeskOauth2    DropboxOauth2
GitlabOauth2    BoxOauth2       AsanaOauth2      TrelloOauth2
JiraOauth2      ConfluenceOauth2 NotionOauth2    AdobeOauth2
ZoomOauth2      TwitterOauth2   InstagramOauth2  FacebookOauth2
SpotifyOauth2
```

### GetAtt

| Attribute | Description |
|-----------|-------------|
| CredentialProviderArn | ARN of the credential provider |
| CallbackUrl | OAuth2 redirect/callback URL (AgentCore-managed) |
| ClientSecretJsonKey | JSON key used to read the client secret from the managed secret |
| ClientSecretSource | MANAGED or EXTERNAL |
| CreatedTime | ISO-8601 creation timestamp |
| LastUpdatedTime | ISO-8601 last-update timestamp |

---

## Oauth2ProviderConfigInput — Sub-property Types

Exactly one of the following properties should be set, matching `CredentialProviderVendor`.

### CustomOauth2ProviderConfigInput

For `CredentialProviderVendor: CustomOauth2`. Requires an explicit `OauthDiscovery`.

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| OauthDiscovery | Oauth2Discovery | **Yes** | Discovery URL or inline metadata |
| ClientId | String | No | 1–256 chars |
| ClientSecret | String | No | 1–2048 chars; inline secret |
| ClientSecretConfig | SecretReference | No | Required when `ClientSecretSource: EXTERNAL` |
| ClientSecretSource | String | No | `MANAGED \| EXTERNAL` |
| ClientAuthenticationMethod | String | No | `CLIENT_SECRET_BASIC \| CLIENT_SECRET_POST \| AWS_IAM_ID_TOKEN_JWT` |
| OnBehalfOfTokenExchangeConfig | OnBehalfOfTokenExchangeConfig | No | RFC 8693/7523 token exchange |

### Oauth2Discovery

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| DiscoveryUrl | String | No | Pattern: `^.+/\.well-known/openid-configuration$` |
| AuthorizationServerMetadata | Oauth2AuthorizationServerMetadata | No | Inline server metadata |

### IncludedOauth2ProviderConfigInput

For any built-in vendor (e.g. GoogleOauth2, GithubOauth2, SlackOauth2, etc.) when you want to override endpoints.
Use when the vendor has a specific sub-config type (see GoogleOauth2ProviderConfigInput below) or default to `IncludedOauth2ProviderConfig`.

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| ClientId | String | **Yes** | 1–256 chars |
| ClientSecret | String | No | 1–2048 chars; inline secret |
| ClientSecretConfig | SecretReference | No | Required when `ClientSecretSource: EXTERNAL` |
| ClientSecretSource | String | No | `MANAGED \| EXTERNAL` |
| AuthorizationEndpoint | String | No | Override provider's authorization endpoint |
| TokenEndpoint | String | No | Override provider's token endpoint |
| Issuer | String | No | Override provider's issuer |

### GoogleOauth2ProviderConfigInput

Specific type for `CredentialProviderVendor: GoogleOauth2`.

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| ClientId | String | **Yes** | 1–256 chars |
| ClientSecret | String | No | 1–2048 chars; inline |
| ClientSecretConfig | SecretReference | No | Required when `ClientSecretSource: EXTERNAL` |
| ClientSecretSource | String | No | `MANAGED \| EXTERNAL` |

### MicrosoftOauth2ProviderConfigInput

Specific type for `CredentialProviderVendor: MicrosoftOauth2` (Microsoft Entra ID / Azure AD).

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| ClientId | String | **Yes** | 1–256 chars; Application (client) ID from Entra app registration |
| TenantId | String | No | 1–2048 chars; Entra Directory (tenant) ID; omit for multi-tenant apps |
| ClientSecret | String | No | 1–2048 chars; inline |
| ClientSecretConfig | SecretReference | No | Required when `ClientSecretSource: EXTERNAL` |
| ClientSecretSource | String | No | `MANAGED \| EXTERNAL` |

### CognitoOauth2 — use IncludedOauth2ProviderConfigInput

`CognitoOauth2` has no dedicated vendor config type. Use `IncludedOauth2ProviderConfig` and override
`AuthorizationEndpoint`, `TokenEndpoint`, and `Issuer` with the pool's hosted-UI URLs:

```
AuthorizationEndpoint: https://<domain>.auth.<region>.amazoncognito.com/oauth2/authorize
TokenEndpoint:         https://<domain>.auth.<region>.amazoncognito.com/oauth2/token
Issuer:                https://cognito-idp.<region>.amazonaws.com/<userPoolId>
```

### SecretReference (shared)

| Property | Type | Required | Notes |
|----------|------|----------|-------|
| JsonKey | String | Yes | 1–128 chars |
| SecretId | String | Yes | 1–2048 chars; ARN or name |

---

## Operator Semantics

### ApiKeySecretSource
- `MANAGED` — AgentCore creates and stores the secret; supply `ApiKey` with the raw value.
- `EXTERNAL` — you own the Secrets Manager secret; supply `ApiKeySecretConfig.SecretId` + `JsonKey`.

### ClientSecretSource (OAuth2)
- `MANAGED` — AgentCore creates and stores the client secret; supply `ClientSecret` inline.
- `EXTERNAL` — you own the Secrets Manager secret; supply `ClientSecretConfig.SecretId` + `JsonKey`.

### CallbackUrl (GetAtt)
AgentCore generates a redirect URI for the OAuth2 authorization code flow. Register this URL in your OAuth2 provider's allowed redirect URIs after stack creation.

---

## Minimal Example (all three resources)

```yaml
WorkloadIdentity:
  Type: AWS::BedrockAgentCore::WorkloadIdentity
  Properties:
    Name: my-agent

ApiKeyProvider:
  Type: AWS::BedrockAgentCore::ApiKeyCredentialProvider
  Properties:
    Name: my-api-key
    ApiKey: sk-xxxxxx
    ApiKeySecretSource: MANAGED

GoogleOAuthProvider:
  Type: AWS::BedrockAgentCore::OAuth2CredentialProvider
  Properties:
    Name: my-google-oauth
    CredentialProviderVendor: GoogleOauth2
    Oauth2ProviderConfigInput:
      GoogleOauth2ProviderConfig:
        ClientId: "123456.apps.googleusercontent.com"
        ClientSecret: "GOCSPX-xxxxxx"
        ClientSecretSource: MANAGED
```
