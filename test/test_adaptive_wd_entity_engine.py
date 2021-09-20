import unittest
import os
import sys
import contextlib
import io
from typing import Final
from wikidataintegrator import wdi_core, wdi_login

from tw_politicians_bot.adaptive_entity_engine import AdaptiveWDEntityEngine

WDUSER = os.getenv("WDUSER")
WDPASS = os.getenv("WDPASS")

assert WDUSER is not None
assert WDPASS is not None

TEST_API_URL = 'https://test.wikidata.org/w/api.php'
TEST_SITE_URL = 'https://test.wikidata.org'


class TestAdaptiveWDEntityEngine(unittest.TestCase):

    Q_Party : Final = 'Q7278'
    P_PartyId : Final = 'P5296'
    P_InstanceOf : Final = 'P31'

    def setUp(self):
        self.test_login = wdi_login.WDLogin(
            user = WDUSER,
            pwd = WDPASS,
            mediawiki_api_url = TEST_API_URL,
            mediawiki_index_url = TEST_SITE_URL,
        )
        print(f'login as {self.test_login.user}')

    def test_AdaptiveWDEntityEngine_findExisting(self, test_item_id = 'Q216013'):
        '''
        Note that this test may fail if the test item [Q216013](https://test.wikidata.org/wiki/Q216013) is modified
        or the test property [P95823](https://test.wikidata.org/wiki/Property:P95823) does not exist.
        '''
        
        partyId = wdi_core.WDString('365', self.P_PartyId)
        instanceOf = wdi_core.WDItemID(self.Q_Party, self.P_InstanceOf)
        data = [instanceOf, partyId]

        item = AdaptiveWDEntityEngine(self.test_login, data=data)
        print(f'item.wd_item_id = {item.wd_item_id}')
        self.assertEqual(item.wd_item_id, test_item_id)

    def test_AdaptiveWDItemEngine_create(self):
        '''
        This test may fail when there is item with same label and description on [Test Wikidata](test.wikidata.org)
        If no error is raised, this function will remove labels and descriptions of the newly created item.
        '''
        new_item = AdaptiveWDEntityEngine(self.test_login, wd_item_id='Q5067368')
        print(f'create new item {new_item.wd_item_id} using api endpoint: {new_item.mediawiki_api_url}')
        self.assertEqual(new_item.mediawiki_api_url, TEST_API_URL)
        self.assertEqual(new_item.wd_json_representation['labels']['zh-tw']['value'], '樹寬值')
        
        for lang in new_item.wd_json_representation['labels']:
            new_item.set_label('', lang)
        for lang in new_item.wd_json_representation['descriptions']:
            new_item.set_description('', lang)
        new_item.write(self.test_login)
    

if __name__ == '__main__':
    unittest.main(verbosity=1, buffer=True)
    
    # with io.StringIO() as buf:
    #     suite = unittest.TestSuite()
    #     import __main__
    #     suite = unittest.TestLoader().loadTestsFromModule(__main__)
    #     with contextlib.redirect_stdout(buf):
    #         result = unittest.TextTestRunner(stream=buf).run(suite)
    #         print(type(result))
    #     print('*** Captured text ***:')
    #     print(buf.getvalue())
    #     print('*** End of captured text ***')