import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  BookOpen,
  Info,
  Brain,
  Archive,
  Sparkles,
} from "lucide-react";
import { useState } from "react";
import { GlassCard } from "./ui/GlassCard";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

export function AppSidebar() {
  const [collapsed, setCollapsed] = useState(false);

  return (
    <motion.aside
      className="relative z-20 h-full"
      initial={{ width: 280 }}
      animate={{ width: collapsed ? 64 : 280 }}
      transition={{ duration: 0.3, ease: "easeInOut" }}
    >
      <div className="glass-card h-full rounded-lg p-4 flex flex-col">
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

              {/* Description */}
              <p className="text-xs text-muted-foreground leading-relaxed">
                Submit your manuscript for deep analysis. Our multi-agent system
                examines it against the scholarly corpus to identify
                contributions and assess originality.
              </p>

              {/* Tech Stack Badge */}
              <GlassCard className="p-4 border-primary/10">
                <p className="text-xs font-medium text-muted-foreground/80 mb-3 uppercase tracking-wider">
                  Architecture
                </p>
                <div className="flex flex-wrap gap-2">
                  <TechBadge icon={Brain} label="Ollama" />
                  <TechBadge icon={Archive} label="RAG" />
                  <TechBadge icon={Sparkles} label="Multi-Agent" />
                </div>
              </GlassCard>

              {/* Decorative element */}
              <div className="mt-auto pt-6 border-t border-border/40">
                <p className="text-xs text-muted-foreground/50 text-center tracking-wide">
                  v1.0.0 <span className="mx-2 opacity-30">•</span> Research
                  Grade
                </p>
              </div>
            </motion.div>
          ) : (
            <motion.div
              key="collapsed"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              className="flex flex-col items-center gap-4 pt-8"
            >
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="p-2.5 rounded bg-primary/10 cursor-help border border-primary/20 hover:border-primary/40 transition-colors">
                    <BookOpen className="h-5 w-5 text-primary" />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p className="font-medium">Paper Analysis Mode</p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="p-2.5 rounded bg-muted cursor-help border border-border/50 hover:border-primary/30 transition-colors">
                    <Brain className="h-4 w-4 text-muted-foreground" />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p className="font-medium">Ollama + RAG + Multi-Agent</p>
                </TooltipContent>
              </Tooltip>
            </motion.div>
          )}
        </AnimatePresence>
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
