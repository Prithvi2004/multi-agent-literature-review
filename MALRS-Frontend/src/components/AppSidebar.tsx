import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, FileText, Info, Cpu, Database, Sparkles } from "lucide-react";
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
          className="absolute -right-3 top-6 z-30 p-1.5 rounded-full bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-lg"
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
              <div className="flex items-center gap-2">
                <div className="p-2 rounded-lg bg-primary/10">
                  <FileText className="h-5 w-5 text-primary" />
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-foreground text-sm">
                      Paper-Centric Mode
                    </span>
                    <Tooltip>
                      <TooltipTrigger asChild>
                        <Info className="h-3.5 w-3.5 text-muted-foreground cursor-help" />
                      </TooltipTrigger>
                      <TooltipContent side="right" className="max-w-xs">
                        <p>Your paper content serves as the primary input for novelty assessment.</p>
                      </TooltipContent>
                    </Tooltip>
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="text-xs text-muted-foreground leading-relaxed">
                Provide your paper content as the primary input. The AI will analyze it against existing literature to assess novelty.
              </p>

              {/* Tech Stack Badge */}
              <GlassCard className="p-3">
                <p className="text-xs font-medium text-muted-foreground mb-3">
                  Tech Stack
                </p>
                <div className="flex flex-wrap gap-2">
                  <TechBadge icon={Cpu} label="GPT-4o" />
                  <TechBadge icon={Database} label="RAG" />
                  <TechBadge icon={Sparkles} label="Multi-Agent" />
                </div>
              </GlassCard>

              {/* Decorative element */}
              <div className="mt-auto pt-4 border-t border-border/50">
                <p className="text-xs text-muted-foreground/60 text-center">
                  v1.0.0 • Research Grade
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
                  <div className="p-2 rounded-lg bg-primary/10 cursor-help">
                    <FileText className="h-5 w-5 text-primary" />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p>Paper-Centric Mode</p>
                </TooltipContent>
              </Tooltip>
              <Tooltip>
                <TooltipTrigger asChild>
                  <div className="p-2 rounded-lg bg-muted cursor-help">
                    <Cpu className="h-4 w-4 text-muted-foreground" />
                  </div>
                </TooltipTrigger>
                <TooltipContent side="right">
                  <p>GPT-4o + RAG + Multi-Agent</p>
                </TooltipContent>
              </Tooltip>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </motion.aside>
  );
}

function TechBadge({ icon: Icon, label }: { icon: React.ElementType; label: string }) {
  return (
    <div className="gradient-border px-2.5 py-1 rounded-full flex items-center gap-1.5">
      <Icon className="h-3 w-3 text-primary" />
      <span className="text-xs font-medium text-foreground">{label}</span>
    </div>
  );
}
