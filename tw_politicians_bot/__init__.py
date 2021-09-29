from pprint import pprint
import copy
import code
import os
from re import L
import tkinter as tk
import tkinter.filedialog
import itertools
from typing import List, Dict, Tuple
import time
import csv
from dataclasses import dataclass

from pywikibot import (
    Site,
    ItemPage,
    Claim,
    WbTime,
    WbQuantity,
)
from pywikibot.site import DataSite
from pywikibot.data.api import LoginManager
from pywikibot.page._collections import (
    LanguageDict,
    ClaimCollection,
)

from wikidataintegrator import wdi_core, wdi_login

from .election_data import ElectionData, Gender, District, Candidate, DistrictCode
from .wbsearch import wbsearch
from .entity_ids import ItemIds, PropertyIds
from .wb_time_utils import WbTimePrecision, time_match
from .get_label import get_zhtw_label
from .adaptive_entity import AdaptiveEntity
from .wd_utils import (
    entity_url,
    make_claim,
    find_claim,
    set_claim,
)
from .print_utils import options_interface

# Constants
NO_PARTY = '999'
REFERENCE_URL = 'https://data.gov.tw/dataset/13119'
DATA_RETRIEVED_TIME = WbTime.fromTimestr('+2020-09-07T00:00:00Z', WbTimePrecision.DAY)
WD_URL = 'https://www.wikidata.org'
WD_API_URL = 'https://www.wikidata.org/w/api.php'
TEST_WD_URL = 'https://test.wikidata.org'
TEST_WD_API_URL = 'https://test.wikidata.org/w/api.php'

ELECTORAL_DISTRICT_OPTIONS = ['行政區', '區域立委', '山地立委', '平地立委', '其他']
ELECTION_ID_FILENAME = 'election_id.csv'

WD_SITE:DataSite = Site('wikidata','wikidata')
TEST_WD_SITE:DataSite = Site('test','wikidata')

MAIN_P = PropertyIds(WD_SITE)

IS_TEST = True
SITE_URL = ''
API_URL = ''
SITE = None

P = None
Q = None

ModificationList = List[Tuple[ItemPage,Dict]]



def main(is_test=True, head=-1, sleep_time=0):

    initialize(is_test)

    root = tk.Tk()
    root.overrideredirect(True)
    root.geometry('0x0+0+0')
    root.withdraw()
    

    party_entity_mapping_file = 'PartyID-EntityID.csv'
    if not os.path.isfile(party_entity_mapping_file):
        print(f'找不到 {party_entity_mapping_file}，請手動指定')
        party_entity_mapping_file = tk.filedialog.askdirectory(title='PartyID-EntityID.csv', initialdir=f'{os.getcwd()}/votedata')


    print(f'-----------------------------')
    print(f'請選擇匯入來源')
    # force the window to show on top once
    root.wm_attributes('-topmost', 1)
    root.deiconify()
    root.lift()
    root.focus_force()
    root.wm_attributes('-topmost', 0)

    dir_name = tk.filedialog.askdirectory(parent=root, title='匯入來源', mustexist=True, initialdir=os.getcwd())
    root.withdraw()
    print(f'匯入自：{dir_name}')
    print(f'-----------------------------')

    input_district_type = int(options_interface(
        '[選擇選區類型]',
        [
            '行政區 (僅支援2016年以後的格式)',
            '區域立委',
            '山地立委',
            '平地立委',
            '其他 (將會忽略選區資料)',
        ],
        input_description='：'
    ))
    district_type = ELECTORAL_DISTRICT_OPTIONS[input_district_type - 1]

    
    election_item = None
    while True:
        print(f'----------------------------------')
        print('輸入該選舉的 Wikidata ID')
        print(f'或要讀取 {ELECTION_ID_FILENAME} 則輸入空白行')

        input_election_item_id = input('輸入：').upper()
        if input_election_item_id == '':
            try:
                load_election_item_id_mapping(f'{dir_name}/{ELECTION_ID_FILENAME}')
            except OSError as err:
                print(f'找不到 {ELECTION_ID_FILENAME}，要協助創建嗎？')
                if input('(Y/N): ').upper() == 'Y':
                    election_id_create_interface(dir_name, district_type)
                continue
            except Exception as err:
                print(f'{err}')
                print(f'關於 {ELECTION_ID_FILENAME} 請參閱說明文件')
                continue
            break

        election_item = AdaptiveEntity(SITE, input_election_item_id)
        print()
        print(f'    {get_zhtw_label(election_item)} ({entity_url(SITE_URL, election_item.getID())})')
        print()
        confirm = input('是否正確？ (Y/n): ').upper()
        if confirm == 'N':
            continue
        else:
            break

    print(f'----------------------------------')

    # Load Data
    print('Loading data')
    load_party_mapping(party_entity_mapping_file)
    election_data = ElectionData(dir_name, district_type)
    print(f'已載入 {len(election_data.candidates)} 筆候選人資料')
    print('-----------------------------')

    items_data = prepare_candidate_items_data(SITE, election_data, district_type, election_item, head)

    print('-----------------------------')
    new_item_count = sum(1 for (item, _) in items_data if item.getID()=='-1')
    modify_item_count = len(items_data) - new_item_count
    print(f'新增: {new_item_count}')
    print(f'修改: {modify_item_count}')
    
    while True:
        print('-----------------------------')
        print('  S) start import')
        print('  C) cancel')
        print('  L) list')
        print('  D) debug')
        print('')
        action = input('Action: ').upper()
        if action == 'S':
            print('開始匯入')
            write_candidates_data(SITE, items_data, sleep_time)
            break
        if action == 'C':
            print('取消匯入')
            break
        if action == 'L':
            print_modifications(items_data)
            continue
        if action == 'D':
            code.interact(local=dict(globals(), **locals()))


    code.interact(local=dict(globals(), **locals()))



