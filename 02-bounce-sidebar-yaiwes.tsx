"use client";

import {
  BounceSidebar,
  type BounceSidebarItem,
} from "@/components/ui/bounce-sidebar";

const DEFAULT_ITEMS: BounceSidebarItem[] = [
  { label: "Navegación", heading: true },
  "Inicio",
  "Chat",
  "Archivos",
  "Agentes",
  "Ajustes",
];

export function BounceSidebarYaiwes({
  items = DEFAULT_ITEMS,
}: {
  items?: BounceSidebarItem[];
}) {
  return (
    <div
      data-yaiwes-component="bounce-sidebar"
      style={{
        width: 260,
        padding: 24,
        borderRadius: 18,
        border: "1px solid #3A3A3A",
        background: "#202020",
        color: "#EDEDED",
      }}
    >
      <BounceSidebar items={items} dotColor="#0848F7" />
    </div>
  );
}
