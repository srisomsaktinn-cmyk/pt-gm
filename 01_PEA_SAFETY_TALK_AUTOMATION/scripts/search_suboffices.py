import sys

md1 = r'd:\Kaeha\tableConvert.com_3x9z2h.md'
md2 = r'd:\Kaeha\tableConvert.com_a2vtui.md'

keywords = ['หนองหญ้าปล้อง', 'หญ้าปล้อง', 'ท่าไม้รวก', 'ไม้รวก', 'บางตะบูน', 'ตะบูน']

print("=== SEARCH IN MD1 (Phetchaburi 83 people) ===")
with open(md1, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        for kw in keywords:
            if kw in line:
                print(f"MD1 Line {idx+1}: {line.strip()}")

print("\n=== SEARCH IN MD2 (New Meeting 106 people) ===")
with open(md2, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f):
        for kw in keywords:
            if kw in line:
                print(f"MD2 Line {idx+1}: {line.strip()}")

# Also check for PEA department codes of these sub-offices
# Usually sub-offices in PEA Phetchaburi are:
# หนองหญ้าปล้อง (กฟส.เขาย้อย หรือ กฟย.หนองหญ้าปล้อง)
# ท่าไม้รวก (กฟส.ท่ายาง / ท่าไม้รวก)
# บางตะบูน (กฟส.บ้านแหลม / บางตะบูน)

print("\n=== DEPT CODES CONTAINING SUB-OFFICE ABBREVIATIONS ===")
with open(md1, 'r', encoding='utf-8') as f:
    for line in f:
        if any(k in line for k in ['กฟย', 'กฟสา', 'บตบ', 'ทมร', 'หญป']):
            print(f"MD1 code match: {line.strip()}")
