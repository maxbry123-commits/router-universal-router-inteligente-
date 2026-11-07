"use client";

import { useEffect, useRef, useState } from "react";
import { motion, useReducedMotion, useSpring } from "motion/react";
import { cn } from "@/lib/utils";

const RADIUS = 240;
const PUSH = 80;
const TILT = 14;

const STROKE = "0.02em";
const HOLLOW_MS = 260;

const SPRING = { stiffness: 260, damping: 18, mass: 0.6 } as const;

function DodgingDigit({
  char,
  accent,
  outlined,
}: {
  char: string;
  accent?: boolean;
  outlined: boolean;
}) {
  const ref = useRef<HTMLSpanElement>(null);
  const x = useSpring(0, SPRING);
  const y = useSpring(0, SPRING);
  const rotate = useSpring(0, SPRING);
  const reduceMotion = useReducedMotion();

  useEffect(() => {
    if (reduceMotion) return;

    const rest = () => {
      x.set(0);
      y.set(0);
      rotate.set(0);
    };

    const onMove = (event: PointerEvent) => {
      const el = ref.current;
      if (!el) return;

      const rect = el.getBoundingClientRect();
      const dx = rect.left + rect.width / 2 - x.get() - event.clientX;
      const dy = rect.top + rect.height / 2 - y.get() - event.clientY;
      const distance = Math.hypot(dx, dy);
      if (distance > RADIUS) return rest();

      const force = 1 - distance / RADIUS;
      const push = (PUSH * force) / (distance || 1);
      x.set(dx * push);
      y.set(dy * push);
      rotate.set(-Math.sign(dx) * TILT * force);
    };

    window.addEventListener("pointermove", onMove, { passive: true });
    window.addEventListener("scroll", rest, { passive: true });
    document.addEventListener("pointerleave", rest);
    return () => {
      window.removeEventListener("pointermove", onMove);
      window.removeEventListener("scroll", rest);
      document.removeEventListener("pointerleave", rest);
    };
  }, [reduceMotion, x, y, rotate]);

  return (
    <motion.span
      ref={ref}
      style={{
        x,
        y,
        rotate,
        WebkitTextFillColor: outlined ? "transparent" : "currentColor",
        WebkitTextStrokeColor: "currentColor",
        WebkitTextStrokeWidth: outlined ? STROKE : 0,
        transition: `-webkit-text-fill-color ${HOLLOW_MS}ms ease-out`,
      }}
      className={cn(
        "inline-block will-change-transform",
        accent ? "text-[#FC4C01]" : "text-black dark:text-white",
      )}
    >
      {char}
    </motion.span>
  );
}

export default function DodgingDigits({
  digits,
  accentIndex,
  className,
}: {
  digits: string;
  accentIndex?: number;
  className?: string;
}) {
  const [outlined, setOutlined] = useState(false);

  useEffect(() => {
    const onClick = (event: MouseEvent) => {
      const target = event.target as Element | null;
      if (target?.closest("a, button")) return;
      setOutlined((on) => !on);
    };

    window.addEventListener("click", onClick);
    return () => window.removeEventListener("click", onClick);
  }, []);

  return (
    <div aria-hidden className={cn("flex select-none", className)}>
      {[...digits].map((digit, index) => (
        <DodgingDigit
          key={index}
          char={digit}
          accent={index === accentIndex}
          outlined={outlined}
        />
      ))}
    </div>
  );
}
