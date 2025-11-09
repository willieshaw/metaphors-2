# Sheet Music Metaphor Analyzer

A minimal web application that analyzes sheet music photos using Claude Vision API and provides poetic, sensory performance guidance through metaphors.

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
   - The main metaphor is displayed prominently
   - Musical elements (mood, gesture, motion) are shown below
   - A list of detailed performance metaphors provides additional guidance
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

2. **API Call**: The image is sent to Claude Vision API with a carefully crafted prompt requesting:
   - Mood description
   - Gesture description
   - Motion description
   - Multiple sensory metaphors
   - One final, concise metaphor

3. **JSON Validation**: The response is validated against a strict schema. If validation fails, the system automatically retries with a stricter prompt

4. **Logging**: All API responses and parsed results are logged to the `./logs` directory with timestamps

## JSON Schema

The application expects responses in the following format:

```json
{
  "mood": "string describing the emotional tone",
  "gesture": "string describing the physical gesture",
  "motion": "string describing the movement quality",
  "metaphors": ["metaphor 1", "metaphor 2", "..."],
  "final_metaphor": "one concise metaphor for overall sound shaping"
}
```

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
