import { TESTIMONIALS, type Testimonial } from "@/lib/testimonials";
import { cn } from "@/lib/utils";
import TestimonialCard from "./TestimonialCard";

const VIEWPORT =
  "relative h-[560px] overflow-hidden [mask-image:linear-gradient(to_bottom,transparent,#000_10%,#000_90%,transparent)] motion-reduce:h-auto motion-reduce:[mask-image:none] lg:h-[700px]";

const TRACK =
  "will-change-transform group-hover:[animation-play-state:paused] motion-reduce:[animation:none]";

const DESKTOP_ANIMATIONS = [
  "[animation:marquee-y_44s_linear_infinite_reverse]",
  "[animation:marquee-y_56s_linear_infinite]",
  "[animation:marquee-y_48s_linear_infinite_reverse]",
];

const MOBILE_ANIMATION = "[animation:marquee-y_130s_linear_infinite]";

function columnItems(column: number) {
  return TESTIMONIALS.filter(
    (_, index) => index % DESKTOP_ANIMATIONS.length === column,
  );
}

function MarqueeColumn({
  items,
  animation,
  className,
}: {
  items: Testimonial[];
  animation: string;
  className?: string;
}) {
  const copy = items.map((testimonial) => (
    <TestimonialCard key={testimonial.handle} testimonial={testimonial} />
  ));

  return (
    <div className={cn(VIEWPORT, className)}>
      <div className={cn(TRACK, animation)}>
        {copy}
        <div className="motion-reduce:hidden" aria-hidden="true" inert>
          {copy}
        </div>
      </div>
    </div>
  );
}

export default function TestimonialMarquee({
  className,
}: {
  className?: string;
}) {
  return (
    <div
      className={cn("group grid grid-cols-1 gap-4 lg:grid-cols-3", className)}
    >
      <MarqueeColumn
        items={TESTIMONIALS}
        animation={MOBILE_ANIMATION}
        className="lg:hidden"
      />
      {DESKTOP_ANIMATIONS.map((animation, column) => (
        <MarqueeColumn
          key={animation}
          items={columnItems(column)}
          animation={animation}
          className="hidden lg:block"
        />
      ))}
    </div>
  );
}
