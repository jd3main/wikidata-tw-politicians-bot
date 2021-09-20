from pprint import pprint
import pandas as pd
import code
import os
import tkinter as tk
import tkinter.filedialog
import itertools

from wikidataintegrator import wdi_core, wdi_login
from wikidataintegrator.wdi_core import (
    WDItemEngine as _WDItemEngine,
    WDItemID,
    WDQuantity,
    WDTime,
    WDString,
)

from .election_data import ElectionData, Gender, District, Candidate
from .wd_utils import (
    make_statments_dict,
    item_id,
    entity_url,
)
from .wbsearch import wbsearch
from .entity_ids import ItemIds, PropertyIds
from .wb_time_utils import WbTimePrecision, time_wdi_to_pwb
from .get_label import get_zhtw_label
from .adaptive_entity_engine import AdaptiveWDEntityEngine


# Constants
NO_PARTY = '999'
REFERENCE_URL = 'https://data.gov.tw/dataset/13119'
DATA_RETRIEVED_DATE = '+2020-09-07T00:00:00Z'
WD_URL = 'https://www.wikidata.org'
WD_API_URL = 'https://www.wikidata.org/w/api.php'
TEST_WD_URL = 'https://test.wikidata.org'
TEST_WD_API_URL = 'https://test.wikidata.org/w/api.php'

ELECTORAL_DISTRICT_OPTIONS = ['行政區', '區域立委', '山地立委', '平地立委', '其他']


IS_TEST = True
SITE_URL = ''
API_URL = ''
LOGIN = None

P = None
Q = None

ItemEngine = _WDItemEngine

entity_id_of_party = dict()
def load_party_mapping(filename):
    df = pd.read_csv(filename, header=None)
    for row in df.iloc:
        party_id = row[0]
        entityId = row[1]
        entity_id_of_party[party_id] = entityId


def get_district_item_id(district:District, district_type:str, login_instance=None):

    if district_type not in ELECTORAL_DISTRICT_OPTIONS:
        raise ValueError(f'district_type should be one of {ELECTORAL_DISTRICT_OPTIONS}')

    if district_type == '行政區':
        data = [WDString(district.code.HRCIS_str(), P.ELECTORAL_DISTRICT)]
        return AdaptiveWDEntityEngine(login_instance, data=data, core_props={P.ELECTORAL_DISTRICT})
        
    elif district_type == '區域立委':
        search_results = wbsearch(district.name, dict_id_label=True)
        if len(search_results) == 0:
            return None
        result = search_results[0]
        id = result['id']
        return AdaptiveWDEntityEngine.get_adapted_entity_id(login_instance, id)
    
    elif district_type == '山地立委':
        return Q.HIGHLAND_ABORIGINE_DISTRICT

    elif district_type == '平地立委':
        return Q.LOWLAND_ABORIGINE_DISTRICT

    elif district_type == '其他':
        return None


def same_person_confidence(item, cand:Candidate) -> int:
    confidence = 1

    _, item_label = get_zhtw_label(item)
    if item_label != cand.legal_name:
        return 0
    
    statements = make_statments_dict(item.statements)
    
    if P.CBDB_ID in statements:
        return 0

    if P.INSTANCE_OF in statements:
        values = [f'Q{stm.value}' for stm in statements[P.INSTANCE_OF]]
        if Q.HUMAN not in values:
            return 0

    if P.DATE_OF_BIRTH in statements:
        item_birth_date = time_wdi_to_pwb(statements.get(P.DATE_OF_BIRTH)[0])
        precision = min(item_birth_date.precision, cand.birth_date.precision)

        if precision >= WbTimePrecision.YEAR and item_birth_date.year != cand.birth_date.year:
            return 0
        if precision >= WbTimePrecision.MONTH and item_birth_date.month != cand.birth_date.month:
            return 0
        if precision >= WbTimePrecision.DAY and item_birth_date.day != cand.birth_date.day:
            return 0

        confidence += (precision - WbTimePrecision.YEAR + 1)

    if P.GENDER in statements:
        values = [f'Q{stm.id}' for stm in statements[P.GENDER]]

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

        item_gender = statements[P.GENDER][0]
        if item_gender.value == int(Q.MALE[1:]):
            item_gender = Gender.MALE
        elif item_gender.value == int(Q.FEMALE[1:]):
            item_gender = Gender.FEMALE
        
        if item_gender != cand.gender:
            return 0
        else:
            confidence += 0.5

    if P.NATIONALITY in statements:
        values = [f'Q{stm.value}' for stm in statements[P.NATIONALITY]]
        if Q.TAIWAN in values:
            confidence += 0.5
        else:
            confidence -= 1

    if P.OCCUPATION in statements:
        for stm in statements[P.OCCUPATION]:
            occupation = stm.value
            if occupation == Q.POLITICIAN:
                confidence += 0.5
                break

    if P.PARTY_MEMBERSHIP in statements:
        confidence += 0.1

    return confidence


