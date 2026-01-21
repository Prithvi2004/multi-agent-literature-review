import { motion } from "framer-motion";
import { Sparkles, Brain, Database, Zap } from "lucide-react";

const badges = [
  { icon: Brain, label: "Multi-Agent Analysis" },
  { icon: Database, label: "RAG-Enhanced Retrieval" },
  { icon: Sparkles, label: "Research-Grade Outputs" },
  { icon: Zap, label: "Real-time Insights" },
];

export function HeroBanner() {
  return (
    <header className="relative z-10 px-4 py-12 md:py-16 text-center">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
      >
        <h1 className="heading-xl gradient-text mb-4">
          ResearchNovel
        </h1>
        <p className="body-lg text-muted-foreground max-w-2xl mx-auto mb-8">
          Literature Review & Novelty Assessment — Powered by AI
        </p>

        <motion.div
          className="flex flex-wrap justify-center gap-3"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.3, duration: 0.5 }}
        >
          {badges.map((badge, index) => (
            <motion.div
              key={badge.label}
              className="glass-card glass-card-hover px-4 py-2 flex items-center gap-2 cursor-default"
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.4 + index * 0.1, duration: 0.3 }}
              whileHover={{ scale: 1.05 }}
            >
              <badge.icon className="h-4 w-4 text-primary" />
              <span className="text-sm font-medium text-foreground">
                {badge.label}
              </span>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>
    </header>
  );
}
