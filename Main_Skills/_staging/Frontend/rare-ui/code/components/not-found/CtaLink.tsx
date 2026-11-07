"use client";

import Link from "next/link";
import { Squircle } from "@squircle-js/react";
import { motion, useReducedMotion } from "motion/react";
import { cn } from "@/lib/utils";

const SPRING = { type: "spring", stiffness: 300, damping: 22 } as const;

export default function CtaLink({
  href,
  label,
  primary,
}: {
  href: string;
  label: string;
  primary?: boolean;
}) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      whileHover={reduceMotion ? undefined : { scale: 1.04 }}
      whileTap={reduceMotion ? undefined : { scale: 0.97 }}
      transition={SPRING}
    >
      <Squircle asChild cornerRadius={16} cornerSmoothing={1}>
        <Link
          href={href}
          className={cn(
            "flex h-12 items-center px-6 font-runde text-sm font-semibold text-white transition-colors duration-150 ease-out",
            primary
              ? "bg-[#FC4C01] hover:bg-[#e64500]"
              : "bg-neutral-900 hover:bg-neutral-800",
          )}
        >
          {label}
        </Link>
      </Squircle>
    </motion.div>
  );
}
