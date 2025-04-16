from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, List
import json
import time
from openai import OpenAI
from src.utils.env_loader import get_openai_api_key

class BaseGenerator(ABC):
    """Base class for all data generators."""
    
    def __init__(self, output_dir: str = "data/generated"):
        """Initialize the generator with output directory."""
        self.output_dir = Path(__file__).parent.parent.parent.parent / output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.client = OpenAI(api_key=get_openai_api_key())
    
    @abstractmethod
    def generate_single(self, index: int) -> Dict[str, Any]:
        """Generate a single item. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def create_default(self, index: int) -> Dict[str, Any]:
        """Create a default item if generation fails. Must be implemented by subclasses."""
        pass
    
    def generate(self, num_items: int) -> None:
        """Generate multiple items and save them to files."""
        for i in range(1, num_items + 1):
            print(f"Generating {self.__class__.__name__} #{i}...")
            
            try:
                item = self.generate_single(i)
                self._save_item(item, i)
            except Exception as e:
                print(f"Error generating item #{i}: {str(e)}")
                item = self.create_default(i)
                self._save_item(item, i)
            
            # Add a small delay to avoid rate limiting
            time.sleep(1)
        
        print(f"Generated {num_items} items in {self.output_dir}")
    
    def _save_item(self, item: Dict[str, Any], index: int) -> None:
        """Save a single item to a file."""
        item_type = self.__class__.__name__.lower().replace('generator', '')
        with open(self.output_dir / f"{item_type}_{index}.json", "w") as f:
            json.dump(item, f, indent=2)
    
    def create_combined_dataset(self, output_file: str) -> None:
        """Combine all generated items into a single dataset file."""
        output_path = Path(__file__).parent.parent.parent.parent / output_file
        item_type = self.__class__.__name__.lower().replace('generator', '')
        
        # Get all JSON files for this type
        json_files = list(self.output_dir.glob(f"{item_type}_*.json"))
        
        # Load all items
        items = []
        for file in json_files:
            with open(file, "r") as f:
                items.append(json.load(f))
        
        # Save the combined dataset
        with open(output_path, "w") as f:
            json.dump({f"{item_type}s": items}, f, indent=2)
        
        print(f"Created combined dataset with {len(items)} {item_type}s at {output_path}")
    
    def _call_openai_api(self, prompt: str, system_message: str = None) -> Dict[str, Any]:
        """Make a call to the OpenAI API with error handling."""
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat.completions.create(
                model="gpt-4o-2024-08-06",
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            generated_text = response.choices[0].message.content
            
            # Try to extract JSON from the response
            json_start = generated_text.find('{')
            json_end = generated_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = generated_text[json_start:json_end]
                return json.loads(json_str)
            else:
                raise ValueError("Could not find JSON in response")
                
        except Exception as e:
            print(f"OpenAI API error: {str(e)}")
            raise 