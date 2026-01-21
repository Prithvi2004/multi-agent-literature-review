import { motion } from "framer-motion";
import { Check, FileText, Lightbulb, Layers, BarChart3 } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";

interface Step {
  id: string;
  label: string;
  icon: React.ElementType;
  required: boolean;
}

const steps: Step[] = [
  { id: "paper", label: "Paper Content", icon: FileText, required: true },
  { id: "idea", label: "Research Idea", icon: Lightbulb, required: false },
  { id: "domains", label: "Domains", icon: Layers, required: false },
  { id: "analysis", label: "Analysis", icon: BarChart3, required: false },
];

interface ProgressTrackerProps {
  completedSteps: string[];
  activeStep?: string;
}

export function ProgressTracker({ completedSteps, activeStep }: ProgressTrackerProps) {
  return (
    <div className="glass-card p-4 mb-6" role="navigation" aria-label="Progress tracker">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = completedSteps.includes(step.id);
          const isActive = activeStep === step.id;
          const Icon = step.icon;

          return (
            <div key={step.id} className="flex items-center flex-1">
              <Tooltip>
                <TooltipTrigger asChild>
                  <motion.div
                    className={cn(
                      "relative flex flex-col items-center gap-2 cursor-default",
                      isActive && "scale-105"
                    )}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.1 }}
                  >
                    {/* Step indicator */}
                    <div
                      className={cn(
                        "relative w-10 h-10 rounded-full flex items-center justify-center transition-all duration-300",
                        isCompleted
                          ? "bg-success text-success-foreground"
                          : isActive
                          ? "bg-primary text-primary-foreground"
                          : "bg-muted text-muted-foreground"
                      )}
                    >
                      {isCompleted ? (
                        <Check className="h-5 w-5" />
                      ) : (
                        <Icon className="h-5 w-5" />
                      )}
                      
                      {/* Pulse animation for active step */}
                      {isActive && !isCompleted && (
                        <motion.div
                          className="absolute inset-0 rounded-full border-2 border-primary"
                          animate={{
                            scale: [1, 1.3, 1],
                            opacity: [0.8, 0, 0.8],
                          }}
                          transition={{
                            duration: 1.5,
                            repeat: Infinity,
                            ease: "easeInOut",
                          }}
                        />
                      )}
                    </div>

                    {/* Step label */}
                    <span
                      className={cn(
                        "text-xs font-medium transition-colors text-center",
                        isCompleted || isActive
                          ? "text-foreground"
                          : "text-muted-foreground"
                      )}
                    >
                      {step.label}
                      {step.required && (
                        <span className="text-accent ml-0.5">*</span>
                      )}
                    </span>
                  </motion.div>
                </TooltipTrigger>
                <TooltipContent>
                  <p>
                    {step.required
                      ? "Required: Add at least one paper section"
                      : `Optional: ${step.label}`}
                  </p>
                </TooltipContent>
              </Tooltip>

              {/* Connector line */}
              {index < steps.length - 1 && (
                <div className="flex-1 h-0.5 mx-3">
                  <motion.div
                    className={cn(
                      "h-full rounded-full",
                      isCompleted ? "bg-success" : "bg-border"
                    )}
                    initial={{ scaleX: 0 }}
                    animate={{ scaleX: 1 }}
                    transition={{ delay: index * 0.1 + 0.2, duration: 0.3 }}
                    style={{ transformOrigin: "left" }}
                  />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
