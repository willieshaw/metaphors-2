"""
Utility functions for JSON validation, repair, and logging.
"""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

# Expected JSON schema
SCHEMA = {
    "mood": str,
    "gesture": str,
    "motion": str,
    "notation_details": list,
    "instructional_metaphors": list,
    "final_metaphor": str
}


def setup_logging(log_dir: str = "./logs") -> logging.Logger:
    """
    Set up logging to both file and console.

    Args:
        log_dir: Directory to store log files

    Returns:
        Configured logger instance
    """
    Path(log_dir).mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = Path(log_dir) / f"metaphor_analyzer_{timestamp}.log"

    logger = logging.getLogger("metaphor_analyzer")
    logger.setLevel(logging.INFO)

    # Clear any existing handlers
    logger.handlers.clear()

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(console_formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


def extract_json_from_text(text: str) -> Optional[str]:
    """
    Extract JSON from text that might contain markdown code blocks or prose.

    Args:
        text: Raw text that might contain JSON

    Returns:
        Extracted JSON string or None if no JSON found
    """
    # Try to find JSON in markdown code blocks
    if "```json" in text:
        start = text.find("```json") + 7
        end = text.find("```", start)
        if end > start:
            return text[start:end].strip()

    if "```" in text:
        start = text.find("```") + 3
        end = text.find("```", start)
        if end > start:
            potential_json = text[start:end].strip()
            if potential_json.startswith("{"):
                return potential_json

    # Try to find raw JSON by looking for curly braces
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        return text[start:end + 1].strip()

    return None


def validate_schema(data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validate JSON data against the expected schema.

    Args:
        data: Parsed JSON data to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    for key, expected_type in SCHEMA.items():
        if key not in data:
            return False, f"Missing required field: {key}"

        if not isinstance(data[key], expected_type):
            return False, f"Field '{key}' has wrong type. Expected {expected_type.__name__}, got {type(data[key]).__name__}"

    # Additional validation for notation_details
    if not data["notation_details"]:
        return False, "Field 'notation_details' cannot be empty"

    if not all(isinstance(d, str) for d in data["notation_details"]):
        return False, "All items in 'notation_details' must be strings"

    # Additional validation for instructional_metaphors
    if not data["instructional_metaphors"]:
        return False, "Field 'instructional_metaphors' cannot be empty"

    if len(data["instructional_metaphors"]) != 3:
        return False, f"Field 'instructional_metaphors' must contain exactly 3 items, got {len(data['instructional_metaphors'])}"

    if not all(isinstance(m, str) for m in data["instructional_metaphors"]):
        return False, "All items in 'instructional_metaphors' must be strings"

    return True, None


def parse_and_validate_json(
    response_text: str,
    logger: Optional[logging.Logger] = None
) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Parse and validate JSON response from Claude.

    Args:
        response_text: Raw response text from API
        logger: Optional logger instance

    Returns:
        Tuple of (parsed_data, error_message)
    """
    if logger:
        logger.info(f"Raw response: {response_text[:500]}...")

    # Try to extract JSON
    json_str = extract_json_from_text(response_text)

    if not json_str:
        # Maybe it's already pure JSON
        json_str = response_text.strip()

    # Try to parse
    try:
        data = json.loads(json_str)
    except json.JSONDecodeError as e:
        error = f"JSON parsing failed: {str(e)}"
        if logger:
            logger.error(error)
        return None, error

    # Validate schema
    is_valid, error_msg = validate_schema(data)

    if not is_valid:
        if logger:
            logger.error(f"Schema validation failed: {error_msg}")
        return None, f"Schema validation failed: {error_msg}"

    if logger:
        logger.info(f"Successfully parsed and validated JSON: {json.dumps(data, indent=2)}")

    return data, None


def save_analysis_log(
    image_path: str,
    raw_response: str,
    parsed_data: Optional[Dict[str, Any]],
    error: Optional[str],
    log_dir: str = "./logs"
) -> None:
    """
    Save detailed analysis log to file.

    Args:
        image_path: Path to analyzed image
        raw_response: Raw API response
        parsed_data: Parsed JSON data (if successful)
        error: Error message (if failed)
        log_dir: Directory to store logs
    """
    Path(log_dir).mkdir(exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    log_file = Path(log_dir) / f"analysis_{timestamp}.json"

    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "image_path": image_path,
        "raw_response": raw_response,
        "parsed_data": parsed_data,
        "error": error,
        "success": parsed_data is not None
    }

    with open(log_file, "w", encoding="utf-8") as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)
