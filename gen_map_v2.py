#!/usr/bin/env python3
"""
目标项目地图生成器 v2
直接从征鸿阁 全量项目.db 读取数据
经纬度从 cmd5_coords.json 补充
"""

import json, sqlite3, os, html

WORKSPACE = os.path.expanduser("~/.openclaw/workspace")
ZHENG_DB = os.path.join(WORKSPACE, "听风园", "征鸿阁", "data", "全量项目.db")
COORDS_FILE = os.path.join(WORKSPACE, "bidding", "cmd5_coords.json")
OUTPUT_FILE = "目标项目地图.html"

# 1. 从征鸿阁获取数据
zheng = sqlite3.connect(ZHENG_DB)
zheng.row_factory = sqlite3.Row
cur = zheng.cursor()

# 只选有建联阶段的项目（即目标项目）
rows = cur.execute("""
    SELECT 项目名称, 所属区县, 所属街道, "总建筑面积__万㎡", 单价,
           建联分类, 建联阶段节点, 拓展小组, 拓展组长, 拓展组员,
           备注_项目进度说明, 在管物业公司, 业委会状态
    FROM 项目
    WHERE 建联阶段节点 IS NOT NULL AND 建联阶段节点 != ''
    ORDER BY CAST("总建筑面积__万㎡" AS REAL) DESC
""").fetchall()

zheng.close()

print(f"征鸿阁中带建联阶段的项目: {len(rows)}条")

# 2. 加载经纬度
latlng = {}
if os.path.exists(COORDS_FILE):
    coords = json.load(open(COORDS_FILE, "r"))
    for c in coords:
        latlng[c['name']] = (c['lat'], c['lng'])
    print(f"已有经纬度: {len(latlng)}个")

# 3. 颜色映射
style_map = {
    "A1": "#e74c3c",
    "A2": "#f39c12",
    "A3": "#3498db",
    "E":  "#2ecc71",
    "O":  "#95a5a6",
}

def get_color(stage):
    for key, color in style_map.items():
        if stage.startswith(key):
            return color
    return "#95a5a6"

def get_label(stage):
    labels = {
        "A1-1": "A1 已拜访见面",
        "A1-2": "A1 建立信任中",
        "A2-1": "A2 信息同步",
        "A2-2": "A2 达成条件",
        "A2-3": "A2 已进入招标",
        "A3-1": "A3 未进入招标",
        "A3-2": "A3 已进入招标",
        "E1":   "E 已中标",
        "E2":   "E 未中标",
    }
    for k, v in labels.items():
        if k in stage:
            return v
    return stage

# 4. 生成 HTML
lines = []
lines.append('<!DOCTYPE html>')
lines.append('<html><head><meta charset="utf-8">')
lines.append('<title>时代邻里 · 广州目标项目地图</title>')
lines.append('<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>')
lines.append('<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>')
lines.append("""
<style>
body{margin:0;padding:0}#map{width:100vw;height:100vh}
.legend{background:white;padding:10px;border-radius:6px;box-shadow:0 1px 5px rgba(0,0,0,0.2);font-size:13px;line-height:1.8}
.legend i{width:12px;height:12px;display:inline-block;margin-right:6px;border-radius:50%}
.info{background:white;padding:8px 12px;border-radius:4px;box-shadow:0 1px 3px rgba(0,0,0,0.2);font-size:13px}
.info strong{color:#333}
</style>
</head><body>
<div id="map"></div>
<script>
var map = L.map("map").setView([23.12, 113.3], 11);
L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",{
    maxZoom:19,
    attribution:"&copy; OpenStreetMap contributors"
}).addTo(map);
var bounds = [];
""")

plotted = 0
nocoord = 0
for r in rows:
    name = r[0]
    if name in latlng:
        lat, lng = latlng[name]
    else:
        nocoord += 1
        continue
    
    area = str(r[3]) if r[3] else "?"
    fee = str(r[4]) if r[4] else "?"
    district = r[1] or ""
    street = r[2] or ""
    stage = r[6] or ""
    cls_val = r[5] or ""
    group_val = r[7] or ""
    leader_val = r[8] or ""
    member_val = r[9] or ""
    progress = r[10] or ""
    cur_mgmt = r[11] or ""
    ec_status = r[12] or ""
    
    color = get_color(cls_val or stage)
    radius = max(7, min(22, float(area) * 0.8)) if area not in ("", "?") else 8
    
    popup_lines = [
        f"<b>{html.escape(name)}</b>",
        f"📍 {html.escape(district)} {html.escape(street)}",
        f"📐 {area}万㎡  💰 {fee}元",
        f"📊 {get_label(stage)}" if stage else "",
        f"👥 {html.escape(group_val)}  {html.escape(leader_val)}  {html.escape(member_val)}",
        f"🏢 现物业: {html.escape(cur_mgmt)}" if cur_mgmt else "",
        f"🏛 {html.escape(ec_status)}" if ec_status else "",
        f"💬 {html.escape(progress)}",
    ]
    popup_html = "<br>".join(p for p in popup_lines if p)
    
    lines.append(f"""L.circleMarker([{lat}, {lng}], {{
        radius:{radius},
        fillColor:'{color}',
        color:'#fff',
        weight:1.5,
        fillOpacity:0.7
    }}).addTo(map).bindPopup(`{popup_html}`);""")
    
    lines.append(f"bounds.push([{lat}, {lng}]);")
    plotted += 1

# 自适应
lines.append('if(bounds.length) map.fitBounds(bounds, {padding:[30,30]});')

# 统计信息控件
lines.append(f"""
var info = L.control({{position:"topleft"}});
info.onAdd = function(m){{
    var d = L.DomUtil.create("div","info");
    d.innerHTML = "<strong>时代邻里·广州目标项目</strong><br>{plotted}个项目 | {nocoord}个缺坐标";
    return d;
}};
info.addTo(map);
""")

# 图例
legend_items = []
for key, color in style_map.items():
    legend_items.append(f'<i style="background:{color}"></i>{key}')
lines.append(f"""
var legend = L.control({{position:"bottomright"}});
legend.onAdd = function(m){{
    var d = L.DomUtil.create("div","legend");
    d.innerHTML="<b>建联分类</b><br>{chr(10).join(legend_items)}";
    return d;
}};
legend.addTo(map);
""")

lines.append('</script></body></html>')

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write('\n'.join(lines))

print(f"\n✅ 已生成: {OUTPUT_FILE}")
print(f"   已标绘: {plotted} 个 | 缺坐标: {nocoord} 个")

# 统计
from collections import Counter
stage_count = Counter(r[6] or r[5] or "无阶段" for r in rows if r[0] in latlng)
print(f"\n建联分类分布:")
for k, v in sorted(stage_count.items()):
    label = get_label(k) if k != "无阶段" else k
    print(f"  {label}: {v}个")
