import json
from pathlib import Path
import os

GRAPH_DIR = Path(__file__).resolve().parent.parent / "graph"

def load_graph_data():
    """
    Load graph data from JSON files in the graph directory
    Returns a dictionary containing concepts, rules, examples, and their relationships
    """
    try:
        def load_file(filename):
            file_path = GRAPH_DIR / filename
            if not file_path.exists():
                raise FileNotFoundError(f"File not found: {filename}")
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                return data
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in {filename}: {str(e)}")

        # Ensure graph directory exists
        if not GRAPH_DIR.exists():
            raise FileNotFoundError(f"Graph directory not found at {GRAPH_DIR}")

        # Load all required files
        data = {
            "concepts": load_file("concepts.json"),
            "rules": load_file("rules.json"),
            "examples": load_file("examples.json"),
            "edges": load_file("edges.json")
        }

        # Validate data structure
        if not isinstance(data["concepts"], list):
            raise ValueError("concepts.json must contain a list of concepts")
        if not isinstance(data["rules"], list):
            raise ValueError("rules.json must contain a list of rules")
        if not isinstance(data["edges"], list):
            raise ValueError("edges.json must contain a list of edges")

        return data

    except Exception as e:
        error_msg = f"Error loading graph data: {str(e)}"
        print(error_msg)
        return {
            'error': error_msg,
            'concepts': [],  # Provide empty defaults
            'rules': [],
            'edges': [],
            'examples': []
        }