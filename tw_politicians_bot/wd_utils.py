import copy

from wikidataintegrator import wdi_core, wdi_login
from wikidataintegrator.wdi_core import WDItemEngine, WDItemID

import pywikibot as wiki
from pywikibot import (
    DataSite,
    ItemPage,
    PropertyPage,
    Page
)



def get_wd_repo(isTest = True) -> DataSite:
    if isTest:
        site = wiki.Site()
    else:
        site = wiki.Site('en','wikipedia')
    repo = site.data_repository()
    return repo


def clean_invalid_descriptions(json_data):
    if 'descriptions' not in json_data:
        return
    for lang in list(json_data['descriptions']):
        if lang in json_data['labels'] and json_data['labels'][lang] == json_data['descriptions'][lang]:
            del json_data['descriptions'][lang]


def copy_labels(source:WDItemEngine, target:WDItemEngine, languages=None):
    if languages is None or len(languages)==0:
        target.wd_json_representation['labels'] = copy.deepcopy(source.wd_json_representation['labels'])
    else:
        target.wd_json_representation['labels'] = dict()
        for lang in languages:
            target.wd_json_representation['labels'][lang] = source.wd_json_representation['labels'].get(lang)


def copy_desciptions(source:WDItemEngine, target:WDItemEngine, languages=None):
    if languages is None or len(languages)==0:
        target.wd_json_representation['descriptions'] = copy.deepcopy(source.wd_json_representation['descriptions'])
    else:
        target.wd_json_representation['descriptions'] = dict()
        for lang in languages:
            if lang in source.wd_json_representation['descriptions']:
                target.wd_json_representation['descriptions'][lang] = source.wd_json_representation['descriptions'][lang]


def copy_aliases(source:WDItemEngine, target:WDItemEngine, languages=None):
    if languages is None or len(languages)==0:
        target.wd_json_representation['aliases'] = copy.deepcopy(source.wd_json_representation['aliases'])
    else:
        target.wd_json_representation['aliases'] = dict()
        for lang in languages:
            target.wd_json_representation['aliases'][lang] = source.wd_json_representation['aliases'].get(lang)


def copy_entity_data(source:WDItemEngine, target:WDItemEngine, languages=None,
                     with_labels=True, with_desciptions=True, with_aliases=True, with_claims=False, with_siteLinks=False):
                 
    if 'type' in source.wd_json_representation:
        target.wd_json_representation['type'] = source.wd_json_representation['type']
    if 'datatype' in source.wd_json_representation:
        target.wd_json_representation['datatype'] = source.wd_json_representation['datatype']

    if with_labels:
        copy_labels(source, target, languages)

    if with_desciptions:
        copy_desciptions(source, target, languages)
        clean_invalid_descriptions(target.wd_json_representation)

    if with_aliases:
        copy_aliases(source, target, languages)

    if with_claims:
        target.wd_json_representation['claims'] = copy.deepcopy(source.wd_json_representation['claims'])

    if with_siteLinks:
        target.wd_json_representation['sitelinks'] = copy.deepcopy(source.wd_json_representation['sitelinks'])


def make_statments_dict(statements:WDItemEngine):
    stm_dict = dict()
    for stm in statements:
        if stm.prop_nr not in stm_dict:
            stm_dict[stm.prop_nr] = []
        stm_dict[stm.prop_nr].append(stm)
    return stm_dict


def entity_url(site_url, entity_id) -> str:
    if entity_id is None:
        return ''
    if entity_id[0]=='Q':
        return f'{site_url}/wiki/{entity_id}'
    elif entity_id[0]=='P':
        return f'{site_url}/wiki/Property:{entity_id}'
    else:
        raise ValueError('entity type not supported')

def item_id(wd_item_id: WDItemID):
    if wd_item_id.value is None:
        return None
    else:
        return f'Q{wd_item_id.value}'