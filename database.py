"""
Database module for InSitu vocabulary app.
Handles SQLite connection and CRUD operations for the vocab bank.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

DATABASE_PATH = Path(__file__).parent / "vocab.db"


def get_connection():
    """Get a database connection with row factory enabled."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Initialize the database with the words table."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS words (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            word TEXT NOT NULL UNIQUE,
            definition TEXT,
            source_context TEXT,
            date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            next_review_date DATE DEFAULT (DATE('now', '+1 day')),
            review_count INTEGER DEFAULT 0,
            ease_factor REAL DEFAULT 2.5,
            status TEXT DEFAULT 'learning'
        )
    """)
    
    conn.commit()
    conn.close()


def word_exists(word: str) -> bool:
    """Check if a word already exists in the database (case-insensitive)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT 1 FROM words WHERE LOWER(word) = LOWER(?) LIMIT 1",
        (word,)
    )
    exists = cursor.fetchone() is not None
    
    conn.close()
    return exists


def save_word(word: str, definition: str, source_context: str | None = None) -> tuple[bool, str]:
    """
    Save a word to the vocab bank.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    if word_exists(word):
        return False, "This word is already in your vocab bank"
    
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO words (word, definition, source_context)
            VALUES (?, ?, ?)
            """,
            (word.lower(), definition, source_context)
        )
        conn.commit()
        return True, f"'{word}' saved to your vocab bank!"
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def get_all_words() -> list[dict]:
    """Get all words from the vocab bank."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT id, word, definition, source_context, date_added, 
               next_review_date, review_count, ease_factor, status
        FROM words
        ORDER BY date_added DESC
    """)
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def search_words(query: str) -> list[dict]:
    """Search words by partial match (case-insensitive)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        """
        SELECT id, word, definition, source_context, date_added,
               next_review_date, review_count, ease_factor, status
        FROM words
        WHERE LOWER(word) LIKE LOWER(?)
        ORDER BY date_added DESC
        """,
        (f"%{query}%",)
    )
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]


def delete_word(word_id: int) -> tuple[bool, str]:
    """
    Delete a word from the vocab bank.
    
    Returns:
        tuple: (success: bool, message: str)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM words WHERE id = ?", (word_id,))
        conn.commit()
        
        if cursor.rowcount > 0:
            return True, "Word deleted successfully"
        else:
            return False, "Word not found"
    except sqlite3.Error as e:
        return False, f"Database error: {str(e)}"
    finally:
        conn.close()


def get_word_count() -> int:
    """Get the total number of words in the vocab bank."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM words")
    count = cursor.fetchone()[0]
    
    conn.close()
    return count
