import os, sys, unittest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from integration.chat_mvp import providers as p


class T(unittest.TestCase):
    def setUp(self):
        for k in ('RIU_OMNIROUTE_BASE_URL', 'RIU_OMNIROUTE_ENABLED', 'OMNIROUTE_API_KEY'):
            os.environ.pop(k, None)

    def test_base_default(self):
        self.assertEqual(p.base_url('omniroute'), 'http://127.0.0.1:20128/v1')

    def test_base_env(self):
        os.environ['RIU_OMNIROUTE_BASE_URL'] = 'http://h:1/v1/'
        self.assertEqual(p.base_url('omniroute'), 'http://h:1/v1')

    def test_off_by_default(self):
        self.assertFalse(p.configured('omniroute'))

    def test_enabled(self):
        os.environ['RIU_OMNIROUTE_ENABLED'] = '1'
        self.assertTrue(p.configured('omniroute'))

    def test_others_untouched(self):
        self.assertEqual(p.base_url('nvidia'), 'https://integrate.api.nvidia.com/v1')


unittest.main() if __name__ == '__main__' else None
