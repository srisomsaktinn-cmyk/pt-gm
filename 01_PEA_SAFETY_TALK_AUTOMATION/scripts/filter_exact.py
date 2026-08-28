import sys

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

# Insert Ms. Rattiya Sukkasem as Sequence 31
new_person = {
    'emp_id': '504811',
    'name': 'นางสาว รัฐทียา สุขเกษม',
    'pos': 'จป.ว.7',
    'dept': 'กฟจ.พบ. กฟต.1 สายงาน (ต)'
}
participants.insert(30, new_person)

for idx, p in enumerate(participants):
    p['seq'] = str(idx + 1)

def is_pb(p):
    return 'กฟจ.พบ.' in p['dept']

def is_jp(p):
    return 'จป' in p['pos'] or 'จป' in p['dept']

def is_phajof(p):
    return 'ผจฟ' in p['pos'] or 'ผจฟ' in p['dept']

# Interpretation 1: Union (พนักงานเพชรบุรี + จป. ทุกคน + ผจฟ. ทุกคน)
union_list = [p for p in participants if is_pb(p) or is_jp(p) or is_phajof(p)]

# Interpretation 2: Intersection inside Phetchaburi (พนักงานในเพชรบุรี ที่เป็น จป. หรือ ผจฟ.)
pb_jp_phajof = [p for p in participants if is_pb(p) and (is_jp(p) or is_phajof(p))]

with open(r'd:\Kaeha\filtered_results.txt', 'w', encoding='utf-8') as out:
    out.write("===============================================================\n")
    out.write(" สรุปการคัดเลือกผู้เข้าร่วมประชุม (จากทั้งหมด 83 คน)\n")
    out.write(" เงื่อนไข: 1. พนักงานในเพชรบุรี (กฟจ.พบ.) / 2. จป. / 3. ผจฟ.\n")
    out.write("===============================================================\n\n")

    out.write(f"📌 กรณีที่ 1: รวมคนที่อยู่กลุ่มใดกลุ่มหนึ่งใน 3 กลุ่มนี้ (รวม {len(union_list)} คน)\n")
    out.write("---------------------------------------------------------------\n")
    for p in union_list:
        tags = []
        if is_pb(p): tags.append("เพชรบุรี")
        if is_jp(p): tags.append("จป.")
        if is_phajof(p): tags.append("ผจฟ.")
        out.write(f"• ลำดับที่ {p['seq']:2s} | รหัส {p['emp_id']:7s} | {p['name']:25s} | ตำแหน่ง: {p['pos']:10s} | สังกัด: {p['dept']} | [{', '.join(tags)}]\n")

    out.write("\n" + "=" * 63 + "\n\n")

    out.write(f"📌 กรณีที่ 2: เฉพาะพนักงานในจังหวัดเพชรบุรี ที่เป็น จป. หรือ ผจฟ. (รวม {len(pb_jp_phajof)} คน)\n")
    out.write("---------------------------------------------------------------\n")
    for p in pb_jp_phajof:
        tags = []
        if is_jp(p): tags.append("จป.")
        if is_phajof(p): tags.append("ผจฟ.")
        out.write(f"• ลำดับที่ {p['seq']:2s} | รหัส {p['emp_id']:7s} | {p['name']:25s} | ตำแหน่ง: {p['pos']:10s} | สังกัด: {p['dept']} | [{', '.join(tags)}]\n")

print("Generated filtered_results.txt successfully!")
