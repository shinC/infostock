import re

NEW_TRANS = {
    '3D Printing': '3D 프린팅', '5G': '5G', 'AGI': 'AGI', 'AI Platforms': 'AI 플랫폼', 'AV & Mobility': '자율주행/모빌리티',
    'Ads & Media': '광고/미디어', 'Ads & Search': '광고/검색', 'Advertising': '광고', 'Aging Pharma': '노화방지 제약',
    'Agriculture': '농업', 'Air Cargo': '항공 화물', 'Air Quality': '공기 질', 'Air Travel': '항공 여행', 'Alt Protein': '대체 단백질',
    'Analog': '아날로그', 'Analytics & BI': '분석/BI', 'App Security': '앱 보안', 'Apparel': '의류', 'Applications': '어플리케이션',
    'Automation': '자동화', 'Aviation': '항공', 'Batteries': '배터리', 'Battery': '배터리', 'Betting': '베팅', 'Biofuels': '바이오연료',
    'Blockchain': '블록체인', 'CRM': '고객관계관리(CRM)', 'Charging': '충전', 'Chips': '반도체 칩', 'Climate': '기후',
    'Cloud': '클라우드', 'Cloud & Edge': '클라우드/엣지', 'Collaboration': '협업', 'Compute': '컴퓨트', 'Consumer': '소비자',
    'Crop Inputs': '농작물 투입재', 'Curriculum': '교육과정', 'CyberDefense': '사이버 방어', 'DTC': '소비자 직거래(DTC)',
    'Data': '데이터', 'Data Analytics': '데이터 분석', 'Data Centers': '데이터센터', 'Databases': '데이터베이스', 'Defense': '방산',
    'Design': '디자인', 'Design Tools': '설계 도구', 'DevOps': '데브옵스', 'Devices': '기기', 'Diagnostics': '진단', 'Drones': '드론',
    'E-Commerce': '이커머스', 'Edge': '엣지', 'Edge Devices': '엣지 디바이스', 'Electronics': '전자제품', 'Enabling Tech': '기반 기술',
    'Endpoint': '엔드포인트', 'Energy': '에너지', 'Enterprise': '엔터프라이즈', 'Exchanges': '거래소', 'Farm-Direct': '농장 직거래',
    'Fertilizers': '비료', 'Fleets': '차량 그룹(Fleets)', 'Food': '식품', 'Foundries': '파운드리', 'Gambling': '겜블링',
    'Gaming': '게이밍', 'Gas & LNG': '천연가스/LNG', 'Genomics': '유전체학', 'Geothermal': '지열', 'Gold': '금',
    'Gov & Defense': '정부/방산', 'Grains': '곡물', 'Grocery': '식료품', 'H-SaaS': 'H-SaaS', 'Hardware': '하드웨어',
    'Healthcare': '헬스케어', 'Healthy Aging': '건강한 노화', 'Household': '가정용', 'Housing': '주택', 'Hybrid Cloud': '하이브리드 클라우드',
    'Hydrogen': '수소', 'Hyperscalers': '하이퍼스케일러', 'IT & Data': 'IT/데이터', 'IT & Telecom': 'IT/통신', 'Identity': '신원확인',
    'Identity IAM': '신원/접근 관리', 'Immersive': '몰입형', 'Indoor Farming': '실내 농업', 'Industrial': '산업용',
    'Industrial IoT': '산업용 IoT', 'Infrastructure': '인프라', 'Insurance': '보험', 'IoT': '사물인터넷(IoT)', 'Launch': '로켓 발사',
    'Lending': '대출', 'Lithography': '노광 장비', 'Livestock': '가축', 'Logistics': '물류', 'Luxury': '명품',
    'Machine Vision': '머신비전', 'Majors': '주요 기업', 'Manufacturers': '제조사', 'Manufacturing': '제조', 'Maritime': '해운',
    'Marketplaces': '마켓플레이스', 'Materials': '소재', 'Meal Delivery': '식사 배달', 'Medical': '의료', 'Medicine': '의학',
    'Memory': '메모리', 'Metabolic': '대사질환', 'Mining': '광산', 'Missiles': '미사일', 'Models': '모델', 'Multi Cloud': '멀티 클라우드',
    'Music': '음악', 'Neobanks': '인터넷 전문은행', 'Network': '네트워크', 'Networking': '네트워킹', 'Networks': '네트워크',
    'Next-Gen': '차세대', 'Niche': '니치 시장', 'Nuclear': '원자력', 'OS': '운영체제', 'Office': '오피스', 'Oil': '석유',
    'Oil Production': '원유 생산', 'Oil Refining': '원유 정제', 'Oil Services': '석유 서비스', 'Omnichannel': '옴니채널',
    'Oncology': '항암', 'PCs & Devices': 'PC/기기', 'PaaS': 'PaaS', 'Packaging': '패키징', 'Payments': '결제',
    'Platforms': '플랫폼', 'Precious': '귀금속', 'Printing': '프린팅', 'Processing': '가공', 'Products': '제품',
    'Providers': '서비스 제공자', 'Rail': '철도', 'Rare Earth': '희토류', 'Recycling': '재활용', 'Research Tools': '연구 도구',
    'Retail': '유통', 'Retailers': '소매점', 'Robotics': '로보틱스', 'SIEM': 'SIEM(보안관제)', 'Satcom': '위성통신',
    'Satellites': '위성', 'Secondhand': '중고', 'Security': '보안', 'Self-Driving': '자율주행', 'Senior Living': '실버 타운',
    'Serverless': '서버리스', 'Servers': '서버', 'Silver': '은', 'Smart Farming': '스마트 농업', 'Smart Grid': '스마트 그리드',
    'Smartwatches': '스마트워치', 'Social': '소셜', 'Softs': '소프트원자재', 'Software': '소프트웨어', 'Solar': '태양광',
    'SpaceTech': '우주 기술', 'Specialized': '특수/전문', 'Sport': '스포츠', 'Storage': '스토리지', 'Supplements': '보충제',
    'Suppliers': '공급망', 'Telecom': '통신', 'Telemedicine': '원격진료', 'Therapeutics': '치료제', 'Thermal': '열/화력',
    'ThreatOps': '위협 대응', 'Tokenization': '토큰화', 'Tourism': '관광', 'Trading': '트레이딩', 'Trucking': '트럭 운송',
    'Uranium': '우라늄', 'Utilities': '유틸리티', 'V-SaaS': 'V-SaaS', 'Video': '비디오', 'Visual Content': '시각 콘텐츠',
    'Voice & AI': '음성 AI', 'Warehousing': '창고업', 'Waste': '폐기물', 'Water': '수질 관리', 'Weapons': '무기',
    'Wind': '풍력', 'Wireless': '무선', 'Workforce': '인적자원', 'ZeroTrust': '제로 트러스트'
}

with open("app.py", "r", encoding="utf-8") as f:
    code = f.read()

# Update translations dict
trans_insert = "    # 하위 테마 영문 번역 추가\n"
for k, v in NEW_TRANS.items():
    trans_insert += f'    "{k}": "{v}",\n'

code = code.replace("TRANSLATIONS = {", f"TRANSLATIONS = {{\n{trans_insert}")

# Modify display name logic
# Old: display_name = f"{main_kr} - {sub_kr}"
# New: display_name = sub_kr
code = code.replace('display_name = f"{main_kr} - {sub_kr}"', 'display_name = sub_kr')

with open("app.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Updates successful.")
