import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import {
  getInlineCodeText, HexColorCode, isHexColor,
  renderChildrenWithHexColors, renderTextWithHexColors,
} from "@/components/design-md-hex";

export function DesignDocument({ content, imagesInGallery = false }: { content: string; imagesInGallery?: boolean }) {
  return (
    <div className="flex min-w-0 flex-1 justify-center p-6">
      <article className={`mx-auto w-full min-w-0 max-w-3xl [overflow-wrap:anywhere] ${imagesInGallery ? "lg:[&_p:has(img)]:hidden" : ""}`}>
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            img: ({ src, alt }) => <a href={typeof src === "string" ? src : undefined} target="_blank" rel="noreferrer"><img src={src} alt={alt ?? "Captured website"} loading="lazy" className="my-4 max-h-[600px] w-full rounded-lg border object-contain object-top" /></a>,
            h1: ({ children }) => (
              <h1 className="text-2xl font-semibold tracking-tight mb-6">{children}</h1>
            ),
            h2: ({ children }) => (
              <h2 className="text-base font-semibold mt-10 mb-3 pb-2 border-b">{children}</h2>
            ),
            h3: ({ children }) => (
              <h3 className="text-sm font-semibold mt-6 mb-2 text-muted-foreground uppercase tracking-wider">{children}</h3>
            ),
            p: ({ children }) => (
              <p className="text-sm leading-relaxed text-muted-foreground mb-3 text-justify">{renderChildrenWithHexColors(children)}</p>
            ),
            ul: ({ children }) => (
              <ul className="text-sm text-muted-foreground space-y-1 mb-3 ml-4 list-disc">{children}</ul>
            ),
            li: ({ children }) => (
              <li className="leading-relaxed text-justify">{renderChildrenWithHexColors(children)}</li>
            ),
            table: ({ children }) => (
              <div className="overflow-x-auto mb-4">
                <table className="w-full text-sm border-collapse">{children}</table>
              </div>
            ),
            thead: ({ children }) => (
              <thead className="border-b">{children}</thead>
            ),
            th: ({ children }) => (
              <th className="text-left text-xs font-medium text-muted-foreground py-2 pr-6">{children}</th>
            ),
            td: ({ children }) => (
              <td className="py-2 pr-6 text-sm text-muted-foreground align-top">{renderChildrenWithHexColors(children)}</td>
            ),
            tr: ({ children }) => (
              <tr className="border-b border-border/50 last:border-0">{children}</tr>
            ),
            code: ({ children, className }) => {
              const isBlock = className?.includes("language-")
              if (isBlock) {
                return (
                  <code className="block bg-muted rounded-lg p-4 text-xs font-mono overflow-x-auto mb-4">
                    {renderTextWithHexColors(String(children))}
                  </code>
                )
              }
              const text = getInlineCodeText(children)
              if (isHexColor(text)) {
                return <HexColorCode hex={text} />
              }
              return (
                <code className="inline-flex items-center gap-1.5 font-mono text-xs bg-muted px-1.5 py-0.5 rounded">
                  {children}
                </code>
              )
            },
            blockquote: ({ children }) => (
              <blockquote className="border-l-2 pl-4 text-sm text-muted-foreground italic mb-3">{children}</blockquote>
            ),
            hr: () => <hr className="my-6 border-border/50" />,
          }}
        >
          {content}
        </ReactMarkdown>
      </article>
    </div>
  );
}