def initialize(is_test=True):
    global IS_TEST
    global SITE_URL
    global API_URL
    global SITE
    global Q
    global P

    IS_TEST = is_test
    if IS_TEST:
        SITE = TEST_WD_SITE
        SITE_URL = TEST_WD_URL
        API_URL = TEST_WD_API_URL
    else:
        SITE = WD_SITE
        SITE_URL = WD_URL
        API_URL = WD_API_URL

    
    # Login
    WDPASS = os.getenv("WDPASS")
    if WDPASS is None:
        raise ValueError('Environment variable "WDPASS" is required.')

    L = LoginManager(password=WDPASS, site=SITE)
    success = L.login()
    assert success

    Q = ItemIds(SITE)
    P = PropertyIds(SITE)

    print(f'-------------------------')
    print(f'User Name: {L.username}')
    print(f'IS_TEST: {IS_TEST}')
    print(f'-------------------------')


def prepare_candidate_items_data(site, election_data:ElectionData, district_type, election_item:ItemPage, head=-1) -> ModificationList:
    items_data:ModificationList = []

    # For test run
    candidates = election_data.candidates.values()
    if head != -1:
        candidates = itertools.islice(candidates, head)

    for cand in candidates:
        print('-----------------------------')
        print(cand)

        item = None

        search_results = wbsearch(cand.legal_name, API_URL, language='zh-tw', dict_id_label=True, type='item')

        if len(search_results) > 0:
            result_confidences = []
            result_items = []
            for result in search_results:
                id = result['id']
                label = result['label']
                if label != cand.legal_name:
                    continue
                found_item = ItemPage(SITE, id)
                confidence = same_person_confidence(found_item, cand)
                if confidence >= 1:
                    result_confidences.append(confidence)
                    result_items.append(found_item)
                    print(f'({confidence}) {result}')

            if len(result_confidences) > 0:
                max_confidence = max(result_confidences)
                print(f'max_confidence: {max_confidence}')
                best_matched_items = [result_items[i] for i, c in enumerate(result_confidences) if c==max_confidence]
                
                if len(best_matched_items) > 1:
                    raise ValueError('multiple results with same confidence')
                
                best_matched_item = best_matched_items[0]
                print(f'best matched item: {get_zhtw_label(best_matched_item)} ({best_matched_item.concept_uri()})')

                item = best_matched_item

        if item is None:
            print(f'item not yet exist')
            item = ItemPage(SITE)
            data = {
                'labels': LanguageDict({'zh-tw': cand.legal_name}),
                'claims': ClaimCollection(site),
            }
        else:
            data = item.get()
            
        # Set data
        # * [v] 性質 (P31) -> 人類 (Q5)
        # * [v] 國籍 (P27) -> 中華民國 (Q865)
        # * [v] 性別 (P21) -> 男或女        (+參考文獻)
        # * [v] 出生日期 (P569)             (+參考文獻)
        # * [v] 競選(P3602) -> 參與的選舉   (+參考文獻)
        #     * [v] 選區 (P768) -> (Item)
        #     * [v] 代表對象 (P1268) -> (Item) //推薦政黨
        #     * [v] 得票數 (P1111) -> (Quantity)
        #     * [v] 候選人號次 (P4243) -> (String)
        # * [ ] 參考文獻結構
        #     * [ ] 來源網址 (P854) : [政府資料開放平台](https://data.gov.tw/dataset/13119)
        #     * [ ] 作品或名稱語言 (P407) : 中華民國國語 (Q262828)
        #     * [ ] 檢索日期 (P813)

        instance_of = set_claim(data['claims'], site, P.INSTANCE_OF, ItemPage(site, Q.HUMAN))
        nationality = set_claim(data['claims'], site, P.NATIONALITY, ItemPage(site, Q.TAIWAN))

        if cand.gender == Gender.MALE:
            gender = set_claim(data['claims'], site, P.GENDER, ItemPage(site, Q.MALE))
        elif cand.gender == Gender.FEMALE:
            gender = set_claim(data['claims'], site, P.GENDER, ItemPage(site, Q.FEMALE))

        # Date of birth. If our data have higher precision and have no conflict, replace the existing value
        if P.DATE_OF_BIRTH in data['claims']:
            date_of_birth:Claim = data['claims'][P.DATE_OF_BIRTH][0]
            if time_match(date_of_birth.getTarget(), cand.birth_date):
                if date_of_birth.getTarget().precision < cand.birth_date.precision:
                    date_of_birth.setTarget(cand.birth_date)
            else:
                date_of_birth = set_claim(data['claims'], site, P.DATE_OF_BIRTH, cand.birth_date)
        else:
            date_of_birth = set_claim(data['claims'], site, P.DATE_OF_BIRTH, cand.birth_date)

        # Candidacy
        if election_item is None:
            election_item = get_election_item(site, str(cand.district.code))
        candidacy = set_claim(data['claims'], site, P.CANDIDACY, election_item)
        
        district_item = get_district_item(site, cand.district, district_type)
        if district_item is not None:
            set_claim(candidacy.qualifiers, site, P.ELECTORAL_DISTRICT, district_item, is_qualifier=True)

        set_claim(candidacy.qualifiers, site, P.REPRESENTS, get_party_item(site, cand.party_id), is_qualifier=True)
        set_claim(candidacy.qualifiers, site, P.VOTES_RECEIVED, WbQuantity(cand.votes), is_qualifier=True)
        set_claim(candidacy.qualifiers, site, P.CANDIDATE_NUMBER, cand.number, is_qualifier=True)

        references = [
            make_claim(site, P.REFERENCE_URL, REFERENCE_URL, is_reference=True),
            make_claim(site, P.LANGUAGE_OF_WORK, ItemPage(site, Q.NATIONAL_LANGUAGE_OF_ROC), is_reference=True),
            make_claim(site, P.RETRIEVED, DATA_RETRIEVED_TIME, is_reference=True),
        ]

        claims_to_add_references = [gender, date_of_birth, candidacy]
        for claim in claims_to_add_references:
            if len(claim.sources) == 0:
                claim.addSources(copy.deepcopy(references))

        items_data.append((item,data))

    return items_data



