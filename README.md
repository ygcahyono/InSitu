# InSitu

**Learn from the words you encounter in real life**

InSitu is a personal English vocabulary learning tool that helps non-native English speakers learn words from documents they encounter in daily life - letters, emails, notices, and more.

## Features

- **Text Upload**: Paste text from any document you're reading
- **Image OCR**: Upload images of documents and automatically extract text
- **AI-Powered Definitions**: Get clear, friendly explanations with UK/London context examples
- **Vocab Bank**: Save words for later review with spaced repetition tracking

## Prerequisites

### Python

- Python 3.10 or higher

### Tesseract OCR (for image text extraction)

**macOS (using Homebrew):**
```bash
brew install tesseract
```

To verify installation:
```bash
tesseract --version
```

### Anthropic API Key

You'll need an API key from [Anthropic](https://console.anthropic.com/) to use the AI features.

## Setup

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd insitu
```

### 2. Create a virtual environment

```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure your API key

Copy the example environment file and add your API key:

```bash
cp .env.example .env
```

Edit `.env` and replace `your_api_key_here` with your actual Anthropic API key:

```
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx
```

### 5. Run the app

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Usage

### Learning Words

1. Navigate to **📖 Learn** in the sidebar
2. Either:
   - **Paste text** from a document into the text area, or
   - **Upload an image** (JPG/PNG) of a document
3. Click Submit/Extract to load the text
4. Type any word you want to understand in the lookup field
5. Review the definition and UK-context examples
6. Click **💾 Save Word** to add it to your vocab bank
7. Click **🔄 Refresh Examples** to get different example sentences

### Vocab Bank

1. Navigate to **📚 Vocab Bank** in the sidebar
2. View all your saved words with definitions
3. Use the search box to filter words
4. Click the expand arrow to see full details
5. Use the 🗑️ button to delete words you no longer need

## Deploying to Streamlit Cloud

1. Push your code to a GitHub repository
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Click "New app" and connect your GitHub repository
4. Select `app.py` as the main file
5. Add your `ANTHROPIC_API_KEY` in the "Secrets" section:
   ```
   ANTHROPIC_API_KEY = "your-api-key-here"
   ```
6. Click "Deploy"

**Note**: The SQLite database won't persist on Streamlit Cloud's ephemeral filesystem. For production use, consider migrating to a cloud database.

## Project Structure

```
insitu/
├── app.py              # Main Streamlit application
├── database.py         # SQLite database operations
├── ai_helper.py        # Claude API integration
├── ocr_helper.py       # Image text extraction (OCR)
├── requirements.txt    # Python dependencies
├── .env.example        # Environment template
├── .env                # Your API key (not committed)
├── vocab.db            # SQLite database (created on first run)
└── README.md           # This file
```

## License

MIT
