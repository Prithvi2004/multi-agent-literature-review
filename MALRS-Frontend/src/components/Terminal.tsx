import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  Terminal as TerminalIcon,
  X,
  Minimize2,
  Maximize2,
  Copy,
  Trash2,
  Lock,
  Unlock,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
  raw: string;
}

interface TerminalProps {
  isVisible: boolean;
  onClose: () => void;
}

export function Terminal({ isVisible, onClose }: TerminalProps) {
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [isScrollLocked, setIsScrollLocked] = useState(false);
  const [isMinimized, setIsMinimized] = useState(false);
  const [isConnected, setIsConnected] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const logsContainerRef = useRef<HTMLDivElement>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Auto-scroll to bottom when new logs arrive
  const scrollToBottom = () => {
    if (!isScrollLocked && logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  };

  useEffect(() => {
    scrollToBottom();
  }, [logs, isScrollLocked]);

  // Connect to SSE endpoint - keep connection alive always
  useEffect(() => {
    const connectSSE = () => {
      try {
        const eventSource = new EventSource("http://localhost:5000/api/logs/stream");
        eventSourceRef.current = eventSource;

        eventSource.onopen = () => {
          console.log("SSE connection opened");
          setIsConnected(true);
        };

        eventSource.onmessage = (event) => {
          try {
            const logEntry: LogEntry = JSON.parse(event.data);
            setLogs((prev) => [...prev.slice(-999), logEntry]); // Keep last 1000 logs
          } catch (err) {
            console.error("Error parsing log entry:", err);
          }
        };

        eventSource.onerror = (error) => {
          console.error("SSE error:", error);
          setIsConnected(false);
          eventSource.close();
          
          // Attempt reconnection after 3 seconds
          setTimeout(() => {
            connectSSE();
          }, 3000);
        };
      } catch (error) {
        console.error("Error creating EventSource:", error);
      }
    };

    connectSSE();

    // Cleanup only on unmount, NOT on visibility change
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
        setIsConnected(false);
      }
    };
  }, []); // Empty dependency array - connect once on mount

  const handleClear = () => {
    setLogs([]);
  };

  const handleCopy = () => {
    const logText = logs.map((log) => `[${log.timestamp}] ${log.level}: ${log.raw}`).join("\n");
    navigator.clipboard.writeText(logText);
  };

  const getLevelColor = (level: string) => {
    switch (level.toUpperCase()) {
      case "ERROR":
        return "text-red-400";
      case "WARNING":
        return "text-yellow-400";
      case "INFO":
        return "text-blue-400";
      case "DEBUG":
        return "text-gray-400";
      case "OUTPUT":
        return "text-green-400"; // For print statements and stdout
      default:
        return "text-foreground/80";
    }
  };

  if (!isVisible) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0, y: 20, scale: 0.95 }}
        animate={{ opacity: 1, y: 0, scale: 1 }}
        exit={{ opacity: 0, y: 20, scale: 0.95 }}
        transition={{ duration: 0.3, ease: "easeOut" }}
        className="w-full"
      >
        {/* macOS-style Terminal Window */}
        <div className="relative rounded-lg overflow-hidden glass-card border border-border/50 shadow-2xl">
          {/* Title Bar */}
          <div className="bg-gradient-to-b from-muted/80 to-muted/60 backdrop-blur-xl border-b border-border/40 px-4 py-3 flex items-center justify-between">
            {/* Traffic Lights */}
            <div className="flex items-center gap-2">
              <button
                onClick={onClose}
                className="w-3 h-3 rounded-full bg-red-500 hover:bg-red-600 transition-colors shadow-sm"
                aria-label="Close terminal"
              />
              <button
                onClick={() => setIsMinimized(!isMinimized)}
                className="w-3 h-3 rounded-full bg-yellow-500 hover:bg-yellow-600 transition-colors shadow-sm"
                aria-label="Minimize terminal"
              />
              <button
                className="w-3 h-3 rounded-full bg-green-500 hover:bg-green-600 transition-colors shadow-sm"
                aria-label="Maximize terminal"
              />
            </div>

            {/* Title */}
            <div className="absolute left-1/2 transform -translate-x-1/2 flex items-center gap-2">
              <TerminalIcon className="h-4 w-4 text-foreground/60" />
              <span className="text-sm font-medium text-foreground/80">
                Terminal
              </span>
              {isConnected && (
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
                </span>
              )}
            </div>

            {/* Controls */}
            <div className="flex items-center gap-2">
              <button
                onClick={() => setIsScrollLocked(!isScrollLocked)}
                className="p-1.5 hover:bg-muted/60 rounded transition-colors"
                title={isScrollLocked ? "Unlock scroll" : "Lock scroll"}
              >
                {isScrollLocked ? (
                  <Lock className="h-3.5 w-3.5 text-foreground/60" />
                ) : (
                  <Unlock className="h-3.5 w-3.5 text-foreground/60" />
                )}
              </button>
              <button
                onClick={handleCopy}
                className="p-1.5 hover:bg-muted/60 rounded transition-colors"
                title="Copy all logs"
              >
                <Copy className="h-3.5 w-3.5 text-foreground/60" />
              </button>
              <button
                onClick={handleClear}
                className="p-1.5 hover:bg-muted/60 rounded transition-colors"
                title="Clear terminal"
              >
                <Trash2 className="h-3.5 w-3.5 text-foreground/60" />
              </button>
            </div>
          </div>

          {/* Terminal Content */}
          <motion.div
            initial={false}
            animate={{ height: isMinimized ? 0 : "400px" }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div
              ref={logsContainerRef}
              className="h-full overflow-y-auto bg-black/90 backdrop-blur-xl p-4 font-mono text-sm terminal-scrollbar"
            >
              {logs.length === 0 ? (
                <div className="text-muted-foreground/60 text-center py-8">
                  Waiting for logs...
                </div>
              ) : (
                logs.map((log, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -10 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.2 }}
                    className="mb-1 leading-relaxed"
                  >
                    <span className="text-muted-foreground/60 text-xs">
                      [{log.timestamp}]
                    </span>{" "}
                    <span className={cn("font-semibold", getLevelColor(log.level))}>
                      {log.level}:
                    </span>{" "}
                    <span className="text-foreground/90">{log.raw}</span>
                  </motion.div>
                ))
              )}
              <div ref={logsEndRef} />
            </div>
          </motion.div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
}
