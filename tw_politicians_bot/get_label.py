
from typing import Union

from wikidataintegrator import wdi_core, wdi_login
from wikidataintegrator.wdi_core import WDItemEngine

from pywikibot.page import WikibasePage

FALLBACK_CHAIN_ZHTW_EN = ['zh-tw', 'zh-hant', 'zh', 'en']
FALLBACK_CHAIN_ZHTW = ['zh-tw', 'zh-hant', 'zh']

def get_zhtw_label(item:Union[WDItemEngine,WikibasePage], include_en=False):
    if include_en:
        return get_label_fallback(item, FALLBACK_CHAIN_ZHTW_EN)
    else:
        return get_label_fallback(item, FALLBACK_CHAIN_ZHTW)

def get_label_fallback(item:Union[WDItemEngine,WikibasePage], fallback_chain):
    '''
    Returns
    ---
        lang: str
        label: str
    '''
    if isinstance(item, WDItemEngine):
        return get_label_fallback_WDItemEngine(item, fallback_chain)
    if isinstance(item, WikibasePage):
        return get_label_fallback_WikibasePage(item, fallback_chain)
    else:
        raise TypeError


def get_label_fallback_WDItemEngine(item:WDItemEngine, fallback_chain):
    for lang in fallback_chain:
        label = item.get_label(lang)
        if label != '':
            return label
    return ''


def get_label_fallback_WikibasePage(itemPage:WikibasePage, fallback_chain):
    for lang in fallback_chain:
        label = itemPage.labels.get(lang)
        if label is not None:
            return label
    return None
