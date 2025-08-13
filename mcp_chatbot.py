from dotenv import load_dotenv
import openai
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
from typing import List, Dict, TypedDict
from contextlib import AsyncExitStack
import json
import asyncio

load_dotenv()

class ToolDefinition(TypedDict):
    name: str
    description: str
    input_schema: dict

class MCP_ChatBot:

    def __init__(self):
        # Initialize session and client objects
        self.sessions: List[ClientSession] = [] # new
        self.exit_stack = AsyncExitStack() # new
        self.openai_client = openai.OpenAI()
        self.available_tools: List[ToolDefinition] = [] # new
        self.tool_to_session: Dict[str, ClientSession] = {} # new


    async def connect_to_server(self, server_name: str, server_config: dict) -> None:
        """Connect to a single MCP server."""
        try:
            server_params = StdioServerParameters(**server_config)
            stdio_transport = await self.exit_stack.enter_async_context(
                stdio_client(server_params)
            ) # new
            read, write = stdio_transport
            session = await self.exit_stack.enter_async_context(
                ClientSession(read, write)
            ) # new
            await session.initialize()
            self.sessions.append(session)
            
            # List available tools for this session
            response = await session.list_tools()
            tools = response.tools
            print(f"\nConnected to {server_name} with tools:", [t.name for t in tools])
            
            for tool in tools: # new
                self.tool_to_session[tool.name] = session
                self.available_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.inputSchema
                    }
                })
        except Exception as e:
            print(f"Failed to connect to {server_name}: {e}")

    async def connect_to_servers(self): # new
        """Connect to all configured MCP servers."""
        try:
            with open("server_config.json", "r") as file:
                data = json.load(file)
            
            servers = data.get("mcpServers", {})
            
            for server_name, server_config in servers.items():
                await self.connect_to_server(server_name, server_config)
        except Exception as e:
            print(f"Error loading server configuration: {e}")
            raise

    def _format_tool_content(self, result) -> str:
        """Convert MCP tool result content to a plain string for OpenAI tool messages."""
        try:
            content = getattr(result, "content", result)
            if isinstance(content, list):
                parts = []
                for item in content:
                    if isinstance(item, dict):
                        if item.get("type") == "text" and "text" in item:
                            parts.append(item["text"])
                        else:
                            parts.append(json.dumps(item))
                    else:
                        parts.append(str(item))
                return "\n".join(parts)
            if isinstance(content, (dict, list)):
                return json.dumps(content)
            return str(content)
        except Exception:
            return str(result)
    
    async def process_query(self, query):
        system_instruction = (
            "You are a helpful assistant with access to multiple MCP servers and their tools. "
            "Follow these rules: "
            "1) Use the 'fetch' tool for HTTP/HTTPS URLs. "
            "2) When the user asks to save or write content, ALWAYS use the filesystem 'write_file' tool. "
            "   - Prefer writing to './<filename>' in the current working directory if allowed. "
            "   - If paths are restricted, first call 'list_allowed_directories' and choose an allowed directory. "
            "3) After fetching content from the web, summarize or transform as requested, then persist the result using 'write_file'. "
            "4) For diagrams, produce an ASCII/textual diagram and save it to a .txt or .md file using 'write_file'. "
            "5) Confirm the exact file path after saving. "
        )
        messages = [
            {'role': 'system', 'content': system_instruction},
            {'role': 'user', 'content': query}
        ]
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=self.available_tools,
            max_tokens=2024
        )
        process_query = True
        while process_query:
            assistant_message = response.choices[0].message
            assistant_content = assistant_message.content
            
            if assistant_content:
                print(assistant_content)
                messages.append({'role': 'assistant', 'content': assistant_content})
                
                if not assistant_message.tool_calls:
                    process_query = False
                    continue
            
            if assistant_message.tool_calls:
                messages.append({'role': 'assistant', 'content': assistant_content, 'tool_calls': assistant_message.tool_calls})
                
                for tool_call in assistant_message.tool_calls:
                    tool_id = tool_call.id
                    tool_args = tool_call.function.arguments
                    tool_name = tool_call.function.name
                    
                    print(f"Calling tool {tool_name} with args {tool_args}")
                    
                    # Parse tool_args from JSON string to dictionary
                    try:
                        tool_args_dict = json.loads(tool_args)
                    except json.JSONDecodeError as e:
                        print(f"Error parsing tool arguments: {e}")
                        tool_args_dict = {}
                    
                    # Call a tool
                    session = self.tool_to_session[tool_name] # new
                    result = await session.call_tool(tool_name, arguments=tool_args_dict)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_id,
                        "content": self._format_tool_content(result)
                    })
                
                response = self.openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=self.available_tools,
                    max_tokens=2024
                )
                
                if not response.choices[0].message.tool_calls:
                    print(response.choices[0].message.content)
                    process_query = False

    
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Chatbot Started!")
        print("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
        
                if query.lower() == 'quit':
                    break
                    
                await self.process_query(query)
                print("\n")
                    
            except Exception as e:
                print(f"\nError: {str(e)}")
    
    async def cleanup(self): # new
        """Cleanly close all resources using AsyncExitStack."""
        await self.exit_stack.aclose()


async def main():
    chatbot = MCP_ChatBot()
    try:
        # the mcp clients and sessions are not initialized using "with"
        # like in the previous lesson
        # so the cleanup should be manually handled
        await chatbot.connect_to_servers() # new! 
        await chatbot.chat_loop()
    finally:
        await chatbot.cleanup() #new! 


if __name__ == "__main__":
    asyncio.run(main())