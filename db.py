import psycopg2
import uuid
from datetime import datetime

def get_connection():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        database="ai_ops_db",
        user="admin",
        password="password"
    )

def create_conversation() -> str:
    """Creates a new conversation and returns its ID."""
    conversation_id = str(uuid.uuid4())
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO conversations (id, created_at) VALUES (%s, %s)",
        (conversation_id, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()
    return conversation_id

def save_message(conversation_id: str, role: str, content: str):
    """Saves a single message to the messages table."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO messages (id, conversation_id, role, content, created_at) VALUES (%s, %s, %s, %s, %s)",
        (str(uuid.uuid4()), conversation_id, role, content, datetime.utcnow())
    )
    conn.commit()
    cur.close()
    conn.close()