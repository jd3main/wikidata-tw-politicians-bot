from typing import Union, MutableMapping

from wikidataintegrator.wdi_core import WDItemEngine
from pywikibot.page import WikibasePage


FALLBACK_CHAIN_ZHTW_EN = ['zh-tw', 'zh-hant', 'zh', 'en']
FALLBACK_CHAIN_ZHTW = ['zh-tw', 'zh-hant', 'zh']


def get_zhtw_label(obj:Union[WDItemEngine, WikibasePage, MutableMapping], include_en=False):
    if include_en:
        return get_label_fallback(obj, FALLBACK_CHAIN_ZHTW_EN)
    else:
        return get_label_fallback(obj, FALLBACK_CHAIN_ZHTW)


def get_label_fallback(obj:Union[WDItemEngine, WikibasePage, MutableMapping], fallback_chain):
    if isinstance(obj, WDItemEngine):
        return get_label_fallback_WDItemEngine(obj, fallback_chain)
    if isinstance(obj, WikibasePage):
        return get_label_fallback_LanguageDict(obj.labels, fallback_chain)
    if isinstance(obj, MutableMapping):
        return get_label_fallback_LanguageDict(obj, fallback_chain)

    raise TypeError


def get_label_fallback_WDItemEngine(item:WDItemEngine, fallback_chain):
    for lang in fallback_chain:
        label = item.get_label(lang)
        if label != '':
            return label
    return ''


def get_label_fallback_LanguageDict(labels:MutableMapping, fallback_chain):
    for lang in fallback_chain:
        label = labels.get(lang)
        if label is not None and label != '':
            return label
    return None
