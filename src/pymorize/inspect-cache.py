import os
import json
from pathlib import Path
import pickle

def inspect_cache(cache_dir='~/.prefect/storage'):
    cache_path = Path(cache_dir).expanduser()
    
    for file in cache_path.glob('*'):
        print(f"File: {file.name}")
        try:
            with open(file, 'rb') as f:
                # First, try to load as JSON
                try:
                    data = json.load(f)
                    print("  Content type: JSON")
                    print(f"  Content: {json.dumps(data, indent=2)}")
                except json.JSONDecodeError:
                    # If not JSON, try to load as pickle
                    f.seek(0)
                    try:
                        data = pickle.load(f)
                        print("  Content type: Pickle")
                        print(f"  Content: {data}")
                    except pickle.UnpicklingError:
                        print("  Unable to decode file content")
        except Exception as e:
            print(f"  Error reading file: {str(e)}")
        print("\n")

if __name__ == "__main__":
    inspect_cache()
