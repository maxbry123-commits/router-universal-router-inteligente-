"use client";

import { motion, useReducedMotion } from "motion/react";

const SPRING = { type: "spring", stiffness: 300, damping: 22 } as const;
const STEP = 0.09;

export default function Rise({
  index = 0,
  className,
  children,
}: {
  index?: number;
  className?: string;
  children: React.ReactNode;
}) {
  const reduceMotion = useReducedMotion();

  return (
    <motion.div
      initial={reduceMotion ? false : { y: 18, filter: "blur(4px)" }}
      animate={{ y: 0, filter: "blur(0px)" }}
      transition={
        reduceMotion ? { duration: 0 } : { ...SPRING, delay: index * STEP }
      }
      className={className}
    >
      {children}
    </motion.div>
  );
}
