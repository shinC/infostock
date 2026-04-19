개요 : 미국 주식 전날기준 섹터별 등락율 표를 보여주는 프로그램 작성.
개발환경 : 파이썬, 웹페이지
노출 데이터 : 지수데이터, 섹터데이터, 테마데이터
구현 :

   1. 지수데이터
    - url - https://finviz.com/api/futures_all.ashx?timeframe=NO
 - 주요 지수 (Dow 30, Nasdaq, Nasdaq 100, Russell 2000, NYSE, S&P 500, Philadelphia Semiconductor, WTI, VIX)
    - 표형식으로 나태낸다.
    - 지수 중에 해당url에 없을 경우는 다른 방식을 통해서 가지고 온다.

   2. 섹터데이터 & 테마데이터
    - 섹터데이터 URL - https://finviz.com/api/map_perf_groups.ashx?g=sector&v=510&o=name&st=d1
    - 테마데이터 URL - https://finviz.com/api/map_perf_groups.ashx?g=industry&sg=technology&v=510&o=name&st=d1

    - sg(서브그룹)파라미터에 1에서 구해온 섹터값을 넣어서 테마데이터를 가져온다.(총 11개)
    - 섹터데이터를 끌고 와서 sample2와 같은 형식으로 보여준다.
    - 테마데이터는 sample과 같이 표형식으로 나타낸다.

   3. 하위테마.
    - URL https://finviz.com/api/map_perf.ashx?t=themes&st=d1 
     - 데이터 이름이 프리픽스와 결합되어 있어 예를 들면 aicompute, clouddatabases 이런식이야. ai + compute, cloud + databases 로 테마 + 서브테마로 되어 있는거야. 이렇게 나눠서 섹터데이터+테마데이터 형식 처럼 만들어줘. 

백엔드 : 
   - 실시간은 아니며, 전일 종가 기준으로 데이터 호출.

 프론트엔드 UI :
   - 샘플이미지를 참조해서 한눈에 볼 수 있도록 작성.
   - 시각적 강조 효과: 등락률에 따라 색상을 다르게 표현(상승은 pos, 하락은 neg, 보합은 neu)하여 직관적인 히트맵 스타일 UI (색상은 상승 3단계, 보합 1단계, 하락 3단계로 진함과 옅음으로 표현)
   - 색상의 진함과 옅음은 당일 전체 고점과 저점에 따라 틀려짐.(예를들어 10%~-10%, 3%~-10% 경우, 각각 3% 색깔 진함은 10%에서는 가장 진하지는 않지만 3%에서는 가장 진함.)
   - 모든 지수, 섹터는 별도의 한글로 맵핑.(테크놀로지, 금융, 경기민감주, 소재, 경기방어주, 헬스케어, 자동차, 방산/우주 등)

