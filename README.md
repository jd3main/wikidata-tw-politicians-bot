# wikidata-tw-politicians-bot
A bot for importing data of Taiwanese politicians into Wikidata

## Data source

* [政府資料開放平台](https://data.gov.tw/dataset/13119)



## Usage

### PowerShell

```
cd wikidata-tw-politicians-bot
$Env:WDPASS = "your_password"
python main.py -t <TEST> -n <N> -s <SLEEP>
```

To see meaning of the arguments:
```
python main.py -h
```

