import Link from "next/link";
import { cn } from "@/lib/utils";

export default function SidebarHeader({
  onNavigate,
  className,
}: {
  onNavigate?: () => void;
  className?: string;
}) {
  return (
    <nav
      aria-label="Breadcrumb"
      className={cn("flex items-center gap-2", className)}
    >
      <Link
        href="/"
        onClick={onNavigate}
        className="flex items-center gap-1.5 text-foreground/50 transition-colors duration-200 hover:text-foreground"
      >
        <img src="/logos/Rareui.svg" alt="" className="size-3.5" />
        Rare UI
      </Link>
      <span aria-hidden className="text-foreground/25">
        /
      </span>
      <Link
        href="/components"
        onClick={onNavigate}
        className="text-foreground"
      >
        Components
      </Link>
    </nav>
  );
}
