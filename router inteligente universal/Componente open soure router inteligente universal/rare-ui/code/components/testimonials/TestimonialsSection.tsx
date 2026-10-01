import Link from "next/link";
import TestimonialMarquee from "./TestimonialMarquee";

export default function TestimonialsSection() {
  return (
    <section className="mx-auto w-full max-w-6xl px-5 pb-24 sm:px-6 md:pb-32">
      <header className="flex flex-col items-center gap-3 text-center">
        <h2 className="max-w-2xl text-balance font-runde text-2xl font-bold tracking-tight sm:text-3xl md:text-4xl">
          Loved by the people who ship
        </h2>
        <p className="max-w-lg text-balance text-sm font-medium text-muted-foreground sm:text-base">
          Designers and engineers ship Rare UI in real products. Here is what
          they say about it.
        </p>
      </header>

      <TestimonialMarquee className="mt-12" />

      <div className="mt-8 flex justify-center">
        <Link
          href="/testimonials"
          className="font-runde text-sm font-semibold text-muted-foreground underline underline-offset-4 transition-colors duration-150 ease-out hover:text-foreground"
        >
          Check all testimonials &rarr;
        </Link>
      </div>
    </section>
  );
}
