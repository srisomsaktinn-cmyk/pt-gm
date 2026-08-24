import sys, zipfile, xml.etree.ElementTree as ET

MD_PATH = r'd:\Kaeha\tableConvert.com_3x9z2h.md'

participants = []
with open(MD_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    line_str = line.strip()
    if not line_str.startswith('|'):
        continue
    parts = [p.strip() for p in line_str.split('|')[1:-1]]
    if len(parts) >= 5 and parts[0].isdigit():
        participants.append({
            'emp_id': parts[1],
            'name': parts[2],
            'pos': parts[3],
            'dept': parts[4]
        })

# Insert Ms. Rattiya Sukkasem at sequence 31
new_person = {
    'emp_id': '504811',
    'name': 'นางสาว รัฐทียา สุขเกษม',
    'pos': 'จป.ว.7',
    'dept': 'กฟจ.พบ. กฟต.1 สายงาน (ต)'
}
participants.insert(30, new_person)

for idx, p in enumerate(participants):
    p['seq'] = str(idx + 1)

# Criteria:
# 1. พนักงานในเพชรบุรี (กฟจ.พบ. or Phetchaburi branches)
# 2. จป. (Position or Dept contains จป.)
# 3. ผจฟ (Position or Dept contains ผจฟ)

print(f"Total initial participants: {len(participants)}")

pb_people = [p for p in participants if 'กฟจ.พบ.' in p['dept']]
jp_people = [p for p in participants if 'จป' in p['pos'] or 'จป' in p['dept']]
phajof_people = [p for p in participants if 'ผจฟ' in p['pos'] or 'ผจฟ' in p['dept']]

# Combined target list (Union or Intersection?)
# The phrasing: "เอาแค่ พนักงานในเพชรบุรี จป. กับ ผจฟ"
# Usually means: Keep (1) พนักงานในเพชรบุรี + (2) จป. ทุกคน + (3) ผจฟ. ทุกคน
# Or does it mean: Filter down to (พนักงานในเพชรบุรี) + (จป.) + (ผจฟ.)?

union_set = {}
for p in pb_people + jp_people + phajof_people:
    union_set[p['seq']] = p

filtered = sorted(union_set.values(), key=lambda x: int(x['seq']))

print("=== BREAKDOWN BY CRITERIA ===")
print(f"1. พนักงานในเพชรบุรี (กฟจ.พบ. & สาขา): {len(pb_people)} คน")
print(f"2. จป. (เจ้าหน้าที่ความปลอดภัย): {len(jp_people)} คน")
print(f"3. ผจฟ. (ผู้จัดการแผนก/งานปฏิบัติการสถานีไฟฟ้า): {len(phajof_people)} คน")
print(f"รวมผู้ที่เข้าเงื่อนไขทั้งหมด (ไม่ซ้ำ): {len(filtered)} คน")
print()

for p in filtered:
    reasons = []
    if 'กฟจ.พบ.' in p['dept']: reasons.append('เพชรบุรี')
    if 'จป' in p['pos'] or 'จป' in p['dept']: reasons.append('จป.')
    if 'ผจฟ' in p['pos'] or 'ผจฟ' in p['dept']: reasons.append('ผจฟ.')
    print(f"ลำดับ {p['seq']:2s} | รหัส {p['emp_id']:7s} | {p['name']:25s} | ตำแหน่ง: {p['pos']:10s} | สังกัด: {p['dept']} | (เข้าเงื่อนไข: {', '.join(reasons)})")
