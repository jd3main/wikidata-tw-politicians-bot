import requests
from wikidataintegrator.wdi_config import config
from wikidataintegrator.wdi_core import WDSearchError
import wikidataintegrator.wdi_core as wdi_core

WB_SEARCH_DEFAULT_LANG = 'zh-tw'

def wbsearch(search_string='', mediawiki_api_url=None,
                              user_agent=None, max_results=500,
                              language=WB_SEARCH_DEFAULT_LANG, dict_id_label=False, dict_id_all_info=False,
                              **kargs):
        """
        Search in WD by a string
        This fucntion is copied from WDItemEngine.get_wd_search_results() and modified to deal with language correctly.
        It also accepts additional arguments that will be pass to wbsearchentities directly.

        Parameters
        ---
        search_string: str
            a string which should be searched for in WD
        mediawiki_api_url: str
            Specify the mediawiki_api_url.
        user_agent: str
            The user agent string transmitted in the http header
        max_results: int
            The maximum number of search results returned. Default 500
        language: str
            The language in which to perform the search. Default 'en'
        dict_id_label: boolean
            returns a list of QIDs found in the search and a list of labels complementary to the QIDs
        dict_id_all_info: boolean
            returns a list of QIDs found in the search and a list of labels, descriptions, and wikidata urls complementary to the QIDs

        Returns
        ---
        list
            a list of id or list of dicts with id, label, ... etc.
        """

        mediawiki_api_url = config['MEDIAWIKI_API_URL'] if mediawiki_api_url is None else mediawiki_api_url
        user_agent = config['USER_AGENT_DEFAULT'] if user_agent is None else user_agent

        params = {
            'action': 'wbsearchentities',
            'language': language,
            'search': search_string,
            'format': 'json',
            'limit': 50,
            'uselang': language,
            **kargs
        }
        

        headers = {
            'User-Agent': user_agent
        }

        cont_count = 1
        results = []

        while cont_count > 0:
            params.update({'continue': 0 if cont_count == 1 else cont_count})

            reply = requests.get(mediawiki_api_url, params=params, headers=headers)
            reply.raise_for_status()
            search_results = reply.json()

            if search_results['success'] != 1:
                raise WDSearchError('WD search failed')
            else:
                for i in search_results['search']:
                    if dict_id_all_info: # overrides dict_id_label if both are set to True
                        description = i['description'] if 'description' in i else ""
                        url = i['url'] if 'url' in i else ""
                        results.append({'id': i['id'], 'label': i['label'], 'description': description, 'url': url})
                    elif dict_id_label:
                        results.append({'id': i['id'], 'label': i['label']})
                    else:
                        results.append(i['id'])

            if 'search-continue' not in search_results:
                cont_count = 0
            else:
                cont_count = search_results['search-continue']

            if cont_count > max_results:
                break

        return results
