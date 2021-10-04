# wikidata-tw-politicians-bot
A bot for importing data of Taiwanese politicians into Wikidata
這個 bot 是用來把選舉資料庫中的候選人資料倒入 Wikidata

## Data source

* [政府資料開放平台](https://data.gov.tw/dataset/13119)



## Usage

先從[這個連結](http://data.cec.gov.tw/選舉資料庫/votedata.zip)下載檔案，解壓縮到根目錄

### PowerShell

```
cd wikidata-tw-politicians-bot
$Env:WDPASS = "your_password"
python main.py -t <TEST> -n <N> -s <SLEEP>
```

查看參數說明：
```
python main.py -h
```

