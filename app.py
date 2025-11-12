"""
Sheet Music Metaphor Analyzer - Main Gradio Application
"""

import base64
import csv
import io
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import anthropic
import gradio as gr
from PIL import Image

try:
    from huggingface_hub import HfApi, hf_hub_download
    HF_AVAILABLE = True
except ImportError:
    HF_AVAILABLE = False

from utils import (
    parse_and_validate_json,
    save_analysis_log,
    setup_logging,
)

# Initialize logger
logger = setup_logging()

# Multiple Claude API prompts for testing
# To add/edit prompts: simply add or modify entries in this dictionary
# Each prompt must return the same JSON schema
ANALYSIS_PROMPTS = {
    "Prompt 1": """You are an experienced music conductor and teacher analyzing sheet music to provide performance guidance.

Follow this step-by-step process:

STEP 1: CONDUCTOR ANALYSIS
As an experienced conductor, examine the musical notation carefully and describe:
- mood: The emotional tone and feeling the notation suggests
- gesture: The physical conducting gesture or body movement this would inspire
- motion: The type of movement quality (e.g., flowing, crisp, sustained, bouncing)

STEP 2: NOTATION INSIGHTS
Identify 2-4 specific aspects of the notation that caught your attention and influenced your interpretation. These might be dynamics, articulation, tempo markings, phrase shapes, rhythmic patterns, or harmonic progressions. Write these as clear observations that help explain how you arrived at your interpretation.

STEP 3: INSTRUCTIONAL METAPHORS
Based on your analysis, create exactly 3 simple, direct instructional metaphors for the performer. Each should:
- Start with a phrase like "Play this like...", "Think of...", "Imagine...", or similar
- Use simple, everyday imagery that's easy to grasp
- Be direct and practical, not flowery or ornate
- Avoid technical music terminology
- Focus on feeling and physicality
- Keep it grounded - prefer "walking through tall grass" over "dancing through celestial meadows"

STEP 4: FINAL METAPHOR
Synthesize everything above into one concise, simple instructional metaphor. Keep it direct and practical - a clear image the performer can immediately use. Avoid overly poetic or elaborate language.

Return ONLY valid JSON matching this exact schema:

{
  "mood": "string",
  "gesture": "string",
  "motion": "string",
  "notation_details": ["observation 1", "observation 2", "..."],
  "instructional_metaphors": ["metaphor 1", "metaphor 2", "metaphor 3"],
  "final_metaphor": "one simple, direct metaphor"
}

Remember: Return ONLY the JSON object, no additional text or explanation.""",

    "Prompt 2": """You are an experienced music conductor and teacher analyzing sheet music to provide performance guidance.

Follow this step-by-step process:

STEP 1: CONDUCTOR ANALYSIS
As an experienced conductor, examine the musical notation carefully and describe:
- mood: The emotional tone and feeling the notation suggests
- gesture: The physical conducting gesture or body movement this would inspire
- motion: The type of movement quality (e.g., flowing, crisp, sustained, bouncing)

STEP 2: NOTATION INSIGHTS
Identify 2-4 specific aspects of the notation that caught your attention and influenced your interpretation. These might be dynamics, articulation, tempo markings, phrase shapes, rhythmic patterns, or harmonic progressions. Write these as clear observations that help explain how you arrived at your interpretation.

STEP 3: INSTRUCTIONAL METAPHORS
Based on your analysis, create exactly 3 simple, direct instructional metaphors for the performer. Each should:
- Start with a phrase like "Play this like...", "Think of...", "Imagine...", or similar
- Use simple, everyday imagery that's easy to grasp
- Be direct and practical, not flowery or ornate
- Avoid technical music terminology
- Focus on feeling and physicality
- Keep it grounded - prefer "walking through tall grass" over "dancing through celestial meadows"

STEP 4: FINAL METAPHOR
Now, keep in mind the following weights as you deliver your final metaphor: The mood 25%, gesture 25%, motion 50%. 
Synthesize everything above — including 20% more emphasis on the Notation Insights — into one concise, simple instructional metaphor that reflects how emotion, gesture, and movement emerge directly from the score.
Keep it direct and practical, giving a clear, physical image the performer can immediately use.

Return ONLY valid JSON matching this exact schema:

{
  "mood": "string",
  "gesture": "string",
  "motion": "string",
  "notation_details": ["observation 1", "observation 2", "..."],
  "instructional_metaphors": ["metaphor 1", "metaphor 2", "metaphor 3"],
  "final_metaphor": "one simple, direct metaphor"
}

Remember: Return ONLY the JSON object, no additional text or explanation.""",

    "Prompt 3": """[Add your third test prompt here - must return the same JSON schema]""",

    "Prompt 4": """[Add your fourth test prompt here - must return the same JSON schema]""",

    "Prompt 5": """[Add your fifth test prompt here - must return the same JSON schema]"""
}


