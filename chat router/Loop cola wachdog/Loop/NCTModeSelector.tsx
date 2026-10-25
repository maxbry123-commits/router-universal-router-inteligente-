import React from "react";

/** Componente aislado: cablear onChange al state/store YA EXISTENTE de la UI. */
type Mode = "manual" | "semi_auto" | "nct_continuous";
export function NCTModeSelector({
  mode,
  onChange,
  disabled = false,
}: {
  mode: Mode;
  onChange: (mode: Mode) => void;
  disabled?: boolean;
}) {
  const choices: { value: Mode; label: string }[] = [
    { value: "manual", label: "Manual" },
    { value: "semi_auto", label: "Semi-automático" },
    { value: "nct_continuous", label: "Continuo (NCT)" },
  ];
  return (
    <div role="group" aria-label="Modo de trabajo" style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {choices.map((choice) => (
        <button
          key={choice.value}
          type="button"
          disabled={disabled}
          aria-pressed={mode === choice.value}
          onClick={() => onChange(choice.value)}
          style={{
            fontFamily: "inherit", fontSize: 13, fontWeight: 600,
            borderRadius: 9, padding: "9px 14px", cursor: disabled ? "not-allowed" : "pointer",
            backgroundColor: mode === choice.value ? "#e8f2ff" : "#ffffff",
            color: mode === choice.value ? "#176bce" : "#303b4b",
            border: `1px solid ${mode === choice.value ? "#176bce" : "#e3e7ed"}`,
          }}
        >
          {choice.label}
        </button>
      ))}
    </div>
  );
}
