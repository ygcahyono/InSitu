# InSitu

**Learn vocabulary from the documents you actually read.**

InSitu is a personal vocabulary learning tool for non-native English speakers. Paste text from a real document — a lease, a bank letter, a work email — look up words you don't know, and get AI-powered definitions in the context you found them. Every word is saved to a personal vocab bank for future review.

Everything runs locally. No account, no cloud database, no tracking.

## How It Works

1. **Paste text** from any document, or **upload a photo** of a physical document (OCR extracts the text)
2. **Type a word** you want to understand and click Look Up
3. Get a **plain-language definition**, the **sentence from your text** where it appeared, and **example sentences**
4. The word is **automatically saved** to your vocab bank

## Tech Stack

- **Streamlit** — web UI
- **Claude AI** (Anthropic) — contextual word definitions and examples
- **SQLite** — local vocab bank storage
- **Tesseract OCR** — text extraction from images

## Setup

### Prerequisites

- Python 3.10+
- [Tesseract OCR](https://github.com/tesseract-ocr/tesseract) (`brew install tesseract` on macOS)
- [Anthropic API key](https://console.anthropic.com/)

### Install and run

```bash
git clone https://github.com/ygcahyono/InSitu.git
cd InSitu
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file with your API key:

```
ANTHROPIC_API_KEY=your-key-here
```

Run the app:

```bash
streamlit run app.py
```

Opens at `http://localhost:8501`.

## Project Structure

```
InSitu/
├── app.py              # Main Streamlit application
├── ai_helper.py        # Claude API integration
├── database.py         # SQLite database operations
├── ocr_helper.py       # Image text extraction (OCR)
├── requirements.txt    # Python dependencies
└── .env.example        # Environment template
```

## License

MIT
