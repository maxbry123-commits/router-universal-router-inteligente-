import { sponsorsByTier } from "@/lib/sponsors";

export default function BackedBy() {
  const sponsors = sponsorsByTier("diamond");
  if (sponsors.length === 0) return null;

  return (
    <div className="inline-flex items-center gap-3 rounded-full border border-black/[0.07] bg-white/70 py-1 pl-4 pr-1 ring-black/15 has-[:focus-visible]:ring-2 sm:gap-4 dark:border-transparent dark:border-apple dark:bg-white/[0.045] dark:ring-white/25">
      <span className="font-runde text-[11px] font-semibold uppercase tracking-[0.12em] text-black/45 dark:text-white/45">
        Backed by
      </span>
      <span className="h-3.5 w-px bg-black/10 dark:bg-white/15" />
      <span className="flex items-center gap-1.5">
        {sponsors.map((sponsor) => (
          <a
            key={sponsor.name}
            href={sponsor.href}
            target="_blank"
            rel="noopener"
            data-track="sponsor_click"
            data-sponsor={sponsor.name}
            data-placement="hero"
            className="rounded-full outline-none grayscale transition-[filter] duration-200 ease-out hover:grayscale-0 focus-visible:grayscale-0"
          >
            <img
              src={sponsor.avatarSrc}
              alt={sponsor.name}
              title={sponsor.name}
              className="size-6 rounded-full ring-1 ring-black/10 dark:ring-white/10"
            />
          </a>
        ))}
      </span>
    </div>
  );
}
