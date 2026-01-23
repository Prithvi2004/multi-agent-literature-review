# session_manager.py
"""
Session Management Module for Multi-Agent Literature Review System
Handles saving, loading, listing, and deleting research sessions.
"""

import sqlite3
import json
import logging
from datetime import datetime
from contextlib import contextmanager
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect('sessions.db')
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_sessions_db():
    """Initialize sessions database with schema."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                research_idea TEXT,
                selected_domains TEXT,
                paper_sections TEXT,
                analysis_result TEXT,
                metadata TEXT
            )
        ''')
    logger.info("Sessions database initialized")

def save_session(session_data: Dict[str, Any]) -> str:
    """
    Save a research session to the database.
    
    Args:
        session_data: Dictionary containing session information
        
    Returns:
        session_id: The ID of the saved session
    """
    session_id = session_data.get('id', str(datetime.now().timestamp()))
    session_name = session_data.get('name', f"Session {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    with get_db_connection() as conn:
        conn.execute('''
            INSERT OR REPLACE INTO sessions 
            (id, name, created_at, updated_at, research_idea, selected_domains, 
             paper_sections, analysis_result, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            session_id,
            session_name,
            session_data.get('created_at', datetime.now().isoformat()),
            datetime.now().isoformat(),
            session_data.get('research_idea', ''),
            json.dumps(session_data.get('selected_domains', [])),
            json.dumps(session_data.get('paper_sections', [])),
            json.dumps(session_data.get('analysis_result')),
            json.dumps(session_data.get('metadata', {}))
        ))
    
    logger.info(f"Session saved: {session_id}")
    return session_id

def list_sessions() -> List[Dict[str, Any]]:
    """
    List all saved sessions.
    
    Returns:
        List of session metadata dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.execute('''
            SELECT id, name, created_at, updated_at, metadata
            FROM sessions
            ORDER BY updated_at DESC
        ''')
        sessions = []
        for row in cursor.fetchall():
            sessions.append({
                'id': row['id'],
                'name': row['name'],
                'created_at': row['created_at'],
                'updated_at': row['updated_at'],
                'metadata': json.loads(row['metadata']) if row['metadata'] else {}
            })
    
    return sessions

def load_session(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Load a specific session from the database.
    
    Args:
        session_id: The ID of the session to load
        
    Returns:
        Session data dictionary or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.execute('''
            SELECT * FROM sessions WHERE id = ?
        ''', (session_id,))
        row = cursor.fetchone()
        
        if not row:
            return None
        
        session_data = {
            'id': row['id'],
            'name': row['name'],
            'created_at': row['created_at'],
            'updated_at': row['updated_at'],
            'research_idea': row['research_idea'],
            'selected_domains': json.loads(row['selected_domains']) if row['selected_domains'] else [],
            'paper_sections': json.loads(row['paper_sections']) if row['paper_sections'] else [],
            'analysis_result': json.loads(row['analysis_result']) if row['analysis_result'] and row['analysis_result'] != 'null' else None,
            'metadata': json.loads(row['metadata']) if row['metadata'] else {}
        }
    
    logger.info(f"Session loaded: {session_id}")
    return session_data

def delete_session(session_id: str) -> bool:
    """
    Delete a specific session from the database.
    
    Args:
        session_id: The ID of the session to delete
        
    Returns:
        True if deleted, False if not found
    """
    with get_db_connection() as conn:
        cursor = conn.execute('DELETE FROM sessions WHERE id = ?', (session_id,))
        deleted = cursor.rowcount > 0
    
    if deleted:
        logger.info(f"Session deleted: {session_id}")
    
    return deleted

# Initialize database on module import
init_sessions_db()
