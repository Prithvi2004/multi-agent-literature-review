/**
 * Session Persistence Hook
 * Provides auto-save functionality and session management using IndexedDB
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { ResearchState } from './useResearchState';

const DB_NAME = 'malrs_sessions';
const DB_VERSION = 1;
const STORE_NAME = 'sessions';
const AUTO_SAVE_INTERVAL = 30000; // 30 seconds

interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
  research_idea: string;
  selected_domains: string[];
  paper_sections: any[];
  analysis_result: any | null;
  metadata: {
    auto_saved?: boolean;
    [key: string]: any;
  };
}

/**
 * Initialize IndexedDB database
 */
const initDB = (): Promise<IDBDatabase> => {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);

    request.onerror = () => reject(request.error);
    request.onsuccess = () => resolve(request.result);

    request.onupgradeneeded = (event) => {
      const db = (event.target as IDBOpenDBRequest).result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        const objectStore = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        objectStore.createIndex('updated_at', 'updated_at', { unique: false });
        objectStore.createIndex('name', 'name', { unique: false });
      }
    };
  });
};

/**
 * Save session to IndexedDB
 */
const saveToIndexedDB = async (session: Session): Promise<void> => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.put(session);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

/**
 * Load session from IndexedDB
 */
const loadFromIndexedDB = async (sessionId: string): Promise<Session | null> => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.get(sessionId);

    request.onsuccess = () => resolve(request.result || null);
    request.onerror = () => reject(request.error);
  });
};

/**
 * List all sessions from IndexedDB
 */
const listFromIndexedDB = async (): Promise<Session[]> => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readonly');
    const store = transaction.objectStore(STORE_NAME);
    const index = store.index('updated_at');
    const request = index.openCursor(null, 'prev'); // Descending order
    const sessions: Session[] = [];

    request.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest).result;
      if (cursor) {
        sessions.push(cursor.value);
        cursor.continue();
      } else {
        resolve(sessions);
      }
    };

    request.onerror = () => reject(request.error);
  });
};

/**
 * Delete session from IndexedDB
 */
const deleteFromIndexedDB = async (sessionId: string): Promise<void> => {
  const db = await initDB();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction([STORE_NAME], 'readwrite');
    const store = transaction.objectStore(STORE_NAME);
    const request = store.delete(sessionId);

    request.onsuccess = () => resolve();
    request.onerror = () => reject(request.error);
  });
};

/**
 * Session Persistence Hook
 */
