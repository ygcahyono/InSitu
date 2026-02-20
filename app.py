"""
InSitu - Personal English Vocabulary Learning Tool
Main Streamlit application.
"""

import streamlit as st
from streamlit_js_eval import streamlit_js_eval
from database import init_db, save_word, get_all_words, search_words, delete_word, get_word_count
from ai_helper import get_word_explanation, refresh_examples, check_api_key
from ocr_helper import extract_text_from_image

# Page configuration
st.set_page_config(
    page_title="InSitu",
    page_icon="📖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for minimal styling
st.markdown("""
<style>
    .word-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 10px 0;
        border-left: 4px solid #4CAF50;
    }
    .definition-text {
        font-size: 1.1em;
        color: #333;
        margin-bottom: 15px;
    }
    .example-item {
        background-color: #fff;
        padding: 10px 15px;
        margin: 5px 0;
        border-radius: 5px;
        border-left: 3px solid #2196F3;
        color: #333;
    }
    .source-context {
        background-color: #fff3cd;
        padding: 10px 15px;
        border-radius: 5px;
        font-style: italic;
        margin-top: 10px;
        color: #856404;
    }
    .text-display {
        background-color: #f5f5f5;
        padding: 20px;
        border-radius: 10px;
        max-height: 300px;
        overflow-y: auto;
        color: #333;
        line-height: 1.8;
        font-size: 1.05em;
        user-select: text;
        cursor: text;
    }
    .stats-box {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 8px;
        text-align: center;
        color: #333;
    }
    .selection-hint {
        background-color: #e8f5e9;
        padding: 10px 15px;
        border-radius: 5px;
        color: #2e7d32;
        font-size: 0.9em;
        margin: 10px 0;
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
if "lookup_triggered" not in st.session_state:
    st.session_state.lookup_triggered = False
if "lookup_counter" not in st.session_state:
    st.session_state.lookup_counter = 0


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
    
    # Examples
    st.markdown("**Examples:**")
    for i, example in enumerate(result["examples"], 1):
        st.markdown(f'<div class="example-item">{i}. {example}</div>', 
                    unsafe_allow_html=True)
    
    # Source context
    if result.get("source_context"):
        st.markdown("**From your text:**")
        st.markdown(f'<div class="source-context">"{result["source_context"]}"</div>', 
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
    
    # Input section - two columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Option A: Paste Text**")
        text_input = st.text_area(
            "Paste text from a letter, email, or document",
            height=200,
            placeholder="Paste your text here...",
            key="text_paste"
        )
        if st.button("Submit Text", key="submit_text"):
            if text_input.strip():
                st.session_state.uploaded_text = text_input.strip()
                st.session_state.word_result = None
                st.rerun()
    
    with col2:
        st.markdown("**Option B: Upload Image**")
        uploaded_file = st.file_uploader(
            "Upload an image (JPG, PNG)",
            type=["jpg", "jpeg", "png"],
            key="image_upload"
        )
        if uploaded_file is not None:
            if st.button("Extract Text", key="extract_text"):
                with st.spinner("Extracting text from image..."):
                    success, result = extract_text_from_image(uploaded_file)
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
        st.markdown(
            '<div class="selection-hint">💡 <strong>Tip:</strong> Highlight any word above, then click "Look Up Selected Word" below</div>',
            unsafe_allow_html=True
        )
        
        # Track text selection via JavaScript.
        # A mouseup listener on the parent document stores the selected text
        # in parent.window._insituSelectedText, which persists across Streamlit
        # reruns (DOM rebuilds don't affect the window object).
        streamlit_js_eval(
            js_expressions="""
            (function() {
                try {
                    var pd = parent.document;
                    var pw = parent.window;
                    if (!pw._insituListenerAdded) {
                        pd.addEventListener('mouseup', function() {
                            try {
                                var s = pd.getSelection().toString().trim();
                                if (s.length > 0) {
                                    pw._insituSelectedText = s;
                                }
                            } catch(e) {}
                        });
                        pw._insituListenerAdded = true;
                    }
                } catch(e) {}
                return 'ready';
            })()
            """,
            key="selection_setup"
        )
        
        # Button row
        col1, col2 = st.columns([1, 3])
        
        with col1:
            if st.button("🗑️ Clear Text", key="clear_text"):
                st.session_state.uploaded_text = ""
                st.session_state.word_result = None
                st.rerun()
        
        # Word lookup section
        st.markdown("---")
        st.markdown("### Look Up a Word")
        
        # Look Up Selected Word button - captures browser selection
        if st.button("🔍 Look Up Selected Word", key="lookup_selected_btn", type="primary"):
            st.session_state.lookup_counter += 1
            st.session_state.lookup_triggered = True
            st.rerun()
        
        # Get selected text from browser if lookup was triggered.
        # Uses a dynamic key so each click creates a fresh streamlit_js_eval
        # component, avoiding stale cached values.
        if st.session_state.lookup_triggered:
            selected_text = streamlit_js_eval(
                js_expressions="(function() { try { return parent.window._insituSelectedText || ''; } catch(e) { return ''; } })()",
                key=f"get_selection_{st.session_state.lookup_counter}"
            )
            
            if selected_text is not None and len(selected_text.strip()) > 0:
                # Clean the selected word (take first word if multiple selected)
                word = selected_text.strip().split()[0].lower()
                # Remove punctuation from start/end
                word = word.strip('.,!?;:"\'-()[]{}')
                
                if word:
                    st.session_state.lookup_triggered = False
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
                    st.session_state.lookup_triggered = False
                    st.warning("Please highlight a word in the text above first, then click the button.")
            elif selected_text is not None:
                # JS executed but no selection was stored
                st.session_state.lookup_triggered = False
                st.warning("Please highlight a word in the text above first, then click the button.")
            # else: selected_text is None means JS hasn't returned yet, wait for next render
        
        st.markdown("---")
        st.caption("Or type a word manually:")
        
        word_input = st.text_input(
            "Type a word you want to understand",
            placeholder="Enter a word...",
            key="word_lookup",
            label_visibility="collapsed"
        )
        
        if st.button("🔍 Look Up", key="lookup_btn"):
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
                # Truncate definition
                definition = word_data['definition'] or ""
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
            st.markdown(f"**Definition:** {word_data['definition']}")
            if word_data.get('source_context'):
                st.markdown(f"**Original context:** _{word_data['source_context']}_")
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
