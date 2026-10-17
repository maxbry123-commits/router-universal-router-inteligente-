"use client";

import ProximitySidebar, {
  type ProximitySection,
} from "@/components/ui/proximity-sidebar";

const SECTIONS: ProximitySection[] = [
  { id: "rui-title", label: "Título", kind: "title" },
  { id: "rui-subtitle", label: "Subtítulo", kind: "subtitle" },
  { id: "rui-section", label: "Sección", kind: "section" },
  { id: "rui-body", label: "Cuerpo", kind: "body" },
];

export function ProximitySidebarYaiwes() {
  return (
    <div
      data-yaiwes-component="proximity-sidebar"
      style={{
        display: "grid",
        gridTemplateColumns: "150px minmax(0, 1fr)",
        minHeight: 520,
        overflow: "hidden",
        borderRadius: 24,
        border: "1px solid #3A3A3A",
        background: "#1B1B1B",
        color: "#EDEDED",
      }}
    >
      <aside
        style={{
          minHeight: 0,
          borderRight: "1px solid #3A3A3A",
          background: "#202020",
        }}
      >
        <ProximitySidebar sections={SECTIONS} side="left" />
      </aside>

      <div
        style={{
          height: 520,
          overflowY: "auto",
          padding: 28,
        }}
      >
        <section id="rui-title" style={{ minHeight: 300 }}>
          <h1 style={{ fontSize: 34, margin: 0 }}>Título YAIWES</h1>
          <p style={{ color: "#BFBFBF" }}>
            El minimapa conserva el comportamiento por proximidad.
          </p>
        </section>

        <section id="rui-subtitle" style={{ minHeight: 300 }}>
          <h2>Subtítulo</h2>
          <p style={{ color: "#BFBFBF" }}>
            La capa cromática usa los tokens grises aprobados.
          </p>
        </section>

        <section id="rui-section" style={{ minHeight: 300 }}>
          <h3>Sección</h3>
          <p style={{ color: "#BFBFBF" }}>
            Las rayas reaccionan a la distancia del puntero.
          </p>
        </section>

        <section id="rui-body" style={{ minHeight: 300 }}>
          <h4>Cuerpo</h4>
          <p style={{ color: "#BFBFBF" }}>
            Fin de la prueba funcional del componente.
          </p>
        </section>
      </div>
    </div>
  );
}
