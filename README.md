# Sheet Music Metaphor Analyzer

A minimal web application that analyzes sheet music photos using Claude Vision API and provides poetic, sensory performance guidance through metaphors.

## Deploy to Hugging Face Spaces (FREE)

Want to host this for others to use? Deploy it for free on Hugging Face Spaces!

**[View Deployment Guide →](DEPLOYMENT.md)**

Quick steps:
1. Create a free [Hugging Face](https://huggingface.co/) account
2. Create a new Space with Gradio SDK
3. Upload these files or connect your GitHub repo
4. Set up persistent feedback storage (optional) - **[Setup Guide →](HF_FEEDBACK_SETUP.md)**
5. Share the URL - users provide their own API keys

## Feedback Storage

The app includes a 5-star rating system for user feedback on metaphors. Feedback can be stored:

- **On Hugging Face Spaces**: Set `HF_TOKEN` secret to enable persistent storage to a HF Dataset
- **Locally**: Automatically saves to `./feedback/ratings.csv` (for development/testing)

**[Complete Feedback Setup Guide →](HF_FEEDBACK_SETUP.md)**

## Features

- Upload photos of printed sheet music
- AI-powered analysis using Claude's vision capabilities
- Get sensory and emotional metaphors for performance guidance
- Clean, modern UI with Gradio
- Automatic JSON validation and retry logic
- Comprehensive logging and debugging tools

## Requirements

- Python 3.10 or higher
- Anthropic API key

## Installation

1. Clone or download this repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set your Anthropic API key as an environment variable:
```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

Alternatively, you can enter your API key directly in the web interface.

## Usage

1. Start the application:
```bash
python app.py
```

2. Open your browser and navigate to:
```
http://localhost:7860
```

3. Upload a photo of sheet music

4. Click "Analyze Music" and wait for the results

5. View your metaphorical performance guidance:
   - The final instructional metaphor is displayed prominently
   - Conductor analysis (mood, gesture, motion) provides context
   - Notation insights show what caught the conductor's attention
   - Three instructional metaphors guide your performance approach
   - Expand the "Debug" section to see the raw JSON response

## Project Structure

```
.
├── app.py              # Main Gradio application and Claude API integration
├── utils.py            # JSON validation, parsing, and logging utilities
├── requirements.txt    # Python dependencies
├── README.md          # This file
└── logs/              # Generated log files (created automatically)
```

## How It Works

1. **Image Processing**: Uploaded images are resized to a maximum width of 1400px to optimize API usage

2. **Chain-of-Thought Analysis**: The image is sent to Claude Vision API with a structured prompt that guides the AI through:
   - **Step 1**: Conductor analysis of mood, gesture, and motion
   - **Step 2**: Identification of notable aspects in the notation
   - **Step 3**: Creation of exactly 3 instructional metaphors for the performer
   - **Step 4**: Synthesis into one final, powerful instructional metaphor

3. **JSON Validation**: The response is validated against a strict schema requiring:
   - All conductor analysis fields
   - 2-4 notation detail observations
   - Exactly 3 instructional metaphors (starting with "Play this like...")
   - One final metaphor
   - If validation fails, the system automatically retries with a stricter prompt

4. **Logging**: All API responses and parsed results are logged to the `./logs` directory with timestamps

## JSON Schema

The application expects responses in the following format:

```json
{
  "mood": "string describing the emotional tone",
  "gesture": "string describing the physical conducting gesture",
  "motion": "string describing the movement quality",
  "notation_details": [
    "observation about specific notation element",
    "another observation that influenced interpretation"
  ],
  "instructional_metaphors": [
    "Play this like...",
    "Play this like...",
    "Play this like..."
  ],
  "final_metaphor": "Play this like... (one concise, powerful metaphor)"
}
```

The schema enforces:
- Exactly 3 instructional metaphors
- At least 2 notation detail observations
- All fields must be present and non-empty

## Troubleshooting

**API Key Errors**:
- Ensure `ANTHROPIC_API_KEY` is set in your environment
- Or enter it directly in the web interface

**Module Import Errors**:
- Verify all dependencies are installed: `pip install -r requirements.txt`
- Check Python version: `python --version` (must be 3.10+)

**JSON Parsing Errors**:
- Check the logs directory for detailed error information
- The app automatically retries once if the first response is invalid
- Use the debug panel to inspect raw API responses

## Logs

All analysis sessions are logged to `./logs/` with:
- Timestamped log files
- Raw API responses
- Parsed JSON data
- Error messages (if any)

## License

This project is provided as-is for educational and creative purposes.

## Tips for Best Results

- Use clear, well-lit photos of sheet music
- Focus on short musical phrases (2-8 measures works best)
- Ensure the notation is legible in the photo
- Avoid blurry or low-resolution images
