# %%writefile mcp_project/research_server.py

import arxiv
import json
import os
import logging
from typing import List, Dict, Any
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PAPER_DIR = "papers"

mcp = FastMCP("research-papers")

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
    try:
        logger.info(f"Searching for papers on topic: {topic}")
        
         
        client = arxiv.Client()     # Use arxiv to find the papers

        # Search for the most relevant articles matching the queried topic
        search = arxiv.Search(
            query = topic,
            max_results = max_results,
            sort_by = arxiv.SortCriterion.Relevance
        )

        papers = list(client.results(search))
        
        if not papers:
            logger.warning(f"No papers found for topic: {topic}")
            return []
        
        path = os.path.join(PAPER_DIR, topic.lower().replace(" ", "_"))
        os.makedirs(path, exist_ok=True)
        
        file_path = os.path.join(path, "papers_info.json")

        try:
            with open(file_path, "r") as json_file:
                papers_info = json.load(json_file)
        except (FileNotFoundError, json.JSONDecodeError):
            papers_info = {}

        # Process each paper and add to papers_info  
        paper_ids = []
        for paper in papers:
            paper_id = paper.get_short_id()
            paper_ids.append(paper_id)
            paper_info = {
                'title': paper.title,
                'authors': [author.name for author in paper.authors],
                'summary': paper.summary,
                'pdf_url': paper.pdf_url,
                'published': str(paper.published.date())
            }
            papers_info[paper_id] = paper_info
        
        # Save updated papers_info to json file
        with open(file_path, "w") as json_file:
            json.dump(papers_info, json_file, indent=2)
        
        logger.info(f"Found {len(paper_ids)} papers for topic '{topic}'. Results saved in: {file_path}")
        return paper_ids
        
    except Exception as e:
        logger.error(f"Error searching papers for topic '{topic}': {str(e)}")
        raise

@mcp.tool()
def extract_info(paper_id: str) -> str:
    """
    Search for information about a specific paper across all topic directories.
    
    Args:
        paper_id: The ID of the paper to look for
        
    Returns:
        JSON string with paper information if found, error message if not found
    """
    try:
        logger.info(f"Extracting info for paper ID: {paper_id}")
        
        if not os.path.exists(PAPER_DIR):
            return f"Papers directory '{PAPER_DIR}' does not exist."
 
        for item in os.listdir(PAPER_DIR):
            item_path = os.path.join(PAPER_DIR, item)
            if os.path.isdir(item_path):
                file_path = os.path.join(item_path, "papers_info.json")
                if os.path.isfile(file_path):
                    try:
                        with open(file_path, "r") as json_file:
                            papers_info = json.load(json_file)
                            if paper_id in papers_info:
                                logger.info(f"Found paper {paper_id} in topic directory: {item}")
                                return json.dumps(papers_info[paper_id], indent=2)
                    except (FileNotFoundError, json.JSONDecodeError) as e:
                        logger.warning(f"Error reading {file_path}: {str(e)}")
                        continue
        
        logger.warning(f"Paper {paper_id} not found in any topic directory")
        return f"There's no saved information related to paper {paper_id}."
        
    except Exception as e:
        logger.error(f"Error extracting info for paper {paper_id}: {str(e)}")
        raise

@mcp.tool()
def list_topics() -> List[str]:
    """
    List all available research topics that have been searched.
    
    Returns:
        List of topic names
    """
    try:
        if not os.path.exists(PAPER_DIR):
            return []
            
        topics = []
        for item in os.listdir(PAPER_DIR):
            item_path = os.path.join(PAPER_DIR, item)
            if os.path.isdir(item_path):
                topics.append(item.replace("_", " "))
        
        logger.info(f"Found {len(topics)} topics: {topics}")
        return topics
        
    except Exception as e:
        logger.error(f"Error listing topics: {str(e)}")
        raise

@mcp.tool()
def get_paper_count(topic: str = None) -> Dict[str, Any]:
    """
    Get the count of papers for a specific topic or all topics.
    
    Args:
        topic: The topic to count papers for (optional, if None counts all topics)
        
    Returns:
        Dictionary with topic names and paper counts
    """
    try:
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
        
        logger.info(f"Paper counts: {counts}")
        return counts
        
    except Exception as e:
        logger.error(f"Error getting paper count: {str(e)}")
        raise

if __name__ == "__main__":
    logger.info("Starting Research Papers MCP Server...")
    # Initialize and run the server
    mcp.run(transport='stdio')