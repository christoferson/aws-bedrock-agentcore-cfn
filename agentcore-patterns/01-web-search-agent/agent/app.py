import os
import logging
from datetime import date

from bedrock_agentcore import BedrockAgentCoreApp
from strands import Agent
from strands.models.bedrock import BedrockModel
from strands.tools.mcp import MCPClient
from mcp_proxy_for_aws.client import aws_iam_streamablehttp_client

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = BedrockAgentCoreApp()

GATEWAY_URL = os.environ["GATEWAY_URL"]
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AWS_SERVICE = os.environ.get("AWS_SERVICE", "bedrock-agentcore")

MODEL_ID = os.environ.get(
    "MODEL_ID",
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
)

SYSTEM_PROMPT = (
    f"You are a helpful research assistant. Today's date is {date.today().isoformat()}. "
    "Use the available web search tool when you need current information. "
    "Cite sources in your responses."
)


def extract_agent_result(result) -> str:
    if result is None:
        return ""

    if isinstance(result, str):
        return result

    # Strands AgentResult often renders well with str(result),
    # but try common fields first.
    for attr in ["message", "text", "content"]:
        value = getattr(result, attr, None)
        if value:
            return str(value)

    return str(result)


def create_mcp_client():
    return MCPClient(
        lambda: aws_iam_streamablehttp_client(
            endpoint=GATEWAY_URL,
            aws_region=AWS_REGION,
            aws_service=AWS_SERVICE,
        )
    )


@app.entrypoint
async def handler(request):
    prompt = request.get("prompt")
    if not prompt:
        return {
            "status": "error",
            "error": "Missing 'prompt' in request payload.",
        }

    logger.info("Gateway URL: %s", GATEWAY_URL)
    logger.info("Prompt: %s", prompt[:200])

    try:
        mcp_client = create_mcp_client()

        with mcp_client:
            tools = mcp_client.list_tools_sync()
            logger.info("Discovered MCP tools: %s", tools)

            agent = Agent(
                model=BedrockModel(
                    model_id=MODEL_ID,
                    region_name=AWS_REGION,
                    streaming=False,
                ),
                tools=tools,
                system_prompt=SYSTEM_PROMPT,
                callback_handler=None,
            )

            result = agent(prompt)
            response_text = extract_agent_result(result).strip()

            return {
                "status": "success" if response_text else "empty_response",
                "response": response_text,
            }

    except Exception as e:
        logger.exception("Agent invocation failed")
        return {
            "status": "error",
            "error": str(e),
        }


if __name__ == "__main__":
    app.run()