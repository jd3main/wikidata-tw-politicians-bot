# wikidata-tw-politicians-bot
A bot for importing data of Taiwanese politicians into Wikidata

## Data source

* [政府資料開放平台](https://data.gov.tw/dataset/13119)



## Usage

### PowerShell

```
cd wikidata-tw-politicians-bot
$Env:WDUSER = "your_user_name"
$Env:WDPASS = "your_password"
python .\main.py -t <TEST> -n <N>
```