def resize_image(image: Image.Image, max_width: int = 1400) -> Image.Image:
    """
    Resize image to max width while maintaining aspect ratio.

    Args:
        image: PIL Image to resize
        max_width: Maximum width in pixels

    Returns:
        Resized PIL Image
    """
    if image.width <= max_width:
        return image

    ratio = max_width / image.width
    new_height = int(image.height * ratio)
    return image.resize((max_width, new_height), Image.Resampling.LANCZOS)


def image_to_base64(image: Image.Image) -> str:
    """
    Convert PIL Image to base64 string.

    Args:
        image: PIL Image to convert

    Returns:
        Base64 encoded string
    """
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    return base64.b64encode(buffered.getvalue()).decode("utf-8")


def save_feedback(metaphor: str, rating: int, parsed_data: Dict[str, Any]) -> str:
    """
    Save user feedback to Hugging Face Dataset (if HF_TOKEN available) or CSV file (fallback).

    Args:
        metaphor: The final metaphor that was rated
        rating: User rating (1-5)
        parsed_data: Full parsed response data

    Returns:
        Timestamp of the feedback entry (for undo functionality)
    """
    # Prepare feedback data with timestamp
    timestamp = datetime.now().isoformat()
    feedback_entry = {
        "timestamp": timestamp,
        "rating": rating,
        "final_metaphor": metaphor,
        "mood": parsed_data.get("mood", ""),
        "gesture": parsed_data.get("gesture", ""),
        "motion": parsed_data.get("motion", ""),
        "instructional_metaphors": " | ".join(parsed_data.get("instructional_metaphors", [])),
        "notation_details": " | ".join(parsed_data.get("notation_details", []))
    }

    # Try to save to Hugging Face Dataset
    hf_token = os.getenv("HF_TOKEN")
    hf_dataset_name = os.getenv("HF_DATASET_NAME", "sheet-music-feedback")

    if HF_AVAILABLE and hf_token:
        try:
            api = HfApi(token=hf_token)

            # Get HF username from token
            user_info = api.whoami()
            username = user_info['name']
            dataset_id = f"{username}/{hf_dataset_name}"

            # Download existing data or create new
            try:
                # Try to download existing dataset
                local_file = hf_hub_download(
                    repo_id=dataset_id,
                    filename="feedback.csv",
                    repo_type="dataset",
                    token=hf_token
                )
                # Read existing data
                import pandas as pd
                df = pd.read_csv(local_file)
                # Append new feedback
                df = pd.concat([df, pd.DataFrame([feedback_entry])], ignore_index=True)
            except Exception:
                # Dataset doesn't exist yet, create new DataFrame
                import pandas as pd
                df = pd.DataFrame([feedback_entry])

            # Save to temporary file
            temp_file = Path("./temp_feedback.csv")
            df.to_csv(temp_file, index=False)

            # Upload to HF
            api.upload_file(
                path_or_fileobj=str(temp_file),
                path_in_repo="feedback.csv",
                repo_id=dataset_id,
                repo_type="dataset",
                commit_message=f"Add feedback: rating {rating}"
            )

            # Create dataset if it doesn't exist
            try:
                api.create_repo(repo_id=dataset_id, repo_type="dataset", private=False, exist_ok=True)
            except Exception:
                pass  # Repo might already exist

            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

            logger.info(f"Feedback saved to HF dataset {dataset_id}: rating={rating}, metaphor={metaphor[:50]}...")
            return timestamp

        except Exception as e:
            logger.warning(f"Failed to save to HF dataset, falling back to CSV: {e}")

    # Fallback to CSV (for local development or if HF fails)
    feedback_dir = Path("./feedback")
    feedback_dir.mkdir(exist_ok=True)
    feedback_file = feedback_dir / "ratings.csv"

    # Check if file exists to write header
    file_exists = feedback_file.exists()

    with open(feedback_file, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow([
                "timestamp",
                "rating",
                "final_metaphor",
                "mood",
                "gesture",
                "motion",
                "instructional_metaphors",
                "notation_details"
            ])

        writer.writerow([
            feedback_entry["timestamp"],
            feedback_entry["rating"],
            feedback_entry["final_metaphor"],
            feedback_entry["mood"],
            feedback_entry["gesture"],
            feedback_entry["motion"],
            feedback_entry["instructional_metaphors"],
            feedback_entry["notation_details"]
        ])

    logger.info(f"Feedback saved to local CSV: rating={rating}, metaphor={metaphor[:50]}...")
    return timestamp


def undo_feedback(timestamp: str) -> bool:
    """
    Delete a feedback entry by timestamp from HF Dataset or CSV file.

    Args:
        timestamp: ISO format timestamp of the feedback to delete

    Returns:
        True if deletion was successful, False otherwise
    """
    # Try to delete from Hugging Face Dataset
    hf_token = os.getenv("HF_TOKEN")
    hf_dataset_name = os.getenv("HF_DATASET_NAME", "sheet-music-feedback")

    if HF_AVAILABLE and hf_token:
        try:
            api = HfApi(token=hf_token)

            # Get HF username from token
            user_info = api.whoami()
            username = user_info['name']
            dataset_id = f"{username}/{hf_dataset_name}"

            # Download existing data
            local_file = hf_hub_download(
                repo_id=dataset_id,
                filename="feedback.csv",
                repo_type="dataset",
                token=hf_token
            )

            # Read and filter data
            import pandas as pd
            df = pd.read_csv(local_file)
            original_len = len(df)

            # Remove row with matching timestamp
            df = df[df['timestamp'] != timestamp]

            if len(df) == original_len:
                logger.warning(f"Timestamp {timestamp} not found in HF dataset")
                return False

            # Save to temporary file
            temp_file = Path("./temp_feedback.csv")
            df.to_csv(temp_file, index=False)

            # Upload to HF
            api.upload_file(
                path_or_fileobj=str(temp_file),
                path_in_repo="feedback.csv",
                repo_id=dataset_id,
                repo_type="dataset",
                commit_message="Undo feedback submission"
            )

            # Clean up temp file
            if temp_file.exists():
                temp_file.unlink()

            logger.info(f"Feedback with timestamp {timestamp} removed from HF dataset")
            return True

        except Exception as e:
            logger.warning(f"Failed to undo from HF dataset, trying CSV: {e}")

    # Fallback to CSV (for local development or if HF fails)
    feedback_file = Path("./feedback/ratings.csv")

    if not feedback_file.exists():
        logger.warning("No local feedback CSV file found")
        return False

    try:
        # Read all rows
        rows = []
        with open(feedback_file, "r", newline="", encoding="utf-8") as f:
            reader = csv.reader(f)
            headers = next(reader)
            rows = [headers]

            found = False
            for row in reader:
                # Skip the row with matching timestamp
                if row[0] == timestamp:
                    found = True
                    continue
                rows.append(row)

        if not found:
            logger.warning(f"Timestamp {timestamp} not found in local CSV")
            return False

        # Write back all rows except the one we're deleting
        with open(feedback_file, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

        logger.info(f"Feedback with timestamp {timestamp} removed from local CSV")
        return True

    except Exception as e:
        logger.error(f"Failed to undo feedback from CSV: {e}")
        return False


def analyze_sheet_music(
    image: Optional[Image.Image],
    api_key: Optional[str] = None,
    prompt_key: str = "Prompt 1 (Current)"
) -> Tuple[str, str, str, Dict[str, Any]]:
    """
    Analyze sheet music image using Claude Vision API.

    Args:
        image: PIL Image of sheet music
        api_key: Optional API key (uses env var if not provided)
        prompt_key: Which prompt to use from ANALYSIS_PROMPTS dictionary

    Returns:
        Tuple of (final_metaphor_html, interpretability_html, json_output, parsed_data_dict)
        Errors are returned as HTML in the final_metaphor_html slot
    """
    def create_error_html(error_msg: str) -> str:
        """Create error HTML for display in metaphor box."""
        return f"""
        <div style="padding: 30px 20px; background: #fee; border: 2px solid #c33;
                    border-radius: 15px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
            <p style="color: #c33; font-size: clamp(16px, 5vw, 18px); font-weight: 500; line-height: 1.4;
                      margin: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                Error: {error_msg}
            </p>
        </div>
        """

    if image is None:
        return create_error_html("Please upload an image first."), "", "", {}

    # Get API key
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        error_msg = "API key required. Please paste in your API key."
        logger.error(error_msg)
        return create_error_html(error_msg), "", "", {}

    try:
        # Resize image
        logger.info(f"Processing image of size {image.size}")
        resized_image = resize_image(image)
        logger.info(f"Resized to {resized_image.size}")

        # Convert to base64
        image_b64 = image_to_base64(resized_image)

        # Initialize Anthropic client
        client = anthropic.Anthropic(api_key=api_key)

        # First attempt
        logger.info("Sending request to Claude Vision API...")
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            temperature=0.2,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": ANALYSIS_PROMPTS[prompt_key]
                        }
                    ],
                }
            ],
        )

        raw_response = response.content[0].text
        logger.info(f"Received response: {raw_response[:200]}...")

        # Parse and validate
        parsed_data, error = parse_and_validate_json(raw_response, logger)

        # If parsing failed, retry with stricter instruction
        if parsed_data is None and error:
            logger.warning(f"First attempt failed: {error}. Retrying with stricter prompt...")

            retry_response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                temperature=0.1,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/png",
                                    "data": image_b64,
                                },
                            },
                            {
                                "type": "text",
                                "text": ANALYSIS_PROMPTS[prompt_key]
                            }
                        ],
                    },
                    {
                        "role": "assistant",
                        "content": raw_response
                    },
                    {
                        "role": "user",
                        "content": "Return valid JSON only, no prose. Use the exact schema structure provided."
                    }
                ],
            )

            raw_response = retry_response.content[0].text
            parsed_data, error = parse_and_validate_json(raw_response, logger)

        # Save log
        save_analysis_log(
            image_path="uploaded_image",
            raw_response=raw_response,
            parsed_data=parsed_data,
            error=error
        )

        # Handle results
        if parsed_data is None:
            return create_error_html(f"Failed to parse response: {error}"), "", raw_response, {}

        # Format main metaphor output
        final_metaphor_html = f"""
        <div style="padding: 30px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 10px; text-align: center;">
            <p style="color: white; font-size: clamp(20px, 6vw, 28px); font-weight: 500; line-height: 1.4;
                    margin: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                {parsed_data['final_metaphor']}
            </p>
        </div>
        """

        # Format interpretability sections (for admin/debug)
        interpretability_html = f"""
        <div style="margin-top: 20px; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
            <div style="margin-bottom: 15px; padding: 15px; background: #f8f9fa;
                        border-radius: 10px; border-left: 4px solid #667eea;">
                <h3 style="margin-top: 0; color: #333; font-size: 16px;">Conductor Analysis</h3>
                <p style="margin: 8px 0; font-size: 14px;"><strong>Mood:</strong> {parsed_data['mood']}</p>
                <p style="margin: 8px 0; font-size: 14px;"><strong>Gesture:</strong> {parsed_data['gesture']}</p>
                <p style="margin: 8px 0; font-size: 14px;"><strong>Motion:</strong> {parsed_data['motion']}</p>
            </div>

            <div style="margin-bottom: 15px; padding: 15px; background: #e7f3ff;
                        border-radius: 10px; border-left: 4px solid #2196f3;">
                <h3 style="margin-top: 0; color: #333; font-size: 16px;">What the Conductor Noticed</h3>
                <ul style="margin: 8px 0; padding-left: 20px; line-height: 1.6; font-size: 14px;">
                    {"".join(f'<li style="margin-bottom: 5px;">{detail}</li>' for detail in parsed_data['notation_details'])}
                </ul>
            </div>

            <div style="padding: 15px; background: #fff3cd;
                        border-radius: 10px; border-left: 4px solid #ffc107;">
                <h3 style="margin-top: 0; color: #333; font-size: 16px;">All Instructional Metaphors</h3>
                <ul style="margin: 8px 0; padding-left: 20px; line-height: 1.6; font-size: 14px;">
                    {"".join(f'<li style="margin-bottom: 5px;">{m}</li>' for m in parsed_data['instructional_metaphors'])}
                </ul>
            </div>
        </div>
        """

        json_output = json.dumps(parsed_data, indent=2, ensure_ascii=False)

        logger.info("Analysis completed successfully")
        return final_metaphor_html, interpretability_html, json_output, parsed_data

    except anthropic.APIError as e:
        error_msg = f"API Error: {str(e)}"
        logger.error(error_msg)
        return create_error_html(error_msg), "", "", {}
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return create_error_html(error_msg), "", "", {}


