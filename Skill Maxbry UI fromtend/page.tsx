import { FolderYaiwes } from "@/components/yaiwes/01-folder-yaiwes";
import { BounceSidebarYaiwes } from "@/components/yaiwes/02-bounce-sidebar-yaiwes";
import { HookSidebarYaiwes } from "@/components/yaiwes/03-hook-sidebar-yaiwes";
import { FamilyDrawerYaiwes } from "@/components/yaiwes/04-family-drawer-yaiwes";
import { ProximitySidebarYaiwes } from "@/components/yaiwes/05-proximity-sidebar-yaiwes";

const panelStyle = {
  border: "1px solid #3A3A3A",
  borderRadius: 24,
  background: "#202020",
  padding: 20,
} as const;

export default function RuiDemoPage() {
  return (
    <main
      style={{
        minHeight: "100vh",
        background: "#1B1B1B",
        color: "#EDEDED",
        padding: 24,
      }}
    >
      <h1 style={{ marginTop: 0 }}>Rare UI → YAIWES · 01–05</h1>

      <div
        style={{
          display: "grid",
          gridTemplateColumns: "repeat(auto-fit, minmax(320px, 1fr))",
          gap: 18,
        }}
      >
        <section style={panelStyle}>
          <h2>01 · Folder</h2>
          <FolderYaiwes />
        </section>

        <section style={panelStyle}>
          <h2>02 · Bounce Sidebar</h2>
          <BounceSidebarYaiwes />
        </section>

        <section style={panelStyle}>
          <h2>03 · Hook Sidebar</h2>
          <HookSidebarYaiwes />
        </section>

        <section style={panelStyle}>
          <h2>04 · Family Drawer</h2>
          <FamilyDrawerYaiwes />
        </section>

        <section style={{ ...panelStyle, gridColumn: "1 / -1" }}>
          <h2>05 · Proximity Sidebar</h2>
          <ProximitySidebarYaiwes />
        </section>
      </div>
    </main>
  );
}
