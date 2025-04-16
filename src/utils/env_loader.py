import os
from dotenv import load_dotenv
from pathlib import Path

def load_env_variables():
    """
    Load environment variables from .env file.
    
    Returns:
        dict: Dictionary containing environment variables
    """
    # Get the project root directory
    project_root = Path(__file__).parent.parent.parent
    
    # Load environment variables from .env file
    env_path = project_root / '.env'
    load_dotenv(dotenv_path=env_path)
    
    # Return a dictionary of environment variables
    return {
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        # Add other environment variables as needed
    }

def get_openai_api_key():
    """
    Get the OpenAI API key from environment variables.
    
    Returns:
        str: OpenAI API key
    """
    load_env_variables()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        raise ValueError("OpenAI API key not found. Please set OPENAI_API_KEY in .env file.")
    
    return api_key 