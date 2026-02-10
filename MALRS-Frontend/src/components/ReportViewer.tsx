import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { FileText, ChevronDown, ChevronUp, Loader2, Download, Copy } from "lucide-react";
import { cn } from "@/lib/utils";

interface ReportViewerProps {
  title: string;
  endpoint: string;
  isAnalyzing: boolean;
  hasAnalysisCompleted: boolean; // New prop to track if analysis ever completed
  type: "markdown" | "text";
  icon?: React.ReactNode;
  preloadedContent?: string;
}

export function ReportViewer({
  title,
  endpoint,
  isAnalyzing,
  hasAnalysisCompleted,
  type,
  icon,
  preloadedContent,
}: ReportViewerProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [content, setContent] = useState<string>("");
  const [status, setStatus] = useState<"idle" | "pending" | "loading" | "success" | "error">("idle");
  const [errorMessage, setErrorMessage] = useState("");

  // Determine current stage
  const getStage = () => {
    if (!hasAnalysisCompleted && !isAnalyzing) return "idle"; // Yet to execute
    if (isAnalyzing) return "analyzing"; // In progress
    if (hasAnalysisCompleted) return "completed"; // Analysis completed
    return "idle";
  };

  // Fetch content automatically when analysis completes
  useEffect(() => {
    if (preloadedContent) {
      setContent(preloadedContent);
      setStatus("success");
      return;
    }

    if (!hasAnalysisCompleted) {
      if (status !== "idle") {
        setStatus("idle");
        setContent("");
      }
      return;
    }

    // Don't re-fetch if already successful or currently loading (unless polling)
    if (status === "success" || status === "loading") return;

    const fetchContent = async () => {
      try {
        // Only set loading if initial fetch (not polling) to avoid flickering
        if (status === "idle") setStatus("loading");
        
        const response = await fetch(endpoint);
        const data = await response.json();

        if (response.status === 202) {
          // Still processing
          setStatus("pending");
        } else if (response.ok) {
          setStatus("success");
          setContent(data.content || "");
        } else {
          setStatus("error");
          setErrorMessage(data.message || "Failed to load content");
        }
      } catch (error) {
        setStatus("error");
        setErrorMessage(error instanceof Error ? error.message : "Failed to fetch content");
      }
    };

    // Initial fetch
    if (status === "idle") {
      fetchContent();
    }

    // Poll every 3 seconds if pending
    if (status === "pending") {
      const interval = setInterval(fetchContent, 3000);
      return () => clearInterval(interval);
    }
  }, [hasAnalysisCompleted, status, endpoint]);

  const handleCopy = () => {
    navigator.clipboard.writeText(content);
  };

  const handleDownload = () => {
    const blob = new Blob([content], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${title.toLowerCase().replace(/\s+/g, "_")}.${type === "markdown" ? "md" : "txt"}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const getStatusDisplay = () => {
    const stage = getStage();

    // Stage 1: Yet to Execute (Idle)
    if (stage === "idle") {
      return (
        <div className="flex items-center gap-2 text-gray-400">
          <div className="h-2.5 w-2.5 rounded-full bg-gray-400" />
          <span>Yet to Execute</span>
        </div>
      );
    }

    // Stage 2: In Progress (Analyzing)
    if (stage === "analyzing") {
      return (
        <div className="flex items-center gap-2 text-yellow-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>In Progress...</span>
        </div>
      );
    }

    // Stage 3: Completed - Loading file
    if (status === "loading") {
      return (
        <div className="flex items-center gap-2 text-blue-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Loading...</span>
        </div>
      );
    }

    // Stage 3: Completed - Still pending file
    if (status === "pending") {
      return (
        <div className="flex items-center gap-2 text-yellow-400">
          <Loader2 className="h-4 w-4 animate-spin" />
          <span>Generating...</span>
        </div>
      );
    }

    // Stage 3: Completed - Error
    if (status === "error") {
      return (
        <div className="flex items-center gap-2 text-red-400">
          <span>Error</span>
        </div>
      );
    }

    // Stage 3: Completed - Ready
    if (status === "success" && content) {
      return (
        <div className="flex items-center gap-2 text-green-400">
          <FileText className="h-4 w-4" />
          <span>Ready</span>
        </div>
      );
    }

    return null;
  };

  return (
    <div className="w-full">
      {/* Header */}
      <div
        className="glass-card p-4 cursor-pointer hover:bg-muted/40 transition-colors"
        onClick={() => setIsExpanded(!isExpanded)}
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            {icon || <FileText className="h-5 w-5 text-primary" />}
            <h3 className="font-semibold text-foreground">{title}</h3>
          </div>

          <div className="flex items-center gap-4">
            {getStatusDisplay()}

            {status === "success" && content && (
              <div className="flex items-center gap-2">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleCopy();
                  }}
                  className="p-2 hover:bg-muted/60 rounded transition-colors"
                  title="Copy content"
                >
                  <Copy className="h-4 w-4 text-foreground/60" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleDownload();
                  }}
                  className="p-2 hover:bg-muted/60 rounded transition-colors"
                  title="Download file"
                >
                  <Download className="h-4 w-4 text-foreground/60" />
                </button>
              </div>
            )}

            <motion.div
              animate={{ rotate: isExpanded ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown className="h-5 w-5 text-foreground/60" />
            </motion.div>
          </div>
        </div>
      </div>

      {/* Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeInOut" }}
            className="overflow-hidden"
          >
            <div className="glass-card mt-2 p-6">
              {status === "idle" && (
                <div className="text-center py-12">
                  <div className="h-16 w-16 mx-auto mb-4 rounded-full bg-gray-400/20 flex items-center justify-center">
                    <FileText className="h-8 w-8 text-gray-400" />
                  </div>
                  <p className="text-muted-foreground font-medium mb-2">
                    {title} not yet started
                  </p>
                  <p className="text-sm text-muted-foreground/60">
                    Run an analysis to generate this report
                  </p>
                </div>
              )}

              {getStage() === "analyzing" && status === "idle" && (
                <div className="text-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-yellow-400" />
                  <p className="text-muted-foreground font-medium mb-2">
                    Analysis in progress...
                  </p>
                  <p className="text-sm text-muted-foreground/60">
                    {title} will be generated automatically
                  </p>
                </div>
              )}

              {status === "pending" && (
                <div className="text-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
                  <p className="text-muted-foreground">
                    Generating {title.toLowerCase()}...
                  </p>
                  <p className="text-sm text-muted-foreground/60 mt-2">
                    This will be available once the analysis completes
                  </p>
                </div>
              )}

              {status === "loading" && (
                <div className="text-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-400" />
                  <p className="text-muted-foreground">Loading content...</p>
                </div>
              )}

              {status === "error" && (
                <div className="text-center py-12">
                  <div className="text-red-400 mb-2">Failed to load content</div>
                  <p className="text-sm text-muted-foreground">{errorMessage}</p>
                </div>
              )}

              {status === "success" && content && (
                <div className="max-h-[600px] overflow-y-auto pr-2 terminal-scrollbar">
                  <pre className="whitespace-pre-wrap font-mono text-sm text-foreground/90 bg-black/20 p-4 rounded leading-relaxed">
                    {content}
                  </pre>
                </div>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
