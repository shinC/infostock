"""
Finviz 테마 JS 파일을 파싱하여 sector_mapping.json 을 생성하는 스크립트.
finviz_themes_raw.js 에서 JSON 트리를 추출하고,
모든 leaf 노드(실제 주식 테마)의 key → {main, main_kr, sub} 매핑을 만듭니다.
"""
import json
import re

# 영문→한글 섹터 번역 사전
SECTOR_KR = {
    "Artificial Intelligence":      "인공지능",
    "Cloud Computing":              "클라우드 컴퓨팅",
    "Semiconductors":               "반도체",
    "Cybersecurity":                "사이버보안",
    "Software":                     "소프트웨어",
    "Hardware":                     "하드웨어",
    "Big Data":                     "빅데이터",
    "Biometrics":                   "생체인식",
    "Virtual & Augmented Reality":  "VR/AR",
    "Quantum Computing":            "양자 컴퓨팅",
    "Autonomous Systems":           "자율주행",
    "Industrial Automation":        "자동화",
    "Electric Vehicles":            "전기차",
    "Robotics":                     "로보틱스",
    "Defense & Aerospace":          "방산",
    "Space Tech":                   "우주기술",
    "Education Technology":         "에듀테크",
    "E-commerce":                   "이커머스",
    "FinTech":                      "핀테크",
    "Consumer Goods":               "소비재",
    "Crypto & Blockchain":          "블록체인",
    "Digital Entertainment":        "디지털 엔터테인먼트",
    "Transportation & Logistics":   "교통/물류",
    "Telecommunications":           "통신",
    "Smart Home":                   "스마트홈",
    "Wearables":                    "웨어러블",
    "Nanotechnology":               "나노기술",
    "Internet of Things":           "사물인터넷(IoT)",
    "Social Media":                 "소셜 미디어",
    "Real Estate & REITs":          "부동산",
    "Energy Renewable":             "신재생 에너지",
    "Energy Traditional":           "전통 에너지",
    "Commodities Energy":           "원자재(에너지)",
    "Commodities Metals":           "원자재(금속)",
    "Commodities Agriculture":      "원자재(농산물)",
    "Agriculture & FoodTech":       "농업/푸드테크",
    "Environmental Sustainability": "환경기술",
    "Healthcare & Biotech":         "헬스케어",
    "Aging Population & Longevity": "고령화/장수",
    "Healthy Food & Nutrition":     "영양/식품",
}

def extract_json_from_js(js_content):
    """JS 파일에서 e.exports=... 부분의 JSON 객체를 추출"""
    # Find the pattern: e.exports={name:"Root",...}
    match = re.search(r'e\.exports=(\{name:"Root".*?\})\}\]\)', js_content)
    if not match:
        raise ValueError("Could not find theme data in JS file")
    
    json_str = match.group(1)
    # JS object notation → valid JSON: unquoted keys → quoted keys
    # The JS uses unquoted property names like {name:"Root",children:[...]}
    # We need to convert to {"name":"Root","children":[...]}
    json_str = re.sub(r'(?<=[{,])(\w+):', r'"\1":', json_str)
    
    return json.loads(json_str)

def walk_tree(node, parent_name=None):
    """재귀적으로 트리를 탐색하여 leaf 노드의 매핑을 수집"""
    results = {}
    name = node.get("name", "")
    children = node.get("children", [])
    
    if not children:
        # Leaf node → 이것이 실제 테마 항목
        # parent_name 이 메인 카테고리, name이 키, displayName이 서브섹터
        if parent_name and "displayName" in node:
            main_en = parent_name
            main_kr = SECTOR_KR.get(main_en, main_en)
            results[name] = {
                "main": main_kr,
                "main_en": main_en,
                "sub": node["displayName"]
            }
        return results
    
    for child in children:
        child_name = child.get("name", "")
        # 숫자 그룹("1", "2", "3"...)은 건너뛰고 parent를 그대로 전달
        if child_name.isdigit():
            results.update(walk_tree(child, parent_name))
        elif "children" in child and any("children" in gc or "displayName" in gc for gc in child.get("children", [])):
            # 이것이 메인 카테고리 노드
            results.update(walk_tree(child, child_name))
        else:
            results.update(walk_tree(child, parent_name or child_name))
    
    return results

def main():
    with open("finviz_themes_raw.js", "r") as f:
        js_content = f.read()
    
    tree = extract_json_from_js(js_content)
    mapping = walk_tree(tree)
    
    # 결과 저장
    with open("sector_mapping.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    
    # 통계 출력
    sectors = {}
    for key, val in mapping.items():
        main = val["main"]
        if main not in sectors:
            sectors[main] = []
        sectors[main].append(f"  {key} → {val['sub']}")
    
    print(f"총 {len(mapping)}개 테마 매핑 완료\n")
    for sector in sorted(sectors.keys()):
        items = sectors[sector]
        print(f"[{sector}] ({len(items)}개)")
        for item in items:
            print(item)
        print()

if __name__ == "__main__":
    main()
