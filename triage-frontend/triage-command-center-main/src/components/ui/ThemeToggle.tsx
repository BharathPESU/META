import { useTheme } from "@/hooks/useTheme";
import { Moon, Sun } from "lucide-react";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  const isDay = theme === "day";
  return (
    <button
      onClick={toggleTheme}
      aria-label="Toggle theme"
      className="inline-flex items-center gap-1.5 border border-border bg-surface px-2.5 py-1.5 font-mono text-[10px] uppercase tracking-wider text-text-secondary transition-colors hover:border-primary hover:text-text-primary"
      style={{ borderRadius: 4 }}
    >
      {isDay ? <Moon className="h-3 w-3" /> : <Sun className="h-3 w-3" />}
      {isDay ? "Night" : "Day"}
    </button>
  );
}
