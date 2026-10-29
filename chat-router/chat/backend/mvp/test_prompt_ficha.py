"""El system prompt vive solo en la ficha (fichas/system-prompt); el Router MVP no guarda otra copia."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from mvp import prompt

REPO = Path(__file__).resolve().parents[4]


class PromptDeLaFicha(unittest.TestCase):
    def test_lee_de_fichas_system_prompt(self):
        self.assertEqual(prompt.FICHA, REPO / "router-mvp" / "fichas" / "system-prompt")
        primera = (REPO / "router-mvp" / "fichas" / "system-prompt" / "system_core.md").read_text(encoding="utf-8").strip().splitlines()[0]
        self.assertIn(primera, prompt.sistema())

    def test_el_router_no_guarda_otra_copia(self):
        self.assertFalse((Path(__file__).resolve().parent / "system-prompt").exists())


if __name__ == "__main__":
    unittest.main()
