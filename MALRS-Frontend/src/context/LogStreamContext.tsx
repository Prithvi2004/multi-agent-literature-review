import React, { createContext, useContext, useEffect, useState, useRef } from 'react';

export interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  raw: string;
}

interface LogStreamContextType {
  logs: LogEntry[];
  isConnected: boolean;
  clearLogs: () => void;
}

const LogStreamContext = createContext<LogStreamContextType | undefined>(undefined);

export function LogStreamProvider({ children }: { children: React.ReactNode }) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    let retryTimeout: NodeJS.Timeout;

    const connectSSE = () => {
      // If already connected or connecting, do nothing
      if (eventSourceRef.current?.readyState === EventSource.OPEN || 
          eventSourceRef.current?.readyState === EventSource.CONNECTING) {
        return;
      }

      try {
        const eventSource = new EventSource("/api/logs/stream");
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          console.log("[LogStream] SSE connection opened");
          setIsConnected(true);
        };

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            // Handle keep-alive or empty messages if any
            if (!data || (data.message === "keep-alive")) return;
            
            setLogs((prev) => [...prev.slice(-999), data]); 
          } catch (err) {
            console.error("[LogStream] Error parsing log entry:", err);
          }
        };

        eventSource.onerror = (error) => {
          console.error("[LogStream] SSE error:", error);
          setIsConnected(false);
          eventSource.close();
          eventSourceRef.current = null;
          
          // Attempt reconnection with exponential backoff or constant delay
          retryTimeout = setTimeout(() => {
             console.log("[LogStream] Attempting reconnection...");
             connectSSE();
          }, 3000);
        };
      } catch (error) {
        console.error("[LogStream] Error creating EventSource:", error);
      }
    };

    connectSSE();

    return () => {
      if (retryTimeout) clearTimeout(retryTimeout);
      if (eventSourceRef.current) {
        console.log("[LogStream] Closing SSE connection");
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setIsConnected(false);
      }
    };
  }, []);

  const clearLogs = () => setLogs([]);

  return (
    <LogStreamContext.Provider value={{ logs, isConnected, clearLogs }}>
      {children}
    </LogStreamContext.Provider>
  );
}

export function useLogStream() {
  const context = useContext(LogStreamContext);
  if (context === undefined) {
    throw new Error('useLogStream must be used within a LogStreamProvider');
  }
  return context;
}
