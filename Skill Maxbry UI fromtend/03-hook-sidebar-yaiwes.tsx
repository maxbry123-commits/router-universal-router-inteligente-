"use client";

import {
  HookSidebar,
  type HookSidebarItem,
} from "@/components/ui/hook-sidebar";

const DEFAULT_ITEMS: HookSidebarItem[] = [
  "Resumen",
  "Actividad",
  "Tareas",
  "Integraciones",
  "Ajustes",
];

export function HookSidebarYaiwes({
  items = DEFAULT_ITEMS,
}: {
  items?: HookSidebarItem[];
}) {
  return (
    <div
      data-yaiwes-component="hook-sidebar"
      style={{
        width: 260,
        padding: 24,
        borderRadius: 18,
        border: "1px solid #3A3A3A",
        background: "#202020",
        color: "#EDEDED",
      }}
    >
      <HookSidebar
        label="YAIWES"
        items={items}
        color="#0848F7"
        dashed
      />
    </div>
  );
}
