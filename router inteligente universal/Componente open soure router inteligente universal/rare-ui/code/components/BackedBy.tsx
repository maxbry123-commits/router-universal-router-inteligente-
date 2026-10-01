import { Fragment } from "react";

import { sponsorsByTier } from "@/lib/sponsors";

export default function BackedBy() {
  const sponsors = sponsorsByTier("diamond").filter(
    (sponsor) => sponsor.avatarSrc,
  );
  if (sponsors.length === 0) return null;

  return (
    <div className="inline-flex items-center gap-2.5 rounded-full border border-black/[0.07] bg-white/70 py-1 pl-4 pr-2 dark:border-transparent dark:border-apple dark:bg-white/[0.045]">
      <span className="font-runde text-[11px] font-semibold uppercase tracking-[0.12em] text-black/45 dark:text-white/45">
        Backed by
      </span>
      <span className="h-3.5 w-px bg-black/10 dark:bg-white/15" />
      <span className="flex items-center gap-1.5">
        {sponsors.map((sponsor, index) => (
          <Fragment key={sponsor.name}>
            {index > 0 && (
              <span className="size-1 rounded-full bg-black/20 dark:bg-white/25" />
            )}
            <a
              href={sponsor.href}
              target="_blank"
              rel="noopener"
              title={sponsor.name}
              className="opacity-90 transition-opacity duration-150 ease-out hover:opacity-100"
            >
              <img
                src={sponsor.avatarSrc}
                alt=""
                className="size-[30px] rounded-full"
              />
              <span className="sr-only">{sponsor.name}</span>
            </a>
          </Fragment>
        ))}
      </span>
    </div>
  );
}
