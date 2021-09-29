import os
import pickle

from .adaptive_entity import AdaptiveEntity



class EntityIds():

    def __init__(self, site):
        self.site = site
        self.adapt()

    def adapt(self):
        if self.site.sitename != 'wikidata:wikidata':
            for field in self.get_constant_fields():
                main_id = getattr(self, field)
                test_id = AdaptiveEntity(self.site, main_id).getID()
                setattr(self, field, test_id)

    def get_constant_fields(self):
        return [f for f in dir(self.__class__) if f.isupper()]


class ItemIds(EntityIds):
    PARTY = 'Q7278'
    HUMAN = 'Q5'
    TAIWAN = 'Q865'
    MALE = 'Q6581097'
    FEMALE = 'Q6581072'
    POLITICIAN = 'Q82955'
    NATIONAL_LANGUAGE_OF_ROC = 'Q262828'
    TAIWAN_LEGISLATIVE_ELECTION_REGIONAL_DISTRICT = 'Q19409201'     
    HIGHLAND_ABORIGINE_DISTRICT = 'Q21055063'
    LOWLAND_ABORIGINE_DISTRICT = 'Q21041600'
    INDEPENDENT_POLITICIAN = 'Q327591'


class PropertyIds(EntityIds):
    PARTY_ID = 'P5296'
    INSTANCE_OF = 'P31'
    NATIONALITY = 'P27'
    GENDER = 'P21'
    DATE_OF_BIRTH = 'P569'
    OCCUPATION = 'P106'
    CANDIDACY = 'P3602'
    REPRESENTS = 'P1268'
    ELECTORAL_DISTRICT = 'P768'
    VOTES_RECEIVED = 'P1111'
    CANDIDATE_NUMBER = 'P4243'
    REFERENCE_URL = 'P854'
    LANGUAGE_OF_WORK = 'P407'
    RETRIEVED = 'P813'
    HRCIS_CODE = 'P5020'
    PARTY_MEMBERSHIP = 'P102'	
    CBDB_ID = 'P497'
