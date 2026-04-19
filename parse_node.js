const fs = require('fs');

const jsContent = fs.readFileSync('finviz_themes_raw.js', 'utf-8');

// 정규식으로 {name:"Root", ...} 부분을 찾아냅니다. 
const regex = /e\.exports=(\{name:"Root".*?\})\}\]\)/;
const match = jsContent.match(regex);

if (!match) {
  console.log("Not found data");
  process.exit(1);
}

// 추출한 문자열
let jsonStr = match[1];

// JS 속성명을 쌍따옴표로 감싸서 유효한 JSON으로 만듭니다.
jsonStr = jsonStr.replace(/([a-zA-Z0-9_]+):/g, '"$1":');

// 약간의 치환을 거쳤을 때 오류가 날 수 있는데, 속성명 중복이나 문자열 안의 따옴표 처리 때문일 수 있으므로
// eval()이나 Function()을 통해 안전한 샌드박스로 파싱하는게 나음

const safeEval = new Function('return ' + match[1]);
const rootData = safeEval();

const result = {};

function traverse(node, parentName) {
  if (node.children && node.children.length > 0) {
    let nextParent = parentName;
    if (isNaN(parseInt(node.name))) {
        nextParent = node.name;
    }
    for (const child of node.children) {
      traverse(child, nextParent);
    }
  } else {
    // Leaf node
    if (parentName) {
      result[node.name] = {
        main_en: parentName,
        sub: node.displayName || node.name
      };
    }
  }
}

traverse(rootData, null);

fs.writeFileSync('finviz_mapped_from_js.json', JSON.stringify(result, null, 2));
console.log("Parsed " + Object.keys(result).length + " keys successfully.");
