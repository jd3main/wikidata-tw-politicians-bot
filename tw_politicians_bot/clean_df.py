import pandas as pd


def stripLeadingApostrophe(df: pd.DataFrame):
    df.replace('^\'*', '', regex=True, inplace=True)


def clean_df(df: pd.DataFrame):
    stripLeadingApostrophe(df)
    for col in df.columns:
        if type(col[0]) == str:
            df[col] = df[col].str.strip()


def test():
    filename = './votedata/20120114-總統及立委/山地立委/elbase.csv'
    df = pd.read_csv(filename, header=None, encoding='utf-8')
    print(df)


if __name__ == '__main__':
    test()
