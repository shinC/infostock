# 📈 Spec: US Stock Sector/Theme Performance Analyzer (v1.1)

## 1. 프로젝트 개요 (Goal)
미국 시장 전체 종목을 관리하고, 지수/섹터/테마별 전일 등락률을 시가총액 가중 평균으로 산출하여 시장의 흐름을 한눈에 파악하는 데이터 파이프라인 구축. 20년 차 개발자의 유지보수 편의성과 AI 기반 개발(Vibe Coding)의 효율성을 극대화하도록 설계함.

---

## 2. 데이터 소스 (Data Sources)

### 2.1 주요 지수 (Index Tickers)
- **종합:** S&P 500 (`^GSPC`), Nasdaq Composite (`^IXIC`), Dow 30 (`^DJI`), Russell 2000 (`^RUT`), NYSE Composite (`^NYA`)
- **특화:** Nasdaq 100 (`^NDX`), 필라델피아 반도체 (`^SOX`), VIX (`^VIX`)

### 2.2 티커 마스터 (Master Tickers)
- **Source:** Nasdaq Trader FTP (`ftp.nasdaqtrader.com/SymbolDirectory/`)
- **Files:** `nasdaqlisted.txt`, `otherlisted.txt` (NYSE, AMEX 포함)

### 2.3 섹터 및 테마 (Sector/Theme Data) - [Update]
| 구분 | 데이터 소스 (Source) | 수집 방법 (Method) |
| :--- | :--- | :--- |
| **섹터/산업** | Finviz / yfinance | `info['sector']`, `info['industry']` 데이터 추출 |
| **테마(ETF)** | Financial Modeling Prep (FMP) | `/api/v3/etf-holder/{ETF_TICKER}` API 호출 (정형 데이터) |
| **테마(Scraping)** | ETFdb.com / ETF.com | 테마별 ETF 리스트(예: AI, Cloud) 페이지 스크래핑 |
| **테마(Issuer)** | iShares, Global X 등 | 자산운용사 공식 홈페이지의 Holdings CSV 파일 URL 참조 |

---

## 3. 데이터베이스 설계 (Schema)

### 3.1 `ticker_master`
- `ticker` (TEXT, PK), `name` (TEXT), `exchange` (TEXT), `sector` (TEXT), `industry` (TEXT), `market_cap` (REAL), `is_active` (BOOLEAN)

### 3.2 `themes` (Theme Registry)
- `theme_id` (INTEGER, PK), `theme_name` (TEXT), `source_etf` (TEXT), `parent_id` (INTEGER)
- *Note: `parent_id`를 통해 "반도체 > AI 반도체" 식의 계층 구조 지원*

### 3.3 `ticker_theme_map` (N:M Mapping)
- `ticker` (FK), `theme_id` (FK), `weight` (REAL)
- *Note: 특정 종목이 여러 테마에 속할 수 있으며, 해당 테마 ETF 내 비중을 가중치로 활용 가능*

### 3.4 `price_history`
- `ticker` (FK), `date` (DATE), `close` (FLOAT), `change_pct` (FLOAT)

---

## 4. 데이터 파이프라인 (Pipeline)

### STEP 1: 마스터 티커 동기화
1. Nasdaq FTP에서 텍스트 파일을 다운로드하여 `ticker_master` 테이블 생성/갱신.
2. `yfinance`를 사용하여 시가총액(`market_cap`) 정보를 배치로 업데이트.

### STEP 2: 섹터 및 테마 매핑 (Tagging Engine) - [Core Logic]
1. **기본 분류:** `yfinance`를 통해 전 종목의 GICS 섹터/산업 정보를 1차 매핑.
2. **테마 Seed 구성:** 시스템에 '테마-참조 ETF' 사전 구축.
   - 예: `{"AI": ["BOTZ", "AIQ"], "Semiconductors": ["SOXX", "SMH"], "M7": ["MAGS"]}`
3. **ETF Holdings 매핑:**
   - 참조 ETF의 구성 종목(Holdings)을 FMP API 또는 스크래핑으로 수집.
   - 구성 종목들을 해당 테마(Theme)로 `ticker_theme_map`에 인서트.
   - 중복 매핑 허용 (NVDA는 AI, 반도체, M7 태그를 모두 가짐).
4. **LLM 보완 (Optional):** 위 데이터가 없는 신규 테마는 LLM에 Business Summary를 입력하여 태깅.

### STEP 3: 일일 시세 업데이트
1. 한국 시간 오전 7시(미국 장 마감 후) 배치 실행.
2. `yfinance.download(tickers, period="1d")`를 멀티스레딩으로 처리하여 전일 종가 및 등락률 수집.

### STEP 4: 지표 계산 (Aggregation)
1. **시가총액 가중 평균 등락률** 산출 로직 적용:
   $$\text{Theme Performance} = \frac{\sum (\text{Ticker Change \%} \times \text{Ticker Market Cap})}{\sum \text{Ticker Market Cap}}$$

---

## 5. 구현 가이드 (Implementation Notes for AI)
- **성능:** 2,000개 이상의 티커를 처리해야 하므로 `pandas` 벡터 연산을 활용하고, DB 처리는 `executemany`로 배치 인서트할 것.
- **확장성:** 새로운 테마 ETF 티커만 추가하면 자동으로 해당 테마 종목들이 업데이트되도록 추상화된 클래스 구조로 작성할 것.
- **예외 처리:** 데이터가 없는 휴장일 처리 및 상장 폐지 티커에 대한 로깅 시스템 포함.