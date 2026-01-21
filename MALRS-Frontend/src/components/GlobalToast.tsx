import { motion, AnimatePresence } from "framer-motion";
import { CheckCircle, X } from "lucide-react";
import { useEffect, useState } from "react";

interface GlobalToastProps {
  show: boolean;
  onClose: () => void;
  title: string;
  message: string;
  duration?: number;
}

export function GlobalToast({
  show,
  onClose,
  title,
  message,
  duration = 4500,
}: GlobalToastProps) {
  const [isVisible, setIsVisible] = useState(show);

  useEffect(() => {
    setIsVisible(show);
    if (show) {
      const timer = setTimeout(() => {
        setIsVisible(false);
        onClose();
      }, duration);
      return () => clearTimeout(timer);
    }
  }, [show, duration, onClose]);

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div
          className="fixed top-4 right-4 z-50"
          initial={{ opacity: 0, x: 50, y: -20 }}
          animate={{ opacity: 1, x: 0, y: 0 }}
          exit={{ opacity: 0, x: 50 }}
          transition={{ type: "spring", stiffness: 500, damping: 30 }}
        >
          <div className="glass-card p-4 pr-10 min-w-[320px] max-w-md shadow-xl">
            <div className="flex items-start gap-3">
              <div className="p-1 rounded-full bg-success/20">
                <CheckCircle className="h-5 w-5 text-success" />
              </div>
              <div>
                <h4 className="font-semibold text-foreground text-sm">
                  {title}
                </h4>
                <p className="text-sm text-muted-foreground mt-0.5">
                  {message}
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                setIsVisible(false);
                onClose();
              }}
              className="absolute top-3 right-3 p-1 rounded-full hover:bg-muted/50 transition-colors"
              aria-label="Dismiss notification"
            >
              <X className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
