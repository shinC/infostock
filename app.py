import json
import urllib.request
import concurrent.futures
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from cachetools import cached, TTLCache
import yfinance as yf

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
client = None
if GEMINI_API_KEY:
    client = genai.Client(api_key=GEMINI_API_KEY)

app = Flask(__name__)

# 10분(600초) 캐시
cache = TTLCache(maxsize=10, ttl=600)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

# 테마 매핑 (finviz themes)
MAPPING_FILE = "/workspaces/stock/sector_mapping.json"
SECTOR_MAPPING = {}
if os.path.exists(MAPPING_FILE):
    with open(MAPPING_FILE, "r", encoding="utf-8") as f:
        doc = json.load(f)
        for sec_key, sec_val in doc.items():
            main_kr = sec_val.get("sector_kr", sec_key)
            for theme_key, theme_val in sec_val.get("themes", {}).items():
                SECTOR_MAPPING[theme_key] = {
                    "main": main_kr,
                    "sub": theme_val.get("kr", theme_key)
                }

def auto_map_new_themes(unmapped_keys):
    if not GEMINI_API_KEY:
        return
    
    # Extract unique main sectors from current mapping
    main_sectors = {}
    try:
        with open(MAPPING_FILE, "r", encoding="utf-8") as f:
            current_doc = json.load(f)
            for cat_k, cat_v in current_doc.items():
                main_sectors[cat_k] = cat_v.get("sector_kr", cat_k)
    except Exception as e:
        print(f"Error loading mapping doc: {e}")
        return
            
    prompt = f"""
I have the following list of unmapped Finviz theme keys: {unmapped_keys}

Extract the theme concept from each key and map it into one of my existing "Main Sectors". You may create a new main sector ONLY IF it doesn't fit any existing one.

Existing Main Sectors:
{json.dumps(main_sectors, ensure_ascii=False)}

Return strictly a JSON array of objects with the exact structure (no markdown tags):
[
  {{ "raw_key": "raw_string", "main_sector_key": "cloud", "main_sector_kr": "클라우드", "theme_en": "Gaming", "theme_kr": "게이밍" }}
]
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        result = json.loads(response.text)
        
        # update document
        for item in result:
            raw_key = item["raw_key"]
            cat_key = item["main_sector_key"]
            if cat_key not in current_doc:
                current_doc[cat_key] = {"sector_en": cat_key, "sector_kr": item["main_sector_kr"], "themes": {}}
            
            if "themes" not in current_doc[cat_key]:
                current_doc[cat_key]["themes"] = {}
                
            current_doc[cat_key]["themes"][raw_key] = {
                "en": item["theme_en"],
                "kr": item["theme_kr"]
            }
            # update in memory SECTOR_MAPPING
            SECTOR_MAPPING[raw_key] = {
                "main": current_doc[cat_key]["sector_kr"],
                "sub": item["theme_kr"]
            }
            
        # flush to disk
        with open(MAPPING_FILE, "w", encoding="utf-8") as f:
            json.dump(current_doc, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"Error calling Gemini: {e}")

# 번역 딕셔너리
TRANSLATIONS = {
    # 하위 테마 영문 번역 추가
    "3D Printing": "3D 프린팅",
    "5G": "5G",
    "AGI": "AGI",
    "AI Platforms": "AI 플랫폼",
    "AV & Mobility": "자율주행/모빌리티",
    "Ads & Media": "광고/미디어",
    "Ads & Search": "광고/검색",
    "Advertising": "광고",
    "Aging Pharma": "노화방지 제약",
    "Agriculture": "농업",
    "Air Cargo": "항공 화물",
    "Air Quality": "공기 질",
    "Air Travel": "항공 여행",
    "Alt Protein": "대체 단백질",
    "Analog": "아날로그",
    "Analytics & BI": "분석/BI",
    "App Security": "앱 보안",
    "Apparel": "의류",
    "Applications": "어플리케이션",
    "Automation": "자동화",
    "Aviation": "항공",
    "Batteries": "배터리",
    "Battery": "배터리",
    "Betting": "베팅",
    "Biofuels": "바이오연료",
    "Blockchain": "블록체인",
    "CRM": "고객관계관리(CRM)",
    "Charging": "충전",
    "Chips": "반도체 칩",
    "Climate": "기후",
    "Cloud": "클라우드",
    "Cloud & Edge": "클라우드/엣지",
    "Collaboration": "협업",
    "Compute": "컴퓨트",
    "Consumer": "소비자",
    "Crop Inputs": "농작물 투입재",
    "Curriculum": "교육과정",
    "CyberDefense": "사이버 방어",
    "DTC": "소비자 직거래(DTC)",
    "Data": "데이터",
    "Data Analytics": "데이터 분석",
    "Data Centers": "데이터센터",
    "Databases": "데이터베이스",
    "Defense": "방산",
    "Design": "디자인",
    "Design Tools": "설계 도구",
    "DevOps": "데브옵스",
    "Devices": "기기",
    "Diagnostics": "진단",
    "Drones": "드론",
    "E-Commerce": "이커머스",
    "Edge": "엣지",
    "Edge Devices": "엣지 디바이스",
    "Electronics": "전자제품",
    "Enabling Tech": "기반 기술",
    "Endpoint": "엔드포인트",
    "Energy": "에너지",
    "Enterprise": "엔터프라이즈",
    "Exchanges": "거래소",
    "Farm-Direct": "농장 직거래",
    "Fertilizers": "비료",
    "Fleets": "차량 그룹(Fleets)",
    "Food": "식품",
    "Foundries": "파운드리",
    "Gambling": "겜블링",
    "Gaming": "게이밍",
    "Gas & LNG": "천연가스/LNG",
    "Genomics": "유전체학",
    "Geothermal": "지열",
    "Gold": "금",
    "Gov & Defense": "정부/방산",
    "Grains": "곡물",
    "Grocery": "식료품",
    "H-SaaS": "H-SaaS",
    "Hardware": "하드웨어",
    "Healthcare": "헬스케어",
    "Healthy Aging": "건강한 노화",
    "Household": "가정용",
    "Housing": "주택",
    "Hybrid Cloud": "하이브리드 클라우드",
    "Hydrogen": "수소",
    "Hyperscalers": "하이퍼스케일러",
    "IT & Data": "IT/데이터",
    "IT & Telecom": "IT/통신",
    "Identity": "신원확인",
    "Identity IAM": "신원/접근 관리",
    "Immersive": "몰입형",
    "Indoor Farming": "실내 농업",
    "Industrial": "산업용",
    "Industrial IoT": "산업용 IoT",
    "Infrastructure": "인프라",
    "Insurance": "보험",
    "IoT": "사물인터넷(IoT)",
    "Launch": "로켓 발사",
    "Lending": "대출",
    "Lithography": "노광 장비",
    "Livestock": "가축",
    "Logistics": "물류",
    "Luxury": "명품",
    "Machine Vision": "머신비전",
    "Majors": "주요 기업",
    "Manufacturers": "제조사",
    "Manufacturing": "제조",
    "Maritime": "해운",
    "Marketplaces": "마켓플레이스",
    "Materials": "소재",
    "Meal Delivery": "식사 배달",
    "Medical": "의료",
    "Medicine": "의학",
    "Memory": "메모리",
    "Metabolic": "대사질환",
    "Mining": "광산",
    "Missiles": "미사일",
    "Models": "모델",
    "Multi Cloud": "멀티 클라우드",
    "Music": "음악",
    "Neobanks": "인터넷 전문은행",
    "Network": "네트워크",
    "Networking": "네트워킹",
    "Networks": "네트워크",
    "Next-Gen": "차세대",
    "Niche": "니치 시장",
    "Nuclear": "원자력",
    "OS": "운영체제",
    "Office": "오피스",
    "Oil": "석유",
    "Oil Production": "원유 생산",
    "Oil Refining": "원유 정제",
    "Oil Services": "석유 서비스",
    "Omnichannel": "옴니채널",
    "Oncology": "항암",
    "PCs & Devices": "PC/기기",
    "PaaS": "PaaS",
    "Packaging": "패키징",
    "Payments": "결제",
    "Platforms": "플랫폼",
    "Precious": "귀금속",
    "Printing": "프린팅",
    "Processing": "가공",
    "Products": "제품",
    "Providers": "서비스 제공자",
    "Rail": "철도",
    "Rare Earth": "희토류",
    "Recycling": "재활용",
    "Research Tools": "연구 도구",
    "Retail": "유통",
    "Retailers": "소매점",
    "Robotics": "로보틱스",
    "SIEM": "SIEM(보안관제)",
    "Satcom": "위성통신",
    "Satellites": "위성",
    "Secondhand": "중고",
    "Security": "보안",
    "Self-Driving": "자율주행",
    "Senior Living": "실버 타운",
    "Serverless": "서버리스",
    "Servers": "서버",
    "Silver": "은",
    "Smart Farming": "스마트 농업",
    "Smart Grid": "스마트 그리드",
    "Smartwatches": "스마트워치",
    "Social": "소셜",
    "Softs": "소프트원자재",
    "Software": "소프트웨어",
    "Solar": "태양광",
    "SpaceTech": "우주 기술",
    "Specialized": "특수/전문",
    "Sport": "스포츠",
    "Storage": "스토리지",
    "Supplements": "보충제",
    "Suppliers": "공급망",
    "Telecom": "통신",
    "Telemedicine": "원격진료",
    "Therapeutics": "치료제",
    "Thermal": "열/화력",
    "ThreatOps": "위협 대응",
    "Tokenization": "토큰화",
    "Tourism": "관광",
    "Trading": "트레이딩",
    "Trucking": "트럭 운송",
    "Uranium": "우라늄",
    "Utilities": "유틸리티",
    "V-SaaS": "V-SaaS",
    "Video": "비디오",
    "Visual Content": "시각 콘텐츠",
    "Voice & AI": "음성 AI",
    "Warehousing": "창고업",
    "Waste": "폐기물",
    "Water": "수질 관리",
    "Weapons": "무기",
    "Wind": "풍력",
    "Wireless": "무선",
    "Workforce": "인적자원",
    "ZeroTrust": "제로 트러스트",

    "Compute": "컴퓨트",
    "Cloud": "클라우드",
    "Databases": "데이터베이스",
    "Security": "보안",
    "Hardware": "하드웨어",
    "Software": "소프트웨어",
    "Networking": "네트워킹",
    "Servers": "서버",

    # 주요 지수
    "Dow 30": "다우존스 30",
    "Nasdaq": "나스닥",
    "Nasdaq 100": "나스닥 100",
    "Russell 2000": "러셀 2000",
    "NYSE": "뉴욕증권거래소",
    "S&P 500": "S&P 500",
    "Philadelphia Semiconductor": "필라델피아 반도체",
    "WTI": "WTI 원유",
    "VIX": "VIX (공포지수)",
    
    # 11개 주요 섹터 명칭
    "basicmaterials": "소재",
    "communicationservices": "통신서비스",
    "consumercyclical": "경기민감주",
    "consumerdefensive": "경기방어주",
    "energy": "에너지",
    "financial": "금융",
    "healthcare": "헬스케어",
    "industrials": "산업재",
    "realestate": "부동산",
    "technology": "테크놀로지",
    "utilities": "유틸리티",
    
    # 주요 테마(Sub-sectors / Industries) 한글 번역 (Finviz 기본 Industries)
    "aerospacedefense": "방산/우주",
    "airlines": "항공",
    "apparelmanufacturing": "의류 제조",
    "apparelspecialty": "의류 전문",
    "assetmanagement": "자산운용",
    "autoandtruckdealerships": "자동차 딜러쉽",
    "automanufacturers": "자동차 제조",
    "autoparts": "자동차 부품",
    "banksdiversified": "다각화 은행",
    "banksregional": "지역 은행",
    "beveragesbrewers": "음료(주류)",
    "beveragesnonalcoholic": "음료(무알콜)",
    "beverageswineriesdistilleries": "음료(와인/증류주)",
    "biotechnology": "바이오테크",
    "broadcasting": "방송",
    "buildingmaterials": "건축 자재",
    "buildingproductsequipment": "건축 제품/장비",
    "capitalmarkets": "자본 시장",
    "chemicals": "화학",
    "communicationequipment": "통신 장비",
    "computerhardware": "컴퓨터 하드웨어",
    "confectioners": "제과",
    "conglomerates": "대기업",
    "consumerelectronics": "가전 기기",
    "copper": "구리",
    "creditreservices": "신용 서비스",
    "departmentstores": "백화점",
    "diagnosticsresearch": "진단/연구",
    "discountstores": "할인점",
    "drugmanufacturersgeneral": "일반 제약",
    "drugmanufacturersspecialtygeneric": "특수/제네릭 제약",
    "educationtrainingservices": "교육/훈련",
    "electroniccomponents": "전자 부품",
    "electronicgamingmultimedia": "게임/멀티미디어",
    "electronicscomputerdistribution": "전자/컴퓨터 유통",
    "entertainment": "엔터테인먼트",
    "farmheavyconstructionmachinery": "농기계/건설중장비",
    "farmproducts": "농산물",
    "financialdatasockexchanges": "금융 데이터/거래소",
    "fooddistribution": "식품 유통",
    "footwearaccessories": "신발/액세서리",
    "furnishingsfixturesappliances": "가구/기구",
    "gold": "금",
    "grocerystores": "식료품점",
    "healthinformationservices": "의료 정보",
    "healthcareplans": "의료 보험",
    "homeimprovementretail": "주택 개선 소매",
    "householdpersonalproducts": "가정/개인 용품",
    "informationtechnologyservices": "IT 서비스",
    "insurancebrokers": "보험 브로커",
    "insurancediversified": "다각화 보험",
    "insurancelife": "생명 보험",
    "insurancepropertycasualty": "손해보험",
    "internetcontentinformation": "인터넷 컨텐츠/정보",
    "internetretail": "인터넷 소매",
    "leisure": "레저",
    "lodging": "숙박",
    "lumberwoodproduction": "목재/벌목",
    "maritimeshipping": "해운",
    "medicalcarefacilities": "의료 시설",
    "medicaldevices": "의료 기기",
    "medicaldistribution": "의료 유통",
    "medicalinstrumentssupplies": "의료 보급/소모품",
    "oilgasdrilling": "석유/가스 시추",
    "oilgasep": "석유/가스 탐사",
    "oilgasequipmentservices": "석유/가스 장비/서비스",
    "oilgasintegrated": "종합 석유/가스",
    "oilgasmidstream": "중류(Midstream)",
    "oilgasrefiningmarketing": "석유/가스 정제/마케팅",
    "packagingcontainers": "포장/용기",
    "paperpaperproducts": "제지",
    "personalservices": "개인 서비스",
    "pharmaceuticalretailers": "약국",
    "pollutiontreatmentcontrols": "오염 처리/통제",
    "railroads": "철도",
    "realestatedevelopment": "부동산 개발",
    "realestateservices": "부동산 서비스",
    "recreationalvehicles": "RV차량",
    "reitdiversified": "REIT (다각화)",
    "reithealthcarefacilities": "REIT (의료)",
    "reithotelmotel": "REIT (호텔)",
    "reitindustrial": "REIT (산업재)",
    "reitmortgage": "REIT (모기지)",
    "reitoffice": "REIT (오피스)",
    "reitresidential": "REIT (주거)",
    "reitretail": "REIT (소매)",
    "reitspecialty": "REIT (특수)",
    "rentalcreasingservices": "렌탈/리스",
    "restaurants": "레스토랑",
    "scientifictechnicalinstruments": "과학기술 기기",
    "semiconductors": "반도체",
    "semiconductorequipmentmaterials": "반도체 장비/소재",
    "softwareapplication": "소프트웨어 (앱)",
    "softwareinfrastructure": "소프트웨어 (인프라)",
    "solar": "태양광",
    "specialtybusinessservices": "특수 비즈니스 서비스",
    "specialtychemicals": "특수 화학",
    "specialtyindustrialmachinery": "특수 산업 기계",
    "specialtyretail": "전문 소매",
    "steel": "철강",
    "telecomservices": "통신 서비스",
    "tobacco": "담배",
    "toolsaccessories": "도구/부속품",
    "travelservices": "여행 서비스",
    "trucking": "트럭 운송",
    "uraniam": "우라늄",
    "utilitiesdiversified": "유틸리티 (다각화)",
    "utilitiesregulatedelectric": "유틸리티 (전력)",
    "utilitiesregulatedgas": "유틸리티 (가스)",
    "utilitiesregulatedwater": "유틸리티 (수도)",
    "utilitiesrenewable": "유틸리티 (신재생)",
    "wastexmanagement": "폐기물 관리",
    "businessequipmentsupplies": "사무 기기/소모품",
    "residentialconstruction": "주거용 건설",
    "consultingservices": "컨설팅 서비스",
    "integratedfreightlogistics": "통합 화물/물류",
    "securityprotectionservices": "보안/보호 서비스",
    "creditservices": "신용 서비스",
    "rentalleasingservices": "임대/리스 서비스",
    "insurancereinsurance": "재보험",
    "resortscasinos": "리조트/카지노",
    "staffingemploymentservices": "인력/고용 서비스",
    "textilemanufacturing": "섬유 제조",
    "publishing": "출판",
    "silver": "은",
    "wastemanagement": "폐기물 관리",
    "otherpreciousmetalsmining": "기타 귀금속 광산",
    "insurancespecialty": "특수 보험",
    "industrialdistribution": "산업재 유통",
    "apparelretail": "의류 소매",
    "aluminum": "알루미늄",
    "utilitiesindependentpowerproducers": "유틸리티 (독립)",
    "autotruckdealerships": "자동차/트럭 딜러십",
    "luxurygoods": "명품",
    "engineeringconstruction": "엔지니어링/건설",
    "otherindustrialmetalsmining": "기타 산업 금속 광산",
    "gambling": "도박/카지노",
    "electricalequipmentparts": "전기 장비/부품",
    "agriculturalinputs": "농업 투입재",
    "metalfabrication": "금속 가공",
    "shellcompanies": "쉘 컴퍼니",
    "airportsairservices": "공항/항공 서비스",
    "cokingcoal": "점결탄",
    "realestatediversified": "부동산 (다각화)",
    "financialconglomerates": "금융 지주사",
    "financialdatastockexchanges": "금융 데이터/거래소",
    "mortgagefinance": "모기지 금융",
    "packagedfoods": "포장 식품",
    "advertisingagencies": "광고 대행사",
    "uranium": "우라늄",
    "thermalcoal": "발전용 석탄",
    "marineshipping": "해운"
}

def translate(text):
    if not text:
        return text
    lower_text = text.lower()
    for k, v in TRANSLATIONS.items():
        if k.lower() == lower_text:
            return v
    return text

def fetch_json(url):
    req = urllib.request.Request(url, headers={'User-Agent': USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode())
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def fetch_yfinance_change(ticker):
    if not ticker:
        return None, None
    try:
        t = yf.Ticker(ticker)
        info = t.info
        if "regularMarketChangePercent" in info:
            change = info["regularMarketChangePercent"]
            data = t.history(period="1d")
            last_date = data.index[-1].strftime("%Y-%m-%d") if not data.empty else None
            return round(change, 2), last_date
        else:
            data = t.history(period="5d")
            if len(data) >= 2:
                prev_close = data['Close'].iloc[-2]
                curr_close = data['Close'].iloc[-1]
                last_date = data.index[-1].strftime("%Y-%m-%d")
                change = float(((curr_close - prev_close) / prev_close) * 100)
                return round(change, 2), last_date
        return None, None
    except Exception as e:
        print(f"Error fetching yfinance for {ticker}: {e}")
        return None, None

def fetch_theme(s_key):
    themes_url = f"https://finviz.com/api/map_perf_groups.ashx?g=industry&sg={s_key}&v=510&o=name&st=d1"
    return s_key, fetch_json(themes_url)

@cached(cache)
def get_market_data():
    # 1. 지수 데이터 수집
    indices = []
    
    # Priority 1: yfinance
    yf_indices = [
        ("Dow 30", "^DJI"),
        ("Nasdaq", "^IXIC"),
        ("Nasdaq 100", "^NDX"),
        ("Russell 2000", "^RUT"),
        ("NYSE", "^NYA"),
        ("S&P 500", "^GSPC"),
        ("Philadelphia Semiconductor", "^SOX"),
        ("WTI", "CL=F"),
        ("VIX", "^VIX")
    ]
    
    found_indices = set()
    market_date = "알 수 없음"
    
    indices_dict = {}
    for name, ticker in yf_indices:
        pct_change, date_val = fetch_yfinance_change(ticker)
        if pct_change is not None:
            if market_date == "알 수 없음" and date_val:
                market_date = date_val
            indices_dict[name] = {"name": translate(name), "original": name, "change": pct_change}
            found_indices.add(name)
            
    # Priority 2: finviz fallback
    futures_map_rev = {
        "Dow 30": "YM",
        "Nasdaq 100": "NQ",
        "Russell 2000": "ER2",
        "S&P 500": "ES",
        "WTI": "CL",
        "VIX": "VX"
    }
    
    missing_indices = [name for name, ticker in yf_indices if name not in found_indices]
    if missing_indices:
        futures_data = fetch_json("https://finviz.com/api/futures_all.ashx?timeframe=NO")
        if futures_data:
            for name in missing_indices:
                if name in futures_map_rev:
                    finviz_key = futures_map_rev[name]
                    if finviz_key in futures_data:
                        f_data = futures_data[finviz_key]
                        if "last" in f_data and "prevClose" in f_data and f_data["prevClose"] != 0:
                            change = ((f_data["last"] - f_data["prevClose"]) / f_data["prevClose"]) * 100
                        else:
                            change = f_data.get("change", 0)
                        indices_dict[name] = {"name": translate(name), "original": name, "change": round(change, 2)}
                        found_indices.add(name)
                        
    # For any still missing, append with 0.0
    for name, ticker in yf_indices:
        if name not in found_indices:
            indices_dict[name] = {"name": translate(name), "original": name, "change": 0.0}
            
    # 배열 순서를 yf_indices 기준 유지
    for name, _ in yf_indices:
        indices.append(indices_dict[name])
            
    # 2. 테마 데이터 단일 스트림 수집 (Themes API)
    sectors_dict = {}
    themes_data = fetch_json("https://finviz.com/api/map_perf.ashx?t=themes&st=d1")
    
    if themes_data and "nodes" in themes_data:
        unmapped_keys = [t_key for t_key in themes_data["nodes"].keys() if t_key not in SECTOR_MAPPING]
        if unmapped_keys and GEMINI_API_KEY:
            print(f"Discovered {len(unmapped_keys)} unmapped keys. Calling Gemini Auto-Mapping...")
            auto_map_new_themes(unmapped_keys)

        for t_key, t_perf in themes_data["nodes"].items():
            if t_key in SECTOR_MAPPING:
                main_kr = SECTOR_MAPPING[t_key]["main"]
                sub_kr = SECTOR_MAPPING[t_key]["sub"]
                display_name = sub_kr
                sector_name = main_kr
            else:
                sector_name = "기타 테마"
                display_name = translate(t_key)
                
            if sector_name not in sectors_dict:
                sectors_dict[sector_name] = {
                    "name": sector_name,
                    "original": sector_name,
                    "change_sum": 0.0,
                    "count": 0,
                    "themes": []
                }
                
            sectors_dict[sector_name]["themes"].append({
                "name": display_name,
                "original": t_key,
                "change": t_perf
            })
            sectors_dict[sector_name]["change_sum"] += t_perf
            sectors_dict[sector_name]["count"] += 1
            
    # Calculate simple average for sectors
    sectors_list = []
    for sec_data in sectors_dict.values():
        if sec_data["count"] > 0:
            sec_data["change"] = round(sec_data["change_sum"] / sec_data["count"], 2)
        else:
            sec_data["change"] = 0.0
        sec_data["themes"].sort(key=lambda x: x["change"], reverse=True)
        del sec_data["change_sum"]
        del sec_data["count"]
        sectors_list.append(sec_data)
        
    sectors_list.sort(key=lambda x: x["change"], reverse=True)
    
    return {
        "market_date": market_date,
        "indices": indices,
        "sectors": sectors_list
    }

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/data")
def api_data():
    data = get_market_data()
    return jsonify(data)

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=8080) 
