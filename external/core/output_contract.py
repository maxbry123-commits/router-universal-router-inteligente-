"""output_contract.py — Pydantic strict OutputContract (8 campos)"""
from __future__ import annotations
from pydantic import BaseModel, ConfigDict, Field
from typing import Literal, List, Optional


class OutputContract(BaseModel):
    model_config = ConfigDict(extra="forbid")

    task: str = Field(..., min_length=1, max_length=200)
    respuesta: str = Field(..., max_length=200)
    analisis: List[str] = Field(..., min_length=1)
    conclusion: str = Field(..., min_length=1)
    propuesta: str = Field(..., min_length=1)
    estado: Literal["COMPLETADO", "EN_PROCESO", "BLOQUEADO"]
    gaps: Optional[List[str]] = None
    goals_pass: int = Field(0, ge=0, le=12)

    def validate_or_raise(self) -> OutputContract:
        if self.estado == "BLOQUEADO" and not self.propuesta:
            raise ValueError("BLOQUEADO exige propuesta de desbloqueo")
        return self

    @classmethod
    def quick(cls, task: str, respuesta: str,
              estado: Literal["COMPLETADO", "EN_PROCESO", "BLOQUEADO"],
              analisis: Optional[List[str]] = None,
              conclusion: str = "", propuesta: str = "",
              gaps: Optional[List[str]] = None, goals_pass: int = 0) -> OutputContract:
        return cls(
            task=task, respuesta=respuesta,
            analisis=analisis or ["Sin analisis"],
            conclusion=conclusion or "Sin conclusion",
            propuesta=propuesta or "Sin propuesta",
            estado=estado, gaps=gaps, goals_pass=goals_pass,
        )