def get_district_item(site:DataSite, district:District, district_type:str):

    if district_type not in ELECTORAL_DISTRICT_OPTIONS:
        raise ValueError(f'district_type should be one of {ELECTORAL_DISTRICT_OPTIONS}')

    if district_type == '行政區':
        hrcis_code = district.code.HRCIS_str
        if len(hrcis_code)==2:
            hrcis_code += '000'
        data = [wdi_core.WDString(hrcis_code, MAIN_P.HRCIS_CODE)]
        item = wdi_core.WDItemEngine(data=data, core_props={MAIN_P.HRCIS_CODE})
        return AdaptiveEntity(site, item.wd_item_id)

    elif district_type == '區域立委':
        search_results = list(WD_SITE.search_entities(district.name, 'zh-tw', 5))
        if len(search_results) == 0:
            return None
        result = search_results[0]
        id = result['id']
        return AdaptiveEntity(site, id)

    elif district_type == '山地立委':
        return ItemPage(Q.HIGHLAND_ABORIGINE_DISTRICT)

    elif district_type == '平地立委':
        return ItemPage(Q.LOWLAND_ABORIGINE_DISTRICT)

    elif district_type == '其他':
        return None


election_item_id_of_district = dict()   # key: district code str, value: item id
def load_election_item_id_mapping(filename):
    with open(filename, 'r') as file:
        for row in csv.reader(file):
            election_item_id_of_district[row[0]] = row[1]

