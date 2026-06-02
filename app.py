"""Strands agent hosted on Amazon Bedrock AgentCore Runtime.

The bedrock-agentcore SDK (BedrockAgentCoreApp) implements the AgentCore HTTP
service contract for us: it serves POST /invocations and GET /ping on
0.0.0.0:8080. We only supply the agent logic in the @app.entrypoint handler.

See aws-documentation/runtime-service-contract.md for the contract details.
"""

import os

from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel

app = BedrockAgentCoreApp()

# Model id is supplied via the Runtime EnvironmentVariables (set in the
# CloudFormation Layer 4 template) so the image stays environment-agnostic.
MODEL_ID = os.environ.get(
    "BEDROCK_MODEL_ID", "global.anthropic.claude-sonnet-4-5-20250929-v1:0", 
    #"us.anthropic.claude-sonnet-4-5-20250929-v1:0"
)
SYSTEM_PROMPT = os.environ.get(
    "AGENT_SYSTEM_PROMPT",
    "You are a helpful, concise production assistant.",
)

agent = Agent(
    model=BedrockModel(model_id=MODEL_ID),
    system_prompt=SYSTEM_PROMPT,
)


@app.entrypoint
def invoke(payload):
    """Handle a single /invocations request.

    payload is the parsed JSON body, e.g. {"prompt": "..."}. Returning a dict
    yields a JSON response; yielding chunks would stream as SSE.
    """
    prompt = payload.get("prompt")
    if not prompt:
        return {"error": "Missing 'prompt' in request payload."}

    result = agent(prompt)
    return {"response": result.message, "status": "success"}


if __name__ == "__main__":
    # Starts the AgentCore-compatible server on 0.0.0.0:8080.
    app.run()
