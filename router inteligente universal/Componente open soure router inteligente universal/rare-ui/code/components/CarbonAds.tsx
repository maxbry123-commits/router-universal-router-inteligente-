"use client";

import { useEffect, useRef, useState } from "react";
import type { ComponentProps } from "react";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const SERVE_URL =
  "//cdn.carbonads.com/carbon.js?serve=CWBI423E&placement=wwwrareuicom&format=responsive";

// carbon.js finds its own tag by this id, so the page can only ever hold one
const SCRIPT_ID = "_carbonads_js";

// carbon's box: 100px image, 0.6em padding, border, and the "ads via carbon" line
const RESERVED_HEIGHT = "min-h-34";

// carbon's terms allow one unit per page, so a second mount is a policy break, not a style bug
let instances = 0;

function useSingleInstance() {
  useEffect(() => {
    if (process.env.NODE_ENV === "production") return;

    instances += 1;
    if (instances > 1) {
      console.error(
        `CarbonAds: ${instances} mounted at once. Carbon serves one unit per page.`,
      );
    }

    return () => {
      instances -= 1;
    };
  }, []);
}

export default function CarbonAds({
  className,
  ...props
}: ComponentProps<"div">) {
  const slotRef = useRef<HTMLDivElement>(null);
  const pathname = usePathname();
  const [blocked, setBlocked] = useState(false);

  useSingleInstance();

  // one script load is one serve; re-running on pathname makes a route change a pageview
  useEffect(() => {
    const slot = slotRef.current;
    if (!slot) return;

    // deferring a tick collapses strict mode's mount, unmount, mount into one injection
    const timer = setTimeout(() => {
      const script = document.createElement("script");
      script.id = SCRIPT_ID;
      script.src = SERVE_URL;
      script.async = true;
      script.onerror = () => setBlocked(true);
      slot.appendChild(script);
    }, 0);

    return () => {
      clearTimeout(timer);
      slot.replaceChildren();
    };
  }, [pathname]);

  // drop the reserved height as well, so a blocked ad leaves no gap
  if (blocked) return null;

  return (
    <div
      ref={slotRef}
      data-slot="carbon-ads"
      className={cn(RESERVED_HEIGHT, className)}
      {...props}
    />
  );
}
