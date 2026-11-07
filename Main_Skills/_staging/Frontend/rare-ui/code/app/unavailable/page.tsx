import type { Metadata } from "next";
import HeroIntro from "@/components/HeroIntro";
import CtaLink from "@/components/not-found/CtaLink";

export const metadata: Metadata = {
  title: "Not available in your country",
  description: "Rare UI is not available in your country.",
  robots: { index: false, follow: false },
};

export default function Unavailable() {
  return (
    <section className="relative w-full p-1.5 md:p-2.5">
      <div
        className="relative flex min-h-[calc(100svh_-_0.75rem)] w-full items-center justify-center overflow-hidden rounded-[45px] border border-black/4 bg-[#F5F5F7] dark:border-transparent dark:border-apple dark:bg-[#121212] md:min-h-[calc(100svh_-_1.25rem)]"
        style={{ cornerShape: "squircle" } as React.CSSProperties}
      >
        <img
          src="/logos/Rareui.svg"
          alt=""
          aria-hidden="true"
          className="pointer-events-none absolute left-1/2 top-[68%] w-[860px] max-w-none -translate-x-1/2 -translate-y-1/2 opacity-5 [filter:brightness(0)] dark:opacity-[0.07] dark:[filter:brightness(0)_invert(1)]"
        />
        <div className="pointer-events-none absolute inset-0 hidden bg-[radial-gradient(120%_75%_at_50%_-5%,rgba(255,255,255,0.07),transparent_60%)] dark:block" />

        <div className="relative mx-auto flex w-full max-w-6xl flex-col items-center justify-center gap-3 px-4 pb-20 pt-28 text-center sm:gap-4 sm:px-6">
          <HeroIntro
            headline="Rare UI isn't available in your country."
            sub="We're sorry. Access to Rare UI is restricted in your region for now. If you think this is a mistake, let us know."
            badge={<img src="/logos/Rareui.svg" alt="Rare UI" className="h-12 w-12" />}
          >
            <div className="mt-4">
              <CtaLink href="https://x.com/swamimalode" label="Contact us" primary />
            </div>
          </HeroIntro>
        </div>
      </div>
    </section>
  );
}
