"""Contrato estatico del arranque del Space, sin acceder a HF ni exponer secretos."""
import unittest
from pathlib import Path


PLANTILLA = Path(__file__).with_name("respaldo_space") / "boot_hf_optimizado.sh"


class TestBootHF(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.shell = PLANTILLA.read_text(encoding="utf-8")

    def test_credenciales_de_acceso_obligatorias_pero_web_opcional(self):
        self.assertIn('GITHUB_TOKEN:?Falta GITHUB_TOKEN', self.shell)
        self.assertIn('RIU_API_KEY:?Falta RIU_API_KEY', self.shell)
        self.assertNotIn('WEB_ACCOUNTS:?', self.shell)
        self.assertNotIn('WEB_PASS:?', self.shell)
        self.assertIn('WEB_CUENTAS_OPCIONALES', self.shell)

    def test_conserva_servicios_y_puertos_existentes(self):
        for s in ('7860', '7861', '7870', '/openclaw.sh', 'router-mvp', 'chat-router', 'npm install'):
            self.assertIn(s, self.shell)
        self.assertIn('exec python -m uvicorn proxy:app', self.shell)

    def test_playwright_no_se_espera_para_arrancar_bridge(self):
        self.assertIn('BRIDGE_PORT=7870 BRIDGE_STATE_DIR=/tmp/state exec node', self.shell)
        self.assertIn('node node_modules/playwright/cli.js install chromium', self.shell)
        self.assertNotIn('&& npx playwright install chromium', self.shell)


if __name__ == "__main__":
    unittest.main()
