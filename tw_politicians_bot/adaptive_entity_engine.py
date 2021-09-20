import os
import code
import pandas as pd
import atexit

from .wd_entity_engine import WDEntityEngine
from .wd_utils import copy_entity_data
from .get_label import get_label_fallback, FALLBACK_CHAIN_ZHTW_EN
from .wbsearch import wbsearch

NORMAL_API_URL = 'https://www.wikidata.org/w/api.php'

class AdaptiveWDEntityEngine(WDEntityEngine):
    '''
    A wrapper of WDEntityEngine that will try to find corresponding item when the test site has no query service.
    Depending on the login_instance, when www.wikidata.org is used, this function act as if the constructor of WDItemEngine.
    When the testing api endpoint is used (e.g. https://test.wikidata.org/w/api.php),
    this function will try to find an item with same label in the test site.
    If such item cannot be found in test site, then the item will be copied from www.wikidata.org to the test site.
    '''

    cache_filename = 'entity_ids_cache.csv'
    test_entity_ids = dict()

    def __init__(self, login_instance=None, max_search_results=10, languages=FALLBACK_CHAIN_ZHTW_EN, **kwargs):
        pass

    def __new__(cls, login_instance=None, max_search_results=10, languages=FALLBACK_CHAIN_ZHTW_EN, **kwargs):
        return cls._get_adapted_entity(login_instance = login_instance,
                                       max_search_results = max_search_results,
                                       languages = languages,
                                       **kwargs)

    @classmethod
    def get_adapted_entity(cls, login_instance, main_id):
        return cls._get_adapted_entity(login_instance, wd_item_id=main_id)

    @classmethod
    def get_adapted_entity_id(cls, login_instance, main_id):
        return cls._get_adapted_entity(login_instance, id_only=True, wd_item_id=main_id)

    # @classmethod
    # def _get_adapted_entity_id(cls, login_instance, max_search_results=10, languages=FALLBACK_CHAIN_ZHTW_EN, **kwargs):
    #     return cls.get_adapted_entity(login_instance, max_search_results, languages, id_only=True, **kwargs)

    @classmethod
    def _get_adapted_entity(cls, login_instance, max_search_results=10, languages=FALLBACK_CHAIN_ZHTW_EN, id_only=False, **kwargs):

        if login_instance is None or login_instance.mediawiki_api_url==NORMAL_API_URL:
            if id_only:
                return kwargs.get('wd_item_id')
            else:
                return WDEntityEngine(**kwargs)

        test_api_url = login_instance.mediawiki_api_url
        
        kwargs['search_only'] = True

        # search in cache
        if kwargs.get('wd_item_id') is not None:
            id = kwargs['wd_item_id']
            test_id = cls.cache_get(id)
            if test_id is not None:
                if id_only:
                    return test_id
                else:
                    return WDEntityEngine(test_id, mediawiki_api_url=test_api_url, core_props={})
                
        # find corresponding entity or create one if not found
        wd_kwargs = kwargs.copy()
        wd_kwargs['mediawiki_api_url'] = NORMAL_API_URL
        entity = WDEntityEngine(**wd_kwargs)
        id = entity.wd_item_id
        
        if id != '':
            # search corresponding item
            label_lang, wd_label = get_label_fallback(entity, languages)
            
            entity_type = entity.wd_json_representation['type']
            property_datatype = entity.wd_json_representation.get('datatype')

            search_results = wbsearch(wd_label, max_results=max_search_results,
                                                language=label_lang, mediawiki_api_url=test_api_url, dict_id_label=True,
                                                type=entity_type)

            for result in search_results:
                result_id = result['id']
                result_label = result['label']
                if result_label == wd_label:
                    found_entity = WDEntityEngine(wd_item_id=result_id, mediawiki_api_url=test_api_url, core_props={})
                    if found_entity.wd_json_representation.get('datatype') != property_datatype:
                        continue
                    found_id = found_entity.wd_item_id
                    cls.cache_set(entity.wd_item_id, found_id)
                    print(f'Adapted: {wd_label} ({found_id})')

                    if id_only:
                        return found_id
                    else:
                        return found_entity

            # create when not found
            new_entity = WDEntityEngine(new_item=True, mediawiki_api_url=test_api_url, core_props={})
            copy_entity_data(entity, new_entity, languages=[label_lang], with_aliases=False)
            
            new_id = new_entity.write(login_instance, entity_type=entity_type, property_datatype=property_datatype)
            cls.cache_set(entity.wd_item_id, new_id)
            print(f'Created: {wd_label} ({new_id})')

            if id_only:
                return new_id
            else:
                return new_entity

        else:
            return None

    @classmethod
    def cache_set(cls, main_id, test_id):
        cls.test_entity_ids[main_id] = test_id

    @classmethod
    def cache_get(cls, main_id):
        return cls.test_entity_ids.get(main_id)

    @classmethod
    def cache_save(cls):
        df = pd.DataFrame(cls.test_entity_ids.items())
        df.to_csv(cls.cache_filename, index=False, header=False)
    
    @classmethod
    def cache_load(cls):
        if os.path.isfile(cls.cache_filename):
            df = pd.read_csv(cls.cache_filename, header=None)
            cls.test_entity_ids = dict(zip(list(df[0]), list(df[1])))



AdaptiveWDEntityEngine.cache_load()
atexit.register(AdaptiveWDEntityEngine.cache_save)
