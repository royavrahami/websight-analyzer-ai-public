"""
Advanced analysis functions with Claude (Anthropic) - Full integration

Requirements:
- pip install anthropic
- Environment variable ANTHROPIC_API_KEY or .env file

Basic usage:
from advanced_analysis import analyze_with_claude
result = analyze_with_claude("טקסט לבדיקה", task="summarize")
print(result)
"""
# ... existing code ...
import os
import anthropic
from dotenv import load_dotenv
import json
import logging
from urllib.parse import urlparse
from pathlib import Path
from typing import Dict, Any, Optional

# Load environment variables from .env file if exists
load_dotenv()

def analyze_with_claude(text: str, task: str = "summarize", model: str = "claude-sonnet-4-20250514", max_tokens: int = 1024, system_prompt: str = None) -> str:
    """
    Run Claude (Anthropic) API on the given text with the specified task.
    :param text: Text to analyze
    :param task: Task for Claude (summarize, explain, review, etc)
    :param model: Claude model name
    :param max_tokens: Max tokens for response
    :param system_prompt: Optional system prompt
    :return: Claude's response as string
    """
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Claude API key not found in environment variable ANTHROPIC_API_KEY")
    client = anthropic.Anthropic(api_key=api_key)
    prompt = f"בצע {task} על הטקסט הבא:\n{text}"
    messages = [{"role": "user", "content": prompt}]
    if system_prompt:
        messages.insert(0, {"role": "system", "content": system_prompt})
    try:
        message = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            messages=messages
        )
        # Claude 3 returns content which is a list of blocks, need to join them
        if hasattr(message, 'content') and isinstance(message.content, list):
            return ''.join([block.text for block in message.content if hasattr(block, 'text')])
        return message.content
    except anthropic.RateLimitError:
        raise RuntimeError("Claude API rate limit reached. Please wait and try again.")
    except anthropic.APIError as e:
        raise RuntimeError(f"Claude API error: {e}")
    except Exception as e:
        raise RuntimeError(f"Unknown Claude integration error: {e}")

def extract_unique_indicators(analysis_dir: str, domain: str = None, analysis_filename: str = None) -> Optional[Dict[str, Any]]:
    """
    Extract unique indicators from an analysis JSON file in the given directory.
    Returns a dictionary with the unique indicators and metadata, or None if failed.
    """
    if analysis_filename:
        filename = analysis_filename
    elif domain:
        filename = f"metadata__{domain}.json"
    else:
        filename = "metadata.json"
    analysis_path = Path(analysis_dir) / filename
    if not analysis_path.exists():
        logging.error(f"Analysis file not found: {analysis_path}")
        return None
    try:
        with open(analysis_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # Extract relevant fields
        unique_indicators = {
            "element_ids": data.get("element_ids", []),
            "element_names": data.get("element_names", []),
            "unique_selectors": data.get("unique_selectors", []),
            "unique_texts": data.get("unique_texts", []),
            "unique_scripts": data.get("unique_scripts", []),
            "meta_tags": data.get("meta_tags", []),
            "structure_signature": data.get("structure_signature", ""),
            "page_url": data.get("page_url", ""),
            "page_title": data.get("page_title", "")
        }
        return unique_indicators
    except Exception as e:
        logging.error(f"Failed to extract unique indicators: {e}")
        return None

def save_unique_indicators_to_file(analysis_dir: str, domain: str = None, analysis_filename: str = None) -> Optional[str]:
    """
    Extract unique indicators and save them to a JSON file with the site address in the filename.
    Returns the output file path if successful, else None.
    """
    indicators = extract_unique_indicators(analysis_dir, domain=domain, analysis_filename=analysis_filename)
    if not indicators:
        return None
    # Determine site/domain for filename
    page_url = indicators.get("page_url", "")
    page_title = indicators.get("page_title", "site")
    domain_for_file = domain or "site"
    if page_url and not domain:
        try:
            parsed = urlparse(page_url)
            domain_for_file = parsed.netloc.replace('.', '_')
            if not domain_for_file:
                domain_for_file = page_title.replace(' ', '_')
        except Exception:
            domain_for_file = page_title.replace(' ', '_')
    else:
        domain_for_file = domain_for_file.replace(' ', '_')
    output_filename = f"unique_indicators_{domain_for_file}.json"
    output_path = Path(analysis_dir) / output_filename
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(indicators, f, ensure_ascii=False, indent=2)
        logging.info(f"Unique indicators saved to: {output_path}")
        return str(output_path)
    except Exception as e:
        logging.error(f"Failed to save unique indicators: {e}")
        return None

# Example usage:
if __name__ == "__main__":
    print("== Testing Claude integration ==")
    try:
        result = analyze_with_claude("שלום עולם! זהו טקסט לבדיקה.", task="summarize")
        print("Claude's response:", result)
    except Exception as e:
        print("Error:", e) 