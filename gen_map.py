# 目标项目地图生成器
# 读取mapdata JSON → 生成Leaflet交互式HTML地图

import json, html, os

DATA_FILE = "mapdata_53目标项目.json"
OUTPUT_FILE = "目标项目地图.html"

data = json.load(open(DATA_FILE, "r", encoding="utf-8"))

style_map = {
    "A1-1": {'color': '#e74c3c', 'label': 'A1 已拜访见面'},
    "A1-2": {'color': '#c0392b', 'label': 'A1 建立信任中'},
    "A2-1": {'color': '#f39c12', 'label': 'A2 信息同步'},
    "A2-2": {'color': '#e67e22', 'label': 'A2 深度跟进'},
    "A3-1": {'color': '#3498db', 'label': 'A3 未进入招标'},
    "A3-2": {'color': '#2980b9', 'label': 'A3 已进入招标'},
}

# 匹配最接近的阶段
def get_style(stage):
    for key, val in style_map.items():
        if key in stage:
            return val
    return {'color': '#95a5a6', 'label': '其他'}

lines = []
lines.append('<!DOCTYPE html>')
lines.append('<html><head><meta charset="utf-8">')
lines.append('<title>时代邻里 · 广州目标项目地图</title>')
lines.append('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>')
lines.append('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>')
lines.append('<style>body{margin:0;padding:0}#map{width:100vw;height:100vh}')
lines.append('.legend{background:white;padding:10px;border-radius:6px;box-shadow:0 1px 5px rgba(0,0,0,0.2);font-size:13px}')
lines.append('.legend i{width:12px;height:12px;display:inline-block;margin-right:6px;border-radius:50%}')
lines.append('</style></head><body><div id="map"></div><script>')
lines.append('var map = L.map("map").setView([23.12, 113.3], 11);')
lines.append('L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{maxZoom:19,attribution:"OpenStreetMap"}).addTo(map);')
lines.append('var bounds = [];')

for d in data:
    s = get_style(d['stage'])
    area_val = float(d['area']) if d['area'] else 0
    radius = max(7, min(22, area_val * 0.8))
    
    # 构建弹出内容
    popup_lines = [
        f"<b>{html.escape(d['name'])}</b>",
        f"📍 {html.escape(d['district'])} {html.escape(d['street'])}",
        f"📐 {d['area']}万㎡ | 💰 {d.get('fee','?')}元",
        f"📊 {d['stage']}",
        f"👤 {d.get('member','')} / {d.get('leader','')}",
        f"👥 {d.get('group','')}",
        f"💬 {html.escape(d.get('progress',''))}"
    ]
    popup_html = '<br>'.join(popup_lines)
    
    lines.append(f"""L.circleMarker([{d['lat']}, {d['lng']}], {{radius:{radius},fillColor:'{s['color']}',color:'#fff',weight:1.5,fillOpacity:0.7}}).addTo(map).bindPopup(`{popup_html}`);""")
    lines.append(f"bounds.push([{d['lat']}, {d['lng']}]);")

# 自适应缩放
lines.append('map.fitBounds(bounds, {padding: [30, 30]});')

# 图例
legend_items = []
for key, val in style_map.items():
    legend_items.append(f"<i style=\"background:{val['color']}\"></i>{val['label']}")
legend_html = '<br>'.join(legend_items)

lines.append(f"""
var legend = L.control({{position:"bottomright"}});
legend.onAdd = function(m) {{
    var d = L.DomUtil.create("div","legend");
    d.innerHTML="<b>建联阶段</b><br>{legend_html}";
    return d;
}};
legend.addTo(map);
""")

lines.append('</script></body></html>')

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write('\n'.join(lines))

print(f"✅ 已生成: {OUTPUT_FILE}")
print(f"   共 {len(data)} 个项目点")
