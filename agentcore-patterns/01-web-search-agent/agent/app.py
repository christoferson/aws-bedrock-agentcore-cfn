import os
import logging
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from strands import Agent
from strands.models import BedrockModel
from strands_tools import MCPClient
from mcp_proxy_for_aws import aws_iam_streamablehttp_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

GATEWAY_URL = os.environ["GATEWAY_URL"]
MODEL_ID = os.environ.get("MODEL_ID", "us.anthropic.claude-sonnet-4-6")

SYSTEM_PROMPT = (
    "You are a helpful research assistant with access to web search. "
    "Use the WebSearch tool to find up-to-date information when needed. "
    "Cite sources in your responses."
)

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload):
    prompt = payload.get("prompt")
    if not prompt:
        return {"error": "Missing 'prompt' in request payload.", "status": "error"}

    logger.info("Invoking agent with prompt: %s", prompt[:100])

    # MCPClient opened per invocation — Gateway handles session state
    mcp_client = MCPClient(lambda: aws_iam_streamablehttp_client(GATEWAY_URL))
    with mcp_client:
        agent = Agent(
            model=BedrockModel(model_id=MODEL_ID),
            system_prompt=SYSTEM_PROMPT,
            tools=mcp_client.list_tools_sync(),
        )
        result = agent(prompt)

    return {"response": str(result.message), "status": "success"}


if __name__ == "__main__":
    app.run()
