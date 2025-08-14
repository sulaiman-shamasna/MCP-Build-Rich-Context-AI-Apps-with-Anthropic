import arxiv
import json
import os
from typing import List
from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
import openai

load_dotenv()

PAPER_DIR = "papers"

# Initialize FastMCP server
mcp = FastMCP("research")

@mcp.tool()
def search_papers(topic: str, max_results: int = 5) -> List[str]:
    """
    Search for papers on arXiv based on a topic and store their information.
    
    Args:
        topic: The topic to search for
        max_results: Maximum number of results to retrieve (default: 5)
        
    Returns:
        List of paper IDs found in the search
    """
    
    # Use arxiv to find the papers 
    client = arxiv.Client()

    # Search for the most relevant articles matching the queried topic
    search = arxiv.Search(
        query = topic,
        max_results = max_results,
        sort_by = arxiv.SortCriterion.Relevance
    )

    papers = client.results(search)
    
    # Create directory for this topic
    path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
    os.makedirs(path, exist_ok=True)
    
    file_path = os.path.join(path, "papers_info.json")

    # Try to load existing papers info
    try:
        with open(file_path, "r") as json_file:
            papers_info = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        papers_info = {}

    # Process each paper and add to papers_info  
    paper_ids = []
    for paper in papers:
        paper_ids.append(paper.get_short_id())
        paper_info = {
            'title': paper.title,
            'authors': [author.name for author in paper.authors],
            'summary': paper.summary,
            'pdf_url': paper.pdf_url,
            'published': str(paper.published.date())
        }
        papers_info[paper.get_short_id()] = paper_info
    
    # Save updated papers_info to json file
    with open(file_path, "w") as json_file:
        json.dump(papers_info, json_file, indent=2)
    
    print(f"Results are saved in: {file_path}")
    
    return paper_ids

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
    """
 
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            file_path = os.path.join(item_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        if paper_id in papers_info:
                            return json.dumps(papers_info[paper_id], indent=2)
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    print(f"Error reading {file_path}: {str(e)}")
                    continue
    
    return f"There's no saved information related to paper {paper_id}."

@mcp.tool()
def list_topics() -> List[str]:
    """
    List all available research topics that have been searched.
    
    Returns:
        List of topic names
    """
    if not os.path.exists(PAPER_DIR):
        return []
        
    topics = []
    for item in os.listdir(PAPER_DIR):
        item_path = os.path.join(PAPER_DIR, item)
        if os.path.isdir(item_path):
            topics.append(item.replace("_", " "))
    
    return topics

@mcp.tool()
def get_paper_count(topic: str = None) -> dict:
    """
    Get the count of papers for a specific topic or all topics.
    
    Args:
        topic: The topic to count papers for (optional, if None counts all topics)
        
    Returns:
        Dictionary with topic names and paper counts
    """
    if not os.path.exists(PAPER_DIR):
        return {"error": "Papers directory does not exist"}
        
    counts = {}
    
    if topic:
        # Count papers for specific topic
        topic_dir = topic.lower().replace(" ", "_")
        topic_path = os.path.join(PAPER_DIR, topic_dir)
        
        if os.path.exists(topic_path):
            file_path = os.path.join(topic_path, "papers_info.json")
            if os.path.isfile(file_path):
                try:
                    with open(file_path, "r") as json_file:
                        papers_info = json.load(json_file)
                        counts[topic] = len(papers_info)
                except (FileNotFoundError, json.JSONDecodeError):
                    counts[topic] = 0
        else:
            counts[topic] = 0
    else:
        # Count papers for all topics
        for item in os.listdir(PAPER_DIR):
            item_path = os.path.join(PAPER_DIR, item)
            if os.path.isdir(item_path):
                file_path = os.path.join(item_path, "papers_info.json")
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "r") as json_file:
                            papers_info = json.load(json_file)
                            counts[item.replace("_", " ")] = len(papers_info)
                    except (FileNotFoundError, json.JSONDecodeError):
                        counts[item.replace("_", " ")] = 0
    
    return counts

@mcp.resource("papers://folders")
def get_available_folders() -> str:
    """
    List all available topic folders in the papers directory.
    
    This resource provides a simple list of all available topic folders.
    """
    folders = []
    
    # Get all topic directories
    if os.path.exists(PAPER_DIR):
        for topic_dir in os.listdir(PAPER_DIR):
            topic_path = os.path.join(PAPER_DIR, topic_dir)
            if os.path.isdir(topic_path):
                papers_file = os.path.join(topic_path, "papers_info.json")
                if os.path.exists(papers_file):
                    folders.append(topic_dir)
    
    # Create a simple markdown list
    content = "# Available Topics\n\n"
    if folders:
        for folder in folders:
            content += f"- {folder}\n"
        content += f"\nUse @{folder} to access papers in that topic.\n"
    else:
        content += "No topics found.\n"
    
    return content

@mcp.resource("papers://{topic}")
def get_topic_papers(topic: str) -> str:
    """
    Get detailed information about papers on a specific topic.
    
    Args:
        topic: The research topic to retrieve papers for
    """
    topic_dir = topic.lower().replace(" ", "_")
    papers_file = os.path.join(PAPER_DIR, topic_dir, "papers_info.json")
    
    if not os.path.exists(papers_file):
        return f"# No papers found for topic: {topic}\n\nTry searching for papers on this topic first."
    
    try:
        with open(papers_file, 'r') as f:
            papers_data = json.load(f)
        
        # Create markdown content with paper details
        content = f"# Papers on {topic.replace('_', ' ').title()}\n\n"
        content += f"Total papers: {len(papers_data)}\n\n"
        
        for paper_id, paper_info in papers_data.items():
            content += f"## {paper_info['title']}\n"
            content += f"- **Paper ID**: {paper_id}\n"
            content += f"- **Authors**: {', '.join(paper_info['authors'])}\n"
            content += f"- **Published**: {paper_info['published']}\n"
            content += f"- **PDF URL**: [{paper_info['pdf_url']}]({paper_info['pdf_url']})\n\n"
            content += f"### Summary\n{paper_info['summary'][:500]}...\n\n"
            content += "---\n\n"
        
        return content
    except json.JSONDecodeError:
        return f"# Error reading papers data for {topic}\n\nThe papers data file is corrupted."

@mcp.prompt()
def generate_search_prompt(topic: str, num_papers: int = 5) -> str:
    """Generate a prompt for Claude to find and discuss academic papers on a specific topic."""
    return f"""Search for {num_papers} academic papers about '{topic}' using the search_papers tool. 

            Follow these instructions:
            1. First, search for papers using search_papers(topic='{topic}', max_results={num_papers})
            2. For each paper found, extract and organize the following information:
            - Paper title
            - Authors
            - Publication date
            - Brief summary of the key findings
            - Main contributions or innovations
            - Methodologies used
            - Relevance to the topic '{topic}'

            3. Provide a comprehensive summary that includes:
            - Overview of the current state of research in '{topic}'
            - Common themes and trends across the papers
            - Key research gaps or areas for future investigation
            - Most impactful or influential papers in this area

            4. Organize your findings in a clear, structured format with headings and bullet points for easy readability.

            Please present both detailed information about each paper and a high-level synthesis of the research landscape in {topic}."""

def run_chatbot():
    """Run the chatbot interface"""
    print("Research Papers Chatbot with GPT Integration")
    print("="*50)
    
    # Initialize OpenAI client
    try:
        openai_client = openai.OpenAI()
        print("✅ OpenAI client initialized")
    except Exception as e:
        print(f"❌ Error initializing OpenAI client: {str(e)}")
        print("Make sure you have set OPENAI_API_KEY in your .env file")
        return
    
    # Define tools for OpenAI
    tools = [
        {
            "type": "function",
            "function": {
                "name": "search_papers",
                "description": "Search for papers on arXiv based on a topic and store their information.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic to search for"
                        },
                        "max_results": {
                            "type": "integer",
                            "description": "Maximum number of results to retrieve",
                            "default": 5
                        }
                    },
                    "required": ["topic"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "extract_info",
                "description": "Search for information about a specific paper across all topic directories.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "paper_id": {
                            "type": "string",
                            "description": "The ID of the paper to look for"
                        }
                    },
                    "required": ["paper_id"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "list_topics",
                "description": "List all available research topics that have been searched.",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_paper_count",
                "description": "Get the count of papers for a specific topic or all topics.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "topic": {
                            "type": "string",
                            "description": "The topic to count papers for (optional, if None counts all topics)"
                        }
                    }
                }
            }
        }
    ]
    
    def call_tool(tool_name: str, arguments: dict):
        """Call a tool function"""
        if tool_name == "search_papers":
            return search_papers(**arguments)
        elif tool_name == "extract_info":
            return extract_info(**arguments)
        elif tool_name == "list_topics":
            return list_topics()
        elif tool_name == "get_paper_count":
            topic = arguments.get("topic")
            return get_paper_count(topic) if topic else get_paper_count()
        else:
            return f"Unknown tool: {tool_name}"
    
    def chat_with_gpt(user_message: str):
        """Chat with GPT using the tools"""
        messages = [
            {
                "role": "system",
                "content": """You are a helpful research assistant that can search for and analyze research papers from arXiv. 
                You have access to tools that can:
                1. Search for papers on specific topics
                2. Extract detailed information about papers
                3. List available research topics
                4. Get paper counts by topic
                
                Use these tools to help users find and understand research papers. Be conversational and helpful.
                When you find papers, provide a summary of the key findings and suggest what might be interesting to explore further."""
            },
            {
                "role": "user",
                "content": user_message
            }
        ]
        
        try:
            # Get initial response from GPT
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=tools,
                max_tokens=1500
            )
            
            assistant_message = response.choices[0].message
            messages.append(assistant_message)
            
            # Handle tool calls if any
            while assistant_message.tool_calls:
                for tool_call in assistant_message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    print(f"Calling tool: {tool_name} with args: {tool_args}")
                    
                    # Call the tool function
                    tool_result = call_tool(tool_name, tool_args)
                    
                    # Add tool result to messages
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": str(tool_result)
                    })
                
                # Get next response from GPT
                response = openai_client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=messages,
                    tools=tools,
                    max_tokens=1500
                )
                
                assistant_message = response.choices[0].message
                messages.append(assistant_message)
            
            return assistant_message.content
            
        except Exception as e:
            return f"Sorry, I encountered an error: {str(e)}"
    
    print("\n" + "="*50)
    print("Chat with your research assistant! (Type 'quit' to exit)")
    print("Available commands:")
    print("- 'Search for papers about machine learning'")
    print("- 'What topics have been searched?'")
    print("- 'How many papers do we have?'")
    print("- 'Tell me about paper 1310.7911v2'")
    print("="*50)
    
    # Chat loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            
            if not user_input:
                continue
            
            print("\nAssistant: ", end="", flush=True)
            response = chat_with_gpt(user_input)
            print(response)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")

if __name__ == "__main__":
    # Check if user wants to run as server or chatbot
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--server":
        # Run as MCP server
        print("Starting MCP Server...")
        mcp.run(transport='stdio')
    else:
        # Run as chatbot (default)
        run_chatbot()