def initialize(is_test=True):
    global IS_TEST
    global SITE_URL
    global API_URL
    global ItemEngine
    global LOGIN
    global Q
    global P

    IS_TEST = is_test
    if IS_TEST:
        SITE_URL = TEST_WD_URL
        API_URL = TEST_WD_API_URL
    else:
        SITE_URL = WD_URL
        API_URL = WD_API_URL

    ItemEngine = _WDItemEngine.wikibase_item_engine_factory(API_URL)
    
    # Login
    WDUSER = os.getenv("WDUSER")
    WDPASS = os.getenv("WDPASS")
    
    if WDUSER is None:
        raise ValueError('Environment variable "WDUSER" is required.')
    if WDPASS is None:
        raise ValueError('Environment variable "WDPASS" is required.')
    
    LOGIN = wdi_login.WDLogin(
        user = WDUSER,
        pwd = WDPASS,
        mediawiki_api_url = API_URL,
        mediawiki_index_url = SITE_URL,
    )

    Q = ItemIds(LOGIN)
    P = PropertyIds(LOGIN)


    print(f'-------------------------')
    print(f'Account: {WDUSER}')
    print(f'IS_TEST: {IS_TEST}')
    print(f'-------------------------')



def main(is_test=True, head=None):

    initialize(is_test)

    # Hide default window
    root = tk.Tk()
    root.withdraw()


    print(f'-----------------------------')
    print(f'請選擇匯入來源')
    dir_name = tk.filedialog.askdirectory(title='匯入來源', mustexist=True, initialdir=os.getcwd())
    print(f'匯入自：{dir_name}')
    print(f'-----------------------------')

    while True:
        input_election_entity_id = input('輸入該選舉的 Wikidata ID: ')
        election_entity = AdaptiveWDEntityEngine.get_adapted_entity(LOGIN, input_election_entity_id)
        election_entity_id = election_entity.wd_item_id
        print(f'{get_zhtw_label(election_entity)[1]} ({entity_url(SITE_URL, election_entity_id)})')
        confirm = input('是否正確？ (Y/n)').upper()
        if confirm == 'N':
            continue
        else:
            break

    party_entity_mapping_file = 'PartyID-EntityID.csv'
    if not os.path.isfile(party_entity_mapping_file):
        party_entity_mapping_file = tk.filedialog.askdirectory(title='PartyID-EntityID.csv', initialdir=os.getcwd())


    print('---------------------')
    print('[選區類型]')
    print('  1. 行政區')
    print('  2. 區域立委')
    print('  3. 山地立委')
    print('  4. 平地立委')
    print('  5. 其他 (將會忽略選區資料)')
    print('')
    input_district_type = None
    while True:
        input_district_type = int(input('輸入選項：'))
        if 1 <= input_district_type <= len(ELECTORAL_DISTRICT_OPTIONS):
            break
    
    district_type = ELECTORAL_DISTRICT_OPTIONS[input_district_type - 1]

    print(f'-----------------------------')

    # Load Data
    print('Loading data')
    load_party_mapping(party_entity_mapping_file)
    election_data = ElectionData(dir_name)
    print(f'已載入 {len(election_data.candidates)} 筆候選人資料')
    print('-----------------------------')

    candidates_items = prepare_candidates_items(LOGIN, election_data, district_type, election_entity_id, head)

    print('-----------------------------')
    new_item_count = sum(1 for c in candidates_items if c.new_item)
    modify_item_count = len(candidates_items) - new_item_count
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
            write_candidates_data(LOGIN, candidates_items)
            break
        if action == 'C':
            print('取消匯入')
            break
        if action == 'L':
            print_modifications(candidates_items)
            continue
        if action == 'D':
            code.interact(local=dict(globals(), **locals()))


    code.interact(local=dict(globals(), **locals()))


