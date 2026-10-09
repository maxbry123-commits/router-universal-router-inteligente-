"use client";

import FamilyDrawer from "@/components/ui/family-drawer";

export function FamilyDrawerYaiwes() {
  return (
    <div
      data-yaiwes-component="family-drawer"
      className="relative overflow-hidden"
      style={{
        minHeight: 480,
        borderRadius: 24,
        border: "1px solid #3A3A3A",
        background: "#1B1B1B",
      }}
    >
      <FamilyDrawer />
    </div>
  );
}
