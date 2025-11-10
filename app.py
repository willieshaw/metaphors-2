"""
Sheet Music Metaphor Analyzer - Main Gradio Application
"""

import base64
import io
import os
from typing import Optional, Tuple

import anthropic
import gradio as gr
from PIL import Image

from utils import (
    parse_and_validate_json,
    save_analysis_log,
    setup_logging,
)

# Initialize logger
logger = setup_logging()

# Claude API prompt
ANALYSIS_PROMPT = """You are an experienced music conductor and teacher analyzing sheet music to provide performance guidance.

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

Remember: Return ONLY the JSON object, no additional text or explanation."""


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


def analyze_sheet_music(
    image: Optional[Image.Image],
    api_key: Optional[str] = None
) -> Tuple[str, str, str]:
    """
    Analyze sheet music image using Claude Vision API.

    Args:
        image: PIL Image of sheet music
        api_key: Optional API key (uses env var if not provided)

    Returns:
        Tuple of (final_metaphor_html, json_output, error_message)
    """
    if image is None:
        return "", "", "Please upload an image first."

    # Get API key
    if not api_key:
        api_key = os.getenv("ANTHROPIC_API_KEY")

    if not api_key:
        error_msg = "ANTHROPIC_API_KEY not found in environment variables."
        logger.error(error_msg)
        return "", "", error_msg

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
                            "text": ANALYSIS_PROMPT
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
                                "text": ANALYSIS_PROMPT
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
            return "", raw_response, f"Failed to parse response: {error}"

        # Format outputs
        final_metaphor_html = f"""
        <div style="padding: 30px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    border-radius: 15px; text-align: center; box-shadow: 0 10px 30px rgba(0,0,0,0.3);">
            <h2 style="color: white; margin-bottom: 20px; font-size: 24px; font-weight: 300;">
                Performance Guidance
            </h2>
            <p style="color: white; font-size: 32px; font-weight: 500; line-height: 1.5;
                      font-style: italic; margin: 0;">
                {parsed_data['final_metaphor']}
            </p>
        </div>

        <div style="margin-top: 25px; padding: 20px; background: #f8f9fa;
                    border-radius: 10px; border-left: 4px solid #667eea;">
            <h3 style="margin-top: 0; color: #333; font-size: 18px;">Conductor Analysis</h3>
            <p style="margin: 10px 0;"><strong>Mood:</strong> {parsed_data['mood']}</p>
            <p style="margin: 10px 0;"><strong>Gesture:</strong> {parsed_data['gesture']}</p>
            <p style="margin: 10px 0;"><strong>Motion:</strong> {parsed_data['motion']}</p>
        </div>

        <div style="margin-top: 20px; padding: 20px; background: #e7f3ff;
                    border-radius: 10px; border-left: 4px solid #2196f3;">
            <h3 style="margin-top: 0; color: #333; font-size: 18px;">What the Conductor Noticed</h3>
            <ul style="margin: 10px 0; padding-left: 20px; line-height: 1.8;">
                {"".join(f'<li>{detail}</li>' for detail in parsed_data['notation_details'])}
            </ul>
        </div>

        <div style="margin-top: 20px; padding: 20px; background: #fff3cd;
                    border-radius: 10px; border-left: 4px solid #ffc107;">
            <h3 style="margin-top: 0; color: #333; font-size: 18px;">Instructional Metaphors</h3>
            <ul style="margin: 10px 0; padding-left: 20px; line-height: 1.8;">
                {"".join(f'<li>{m}</li>' for m in parsed_data['instructional_metaphors'])}
            </ul>
        </div>
        """

        import json
        json_output = json.dumps(parsed_data, indent=2, ensure_ascii=False)

        logger.info("Analysis completed successfully")
        return final_metaphor_html, json_output, ""

    except anthropic.APIError as e:
        error_msg = f"API Error: {str(e)}"
        logger.error(error_msg)
        return "", "", error_msg
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return "", "", error_msg


def create_ui() -> gr.Blocks:
    """
    Create and configure the Gradio UI.

    Returns:
        Configured Gradio Blocks interface
    """
    with gr.Blocks(
        title="Sheet Music Metaphor Analyzer",
        theme=gr.themes.Soft()
    ) as demo:
        gr.Markdown(
            """
            # Sheet Music Metaphor Analyzer

            Upload a photo of sheet music and get poetic, sensory performance guidance.
            """
        )

        with gr.Row():
            with gr.Column(scale=1):
                image_input = gr.Image(
                    type="pil",
                    label="Upload Sheet Music Photo",
                    height=400
                )

                api_key_input = gr.Textbox(
                    label="Anthropic API Key (optional, uses env var if empty)",
                    type="password",
                    placeholder="sk-ant-..."
                )

                analyze_btn = gr.Button(
                    "Analyze Music",
                    variant="primary",
                    size="lg"
                )

            with gr.Column(scale=1):
                result_html = gr.HTML(label="Result")

                error_output = gr.Textbox(
                    label="Errors",
                    visible=True,
                    interactive=False,
                    lines=2
                )

                with gr.Accordion("Debug: Full JSON Response", open=False):
                    json_output = gr.Code(
                        label="Raw JSON",
                        language="json",
                        lines=15
                    )

        # Event handlers
        analyze_btn.click(
            fn=analyze_sheet_music,
            inputs=[image_input, api_key_input],
            outputs=[result_html, json_output, error_output]
        )

        gr.Markdown(
            """
            ---
            **Tips:**
            - Upload clear photos of printed sheet music
            - Works best with short musical phrases
            - The app will provide sensory metaphors to guide your performance
            """
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
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False
    )


if __name__ == "__main__":
    main()
