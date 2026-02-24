"""
InSitu - Personal English Vocabulary Learning Tool
Main Streamlit application.
"""

import streamlit as st
from database import init_db, save_word, get_all_words, search_words, delete_word, get_word_count
from ai_helper import get_word_explanation, refresh_examples, check_api_key, strip_markdown
from ocr_helper import extract_text_from_image
from video_helper import extract_subtitles_from_video

# Page configuration
st.set_page_config(
    page_title="InSitu",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS — uses rgba() semi-transparent backgrounds that adapt
# automatically to both light and dark Streamlit themes.
st.markdown("""
<style>
    .word-card {
        background: rgba(76, 175, 80, 0.08);
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    .definition-text {
        font-size: 1.1em;
        line-height: 1.6;
        margin-bottom: 15px;
    }
    .example-item {
        background: rgba(33, 150, 243, 0.08);
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 5px;
        border-left: 3px solid #2196F3;
    }
    .source-context {
        background: rgba(255, 193, 7, 0.1);
        padding: 10px 15px;
        border-radius: 5px;
        font-style: italic;
        margin-top: 10px;
        border-left: 3px solid #ffc107;
    }
    .text-display {
        background: rgba(128, 128, 128, 0.1);
        padding: 20px;
        border-radius: 10px;
        max-height: 300px;
        overflow-y: auto;
        line-height: 1.8;
        font-size: 1.05em;
        user-select: text;
        cursor: text;
    }
    .stats-box {
        background: rgba(33, 150, 243, 0.08);
        padding: 15px;
        border-radius: 8px;
        text-align: center;
    }
    /* Tab styling for input method selector */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 20px;
        font-size: 1em;
    }
</style>
""", unsafe_allow_html=True)

# Initialize database
init_db()

# Initialize session state
if "uploaded_text" not in st.session_state:
    st.session_state.uploaded_text = ""
if "current_word" not in st.session_state:
    st.session_state.current_word = ""
if "word_result" not in st.session_state:
    st.session_state.word_result = None
if "page" not in st.session_state:
    st.session_state.page = "learn"


def render_sidebar():
    """Render the sidebar navigation."""
    with st.sidebar:
        st.title("📖 InSitu")
        st.caption("*Learn from the words you encounter in real life*")
        
        st.divider()
        
        # Navigation
        if st.button("📖 Learn", use_container_width=True, 
                    type="primary" if st.session_state.page == "learn" else "secondary"):
            st.session_state.page = "learn"
            st.rerun()
            
        if st.button("📚 Vocab Bank", use_container_width=True,
                    type="primary" if st.session_state.page == "vocab" else "secondary"):
            st.session_state.page = "vocab"
            st.rerun()
        
        st.divider()
        
        # Word count
        word_count = get_word_count()
        st.metric("Words Saved", word_count)


def render_word_card(word: str, result: dict):
    """Render the word explanation card."""
    st.markdown("---")
    st.subheader(f"📝 {word.capitalize()}")
    
    # Definition
    st.markdown("**Definition:**")
    st.markdown(f'<div class="definition-text">{result["definition"]}</div>', 
                unsafe_allow_html=True)
    
    # Source context
    if result.get("source_context"):
        st.markdown("**From your text:**")
        st.markdown(f'<div class="source-context">"{result["source_context"]}"</div>', 
                    unsafe_allow_html=True)
    
    # Examples
    st.markdown("**Examples:**")
    for i, example in enumerate(result["examples"], 1):
        st.markdown(f'<div class="example-item">{i}. {example}</div>', 
                    unsafe_allow_html=True)
    
    # Refresh examples button only (Save is automatic now)
    if st.button("🔄 Refresh Examples", key="refresh_btn"):
        with st.spinner("Generating new examples..."):
            success, new_examples = refresh_examples(word, result["definition"])
            if success:
                st.session_state.word_result["examples"] = new_examples
                st.rerun()
            else:
                st.error(new_examples)


def render_learn_page():
    """Render the main learning page."""
    st.header("📖 Learn New Words")
    
    # Check API key
    api_ok, api_msg = check_api_key()
    if not api_ok:
        st.error(api_msg)
        st.info("Create a `.env` file in the app directory with your API key:\n```\nANTHROPIC_API_KEY=your_key_here\n```")
        return
    
    st.markdown("Upload text from documents you encounter in daily life, then look up words you want to understand.")
    
    # Input section - horizontal tabs
    tab_text, tab_image, tab_video = st.tabs([
        "📝 Paste Text",
        "🖼️ Upload Image",
        "🎬 Upload Video",
    ])
    
    with tab_text:
        st.markdown("")
        text_input = st.text_area(
            "Paste text from a letter, email, or document",
            height=200,
            placeholder="Paste your text here...",
            key="text_paste"
        )
        if st.button("Submit Text", key="submit_text", type="primary"):
            if text_input.strip():
                st.session_state.uploaded_text = text_input.strip()
                st.session_state.word_result = None
                st.rerun()
    
    with tab_image:
        st.markdown("")
        uploaded_image = st.file_uploader(
            "Upload an image of a document, letter, or article",
            type=["jpg", "jpeg", "png"],
            key="image_upload"
        )
        if uploaded_image is not None:
            st.image(uploaded_image, caption="Uploaded image", use_container_width=True)
            if st.button("Extract Text from Image", key="extract_text", type="primary"):
                with st.spinner("Extracting text from image..."):
                    success, result = extract_text_from_image(uploaded_image)
                    if success:
                        st.session_state.uploaded_text = result
                        st.session_state.word_result = None
                        st.rerun()
                    else:
                        st.error(result)
    
    with tab_video:
        st.markdown("")
        uploaded_video = st.file_uploader(
            "Upload a video of a speech, lecture, or conversation",
            type=["mp4", "mov", "avi", "mkv", "webm"],
            key="video_upload"
        )
        if uploaded_video is not None:
            st.video(uploaded_video)
            if st.button("Extract Subtitles", key="extract_subtitles", type="primary"):
                with st.spinner("Extracting audio and transcribing speech... This may take a few minutes depending on video length."):
                    success, result = extract_subtitles_from_video(uploaded_video)
                    if success:
                        st.session_state.uploaded_text = result
                        st.session_state.word_result = None
                        st.rerun()
                    else:
                        st.error(result)
    
    # Display uploaded/extracted text
    if st.session_state.uploaded_text:
        st.markdown("---")
        st.markdown("**Your Text:**")
        
        # Display text in a selectable container
        st.markdown(
            f'<div class="text-display">{st.session_state.uploaded_text}</div>', 
            unsafe_allow_html=True
        )
        
        # Hint for user
        st.caption("Type any word from the text above to look it up.")
        
        # Clear button
        if st.button("🗑️ Clear Text", key="clear_text"):
            st.session_state.uploaded_text = ""
            st.session_state.word_result = None
            st.rerun()
        
        # Word lookup section
        st.markdown("---")
        st.markdown("### Look Up a Word")
        
        word_input = st.text_input(
            "Type a word you want to understand",
            placeholder="Enter a word from the text...",
            key="word_lookup",
            label_visibility="collapsed"
        )
        
        if st.button("🔍 Look Up", key="lookup_btn", type="primary"):
            if word_input.strip():
                word = word_input.strip().lower()
                st.session_state.current_word = word
                
                with st.spinner(f"Looking up '{word}'..."):
                    success, result = get_word_explanation(
                        word,
                        st.session_state.uploaded_text
                    )
                    
                    if success:
                        st.session_state.word_result = result
                        
                        # Auto-save to vocab bank
                        save_success, save_msg = save_word(
                            word=word,
                            definition=result["definition"],
                            source_context=result.get("source_context")
                        )
                        if save_success:
                            st.toast(f"✅ '{word}' saved to your vocab bank!")
                        else:
                            st.toast(f"ℹ️ {save_msg}")
                        st.rerun()
                    else:
                        st.error(result)
                        st.session_state.word_result = None
            else:
                st.warning("Please type a word to look up.")
        
        # Display word result
        if st.session_state.word_result:
            render_word_card(st.session_state.current_word, st.session_state.word_result)


def render_vocab_bank_page():
    """Render the vocabulary bank page."""
    st.header("📚 Vocab Bank")
    
    # Stats
    word_count = get_word_count()
    st.markdown(f'<div class="stats-box">📚 You have <strong>{word_count}</strong> words in your vocab bank</div>', 
                unsafe_allow_html=True)
    
    if word_count == 0:
        st.info("Your vocab bank is empty. Start learning words from the Learn page!")
        return
    
    st.markdown("---")
    
    # Search/filter
    search_query = st.text_input("🔍 Search words", placeholder="Type to filter...", key="vocab_search")
    
    # Get words
    if search_query:
        words = search_words(search_query)
    else:
        words = get_all_words()
    
    if not words:
        st.info("No words found matching your search.")
        return
    
    # Display words in a table-like format
    for word_data in words:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 4, 2, 1, 1])
            
            with col1:
                st.markdown(f"**{word_data['word'].capitalize()}**")
            
            with col2:
                # Truncate definition (strip markdown for clean display)
                definition = strip_markdown(word_data['definition'] or "")
                truncated = definition[:80] + "..." if len(definition) > 80 else definition
                st.markdown(truncated)
            
            with col3:
                # Format date
                date_str = word_data['date_added']
                if date_str:
                    try:
                        date_display = date_str.split()[0]  # Just the date part
                    except (AttributeError, IndexError):
                        date_display = str(date_str)
                else:
                    date_display = "N/A"
                st.caption(f"Added: {date_display}")
            
            with col4:
                st.caption(f"Reviews: {word_data['review_count']}")
            
            with col5:
                if st.button("🗑️", key=f"delete_{word_data['id']}", help="Delete word"):
                    success, message = delete_word(word_data['id'])
                    if success:
                        st.toast(f"✅ Word deleted")
                        st.rerun()
                    else:
                        st.error(message)
            
            st.divider()
    
    # Expandable details for each word
    st.markdown("---")
    st.markdown("### Word Details")
    st.caption("Click on a word below to see full details")
    
    for word_data in words:
        with st.expander(f"📝 {word_data['word'].capitalize()}"):
            clean_def = strip_markdown(word_data['definition'] or "")
            st.markdown(f"**Definition:** {clean_def}")
            if word_data.get('source_context'):
                clean_ctx = strip_markdown(word_data['source_context'])
                st.markdown(f"**Original context:** {clean_ctx}")
            st.caption(f"Status: {word_data['status']} | Reviews: {word_data['review_count']} | Next review: {word_data['next_review_date']}")


def main():
    """Main application entry point."""
    render_sidebar()
    
    if st.session_state.page == "learn":
        render_learn_page()
    elif st.session_state.page == "vocab":
        render_vocab_bank_page()


if __name__ == "__main__":
    main()
