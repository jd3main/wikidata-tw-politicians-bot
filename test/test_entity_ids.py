import unittest
import os
import sys
import contextlib
import io
from wikidataintegrator import wdi_core, wdi_login
from wikidataintegrator.wdi_core import WDItemEngine
from pprint import pprint 

from tw_politicians_bot.entity_ids import ItemIds

WDUSER = os.getenv("WDUSER")
WDPASS = os.getenv("WDPASS")

assert WDUSER is not None
assert WDPASS is not None

TEST_API_URL = 'https://test.wikidata.org/w/api.php'
TEST_SITE_URL = 'https://test.wikidata.org'


class TestEntityIds(unittest.TestCase):
    def setUp(self):
        self.test_login = wdi_login.WDLogin(
            user = WDUSER,
            pwd = WDPASS,
            mediawiki_api_url = TEST_API_URL,
            mediawiki_index_url = TEST_SITE_URL,
        )
        print(f'login as {self.test_login.user}')

    def test_main_site(self):
        print("test_main_site")
        Q = ItemIds()
        self.assertEqual(Q.PARTY, 'Q7278')
        self.assertEqual(Q.HUMAN, 'Q5')

    def test_test_site(self):
        print("test_test_site")
        Q = ItemIds(login_instance=self.test_login)
        testPartyItem = WDItemEngine(wd_item_id=Q.PARTY, mediawiki_api_url=TEST_API_URL, core_props={})
        self.assertEqual(testPartyItem.get_label('zh-tw'), '政黨')

if __name__ == '__main__':
    unittest.main(verbosity=1, buffer=True)

    # print("Starting test")
    # with io.StringIO() as buf:
    #     suite = unittest.TestSuite()
    #     import __main__
    #     suite = unittest.TestLoader().loadTestsFromModule(__main__)
    #     with contextlib.redirect_stdout(buf):
    #         unittest.TextTestRunner(stream=buf).run(suite)
    #     print('*** Captured text ***:')
    #     print(buf.getvalue())
    #     print('*** End of captured text ***')