export function useSessionPersistence(state: ResearchState) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [currentSessionId, setCurrentSessionId] = useState<string | null>(null);
  const [isAutoSaveEnabled, setIsAutoSaveEnabled] = useState(true);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const autoSaveTimerRef = useRef<NodeJS.Timeout | null>(null);

  /**
   * Save current state as a session
   */
  const saveSession = useCallback(async (sessionName?: string, isAutoSave = false) => {
    try {
      const sessionId = currentSessionId || `session_${Date.now()}`;
      const now = new Date().toISOString();

      const session: Session = {
        id: sessionId,
        name: sessionName || `Session ${new Date().toLocaleString()}`,
        created_at: currentSessionId ? (await loadFromIndexedDB(sessionId))?.created_at || now : now,
        updated_at: now,
        research_idea: state.researchIdea,
        selected_domains: state.selectedDomains,
        paper_sections: state.paperSections,
        analysis_result: state.analysisResult,
        metadata: {
          auto_saved: isAutoSave,
          sections_count: state.paperSections.length,
          domains_count: state.selectedDomains.length,
          has_analysis: state.analysisResult !== null,
        },
      };

      // Save to IndexedDB
      await saveToIndexedDB(session);

      // Also sync to backend if available
      try {
        const response = await fetch('http://localhost:5000/api/sessions/save', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(session),
        });
        if (!response.ok) {
          console.warn('Failed to sync session to backend');
        }
      } catch (error) {
        console.warn('Backend not available, session saved locally only');
      }

      setCurrentSessionId(sessionId);
      setLastSaved(new Date());
      await refreshSessionList();

      return sessionId;
    } catch (error) {
      console.error('Error saving session:', error);
      throw error;
    }
  }, [state, currentSessionId]);

  /**
   * Load a session by ID
   */
  const loadSession = useCallback(async (sessionId: string) => {
    try {
      // Try loading from IndexedDB first
      let session = await loadFromIndexedDB(sessionId);

      // If not found locally, try backend
      if (!session) {
        try {
          const response = await fetch(`http://localhost:5000/api/sessions/${sessionId}`);
          if (response.ok) {
            const data = await response.json();
            session = data.session;
            // Save to IndexedDB for offline access
            if (session) {
              await saveToIndexedDB(session);
            }
          }
        } catch (error) {
          console.warn('Backend not available');
        }
      }

      if (session) {
        setCurrentSessionId(sessionId);
        return session;
      }

      return null;
    } catch (error) {
      console.error('Error loading session:', error);
      throw error;
    }
  }, []);

  /**
   * Delete a session
   */
  const deleteSession = useCallback(async (sessionId: string) => {
    try {
      // Delete from IndexedDB
      await deleteFromIndexedDB(sessionId);

      // Also delete from backend
      try {
        await fetch(`http://localhost:5000/api/sessions/${sessionId}`, {
          method: 'DELETE',
        });
      } catch (error) {
        console.warn('Backend not available');
      }

      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
      }

      await refreshSessionList();
    } catch (error) {
      console.error('Error deleting session:', error);
      throw error;
    }
  }, [currentSessionId]);

  /**
   * Refresh the list of sessions
   */
  const refreshSessionList = useCallback(async () => {
    try {
      const localSessions = await listFromIndexedDB();
      setSessions(localSessions);
    } catch (error) {
      console.error('Error refreshing session list:', error);
    }
  }, []);

  /**
   * Create a new session (clear current)
   */
  const newSession = useCallback(() => {
    setCurrentSessionId(null);
    setLastSaved(null);
  }, []);

  /**
   * Auto-save functionality
   */
  useEffect(() => {
    if (!isAutoSaveEnabled) return;

    // Clear existing timer
    if (autoSaveTimerRef.current) {
      clearTimeout(autoSaveTimerRef.current);
    }

    // Set up auto-save timer
    autoSaveTimerRef.current = setTimeout(() => {
      // Only auto-save if there's content
      if (state.paperSections.length > 0 || state.researchIdea.trim()) {
        saveSession(undefined, true).catch(console.error);
      }
    }, AUTO_SAVE_INTERVAL);

    return () => {
      if (autoSaveTimerRef.current) {
        clearTimeout(autoSaveTimerRef.current);
      }
    };
  }, [state, isAutoSaveEnabled, saveSession]);

  /**
   * Load sessions on mount
   */
  useEffect(() => {
    refreshSessionList();
  }, [refreshSessionList]);

  /**
   * Attempt to restore last session on mount
   */
  useEffect(() => {
    const restoreLastSession = async () => {
      const lastSessionId = localStorage.getItem('last_session_id');
      if (lastSessionId) {
        try {
          const session = await loadSession(lastSessionId);
          if (session) {
            // Session loaded successfully
            console.log('Restored last session:', lastSessionId);
          }
        } catch (error) {
          console.error('Failed to restore last session:', error);
        }
      }
    };

    restoreLastSession();
  }, []); // Run once on mount

  /**
   * Save current session ID to localStorage
   */
  useEffect(() => {
    if (currentSessionId) {
      localStorage.setItem('last_session_id', currentSessionId);
    } else {
      localStorage.removeItem('last_session_id');
    }
  }, [currentSessionId]);

  return {
    sessions,
    currentSessionId,
    lastSaved,
    isAutoSaveEnabled,
    setIsAutoSaveEnabled,
    saveSession,
    loadSession,
    deleteSession,
    newSession,
    refreshSessionList,
  };
}
