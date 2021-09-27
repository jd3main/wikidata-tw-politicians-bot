import atexit
import os

import pandas as pd

from pywikibot import (
    Site,
    DataSite,
    ItemPage,
    PropertyPage,
)
from pywikibot.page import WikibasePage

from .get_label import get_label_fallback, FALLBACK_CHAIN_ZHTW_EN
from .wd_utils import create_item, create_property


MAIN_SITE = Site('wikidata', 'wikidata')
TEST_SITE = Site('test', 'wikidata')

class AdaptiveEntity(ItemPage, PropertyPage):
    
    cache_filename = 'entity_ids_cache.csv'
    test_entity_ids = dict()


    def __init__(self, site:DataSite, entity_id, ns=None,  search_limit=5, languages=FALLBACK_CHAIN_ZHTW_EN):
        pass

    def __new__(cls, site:DataSite, entity_id, ns=None, search_limit=5, languages=FALLBACK_CHAIN_ZHTW_EN):
        if entity_id[0] == 'Q':
            entity = ItemPage(MAIN_SITE, entity_id, ns)
        elif entity_id[0] == 'P':
            entity = PropertyPage(MAIN_SITE, entity_id)
        else:
            raise ValueError('non supported entity type')

        if site.sitename == TEST_SITE.sitename:
            return cls.adapt(entity)
        else:
            return entity


    @classmethod
    def adapt(cls, wd_entity:WikibasePage, search_limit=5, languages=FALLBACK_CHAIN_ZHTW_EN):
        
        assert wd_entity.site.sitename == 'wikidata:wikidata'
        
        # search in cache
        test_id = cls.cache_get(wd_entity.getID())
        if test_id is not None:
            if test_id[0] == 'Q':
                return ItemPage(TEST_SITE, test_id)
            elif test_id[0] == 'P':
                return PropertyPage(TEST_SITE, test_id)


        # search corresponding item
        wd_label = get_label_fallback(wd_entity, languages)

        search_results = TEST_SITE.search_entities(wd_label,
                                                   languages[0],
                                                   total = search_limit,
                                                   type = wd_entity.entity_type)

        for result in search_results:
            result_id = result['id']
            result_label = result['label']
            if result_label == wd_label:
                if wd_entity.entity_type == 'item':
                    found_entity = ItemPage(TEST_SITE, result_id)
                elif wd_entity.entity_type == 'property':
                    found_entity = PropertyPage(TEST_SITE, result_id)
                    if found_entity.type != wd_entity.type:
                        continue
                cls.cache_set(wd_entity.getID(), found_entity.getID())
                print(f'Adapted: {wd_label} ({wd_entity.getID()}) -> ({found_entity.getID()})')

                return found_entity

        # create when not found

        labels = {languages[0]: wd_label}
        if wd_entity.entity_type == 'item':
            new_entity = create_item(TEST_SITE, labels)
        elif wd_entity.entity_type == 'property':
            new_entity = create_property(TEST_SITE, labels, wd_entity.entity_type)
        
        cls.cache_set(wd_entity.getID(), new_entity.getID())
        print(f'Created: {wd_label} ({new_entity.getID()})')

        return new_entity


    @classmethod
    def cache_set(cls, main_id:str, test_id:str):
        cls.test_entity_ids[main_id] = test_id
        cls.cache_save()

    @classmethod
    def cache_get(cls, main_id:str):
        return cls.test_entity_ids.get(main_id)

    @classmethod
    def cache_save(cls):
        df = pd.DataFrame(cls.test_entity_ids.items())
        df.to_csv(cls.cache_filename, index=False, header=False)
    
    @classmethod
    def cache_load(cls):
        assert os.path.isfile(cls.cache_filename)
        df = pd.read_csv(cls.cache_filename, header=None)
        cls.test_entity_ids = dict(zip(list(df[0]), list(df[1])))


AdaptiveEntity.cache_load()
atexit.register(AdaptiveEntity.cache_save)