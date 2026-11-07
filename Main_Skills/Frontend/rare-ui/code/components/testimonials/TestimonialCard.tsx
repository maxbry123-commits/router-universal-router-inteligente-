import { avatarUrl, type Testimonial } from "@/lib/testimonials";

const CARD =
  "mb-4 break-inside-avoid rounded-[32px] bg-[#F5F5F7] transition-colors duration-200 ease-out hover:bg-white dark:bg-[#121212] dark:hover:bg-muted";

function XIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="currentColor"
      xmlns="http://www.w3.org/2000/svg"
      className="mt-1 size-5 shrink-0 text-muted-foreground/50"
      aria-hidden="true"
    >
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  );
}

function CardBody({
  href,
  children,
}: {
  href?: string;
  children: React.ReactNode;
}) {
  if (!href) return <div className="p-6">{children}</div>;

  return (
    <a href={href} target="_blank" rel="noreferrer" className="block p-6">
      {children}
    </a>
  );
}

export default function TestimonialCard({
  testimonial,
}: {
  testimonial: Testimonial;
}) {
  const { name, handle, role, quote, href } = testimonial;

  const secondary = [name && handle, role].filter(Boolean).join(" · ");

  return (
    <figure
      className={CARD}
      style={{ cornerShape: "squircle" } as React.CSSProperties}
    >
      <CardBody href={href}>
        <div className="flex items-start justify-between gap-4">
          <figcaption className="flex min-w-0 items-center gap-3">
            <img
              src={avatarUrl(handle)}
              alt=""
              aria-hidden="true"
              loading="lazy"
              className="size-11 shrink-0 rounded-full bg-muted object-cover"
            />
            <div className="flex min-w-0 flex-col gap-1">
              <span className="truncate font-runde text-sm font-semibold leading-none">
                {name ?? handle}
              </span>
              {secondary && (
                <span
                  title={secondary}
                  className="truncate text-[13px] leading-snug text-muted-foreground/70"
                >
                  {secondary}
                </span>
              )}
            </div>
          </figcaption>
          <XIcon />
        </div>

        <blockquote
          cite={href}
          className="mt-4 text-pretty text-[15px] leading-relaxed text-muted-foreground"
        >
          {quote}
        </blockquote>
      </CardBody>
    </figure>
  );
}
