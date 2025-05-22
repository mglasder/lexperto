#!/usr/bin/env python
"""
LexPerto - Simple Court Ruling Draft Generator
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables
load_dotenv()

# Get API key from environment
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    print("Error: OPENAI_API_KEY not found in environment variables")
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=api_key)

# Ensure output directory exists
output_dir = Path("data/output")
output_dir.mkdir(parents=True, exist_ok=True)

def read_file(file_path):
    """Read content from a file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

def generate_ruling(court_order_content, case_document_content=None, example_order=None, example_ruling=None):
    """Generate a court ruling draft using OpenAI."""
    # Basic prompt with instructions
    prompt = """Du bist ein erfahrener Richter am deutschen Amtsgericht. Formuliere den Sachverhalt für ein Urteil basierend auf der gegebenen Verfügung. 
Verwende einen sachlichen, neutralen Stil ohne Wertungen oder Beurteilungen."""
    
    # Add example if available
    if example_order and example_ruling:
        prompt += f"\n\nBEISPIEL VERFÜGUNG:\n{example_order}\n\nBEISPIEL SACHVERHALT:\n{example_ruling}\n\n---\n\n"
    
    # Add current case
    prompt += f"\nAKTUELLE VERFÜGUNG:\n{court_order_content}\n\n"
    
    if case_document_content:
        prompt += f"DOKUMENT:\n{case_document_content}\n\n"
    
    prompt += "Verfasse nun einen Sachverhalt für diese Verfügung. Beginne mit \"SACHVERHALT\" und beschränke dich auf die relevanten Fakten."
    
    # Call the API
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Du bist ein erfahrener Richter, der Sachverhalte für Gerichtsurteile verfasst."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

def save_output(output_text, input_filename):
    """Save generated text to output file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"sachverhalt_{Path(input_filename).stem}_{timestamp}.txt"
    output_path = output_dir / output_filename
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(output_text)
    
    return output_path

def main():
    """Main function to process court orders and generate rulings."""
    if len(sys.argv) < 2:
        print("Usage: python lexperto.py <court_order_file> [case_document_file]")
        sys.exit(1)
    
    # Get input files
    court_order_file = sys.argv[1]
    case_document_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Check for example files in templates directory
    templates_dir = Path("data/templates")
    example_order_file = templates_dir / "court_order_sample.txt"
    example_ruling_file = templates_dir / "factual_section_example.txt"
    
    # Read input content
    try:
        court_order_content = read_file(court_order_file)
        case_document_content = read_file(case_document_file) if case_document_file else None
        
        # Read examples if available
        example_order = read_file(example_order_file) if example_order_file.exists() else None
        example_ruling = read_file(example_ruling_file) if example_ruling_file.exists() else None
        
        # Generate ruling
        output_text = generate_ruling(
            court_order_content, 
            case_document_content, 
            example_order, 
            example_ruling
        )
        
        if output_text:
            # Save and display output
            output_path = save_output(output_text, court_order_file)
            print(f"Successfully generated factual section: {output_path}")
            
            print("\n" + "="*50)
            print(output_text)
            print("="*50)
        
    except FileNotFoundError as e:
        print(f"File not found: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