def get_election_item(site, district_code:str):
    id = election_item_id_of_district.get(district_code)
    return AdaptiveEntity(site, id)



entity_id_of_party = dict()     # key: party id, value: entity id
def load_party_mapping(filename):
    with open(filename, 'r') as file:
        for row in csv.reader(file):
            entity_id_of_party[row[0]] = row[1]

def get_party_item(site, party_id):
    if party_id == NO_PARTY:
        return ItemPage(site, Q.INDEPENDENT_POLITICIAN)
    else:
        party_entity_id = entity_id_of_party[party_id]
        return AdaptiveEntity(site, party_entity_id)


def same_person_confidence(item, cand:Candidate) -> int:
    confidence = 1

    item_label = get_zhtw_label(item)
    if item_label != cand.legal_name:
        return 0
    
    
    if P.CBDB_ID in item.claims:
        return 0

    if P.INSTANCE_OF in item.claims:
        if find_claim(item.claims, P.INSTANCE_OF, Q.HUMAN) is None:
            return 0

    if P.DATE_OF_BIRTH in item.claims:
        item_birth_date = item.claims[P.DATE_OF_BIRTH][0].getTarget()
        precision = min(item_birth_date.precision, cand.birth_date.precision)

        if precision >= WbTimePrecision.YEAR and item_birth_date.year != cand.birth_date.year:
            return 0
        if precision >= WbTimePrecision.MONTH and item_birth_date.month != cand.birth_date.month:
            return 0
        if precision >= WbTimePrecision.DAY and item_birth_date.day != cand.birth_date.day:
            return 0

        confidence += (precision - WbTimePrecision.YEAR + 1)

    if P.GENDER in item.claims:
        values = [f'{claim.getTarget().getID()}' for claim in item.claims[P.GENDER]]

        item_is_male = Q.MALE in values
        item_is_female = Q.FEMALE in values

        if cand.gender == Gender.MALE:
            if item_is_male:
                confidence += 0.5
            if item_is_female:
                confidence -= 0.5
        if cand.gender == Gender.FEMALE:
            if item_is_female:
                confidence += 0.5
            if item_is_male:
                confidence -= 0.5

    if P.NATIONALITY in item.claims:
        values = [f'{claim.getTarget().getID()}' for claim in item.claims[P.NATIONALITY]]
        if Q.TAIWAN in values:
            confidence += 0.5
        else:
            confidence -= 1

    if P.OCCUPATION in item.claims:
        for claim in item.claims[P.OCCUPATION]:
            occupation = claim.getTarget()
            if occupation == Q.POLITICIAN:
                confidence += 0.5
                break

    if P.PARTY_MEMBERSHIP in item.claims:
        confidence += 0.1

    return confidence