def handle_feedback(rating: int, parsed_data: Dict[str, Any], feedback_submitted: bool) -> Tuple[str, bool, str, int, bool]:
    """
    Handle user feedback submission.

    Args:
        rating: User rating (1-5)
        parsed_data: The parsed analysis data
        feedback_submitted: Whether feedback has already been submitted

    Returns:
        Tuple of (message, feedback_submitted, timestamp, rating, undo_visible)
    """
    if feedback_submitted:
        return "Feedback already submitted for this analysis.", True, "", rating, True

    if not parsed_data or "final_metaphor" not in parsed_data:
        return "Please analyze an image first before submitting feedback.", False, "", 0, False

    try:
        timestamp = save_feedback(parsed_data["final_metaphor"], rating, parsed_data)
        return f"Feedback submitted ({rating}/5)", True, timestamp, rating, True
    except Exception as e:
        logger.error(f"Failed to save feedback: {e}")
        return "Failed to save feedback. Please try again.", False, "", 0, False


def handle_undo_feedback(timestamp: str) -> Tuple[str, bool, str, int, bool]:
    """
    Handle undoing a feedback submission.

    Args:
        timestamp: Timestamp of the feedback to undo

    Returns:
        Tuple of (message, feedback_submitted, timestamp, rating, undo_visible)
    """
    if not timestamp:
        return "", False, "", 0, False

    try:
        success = undo_feedback(timestamp)
        if success:
            return "", False, "", 0, False
        else:
            return "Failed to undo feedback.", True, timestamp, 0, True
    except Exception as e:
        logger.error(f"Failed to undo feedback: {e}")
        return "Failed to undo feedback.", True, timestamp, 0, True