def prepare_candidates_items(login_instance, election_data, district_type, election_entity_id, head=None):
    candidates_items = []

    candidates = election_data.candidates.values()
    if head is not None:
        candidates = itertools.islice(candidates, head)

    for cand in candidates:
        print(cand)

        if cand.party_id == NO_PARTY:
            party_entity_id = None
        else:
            party_entity_id = entity_id_of_party[cand.party_id]
            if IS_TEST:
                party_entity_id = AdaptiveWDEntityEngine.get_adapted_entity_id(login_instance, party_entity_id)
            
            #
            party = ItemEngine(wd_item_id=party_entity_id, core_props={})
            print(get_zhtw_label(party))

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
                found_item = ItemEngine(id, core_props={})
                # TODO: Check equivalence
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
                print(f'best matched item: {get_zhtw_label(best_matched_item)[1]} ({best_matched_item.wd_item_id})')
                print(f'modify item: ({SITE_URL}/wiki/{best_matched_item.wd_item_id})')

                item = best_matched_item

        if item is None:
            print(f'No existing item found, create new item')
            item = ItemEngine(new_item=True, core_props={})
            item.set_label(cand.legal_name, 'zh-tw')
            
        # Set data
        # * [v] 性質 (P31) -> 人類 (Q5)
        # * [v] 國籍 (P27) -> 中華民國 (Q865)
        # * [v] 性別 (P21) -> 男或女            (+參考文獻)
        # * [v] Date of birth (P569)           (+參考文獻)
        # * [v] 競選(P3602) -> 參與的選舉       (+參考文獻)
        #     * [v] 選區 (P768) -> (Item)
        #     * [v] 代表對象 (P1268) -> (Item) //推薦政黨
        #     * [v] 得票數 (P1111) -> (Quantity)
        #     * [v] 候選人號次 (P4243) -> (String)
        # * [v] 參考文獻結構
        #     * [v] 來源網址 (P854) : [政府資料開放平台](https://data.gov.tw/dataset/13119)
        #     * [v] 作品或名稱語言 (P407) : 中華民國國語 (Q262828)
        #     * [v] 檢索日期 (P813)

        references = [[
            WDString(REFERENCE_URL, P.REFERENCE_URL, is_reference=True),
            WDItemID(Q.NATIONAL_LANGUAGE_OF_ROC, P.LANGUAGE_OF_WORK, is_reference=True),
            WDTime(DATA_RETRIEVED_DATE, P.RETRIEVED, WbTimePrecision.DAY, is_reference=True),
        ]]

        instance_of = WDItemID(Q.HUMAN, P.INSTANCE_OF)
        nationality = WDItemID(Q.TAIWAN, P.NATIONALITY)
        
        # Gender
        gender = None
        if cand.gender == Gender.MALE:
            gender = WDItemID(Q.MALE, P.GENDER, references=references)
        elif cand.gender == Gender.FEMALE:
            gender = WDItemID(Q.FEMALE, P.GENDER, references=references)

        # Date of birth
        birth_date_str = cand.birth_date.toTimestr(True)
        birth_date_precision = cand.birth_date.precision
        date_of_birth = WDTime(birth_date_str, P.DATE_OF_BIRTH, birth_date_precision, references=references)

        # Candidacy
        candidacy_qualifiers = [
            WDQuantity(cand.votes, P.VOTES_RECEIVED, is_qualifier=True),
            WDString(str(cand.number), P.CANDIDATE_NUMBER, is_qualifier=True),
        ]

        if party_entity_id is None:
            candidacy_qualifiers.append(WDItemID(None, P.REPRESENTS, is_qualifier=True, snak_type='novalue'))
        else:
            candidacy_qualifiers.append(WDItemID(party_entity_id, P.REPRESENTS, is_qualifier=True))

        district_item_id = get_district_item_id(cand.district, district_type, login_instance)
        if district_item_id is not None:
            candidacy_qualifiers.append(WDItemID(district_item_id, P.ELECTORAL_DISTRICT, is_qualifier=True))
            #
            district = ItemEngine(district_item_id)
            print(f'District: {get_zhtw_label(district)[1]} ({district_item_id})')
        else:
            print(f'District not found or skipped')

        candidacy = WDItemID(election_entity_id, P.CANDIDACY, qualifiers=candidacy_qualifiers, references=references)

        data = [instance_of, nationality, gender, date_of_birth, candidacy]
        # TODO: correctly prevent overwriting
        item.update(data, append_value=[P.CANDIDACY])
        candidates_items.append(item)

    return candidates_items

def write_candidates_data(login_instance, candidates_data):
    print(f'-----------------------------')
    for item in candidates_data:
        item.write(login_instance)
        
        if item.wd_item_id != '':
            is_new_str = '(new)' if item.new_item else ''
            print(f'寫入： {is_new_str} {(item.wd_item_id)} ({entity_url(SITE_URL, item.wd_item_id)})')
        else:
            print('匯入失敗')
        
        print(f'-----------------------------')
    
def print_modifications(candidates_items):
    for item in candidates_items:
        label = get_zhtw_label(item)[1]
        if item.new_item:
            print(f'(new) {label}')
        else:
            print(f'(modify) {label} ({entity_url(SITE_URL, item.wd_item_id)})')
        statements = make_statments_dict(item.statements)
        if item_id(statements[P.GENDER][0]) == Q.MALE:
            gender = '男'
        elif item_id(statements[P.GENDER][0]) == Q.FEMALE:
            gender = '女'
        print(f'    性別: {gender} ({entity_url(SITE_URL, item_id(statements[P.GENDER][0]))})')
        date_of_birth = statements[P.DATE_OF_BIRTH][0]
        print(f'    出生日期: {date_of_birth.time} (precision:{WbTimePrecision(date_of_birth.precision).name})')
        print(f'    競選: {entity_url(SITE_URL, item_id(statements[P.CANDIDACY][0]))}')
        candidacy_qualifiers = make_statments_dict(statements[P.CANDIDACY][0].qualifiers)
        district_item_id = None
        if P.ELECTORAL_DISTRICT in candidacy_qualifiers:
            district_item_id = item_id(candidacy_qualifiers[P.ELECTORAL_DISTRICT][0])
        print(f'        選區: {entity_url(SITE_URL, district_item_id)}')
        print(f'        政黨: {entity_url(SITE_URL, item_id(candidacy_qualifiers[P.REPRESENTS][0]))}')
        print(f'        號次: {candidacy_qualifiers[P.CANDIDATE_NUMBER][0].value}')
        print(f'        得票: {int(candidacy_qualifiers[P.VOTES_RECEIVED][0].value[0])}')
