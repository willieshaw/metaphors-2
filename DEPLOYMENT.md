# Deployment Guide

## Deploying to Hugging Face Spaces (FREE)

Hugging Face Spaces is the recommended free hosting platform for this Gradio app. Users will provide their own Anthropic API keys through the UI.

### Prerequisites

- A [Hugging Face](https://huggingface.co/) account (free)
- A GitHub account (to connect your repository)

### Step 1: Prepare Your GitHub Repository

1. Push this code to a GitHub repository:
   ```bash
   git push origin main
   ```

2. Make sure your repository includes:
   - `app.py`
   - `utils.py`
   - `requirements.txt`
   - `README.md`
   - `.gitignore` (to exclude logs and cache)

### Step 2: Create a Hugging Face Space

1. Go to [Hugging Face Spaces](https://huggingface.co/spaces)

2. Click **"Create new Space"**

3. Fill in the details:
   - **Space name**: `sheet-music-metaphor-analyzer` (or your preferred name)
   - **License**: Choose your preferred license (MIT recommended)
   - **Select the Space SDK**: Choose **Gradio**
   - **Space hardware**: Choose **CPU basic** (free)
   - **Visibility**: Public (so others can use it)

4. Click **"Create Space"**

### Step 3: Connect to GitHub

You have two options:

#### Option A: Direct Git Push (Recommended)

1. After creating the Space, you'll see a Git URL like:
   ```
   https://huggingface.co/spaces/YOUR-USERNAME/sheet-music-metaphor-analyzer
   ```

2. Clone the empty Space repository:
   ```bash
   git clone https://huggingface.co/spaces/YOUR-USERNAME/sheet-music-metaphor-analyzer
   cd sheet-music-metaphor-analyzer
   ```

3. Copy your files into this directory:
   ```bash
   cp /path/to/your/app.py .
   cp /path/to/your/utils.py .
   cp /path/to/your/requirements.txt .
   cp /path/to/your/README.md .
   cp /path/to/your/.gitignore .
   ```

4. Commit and push:
   ```bash
   git add .
   git commit -m "Initial deployment"
   git push
   ```

#### Option B: GitHub Sync

1. In your Space settings, click on **"Files and versions"** tab

2. Click **"Add file"** > **"Upload files"**

3. Upload all required files:
   - `app.py`
   - `utils.py`
   - `requirements.txt`
   - `README.md`

4. Commit the changes

### Step 4: Verify Deployment

1. Wait 1-2 minutes for the Space to build and start

2. Your app will be available at:
   ```
   https://huggingface.co/spaces/YOUR-USERNAME/sheet-music-metaphor-analyzer
   ```

3. Test the app:
   - Upload a sheet music image
   - Enter your Anthropic API key
   - Click "Analyze Music"
   - Verify the results appear correctly

### Step 5: Share Your Space

Your Space is now live! Share the URL with others:
```
https://huggingface.co/spaces/YOUR-USERNAME/sheet-music-metaphor-analyzer
```

Users will need their own Anthropic API keys to use the app.

## Alternative Deployment Options

### Railway (Limited Free Tier)

1. Sign up at [Railway](https://railway.app/)
2. Create a new project from GitHub
3. Add a start command: `python app.py`
4. Deploy

### Render (Limited Free Tier)

1. Sign up at [Render](https://render.com/)
2. Create a new Web Service
3. Connect your GitHub repository
4. Set build command: `pip install -r requirements.txt`
5. Set start command: `python app.py`
6. Deploy

## Troubleshooting

### Space Won't Start

- Check the logs in the Space's "Logs" tab
- Verify `requirements.txt` has correct package versions
- Ensure `app.py` has `if __name__ == "__main__": main()`

### Import Errors

- Make sure all files are in the root directory of the Space
- Verify `utils.py` is uploaded
- Check that `requirements.txt` includes all dependencies

### API Key Issues

- The app now requires users to input their own API key
- API keys are not stored or logged
- Users need to get keys from [Anthropic Console](https://console.anthropic.com/)

## Security Notes

- Never commit API keys to the repository
- Users provide their own keys through the UI
- Keys are passed only in-memory and not persisted
- Logs directory is gitignored to prevent accidental data exposure

## Updating Your Deployment

To update your deployed Space:

1. Make changes to your local files
2. Commit changes:
   ```bash
   git add .
   git commit -m "Update: description of changes"
   ```
3. Push to Hugging Face Space:
   ```bash
   git push
   ```

The Space will automatically rebuild and redeploy.

## Cost Considerations

- **Hugging Face Spaces**: Completely free for CPU-based Gradio apps
- **API Usage**: Users pay for their own Anthropic API usage
- **Rate Limits**: Consider Anthropic's rate limits for API usage

## Getting an Anthropic API Key

Users will need to:
1. Go to [Anthropic Console](https://console.anthropic.com/)
2. Sign up or log in
3. Navigate to API Keys section
4. Create a new API key
5. Copy and paste into the app

API keys start with `sk-ant-api-` and should be kept secure.
