# electricitymap-korea
Estimating hourly historical electricity production by fuel source for South Korea

## Data Sources
Currently, electricityMap lacks granular data in terms of fuel source for South Korea. The [parser](https://github.com/tmrowco/electricitymap-contrib/pull/1816/files), built in April 2019,  scrapes the current load as well as hydro and nuclear production, and attributes a large share of electricity production to the category **unknown**.

Korea Power Exhange provides an hourly demand [forecast](http://www.kpx.or.kr/www/contents.do?key=223) that can be downloaded in bulk per year (starting from 1999). One could compare the forecasted figures to the historical load that has been scraped by electricityMap since April 2019, in order to validate the accuracy of the forecasts. In this analysis, I assume that the forecasted hourly demand matches the hourly electricity production. 

<!-- **Cross check using this: http://epsis.kpx.or.kr/epsisnew/selectEkgeEpsAepChart.do?menuId=030200** -->

The next step is to break down the hourly electricity production per fuel source. The Electric Power Statistics Information System provides a [breakdown](
http://epsis.kpx.or.kr/epsisnew/selectEkpoBftChart.do?menuId=020100) of power generation capacity by fuel source on a monthly level.

## Naive Estimation
Assume that production will match the maximum capacity for all plants except the marginal one. In the example below, renewable sources and nuclear plants would produce at full capacity which leads to coal production being the following:

$$coal = total - renewable - nuclear$$

<img src="https://www.tmrow.com/static/9ac35e5c7a5e8c445425664447e809a5/20def/merit-order-curve.png" title="https://www.tmrow.com/static/9ac35e5c7a5e8c445425664447e809a5/20def/merit-order-curve.png">_Source: [Tomorrow Blog](https://www.tmrow.com/static/9ac35e5c7a5e8c445425664447e809a5/20def/merit-order-curve.png)_

## Creating Estimations

Set up the environment

```
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
Run the estimations with 

```
python src/korea.py
```


## Outlook

## Sources
Yearly production by source (hydro, thermal, nuclear, renewable) until 2019
Assign renewable to solar? Aggregate renewables on the yearly level after estimation and use this source for validation
http://epsis.kpx.or.kr/epsisnew/selectEkesKepChart.do?menuId=010100&locale=eng 

Energy consumption breakdown by source until 2018
http://epsis.kpx.or.kr/epsisnew/selectEkesKedChart.do?menuId=010400&locale=eng

Split till 2018 http://cms.khnp.co.kr/content/163/main.do?mnCd=FN05040101