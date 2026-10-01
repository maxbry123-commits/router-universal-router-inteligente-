import { HOME_FAQ } from "../../_lib/faq";
import { SITE_DOCS_URL } from "../../_lib/site";

export function FaqSection() {
  return (
    <div className="grid gap-8 lg:grid-cols-[1fr_1.5fr] lg:gap-16">
      <div>
        <h2 className="display-md">Frequently asked questions</h2>
        <p className="mt-4 text-[14px] leading-relaxed text-muted">
          Setup instructions and examples are in the{" "}
          <a className="text-foreground underline underline-offset-4" href={SITE_DOCS_URL}>
            getdesign documentation
          </a>.
        </p>
      </div>
      <div className="divide-y divide-[var(--border)]">
        {HOME_FAQ.map(({ question, answer }) => (
          <details key={question} className="group py-5 first:pt-0">
            <summary className="cursor-pointer text-[15px] font-medium text-foreground focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-[var(--accent)]">
              {question}
            </summary>
            <p className="mt-3 text-[14px] leading-relaxed text-muted">{answer}</p>
          </details>
        ))}
      </div>
    </div>
  );
}