def write_candidates_data(site:DataSite, items_data:ModificationList, sleep_time=1):

    print(f'========================================')
    for (item, data) in items_data:
        
        _data = dict()
        for key in data:
            _data[key] = data[key].toJSON()
        data = _data

        is_new_str = '(new)' if item.getID()=='-1' else ''


        @dataclass
        class EditEntityResult():
            item: ItemPage
            err: Exception

        result = EditEntityResult

        def collect_edit_results(item, err):
            result.item = item
            result.err = err

        item.editEntity(data, callback=collect_edit_results)

        if result.err is None:
            print(f'已寫入： {is_new_str} {(item.getID())} ({item.concept_uri()})')
        else:
            print('匯入失敗')
            print(result.err)

        time.sleep(sleep_time)

        print(f'--------------------------------------')


def print_modifications(items_data:ModificationList):
    
    print(f'========================================')
    for (item,data) in items_data:
        label = get_zhtw_label(data['labels'])
        if item.getID() == '-1':
            print(f'(new)  {label}')
        else:
            print(f'(edit) {label} ({item.concept_uri()})')

        claims:ClaimCollection = data['claims']
        if claims[P.GENDER][0].getTarget().getID() == Q.MALE:
            gender = '男'
        elif claims[P.GENDER][0].getTarget().getID() == Q.FEMALE:
            gender = '女'
        print(f'        性別：{gender} ({claims[P.GENDER][0].getTarget().concept_uri()})')
        
        date_of_birth = claims[P.DATE_OF_BIRTH][0].getTarget()
        print(f'    出生日期：{date_of_birth.toTimestr(True)} (precision:{WbTimePrecision(date_of_birth.precision).name})')
        print(f'        競選：{get_zhtw_label(claims[P.CANDIDACY][0].getTarget())} ({claims[P.CANDIDACY][0].getTarget().concept_uri()})')

        candidacy_qualifiers = claims[P.CANDIDACY][0].qualifiers
        if P.ELECTORAL_DISTRICT in candidacy_qualifiers:
            district_item = candidacy_qualifiers[P.ELECTORAL_DISTRICT][0].getTarget()
            print(f'                |- 選區：{get_zhtw_label(district_item)} ({district_item.concept_uri()})')

        party = candidacy_qualifiers[P.REPRESENTS][0].getTarget()
        print(f'                |- 政黨：{get_zhtw_label(party)} ({party.concept_uri()})')
        print(f'                |- 號次：{candidacy_qualifiers[P.CANDIDATE_NUMBER][0].getTarget()}')
        print(f'                |- 得票：{candidacy_qualifiers[P.VOTES_RECEIVED][0].getTarget().amount}')

    print(f'========================================')


def election_id_create_interface(dir_name, district_type):

    election_data = ElectionData(dir_name, district_type)
    election_data.candidates

    districts = dict()
    for cand in election_data.candidates.values():
        district = cand.district
        if str(district.code) not in districts:
            districts[district.code] = district
    districts = districts.values()

    print(f'========================================')
    print(f'共有 {len(districts)} 個選區需要設定')
    
    id_mapping = dict()

    default_election_item_id = input('輸入預設值 (optional)：')
    if default_election_item_id != '':
        default_election_item = ItemPage(WD_SITE, default_election_item_id)
        print(f'{get_zhtw_label(default_election_item)} ({default_election_item.concept_uri()})')
        id_mapping['*'] = default_election_item_id

    print(f'........................................')
    print('對於每個選區代碼，輸入對應選舉的 Item ID')
    print('空白則套用預設值')
    for district in districts:
        election_item_id = input(f'{district}: ')
        if election_item_id != '':
            election_item = ItemPage(WD_SITE, election_item_id)
            print(f'{get_zhtw_label(election_item)} ({election_item.concept_uri()})')
            id_mapping[str(district.code)] = election_item_id
    
    print(f'id_mapping: {id_mapping}')

    code.interact(local=dict(globals(), **locals()))
    
    with open(f'{dir_name}/election_id.csv', mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        for row in id_mapping.items():
            writer.writerow(row)

    print('創建完成')
    print(f'========================================')