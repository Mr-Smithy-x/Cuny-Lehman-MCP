import asyncio
import requests
import json
#from mcp.client.stdio import StdioClientConnection
from mcp import ClientSession, StdioServerParameters, stdio_client

MCP_TOOL_NAME = "fetch_cuny_information"
MCP_SERVER_CMD_FILE = ["fetch_cuny_information.py"]  # Path to your MCP server
LM_STUDIO_URL = "http://192.168.1.216:1234/v1/chat/completions"
MODEL_NAME = "qwen/qwen3.6-35b-a3b"  # e.g., "llama-3.2-3b-instruct"

async def call_mcp_tool(mcp_server_cmd=None, mcp_tool_name=None, mcp_tool_args={}):
    server_params = StdioServerParameters(
        command="python",
        args=mcp_server_cmd,
        env=None
    )
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Call your tool
            result = await session.call_tool(
                name=mcp_tool_name,
                arguments=mcp_tool_args,
                #arguments={"url": url, "wait_for_selector": "h1"}
            )
            return json.loads(result.content[0].text)

def send_to_lm_studio(html_content: str):
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"Here is rendered HTML:\n{html_content}\n\nSummarize the key points."}
    ]
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": 0.7
    }
    response = requests.post(LM_STUDIO_URL, json=payload)
    print(response.json())
    print(response.json()["choices"][0]["message"]["content"])

if __name__ == "__main__":
    import sys
    print("Current args:", sys.argv)
    url = sys.argv[1] if len(sys.argv) > 1 else "https://charltonsmith.nyc"
    html_result = asyncio.run(
        call_mcp_tool(
            mcp_server_cmd=MCP_SERVER_CMD_FILE,
            mcp_tool_name=MCP_TOOL_NAME,
            mcp_tool_args={}
        )
    )
    json_data = html_result.get("json", "Failed to fetch JSON")
    send_to_lm_studio(json_data)
