import os
import uuid
import json
import asyncio
from datetime import datetime
from flask import Flask, request, jsonify, session
from flask_cors import CORS
from dotenv import load_dotenv
from ollama import Client, ChatResponse
from mcp import ClientSession
from mcp.client.sse import sse_client

load_dotenv()

app = Flask(__name__)
CORS(app, origins=["*"], supports_credentials=True)
app.secret_key = 'supersecretkey'

# =====================================================
# Local storage
DATA_FILE = os.path.join("data", "chat.json")
os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)


def load_data():
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def console(message):
    time = datetime.now().strftime('%d/%m/%Y %H:%M:%S')
    print(f"{time} [LOG]: {message}")


@app.before_request
def get_or_create_user():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())


# =====================================================
# Ollama + MCP Configuration

OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://ollama:11434/")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
MCP_SSE_URL = os.getenv("MCP_SSE_URL", "http://backend-server:5005/sse")

ollama_client = Client(host=OLLAMA_BASE)

# =====================================================
# Async tool discovery and execution

async def fetch_mcp_tools():
    """Fetch tool metadata dynamically from MCP server."""
    console("Fetching MCP tools asynchronously...")
    async with sse_client(MCP_SSE_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as mcp_session:
            await mcp_session.initialize()
            tools_result = await mcp_session.list_tools()
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema,
                    },
                }
                for tool in tools_result.tools
            ]
            console(f"Discovered {len(tools)} tools.")
            return tools


async def call_mcp_tool(tool_name, arguments):
    """Call a tool on the MCP server asynchronously."""
    console(f"Calling MCP tool: {tool_name} with {arguments}")
    async with sse_client(MCP_SSE_URL) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as mcp_session:
            await mcp_session.initialize()
            result = await mcp_session.call_tool(tool_name, arguments)
            if result and result.content:
                combined_output = "".join(
                    c.text if hasattr(c, "text") else str(c)
                    for c in result.content
                )
                return combined_output
            return ""


# =====================================================
# Session management

def start_new_session(user_id):
    data = load_data()
    session_id = str(uuid.uuid4())
    data.setdefault(user_id, {})[session_id] = {
        "messages": [],
        "created_at": datetime.now().isoformat(),
    }
    save_data(data)
    return session_id


def add_message(user_id, session_id, message):
    data = load_data()
    if user_id in data and session_id in data[user_id]:
        data[user_id][session_id]["messages"].append(message)
        save_data(data)


def get_messages(user_id, session_id):
    data = load_data()
    return data.get(user_id, {}).get(session_id, {}).get("messages")


# =====================================================
# LLM Chat + Tool Execution

def chat_with_llm(user_id, session_id):
    msgs = get_messages(user_id, session_id) or []
    messages_payload = [{"role": m["role"], "content": m["content"]} for m in msgs]

    # Inject default system message
    if not any(m["role"] == "system" for m in messages_payload):
        messages_payload.insert(
            0,
            {
                "role": "system",
                "content": "You are a DevOps assistant helping with errors and development. DO NOT reply in json format, reply in human readable text.",
            },
        )

    # Dynamically get available tools
    tools_metadata = asyncio.run(fetch_mcp_tools())

    console(f"Calling Ollama model {OLLAMA_MODEL} with {len(tools_metadata)} tools...")
    response: ChatResponse = ollama_client.chat(
        model=OLLAMA_MODEL,
        messages=messages_payload,
        tools=tools_metadata,
        stream=False,
    )

    tool_calls = getattr(response.message, "tool_calls", None)
    if tool_calls:
        for tool_call in tool_calls:
            fn_name = tool_call.function.name
            args = tool_call.function.arguments
            console(f"MODEL requested tool {fn_name} with args {args}")

            # Run the tool dynamically (no hardcoding)
            tool_result = asyncio.run(call_mcp_tool(fn_name, args))

            add_message(user_id, session_id, {
                "role": "tool",
                "tool_call": fn_name,
                "content": tool_result
            })

            messages_payload.append({"role": "tool", "content": str(tool_result)})

        # Final response after tool usage
        response2: ChatResponse = ollama_client.chat(
            model=OLLAMA_MODEL,
            messages=messages_payload,
            tools=tools_metadata,
            stream=False,
        )
        assistant_content = response2.message.content
    else:
        assistant_content = response.message.content

    add_message(user_id, session_id, {"role": "assistant", "content": assistant_content})
    return assistant_content


# =====================================================
# API Routes

@app.route('/api/start_session', methods=['POST'])
def api_start_session():
    console("API START SESSION")
    user_id = session['user_id']
    session_id = start_new_session(user_id)
    return jsonify({"session_id": session_id})


@app.route('/api/chat', methods=['POST'])
def api_chat():
    console("API CHAT")
    data = request.get_json()
    user_id = session['user_id']
    session_id = data.get("session_id")
    message = data.get("message")

    if not session_id or message is None:
        return jsonify({"error": "Missing session_id or message"}), 400

    messages = get_messages(user_id, session_id)
    if messages is None:
        return jsonify({"error": "Invalid session"}), 400

    add_message(user_id, session_id, {"role": "user", "content": message})
    response = chat_with_llm(user_id, session_id)

    return jsonify({"response": response})


@app.route('/api/history', methods=['POST'])
def api_history():
    console("API HISTORY")
    data = request.get_json()
    user_id = session['user_id']
    session_id = data.get("session_id")

    if not session_id:
        return jsonify({"error": "Missing session_id"}), 400

    messages = get_messages(user_id, session_id)
    if messages is None:
        return jsonify({"error": "Invalid session"}), 400

    return jsonify({"history": messages})


# =====================================================
# Main entry point

if __name__ == '__main__':
    console("Flask API starting on port 5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
