# Hugging Face Feedback Setup Guide

This guide explains how to set up persistent feedback storage using Hugging Face Datasets.

## Why Use Hugging Face Datasets?

- ✅ **Free and persistent** - Feedback survives Space restarts
- ✅ **Easy to view** - Browse feedback directly on Hugging Face
- ✅ **Easy to download** - Export to CSV anytime
- ✅ **Version controlled** - All changes tracked with git
- ✅ **No database needed** - Simple file-based storage

## Setup Instructions

### 1. Create a Hugging Face Token

1. Go to [Hugging Face Settings > Tokens](https://huggingface.co/settings/tokens)
2. Click **"New token"**
3. Name it something like `sheet-music-feedback`
4. Set permissions to **"Write"** (needed to create/update datasets)
5. Click **"Generate token"**
6. **Copy the token** - you'll need it in the next step

### 2. Add Token to Your Space (For Deployment)

If deploying to Hugging Face Spaces:

1. Go to your Space settings
2. Click on **"Variables and secrets"**
3. Add a new secret:
   - **Name**: `HF_TOKEN`
   - **Value**: Paste your token from step 1
4. Click **"Save"**

### 3. (Optional) Customize Dataset Name

By default, feedback is saved to a dataset called `{your-username}/sheet-music-feedback`.

To use a different name:

1. In your Space settings, add another secret:
   - **Name**: `HF_DATASET_NAME`
   - **Value**: Your custom dataset name (e.g., `my-music-feedback`)

## How It Works

### Automatic Dataset Creation

The first time someone submits feedback, the app will:
1. Create a new public dataset on your HF account
2. Upload the first feedback entry as `feedback.csv`
3. Make it publicly viewable (but only you can edit it)

### Viewing Feedback

1. Go to https://huggingface.co/datasets/{your-username}/sheet-music-feedback
2. Click on the `feedback.csv` file
3. You can view, download, or analyze the data

### Downloading Feedback

**Option 1: Direct Download**
- Go to your dataset page
- Click `feedback.csv`
- Click the download button

**Option 2: Using Python**
```python
from huggingface_hub import hf_hub_download

file = hf_hub_download(
    repo_id="your-username/sheet-music-feedback",
    filename="feedback.csv",
    repo_type="dataset"
)

import pandas as pd
df = pd.read_csv(file)
print(df)
```

**Option 3: Git Clone**
```bash
git clone https://huggingface.co/datasets/your-username/sheet-music-feedback
cd sheet-music-feedback
cat feedback.csv
```

## Data Schema

Each feedback entry contains:

| Column | Description | Example |
|--------|-------------|---------|
| `timestamp` | When feedback was submitted | `2025-01-12T10:30:45.123456` |
| `rating` | User rating (1-5) | `4` |
| `final_metaphor` | The metaphor that was rated | `Play this like morning mist` |
| `mood` | Conductor's mood analysis | `calm and reflective` |
| `gesture` | Conductor's gesture description | `smooth, flowing movements` |
| `motion` | Motion quality description | `legato, sustained` |
| `instructional_metaphors` | All 3 metaphors (pipe-separated) | `Meta1 \| Meta2 \| Meta3` |
| `notation_details` | What conductor noticed (pipe-separated) | `Detail1 \| Detail2` |

## Local Development

When running locally **without** `HF_TOKEN`:
- Feedback automatically saves to `./feedback/ratings.csv`
- This is gitignored and won't be committed
- Perfect for testing

When running locally **with** `HF_TOKEN`:
- Set the environment variable: `export HF_TOKEN=your_token_here`
- Feedback will save to your HF dataset
- Useful for testing the HF integration

## Troubleshooting

### "Failed to save to HF dataset, falling back to CSV"

This warning means the app couldn't save to Hugging Face and used local CSV instead. Common causes:

1. **No HF_TOKEN set** - Add it to your Space secrets
2. **Invalid token** - Generate a new token with Write permissions
3. **Network issues** - Temporary HF outage, will retry next time
4. **Quota exceeded** - Free tier has limits, upgrade if needed

### Dataset not appearing

1. Check your HF profile: https://huggingface.co/{your-username}
2. Click "Datasets" tab
3. Look for `sheet-music-feedback`
4. If not there, check the logs for errors

### Permission errors

Make sure your token has **Write** permissions. Read-only tokens won't work.

## Privacy Considerations

**Public Dataset (Default)**
- Anyone can view the feedback
- Good for transparency
- Users should know ratings are public

**Private Dataset (Optional)**
To make the dataset private:

1. Go to your dataset page
2. Click "Settings"
3. Under "Visibility", select "Private"
4. Click "Update"

Note: Only you (and those you grant access) can view private datasets.

## Best Practices

1. **Regular Downloads** - Download feedback CSV weekly for backup
2. **Monitor Dataset** - Check the dataset page occasionally for issues
3. **Review Ratings** - Analyze feedback to improve metaphors
4. **Token Security** - Never commit HF_TOKEN to git

## Example: Analyzing Feedback

```python
from huggingface_hub import hf_hub_download
import pandas as pd
import matplotlib.pyplot as plt

# Download feedback
file = hf_hub_download(
    repo_id="your-username/sheet-music-feedback",
    filename="feedback.csv",
    repo_type="dataset"
)

# Load and analyze
df = pd.read_csv(file)

# Average rating
print(f"Average rating: {df['rating'].mean():.2f}")

# Rating distribution
df['rating'].value_counts().sort_index().plot(kind='bar')
plt.title('Feedback Distribution')
plt.xlabel('Rating')
plt.ylabel('Count')
plt.show()

# Best-rated metaphors
top_rated = df[df['rating'] >= 4]['final_metaphor'].value_counts()
print("\nMost helpful metaphors:")
print(top_rated.head())
```

## Support

If you encounter issues:

1. Check the Space logs for error messages
2. Verify your HF_TOKEN is set correctly
3. Ensure the token has Write permissions
4. Check [Hugging Face Status](https://status.huggingface.co/) for outages
