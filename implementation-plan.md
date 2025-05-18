# Implementation Plan for Court Ruling Draft Generator MVP

## Overview
Create a minimal viable product (MVP) that can generate the factual section ("Sachverhalt") of a court ruling based on court orders ("Verfügung") and potentially other case documents. The system will use input-output examples for few-shot learning.

## Components

### 1. Document Processing
- Create functions to read text documents from file system


### 2. Prompt Engineering
- Design a prompt template that includes:
  - Instructions for generating the factual section in formal German legal style
  - The input court order document
  - Additional case documents (if available)
  - Few-shot examples of input court orders and corresponding output factual sections
  - Explicit instructions to maintain the structure and style from examples

### 3. LLM Integration
- Implement connection to LLM API (Anthropic's Claude or OpenAI)
- Configure appropriate parameters (temperature, max tokens, etc.)
- Set up error handling for API calls

### 4. Output Processing
- Extract generated text from LLM response
- Format output for console display
- Implement file saving functionality to save to markdown files


## Implementation Steps

## Required Information for Coding Agent
- API Key access method (environment variable)
- LLM model specification (Claude or GPT model name)
- Input/output file naming conventions
- Expected format of generated output
- Error handling requirements

## Preferred Technologies
- Python 3.11
- Pydantic
- OpenAI assistant api
- Typer for CLI (later)

## Testing Strategy (later)
1. Test with a single court order document
2. Test with multiple additional documents
3. Test with different numbers of examples
4. Validate output formatting meets legal document standards