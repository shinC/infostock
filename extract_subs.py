import json
import re

def create_mapping_from_js():
    with open('/workspaces/stock/finviz_themes_raw.js', 'r', encoding='utf-8') as f:
        js = f.read()

    # 정규식을 이용해 모든 리프 노드 찾아내기
    # 예: {name:"aicompute",displayName:"Compute",description:"Compute & Acceleration",extra:"..."}
    # name과 displayName 쌍을 찾습니다.
    
    pattern = r'\{name:"([^"]+)",displayName:"([^"]+)"'
    matches = re.findall(pattern, js)
    
    mapping = {}
    for name, display_name in matches:
        mapping[name] = display_name

    with open('/workspaces/stock/fallback_subsectors.json', 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)

    print(f"Sub-sector mappings extracted: {len(mapping)} items.")

if __name__ == "__main__":
    create_mapping_from_js()
