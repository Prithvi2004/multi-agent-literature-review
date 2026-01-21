import { cn } from "@/lib/utils";
import { motion } from "framer-motion";
import { Loader2 } from "lucide-react";
import { ReactNode, MouseEvent } from "react";

interface GradientButtonProps {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  icon?: ReactNode;
  children: ReactNode;
  disabled?: boolean;
  onClick?: (e: MouseEvent<HTMLButtonElement>) => void;
  className?: string;
  type?: "button" | "submit" | "reset";
}

export function GradientButton({
  className,
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  icon,
  children,
  onClick,
  type = "button",
}: GradientButtonProps) {
  const variants = {
    primary:
      "bg-gradient-to-r from-primary to-secondary text-primary-foreground hover:opacity-90",
    secondary:
      "bg-muted text-foreground border border-border hover:bg-muted/80",
    ghost:
      "bg-transparent text-muted-foreground hover:text-foreground hover:bg-muted/50",
    danger:
      "bg-destructive text-destructive-foreground hover:bg-destructive/90",
  };

  const sizes = {
    sm: "px-3 py-1.5 text-sm",
    md: "px-4 py-2.5 text-sm",
    lg: "px-6 py-3 text-base",
  };

  return (
    <motion.button
      type={type}
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
        variants[variant],
        sizes[size],
        className
      )}
      disabled={disabled || loading}
      onClick={onClick}
      whileTap={{ scale: 0.98 }}
      whileHover={{ scale: 1.02 }}
    >
      {loading ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : icon ? (
        icon
      ) : null}
      {children}
    </motion.button>
  );
}
