"use client";

import { useIsFetching } from "@tanstack/react-query";

import { WidgetFallback } from "@/components/dashboard-skeletons";

export function WidgetLoadingGate({ children }: { children: React.ReactNode }) {
  const isFetching = useIsFetching();
  const loading = isFetching > 0;

  return (
    <>
      {loading ? <WidgetFallback /> : null}
      <div style={{ display: loading ? "none" : "contents" }}>{children}</div>
    </>
  );
}
