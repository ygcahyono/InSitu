"""
AI helper module for InSitu vocabulary app.
Handles Claude API calls for word explanations and examples.
"""

import os
import re
from anthropic import Anthropic
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Anthropic client
client = None


def get_client() -> Anthropic:
    """Get or create the Anthropic client."""
    global client
    if client is None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment variables")
        client = Anthropic(api_key=api_key)
    return client


SYSTEM_PROMPT = """You are a friendly English tutor helping a non-native English speaker living in London. 
Explain words clearly and give examples rooted in everyday London/UK life contexts 
(transport, work, weather, food, bureaucracy). Keep explanations concise but warm.

When explaining a word, always respond in this exact format:

DEFINITION:
[Your 1-2 sentence definition in plain English]

EXAMPLES:
1. [First example sentence using UK/London context]
2. [Second example sentence using UK/London context]
3. [Third example sentence using UK/London context]

SOURCE_CONTEXT:
[If you find the word in the provided source text, include the sentence where it appears. If not found, write "Not found in source text."]"""


def find_word_in_context(word: str, source_text: str) -> str | None:
    """
    Find a sentence containing the word in the source text.
    
    Returns the sentence if found, None otherwise.
    """
    if not source_text:
        return None
    
    # Split into sentences (simple approach)
    sentences = re.split(r'[.!?]+', source_text)
    
    word_lower = word.lower()
    for sentence in sentences:
        if word_lower in sentence.lower():
            cleaned = sentence.strip()
            if cleaned:
                return cleaned
    
    return None


def parse_response(response_text: str) -> dict:
    """Parse the structured response from Claude."""
    result = {
        "definition": "",
        "examples": [],
        "source_context": None
    }
    
    # Extract definition
    def_match = re.search(r'DEFINITION:\s*\n(.+?)(?=\n\nEXAMPLES:|$)', response_text, re.DOTALL)
    if def_match:
        result["definition"] = def_match.group(1).strip()
    
    # Extract examples
    examples_match = re.search(r'EXAMPLES:\s*\n(.+?)(?=\n\nSOURCE_CONTEXT:|$)', response_text, re.DOTALL)
    if examples_match:
        examples_text = examples_match.group(1)
        # Parse numbered examples
        examples = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', examples_text, re.DOTALL)
        result["examples"] = [ex.strip() for ex in examples if ex.strip()]
    
    # Extract source context
    source_match = re.search(r'SOURCE_CONTEXT:\s*\n(.+?)$', response_text, re.DOTALL)
    if source_match:
        source_text = source_match.group(1).strip()
        if source_text and "not found" not in source_text.lower():
            result["source_context"] = source_text
    
    return result


def get_word_explanation(word: str, source_text: str = "") -> tuple[bool, dict | str]:
    """
    Get an explanation for a word using Claude API.
    
    Args:
        word: The word to explain
        source_text: The original text where the word was found
        
    Returns:
        tuple: (success: bool, result: dict with definition/examples/source_context OR error message)
    """
    try:
        anthropic_client = get_client()
        
        # Find the word in context first
        found_context = find_word_in_context(word, source_text)
        
        user_message = f'Please explain the word "{word}".'
        if source_text:
            user_message += f'\n\nSource text where this word was found:\n"""\n{source_text}\n"""'
        
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        response_text = response.content[0].text
        parsed = parse_response(response_text)
        
        # Use our found context if Claude didn't find it
        if not parsed["source_context"] and found_context:
            parsed["source_context"] = found_context
        
        # Validate we got the essential parts
        if not parsed["definition"]:
            parsed["definition"] = response_text.split('\n')[0]  # Fallback
        
        if not parsed["examples"]:
            # Try to extract any sentences as examples
            sentences = [s.strip() for s in response_text.split('\n') if s.strip() and len(s) > 20]
            parsed["examples"] = sentences[:3]
        
        return True, parsed
        
    except ValueError as e:
        return False, str(e)
    except Exception as e:
        error_msg = str(e)
        if "api_key" in error_msg.lower() or "authentication" in error_msg.lower():
            return False, "Invalid API key. Please check your ANTHROPIC_API_KEY in the .env file."
        elif "rate" in error_msg.lower():
            return False, "Rate limit exceeded. Please wait a moment and try again."
        else:
            return False, f"Error calling Claude API: {error_msg}"


def refresh_examples(word: str, current_definition: str) -> tuple[bool, list | str]:
    """
    Generate new example sentences for a word.
    
    Args:
        word: The word to generate examples for
        current_definition: The existing definition to maintain consistency
        
    Returns:
        tuple: (success: bool, examples: list of strings OR error message)
    """
    try:
        anthropic_client = get_client()
        
        user_message = f"""The word is "{word}" and its definition is: {current_definition}

Please generate 3 NEW and DIFFERENT example sentences using this word in everyday UK/London contexts.
Format your response as:
1. [First example]
2. [Second example]
3. [Third example]

Make these examples different from typical textbook examples - use real London life situations like:
- Taking the Tube or bus
- Dealing with British weather
- Workplace scenarios
- Shopping at Tesco or local markets
- NHS appointments
- Council communications"""

        response = anthropic_client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system="You are a helpful English tutor specializing in UK/London contexts. Generate practical, relatable example sentences.",
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        response_text = response.content[0].text
        
        # Parse numbered examples
        examples = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|$)', response_text, re.DOTALL)
        examples = [ex.strip() for ex in examples if ex.strip()]
        
        if not examples:
            # Fallback: split by newlines
            examples = [line.strip() for line in response_text.split('\n') 
                       if line.strip() and len(line) > 20][:3]
        
        if examples:
            return True, examples
        else:
            return False, "Could not generate new examples. Please try again."
            
    except Exception as e:
        return False, f"Error refreshing examples: {str(e)}"


def check_api_key() -> tuple[bool, str]:
    """Check if the API key is configured and valid."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    
    if not api_key:
        return False, "API key not configured. Please add ANTHROPIC_API_KEY to your .env file."
    
    if api_key == "your_api_key_here":
        return False, "Please replace the placeholder API key in your .env file with your actual Anthropic API key."
    
    return True, "API key configured"
