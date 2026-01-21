import { motion } from "framer-motion";
import { BookMarked, Lightbulb, ScanSearch, Layers3 } from "lucide-react";

const badges = [
  { icon: Layers3, label: "Multi-Agent Synthesis" },
  { icon: ScanSearch, label: "Deep Retrieval" },
  { icon: BookMarked, label: "Scholarly Rigor" },
  { icon: Lightbulb, label: "Insight Discovery" },
];

export function HeroBanner() {
  return (
    <header className="relative z-10 px-4 py-16 md:py-20 text-center">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
      >
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.9, delay: 0.2 }}
          className="inline-block mb-6"
        >
          <div className="px-4 py-1.5 rounded-full border border-primary/20 bg-primary/5 text-xs font-medium tracking-wider uppercase text-primary">
            Academic Intelligence Platform
          </div>
        </motion.div>

        <h1 className="heading-xl gradient-text mb-6 max-w-4xl mx-auto">
          Literature Review
          <br />
          <span className="text-foreground/90">& Novelty Assessment</span>
        </h1>
        <p className="body-lg text-muted-foreground max-w-2xl mx-auto mb-10 leading-relaxed">
          Navigate the depths of scholarly knowledge with precision.
          <br className="hidden md:block" />
          Multi-agent systems illuminate patterns, uncover gaps, and assess
          novelty in academic literature.
        </p>

        <motion.div
          className="flex flex-wrap justify-center gap-3 max-w-3xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5, duration: 0.6 }}
        >
          {badges.map((badge, index) => (
            <motion.div
              key={badge.label}
              className="group glass-card px-5 py-3 flex items-center gap-2.5 cursor-default border-primary/10 hover:border-primary/30 transition-colors duration-300"
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{
                delay: 0.6 + index * 0.1,
                duration: 0.5,
                ease: [0.16, 1, 0.3, 1],
              }}
              whileHover={{ y: -2 }}
            >
              <badge.icon className="h-4 w-4 text-primary transition-transform duration-300 group-hover:scale-110" />
              <span className="text-sm font-medium text-foreground/90">
                {badge.label}
              </span>
            </motion.div>
          ))}
        </motion.div>
      </motion.div>
    </header>
  );
}
