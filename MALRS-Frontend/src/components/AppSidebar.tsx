import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  BookOpen,
  Info,
  Brain,
  Archive,
  Sparkles,
  History,
} from "lucide-react";
import { useState } from "react";
import { GlassCard } from "./ui/GlassCard";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { SessionManager } from "./SessionManager";
import { ScrollArea } from "./ui/scroll-area";

interface AppSidebarProps {
  sessions: any[];
  currentSessionId: string | null;
  lastSaved: Date | null;
  onSave: (name?: string, isAutoSave?: boolean) => Promise<string>;
  onLoad: (sessionId: string) => Promise<void>;
  onDelete: (sessionId: string) => Promise<void>;
  onNew: () => void;
}

export function AppSidebar({
  sessions,
  currentSessionId,
  lastSaved,
  onSave,
  onLoad,
  onDelete,
  onNew,
}: AppSidebarProps) {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      className="relative z-20 h-[calc(100vh-100px)] sticky top-4 hidden lg:block"
      initial={{ width: 320 }}
      animate={{ width: collapsed ? 80 : 320 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      <div className="glass-card h-full rounded-lg flex flex-col overflow-hidden border border-border/40">
        {/* Toggle Button */}
        <button
          onClick={() => setCollapsed(!collapsed)}
          className="absolute -right-3 top-6 z-30 p-1.5 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-300 shadow-lg hover:shadow-xl hover:shadow-primary/30"
          aria-label={collapsed ? "Expand sidebar" : "Collapse sidebar"}
        >
          {collapsed ? (
            <ChevronRight className="h-4 w-4" />
          ) : (
            <ChevronLeft className="h-4 w-4" />
          )}
        </button>

        <ScrollArea className="flex-1">
          <div className="p-4 flex flex-col gap-6">
            <AnimatePresence mode="wait">
              {!collapsed ? (
                <motion.div
                  key="expanded"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex flex-col gap-6"
                >
                  {/* Mode Indicator */}
                  <div className="flex items-center gap-3">
                    <div className="p-2.5 rounded bg-primary/10 border border-primary/20">
                      <BookOpen className="h-5 w-5 text-primary" />
                    </div>
                    <div className="flex-1">
                      <div className="flex items-center gap-1.5">
                        <span className="font-serif font-semibold text-foreground text-base">
                          Paper Analysis
                        </span>
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help hover:text-primary transition-colors" />
                          </TooltipTrigger>
                          <TooltipContent side="right" className="max-w-xs">
                            <p>
                              Your scholarly work serves as the foundation for
                              comparative analysis and novelty assessment.
                            </p>
                          </TooltipContent>
                        </Tooltip>
                      </div>
                    </div>
                  </div>

                  {/* Architecture Badge */}
                  <GlassCard className="p-4 border-primary/10 bg-primary/5">
                    <p className="text-[10px] font-bold text-primary mb-3 uppercase tracking-[0.2em]">
                      AI Core
                    </p>
                    <div className="flex flex-wrap gap-2">
                      <TechBadge icon={Brain} label="GPT-4o" />
                      <TechBadge icon={Archive} label="RAG" />
                      <TechBadge icon={Sparkles} label="Agents" />
                    </div>
                  </GlassCard>

                  {/* Session Manager Integrated */}
                  <div className="pt-2">
                    <SessionManager
                      sessions={sessions}
                      currentSessionId={currentSessionId}
                      lastSaved={lastSaved}
                      onSave={onSave}
                      onLoad={onLoad}
                      onDelete={onDelete}
                      onNew={onNew}
                    />
                  </div>
                </motion.div>
              ) : (
                <motion.div
                  key="collapsed"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.2 }}
                  className="flex flex-col items-center gap-4 pt-4"
                >
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="p-2.5 rounded bg-primary/10 cursor-help border border-primary/20 hover:border-primary/40 transition-colors">
                        <BookOpen className="h-5 w-5 text-primary" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <p className="font-medium">Paper Analysis</p>
                    </TooltipContent>
                  </Tooltip>
                  
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <div className="p-2.5 rounded bg-muted cursor-help border border-border/50 hover:border-primary/30 transition-colors">
                        <History className="h-5 w-5 text-muted-foreground" />
                      </div>
                    </TooltipTrigger>
                    <TooltipContent side="right">
                      <p className="font-medium">Sessions List</p>
                    </TooltipContent>
                  </Tooltip>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </ScrollArea>

        {/* Dynamic Footer */}
        {!collapsed && (
          <div className="p-4 border-t border-border/40 bg-muted/20 mt-auto">
            <p className="text-[10px] text-muted-foreground/50 text-center tracking-widest uppercase font-semibold">
              v1.1.0 • Research Grade
            </p>
          </div>
        )}
      </div>
    </motion.aside>
  );
}

function TechBadge({
  icon: Icon,
  label,
}: {
  icon: React.ElementType;
  label: string;
}) {
  return (
    <div className="px-3 py-1.5 rounded-full flex items-center gap-2 bg-muted/50 border border-border/50 hover:border-primary/30 transition-colors">
      <Icon className="h-3 w-3 text-primary" />
      <span className="text-xs font-medium text-foreground/90">{label}</span>
    </div>
  );
}
