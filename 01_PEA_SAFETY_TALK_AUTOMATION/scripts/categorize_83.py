import sys, os
from collections import defaultdict

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

# Re-assign sequence 1 to 83
for idx, p in enumerate(participants):
    p['seq'] = str(idx + 1)

print(f"Total participants to categorize: {len(participants)}")

# Categorization Logic
# Group 1: กฟจ.พบ. (การไฟฟ้าส่วนภูมิภาคจังหวัดเพชรบุรี และ กฟส.สาขาต่าง ๆ ในเพชรบุรี)
# Group 2: หน่วยงานระดับเขต/ฝ่ายบริหาร กฟต.1 (การไฟฟ้าส่วนภูมิภาคภาคใต้ เขต 1)

pb_group = []
regional_group = []

for p in participants:
    dept = p['dept']
    if 'กฟจ.พบ.' in dept:
        pb_group.append(p)
    else:
        regional_group.append(p)

with open(r'd:\Kaeha\categorized_83_summary.txt', 'w', encoding='utf-8') as out:
    out.write("===============================================================\n")
    out.write(f"  สรุปการแยกสังกัดผู้เข้าร่วมประชุม ทั้งหมด {len(participants)} คน\n")
    out.write("===============================================================\n\n")

    out.write(f"📊 สรุปสัดส่วนภาพรวม:\n")
    out.write(f" 1. สังกัดการไฟฟ้าในจังหวัดเพชรบุรี (กฟจ.พบ. และ กฟส.สาขาในจังหวัด): {len(pb_group)} คน\n")
    out.write(f" 2. สังกัดหน่วยงานระดับเขต / ฝ่ายบริหาร / กองต่าง ๆ (กฟต.1): {len(regional_group)} คน\n")
    out.write("=" * 63 + "\n\n")

    # 1. PEA Phetchaburi Breakdown
    out.write("---------------------------------------------------------------\n")
    out.write(f" 📍 Group 1: สังกัดการไฟฟ้าในจังหวัดเพชรบุรี (รวม {len(pb_group)} คน)\n")
    out.write("---------------------------------------------------------------\n\n")

    pb_sub = defaultdict(list)
    for p in pb_group:
        d = p['dept']
        if 'กฟส.บลด.' in d: key = 'กฟส.บ้านลาด (การไฟฟ้าส่วนภูมิภาคสาขาบ้านลาด)'
        elif 'กฟส.ชอ.' in d: key = 'กฟส.ชะอำ (การไฟฟ้าส่วนภูมิภาคสาขาชะอำ)'
        elif 'กฟส.ขยย.' in d: key = 'กฟส.เขาย้อย (การไฟฟ้าส่วนภูมิภาคสาขาเขาย้อย)'
        elif 'กฟส.บห.' in d: key = 'กฟส.บ้านแหลม (การไฟฟ้าส่วนภูมิภาคสาขาบ้านแหลม)'
        elif 'กฟส.กกจ.' in d or 'กฟส.ทย.' in d: key = 'กฟส.แก่งกระจาน / กฟส.ท่ายาง (สาขาแก่งกระจาน / ท่ายาง)'
        else: key = 'กฟจ.เพชรบุรี สำนักงานใหญ่จังหวัด (สำนักงาน อ.เมืองเพชรบุรี)'
        pb_sub[key].append(p)

    for sub_name, members in sorted(pb_sub.items(), key=lambda x: len(x[1]), reverse=True):
        out.write(f"🔹 {sub_name} — ({len(members)} คน)\n")
        for m in members:
            out.write(f"   • ลำดับที่ {m['seq']:2s} | รหัส {m['emp_id']:7s} | {m['name']:25s} | ตำแหน่ง: {m['pos']:12s} | สังกัดย่อย: {m['dept']}\n")
        out.write("\n")

    # 2. Regional HQ Breakdown
    out.write("---------------------------------------------------------------\n")
    out.write(f" 🏢 Group 2: สังกัดหน่วยงานระดับเขต / ฝ่ายบริหาร / กองต่าง ๆ (รวม {len(regional_group)} คน)\n")
    out.write("---------------------------------------------------------------\n\n")

    reg_sub = defaultdict(list)
    for p in regional_group:
        d = p['dept']
        reg_sub[d].append(p)

    for sub_name, members in sorted(reg_sub.items(), key=lambda x: len(x[1]), reverse=True):
        out.write(f"🔸 {sub_name} — ({len(members)} คน)\n")
        for m in members:
            out.write(f"   • ลำดับที่ {m['seq']:2s} | รหัส {m['emp_id']:7s} | {m['name']:25s} | ตำแหน่ง: {m['pos']:12s}\n")
        out.write("\n")

print("Generated categorized_83_summary.txt successfully!")
