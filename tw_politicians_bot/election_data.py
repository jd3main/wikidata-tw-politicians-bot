from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Tuple,Dict

import pandas as pd
from pywikibot import WbTime

from .clean_df import clean_df


def parse_birth_date(birth_str:str) -> WbTime:
    y = int(birth_str[0:3]) + 1911
    if len(birth_str) == 7:
        m = int(birth_str[3:5])
        d = int(birth_str[5:7])
    else:
        m = None
        d = None

    wb_time = WbTime(y, m, d)
    return wb_time


class DistrictCode:

    def __init__(self, codes:list):
        self.codes = codes
        self.normalize()

    def __str__(self):
        return ''.join(self.codes)

    def normalize(self):
        if self.codes == ['00', '000', '01', '000', '0000']:
            self.codes[2] = '00'

    def province(self):
        return self.codes[0]

    def county(self):
        return self.codes[1]

    def electoralDistrict(self):
        return self.codes[2]

    def township(self):
        return self.codes[3]

    def village(self):
        return self.codes[4]

    @property
    def HRCIS(self):
        if not self.village()[0].isnumeric():
            return None
        hrcis = self.codes[0:2] + self.codes[3:5]
        while len(hrcis) > 0 and all(c == '0' for c in hrcis[-1]):
            hrcis.pop()
        return hrcis

    @property
    def HRCIS_str(self):
        hrcis = self.HRCIS
        if hrcis is None:
            return None
        return ''.join(hrcis)


@dataclass
class District:
    code: DistrictCode
    name: str

    def __str__(self):
        return f'({self.code}, {self.name})'


class Gender(Enum):
    MALE = 1
    FEMALE = 2


@dataclass
class Candidate:
    district: District
    number: str
    legal_name: str
    party_id: str
    gender: Gender
    birth_date: WbTime
    birth_place: str
    votes: int = -1

    def __str__(self):
        return (f'Candidate:(\n' +
                f'    District: {self.district}\n' +
                f'    Number:   {self.number}\n' +
                f'    Name:     {self.legal_name}\n' +
                f'    Party:    {self.party_id}\n' +
                f'    Gender:   {self.gender}\n' +
                f')')


def read_csv_clean(filename, **kwargs):
    df = pd.read_csv(filename, **kwargs)
    clean_df(df)
    return df


class ElectionData():

    def __init__(self, dir_name, district_type, elbase='elbase.csv', elcand='elcand.csv', elctks='elctks.csv'):
        self.dir = Path(dir_name)
        self.district_type = district_type
        self.elbase = elbase
        self.elcand = elcand
        self.elctks = elctks

        self.candidates:Dict[Tuple[str,str],Candidate] = None

        self.load_districts()
        self.load_candidates()
        self.load_votes()

    def load_districts(self):
        header = ['??????', '??????', '??????', '????????????', '??????', '??????']
        df = read_csv_clean(self.dir/self.elbase, names=header, dtype=str)

        if self.district_type == '?????????':
            df['??????'] = '00'

        self.districts = dict()
        for row in df.iloc:
            code = DistrictCode(list(row[0:5]))
            name = row[5]
            self.districts[str(code)] = District(code, name)

    def load_candidates(self):
        header = ['??????', '??????', '??????', '????????????', '??????', '??????',
                  '??????', '????????????', '??????', '????????????', '??????', '?????????',
                  '??????', '??????', '????????????', '??????']
        df = read_csv_clean(self.dir/self.elcand, names=header, dtype=str)
        df = df.astype({'??????': int}, copy=False)

        if self.district_type == '?????????':
            df['??????'] = '00'

        self.candidates = dict()
        for row in df.iloc:
            code_str = str(DistrictCode(list(row[0:5])))
            district = self.districts.get(code_str)
            number = row['??????']
            legal_name = row['??????']
            party_id = row['????????????']
            gender = Gender(row['??????'])
            birth_date = parse_birth_date(row['????????????'])
            birth_place = row['?????????']
            candidate = Candidate(district, number, legal_name, party_id, gender, birth_date, birth_place)
            self.candidates[(code_str, number)] = candidate

    def load_votes(self):
        header = ['??????', '??????', '??????', '????????????', '??????', '????????????', '??????', '?????????', '?????????', '????????????']
        df = read_csv_clean(self.dir/self.elctks, names=header, dtype=str)
        df = df.astype({'?????????': int}, copy=False)

        if self.district_type == '?????????' and (df['??????'] == '01').all():
            df['??????'] = '00'

        full_district_code = df[header[0]].str.cat(df[header[1:5]])
        df.insert(0, 'FullDistrictCode', full_district_code)
        main_district_codes = [key[0] for key in self.candidates.keys()]
        df = df[df['FullDistrictCode'].isin(main_district_codes)]

        if df.shape[0] == 0:
            raise RuntimeError(f'Cannot load {self.elctks} correctly')

        for row in df.iloc:
            code = row['FullDistrictCode']
            number = row['??????']
            votes = row['?????????']

            cand = self.candidates[(code, number)]
            cand.votes = votes
