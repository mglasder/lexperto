import os
import re
from pathlib import Path

def update_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Update imports
    replacements = [
        (r'from models\.', 'from src.models.'),
        (r'from helpers import', 'from src.utils.helpers import'),
        (r'from search import', 'from src.core.search import'),
        (r'from store import', 'from src.core.store import'),
        (r'from extraction import', 'from src.core.extraction import'),
        (r'from preprocessing import', 'from src.core.preprocessing import'),
    ]
    
    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)
    
    # Update file paths
    path_replacements = [
        ('prompts-test/', 'prompts/test/'),
        ('prompts/', 'prompts/production/'),
        ('models/', 'src/models/'),
    ]
    
    for old_path, new_path in path_replacements:
        content = content.replace(old_path, new_path)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

def process_directory(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                print(f"Updating imports in {file_path}")
                update_imports(file_path)

if __name__ == "__main__":
    # Process both src and experiments directories
    process_directory('src')
    process_directory('experiments')
    process_directory('tests') 