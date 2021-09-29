from typing import List, Union, Mapping

from pywikibot import (
    ItemPage,
    PropertyPage,
    Claim,
    WbTime,
    WbQuantity,
)


ClaimsDict = Mapping[str, List[Claim]]
DataType = Union[str, ItemPage, PropertyPage, WbTime, WbQuantity]


def create_item(site, label_dict, **kargs):
    new_item = ItemPage(site)
    new_item.editLabels(labels=label_dict, **kargs)
    return new_item


def create_property(site, label_dict, datatype, **kargs):
    new_prop = PropertyPage(site, None, datatype)
    new_prop.editLabels(labels=label_dict, **kargs)
    return new_prop


def make_claim(site, prop, value:DataType,
               snak=None, hash=None, is_reference=False, is_qualifier=False, rank='normal', **kargs):
    claim = Claim(site, prop, snak, hash, is_reference, is_qualifier, rank, **kargs)
    claim.setTarget(value)
    return claim


def find_claim(claims:ClaimsDict, prop, value:DataType) -> Union[Claim, None]:
    if prop not in claims:
        return None
    for claim in claims[prop]:
        if claim.target_equals(value):
            return claim
    return None


def set_claim(claims:ClaimsDict, site, prop, value:DataType,
              is_reference=False, is_qualifier=False, **kargs) -> Claim:
    found_claim = find_claim(claims, prop, value)
    if found_claim is not None:
        return found_claim
    new_claim = make_claim(site, prop, value, is_reference=is_reference, is_qualifier=is_qualifier, **kargs)
    claims.setdefault(prop, []).append(new_claim)
    return new_claim
