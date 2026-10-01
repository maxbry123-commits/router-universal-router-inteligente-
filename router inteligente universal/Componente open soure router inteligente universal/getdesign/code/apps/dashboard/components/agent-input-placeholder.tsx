"use client";

import { InputBar } from "@/components/agent-elements/input-bar";

/** Keep the disabled input's callbacks inside the client boundary. */
export function AgentInputPlaceholder() {
  return (
    <InputBar
      size="lg"
      value=""
      onChange={() => {}}
      sendLabel="Start extraction"
      className="px-0 pb-0"
      status="ready"
      disabled
      placeholder="Enter a URL..."
      onStop={() => {}}
      onSend={() => {}}
    />
  );
}
