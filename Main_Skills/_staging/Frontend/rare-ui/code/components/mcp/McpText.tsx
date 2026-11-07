import { Fragment } from "react";

export default function McpText({ children }: { children: string }) {
  return (
    <p className="text-[15px] leading-relaxed text-muted-foreground">
      {children.split(/`([^`]+)`/).map((part, index) =>
        index % 2 ? (
          <code
            key={index}
            className="rounded-md bg-muted px-1.5 py-0.5 font-mono text-[13px] text-foreground/80"
          >
            {part}
          </code>
        ) : (
          <Fragment key={index}>{part}</Fragment>
        ),
      )}
    </p>
  );
}
