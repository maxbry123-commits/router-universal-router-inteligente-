"use client";

import { Folder } from "@/components/ui/folder-component";

type FolderYaiwesProps = {
  size?: "sm" | "md" | "lg";
  className?: string;
};

export function FolderYaiwes({
  size = "md",
  className,
}: FolderYaiwesProps) {
  return (
    <div
      className={className}
      data-yaiwes-component="folder"
      style={{
        display: "grid",
        placeItems: "center",
        minHeight: 320,
        background: "#1B1B1B",
      }}
    >
      <Folder color="black" size={size} />
    </div>
  );
}