def create_ui() -> gr.Blocks:
    """
    Create and configure the Gradio UI.

    Returns:
        Configured Gradio Blocks interface
    """
    # Custom CSS for mobile optimization and Helvetica Neue font
    custom_css = """
    * {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif !important;
    }

    /* Mobile-friendly adjustments */
    @media (max-width: 768px) {
        .gradio-container {
            padding: 10px !important;
        }

        h1 {
            font-size: 24px !important;
        }

        .gr-button {
            font-size: 16px !important;
            padding: 12px 20px !important;
        }
    }

    /* Improve touch targets for mobile */
    button {
        min-height: 44px;
    }

    /* Better spacing on mobile */
    .gr-form {
        gap: 15px;
    }

    /* Rating buttons styling */
    .rating-buttons {
        display: flex !important;
        gap: 8px !important;
        flex-wrap: nowrap !important;
        width: 100% !important;
    }

    .rating-button {
        flex: 1 1 0 !important;
        min-width: 0 !important;
        font-size: 20px !important;
        font-weight: 600 !important;
        padding: 12px 8px !important;
    }

    /* Feedback section styling */
    .feedback-section {
        padding: 20px;

        border-radius: 10px;
        border-left: 4px solid #667eea;
        margin-top: 20px;
    }

    .feedback-title {
        margin: 0 0 15px 0 !important;
        font-size: 16px !important;
        font-weight: 500 !important;
    }

    /* Accordion title styling with purple */
    .accordion-title {
        color: #667eea !important;
        font-weight: 500 !important;
    }

    /* Override Gradio accordion styling */
    .gr-accordion {
        border-left: 4px solid #667eea !important;
    }

    /* Instructional metaphor section header */
    .metaphor-section-header {
        font-size: 18px !important;
        font-weight: 500 !important;
        color: #667eea !important;
    }
    """

    with gr.Blocks(
        title="Instructional Metaphors",
        theme=gr.themes.Soft(),
        css=custom_css
    ) as demo:
        gr.Markdown(
            """
            # Instructional Metaphors

            Take a photo of the sheet music you're practicing to receive an instructional metaphor that helps guide your practice of that piece or passage.

            **Note:** Paste in the API key you were provided. If you're not sure whether you received an API key, contact Willie or Crystal.
            """,
            elem_classes=["main-header"]
        )

        # State variables to track data and rerolls
        current_image_state = gr.State(None)
        parsed_data_state = gr.State({})
        reroll_count_state = gr.State(0)

        # State variables for feedback tracking
        feedback_submitted_state = gr.State(False)
        feedback_timestamp_state = gr.State("")
        submitted_rating_state = gr.State(0)

        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(
                    type="pil",
                    label="Take a photo",
                    height=400,
                    sources=["upload", "webcam"]  # Enable both upload and camera for mobile
                )

                api_key_input = gr.Textbox(
                    label="API Key",
                    type="password",
                    placeholder="Paste your API key here..."
                )

                prompt_selector = gr.Dropdown(
                    choices=list(ANALYSIS_PROMPTS.keys()),
                    value="Prompt 1 (Current)",
                    label="Prompt Selection (for testing)",
                    info="Select which prompt version to use for analysis"
                )

                with gr.Row():
                    analyze_btn = gr.Button(
                        "Analyze Sheet Music",
                        variant="primary",
                        size="lg",
                        scale=2
                    )

                    reroll_btn = gr.Button(
                        "Reroll",
                        variant="secondary",
                        size="lg",
                        scale=1,
                        visible=False
                    )

                reroll_status = gr.Markdown("", visible=False)

            with gr.Column(scale=1):
                # Main instructional metaphor output
                gr.Markdown()
                result_html = gr.HTML(
                    label="",
                    show_label=False,
                    value="""
                    <div style="padding: 30px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                border-radius: 15px; text-align: center;
                                min-height: 100px; display: flex; align-items: center; justify-content: center;">
                        <p style="color: rgba(255, 255, 255, 0.7); font-size: 16px; margin: 0;
                                  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                            Upload a photo to receive your instructional metaphor
                        </p>
                    </div>
                    """
                )

                # Feedback section
                with gr.Group(visible=False, elem_classes=["feedback-section"]) as feedback_group:
                    gr.Markdown("### How helpful was this metaphor?", elem_classes=["feedback-title"])
                    with gr.Row(elem_classes=["rating-buttons"]):
                        rating_1 = gr.Button("1", size="lg", elem_classes=["rating-button"])
                        rating_2 = gr.Button("2", size="lg", elem_classes=["rating-button"])
                        rating_3 = gr.Button("3", size="lg", elem_classes=["rating-button"])
                        rating_4 = gr.Button("4", size="lg", elem_classes=["rating-button"])
                        rating_5 = gr.Button("5", size="lg", elem_classes=["rating-button"])
                    feedback_message = gr.Markdown("")
                    undo_btn = gr.Button("Undo", visible=False, variant="secondary", size="sm")

                # Interpretability sections (hidden by default for users)
                with gr.Accordion("Interpretability Details", open=False, elem_classes=["accordion-title"]):
                    interpretability_output = gr.HTML()

                with gr.Accordion("Full JSON Response", open=False, elem_classes=["accordion-title"]):
                    json_output = gr.Code(
                        label="Raw JSON",
                        language="json",
                        lines=15
                    )

        gr.Markdown(
            """
            ---
            **Tips:**
            - Take clear photos of printed sheet music
            - Works best with short musical phrases (2-8 measures)
            - You can reroll up to 3 times per photo to get different metaphors
            """
        )

        # Analysis function that updates all outputs and states
        def analyze_and_update(image, api_key, prompt_key):
            if image is None:
                error_html = """
                <div style="padding: 30px 20px; background: #fee; border: 2px solid #c33;
                            border-radius: 15px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <p style="color: #c33; font-size: clamp(16px, 5vw, 18px); font-weight: 500; line-height: 1.4;
                              margin: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                        Error: Please upload an image first.
                    </p>
                </div>
                """
                return (
                    error_html, "", "", {},
                    image, {}, 0, gr.update(visible=False), gr.update(visible=False), "",
                    False, "", 0, "", gr.update(visible=False)
                )

            metaphor_html, interp_html, json_out, parsed_data = analyze_sheet_music(image, api_key, prompt_key)

            # Update reroll button visibility and status
            # Show reroll/feedback only if we got valid parsed data (not an error)
            show_reroll = bool(parsed_data)
            reroll_visible = gr.update(visible=show_reroll)
            feedback_visible = gr.update(visible=show_reroll)
            status_msg = "Rerolls remaining: 3" if show_reroll else ""

            return (
                metaphor_html, interp_html, json_out, parsed_data,
                image, parsed_data, 0, reroll_visible, feedback_visible, status_msg,
                False, "", 0, "", gr.update(visible=False)
            )

        # Reroll function
        def reroll_analysis(image, api_key, prompt_key, current_count):
            if current_count >= 3:
                max_error_html = """
                <div style="padding: 30px 20px; background: #fee; border: 2px solid #c33;
                            border-radius: 15px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <p style="color: #c33; font-size: clamp(16px, 5vw, 18px); font-weight: 500; line-height: 1.4;
                              margin: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                        Error: Maximum rerolls (3) reached for this image.
                    </p>
                </div>
                """
                return (
                    max_error_html, gr.update(), gr.update(), gr.update(),
                    current_count, gr.update(visible=False), f"Maximum rerolls reached (3/3)",
                    False, "", 0, "", gr.update(visible=False)
                )

            if image is None:
                no_image_error_html = """
                <div style="padding: 30px 20px; background: #fee; border: 2px solid #c33;
                            border-radius: 15px; text-align: center; box-shadow: 0 5px 15px rgba(0,0,0,0.1);">
                    <p style="color: #c33; font-size: clamp(16px, 5vw, 18px); font-weight: 500; line-height: 1.4;
                              margin: 0; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;">
                        Error: Please upload an image first.
                    </p>
                </div>
                """
                return (
                    no_image_error_html, gr.update(), gr.update(), gr.update(),
                    current_count, gr.update(), f"Rerolls remaining: {3 - current_count}",
                    False, "", 0, "", gr.update(visible=False)
                )

            metaphor_html, interp_html, json_out, parsed_data = analyze_sheet_music(image, api_key, prompt_key)
            new_count = current_count + 1
            remaining = 3 - new_count

            show_reroll = new_count < 3 and bool(parsed_data)
            status_msg = f"Rerolls remaining: {remaining}" if show_reroll else f"Maximum rerolls reached ({new_count}/3)"

            return (
                metaphor_html, interp_html, json_out, parsed_data,
                new_count, gr.update(visible=show_reroll), status_msg,
                False, "", 0, "", gr.update(visible=False)
            )

        # Reset reroll count when new image is uploaded
        def reset_reroll_count(image):
            return 0, gr.update(visible=False), "", False, "", 0, "", gr.update(visible=False)

        # Event handlers
        analyze_btn.click(
            fn=analyze_and_update,
            inputs=[image_input, api_key_input, prompt_selector],
            outputs=[
                result_html, interpretability_output, json_output, parsed_data_state,
                current_image_state, parsed_data_state, reroll_count_state,
                reroll_btn, feedback_group, reroll_status,
                feedback_submitted_state, feedback_timestamp_state, submitted_rating_state,
                feedback_message, undo_btn
            ]
        ).then(
            fn=lambda: gr.update(visible=True),
            outputs=[reroll_status]
        )

        reroll_btn.click(
            fn=reroll_analysis,
            inputs=[current_image_state, api_key_input, prompt_selector, reroll_count_state],
            outputs=[
                result_html, interpretability_output, json_output, parsed_data_state,
                reroll_count_state, reroll_btn, reroll_status,
                feedback_submitted_state, feedback_timestamp_state, submitted_rating_state,
                feedback_message, undo_btn
            ]
        )

        image_input.change(
            fn=reset_reroll_count,
            inputs=[image_input],
            outputs=[
                reroll_count_state, reroll_btn, reroll_status,
                feedback_submitted_state, feedback_timestamp_state, submitted_rating_state,
                feedback_message, undo_btn
            ]
        )

        # Feedback button handlers
        def submit_rating(rating, data, feedback_submitted):
            return handle_feedback(rating, data, feedback_submitted)

        rating_1.click(
            lambda data, submitted: submit_rating(1, data, submitted),
            inputs=[parsed_data_state, feedback_submitted_state],
            outputs=[feedback_message, feedback_submitted_state, feedback_timestamp_state, submitted_rating_state, undo_btn]
        )
        rating_2.click(
            lambda data, submitted: submit_rating(2, data, submitted),
            inputs=[parsed_data_state, feedback_submitted_state],
            outputs=[feedback_message, feedback_submitted_state, feedback_timestamp_state, submitted_rating_state, undo_btn]
        )
        rating_3.click(
            lambda data, submitted: submit_rating(3, data, submitted),
            inputs=[parsed_data_state, feedback_submitted_state],
            outputs=[feedback_message, feedback_submitted_state, feedback_timestamp_state, submitted_rating_state, undo_btn]
        )
        rating_4.click(
            lambda data, submitted: submit_rating(4, data, submitted),
            inputs=[parsed_data_state, feedback_submitted_state],
            outputs=[feedback_message, feedback_submitted_state, feedback_timestamp_state, submitted_rating_state, undo_btn]
        )
        rating_5.click(
            lambda data, submitted: submit_rating(5, data, submitted),
            inputs=[parsed_data_state, feedback_submitted_state],
            outputs=[feedback_message, feedback_submitted_state, feedback_timestamp_state, submitted_rating_state, undo_btn]
        )

        # Undo button handler
        undo_btn.click(
            fn=handle_undo_feedback,
            inputs=[feedback_timestamp_state],
            outputs=[feedback_message, feedback_submitted_state, feedback_timestamp_state, submitted_rating_state, undo_btn]
        )

    return demo


def main():
    """
    Launch the Gradio application.
    """
    logger.info("Starting Sheet Music Metaphor Analyzer...")

    # Check for API key
    if not os.getenv("ANTHROPIC_API_KEY"):
        logger.warning(
            "ANTHROPIC_API_KEY not found in environment. "
            "Users will need to provide it in the UI."
        )

    demo = create_ui()
    demo.launch(share=True)


if __name__ == "__main__":
    main()
