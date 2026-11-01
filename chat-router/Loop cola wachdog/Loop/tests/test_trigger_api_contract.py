"""Smoke tests importables: sin proveedores externos ni escrituras."""
import unittest
from pathlib import Path
from nct_loop.trigger_contract import ContractError, validate_contract, validate_loop
from nct_loop.trigger_bridge import TriggerBridge
from nct_loop.trigger_engine import HostPorts

class ContractSmoke(unittest.TestCase):
    def test_rechaza_json_malicioso(self):
        with self.assertRaises(ContractError):
            validate_contract({"schema":"yaiwes.trigger.v1","id":"x"})
    def test_100_slots_rechaza_vacio(self):
        with self.assertRaises(ContractError):
            validate_loop([])
    def test_puertos_no_confian_en_browser(self):
        from nct_loop.trigger_host import build_ports
        with self.assertRaises(ContractError):
            build_ports({"trusted_host":True,"authenticated":False})

if __name__=="__main__":
    unittest.main()
