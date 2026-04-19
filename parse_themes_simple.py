import json
import re

def parse_finviz_js():
    with open('/workspaces/stock/finviz_themes_raw.js', 'r', encoding='utf-8') as f:
        js_data = f.read()

    # e.exports={...} 부분 추출
    start_str = 'e.exports={'
    start_idx = js_data.find(start_str)
    if start_idx == -1:
        print("Could not find start str")
        return

    # 끝 부분 다듬기
    json_part = js_data[start_idx + len('e.exports='):]
    json_part = json_part.split('}]);')[0]
    
    # 마지막의 잘못된 부분들 정리
    json_part = json_part.split('//# sourceMappingURL')[0]
    # '}' 의 갯수를 세어 올바르게 닫힌 시점까지만 취하기
    
    # 더 쉬운 방법: 정규표현식으로 {name:"Root", ... } 로 시작해서 처음으로 균형이 맞는 } 를 찾기
    
    # JS 속성명을 쌍따옴표로 감싸기
    json_part = re.sub(r'(\b\w+):', r'"\1":', json_part)

    try:
        # 끝에 }}}] 등 불필요하게 닫히거나 열린 괄호를 맞추는 대신 정규표현식을 통해 "children" 배열 구조를 파싱
        # json_part의 맨 끝에서 안 맞는 중괄호 정리
        while True:
            try:
                data = json.loads(json_part)
                break
            except json.JSONDecodeError as e:
                # Extra data 가 나오면 해당 시점 앞까지만 자르기
                if "Extra data" in str(e):
                    idx = int(re.search(r'char (\d+)', str(e)).group(1))
                    json_part = json_part[:idx]
                else:
                    raise e
                    
        print("Parsing successful!")
        
        mapping_data = {}
        
        def process_node(node, parent_name=None):
            if 'children' in node:
                if node['name'].isdigit():
                    next_parent = parent_name
                else:
                    next_parent = node['name']
                
                for child in node['children']:
                    process_node(child, next_parent)
            else:
                if parent_name:
                    mapping_data[node['name']] = {
                        "main_en": parent_name,
                        "sub": node.get('displayName', node['name'])
                    }
        
        process_node(data)
        
        with open('/workspaces/stock/parsed_finviz_mapping.json', 'w', encoding='utf-8') as out:
            json.dump(mapping_data, out, ensure_ascii=False, indent=2)
            
        print(f"Extracted {len(mapping_data)} keys.")
        
    except Exception as e:
        print(f"Parsing failed: {e}")

parse_finviz_js()
