from wikidataintegrator.wdi_core import WDItemEngine


class WDEntityEngine(WDItemEngine):
    '''
    This is a wrapper of WDItemEngine that can also handle property items.
    Type of the entity (and datatype type for properties) will be stored in the json representation.
    '''

    def parse_wd_json(self, wd_json):
        wd_data = super(WDEntityEngine, self).parse_wd_json(wd_json)
        wd_data['type'] = wd_json['type']
        if wd_data['type'] == 'property':
            if 'datatype' in wd_json:
                wd_data['datatype'] = wd_json['datatype']
        return wd_data
