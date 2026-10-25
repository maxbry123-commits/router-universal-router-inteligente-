#!/usr/bin/env python3
"""Ejecutar desde carpeta del proyecto NCT anterior luego de aplicar delta."""
import sys
import unittest

if __name__=='__main__':
    tests=unittest.defaultTestLoader.discover('tests',pattern='test_ecc_delta.py')
    r=unittest.TextTestRunner(verbosity=2).run(tests)
    sys.exit(0 if r.wasSuccessful() else 1)
