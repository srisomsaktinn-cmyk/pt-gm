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

# Get all ผจฟ.
phajof_list = [p for p in participants if 'ผจฟ' in p['pos'] or 'ผจฟ' in p['dept']]

# Substation codes in Phetchaburi:
# - สำนักงาน ผจฟ.1 (ส่วนกลางแผนกสถานีไฟฟ้า)
# - ชอ. / ชอ.2 (สถานีไฟฟ้าชะอำ)
# - ขย. / ขย.1 (สถานีไฟฟ้าเขาย้อย)
# - พธ. (สถานีไฟฟ้าเพชรบุรี)
# - บพ. / บพ.1 (สถานีไฟฟ้าบ้านพาด/บ้านลาด)
# - ชพ. / ชพ.1 (สถานีไฟฟ้าชะอำ/เพชรบุรี)
# - จบ. (งานปฏิบัติการสถานีไฟฟ้าจอมบึง/เพชรบุรี)

pb_substation_keywords = ['ผจฟ.1', 'ชอ', 'ขย', 'พธ', 'บพ', 'ชพ', 'จบ']
outside_substation_keywords = ['รบ', 'รน', 'บป', 'หห', 'ปท', 'กบ', 'หจ']

pb_sub_staff = []
outside_sub_staff = []

for p in phajof_list:
    d = p['dept']
    # Check if outside substation code is explicitly present
    is_outside = any(kw in d for kw in ['รบ.2', 'รน.2', 'บป.2', 'หห.2', 'ปท.1', 'กบ.', 'หจ.2'])
    if is_outside:
        outside_sub_staff.append(p)
    else:
        pb_sub_staff.append(p)

with open(r'd:\Kaeha\substation_pb_summary.txt', 'w', encoding='utf-8') as out:
    out.write("===============================================================\n")
    out.write(f" สรุปการคัดเลือกพนักงานสถานีไฟฟ้า (กลุ่ม ผจฟ.) เฉพาะสถานีในพื้นที่จังหวัดเพชรบุรี\n")
    out.write("===============================================================\n\n")

    out.write(f"📊 จากพนักงานกลุ่ม ผจฟ. ทั้งหมด 28 คน:\n")
    out.write(f" 1. สถานีไฟฟ้า / สำนักงาน ผจฟ.1 ในจังหวัดเพชรบุรี: {len(pb_sub_staff)} คน\n")
    out.write(f" 2. สถานีไฟฟ้าในจังหวัดอื่น ๆ (ราชบุรี, ระนอง, ประจวบฯ ฯลฯ): {len(outside_sub_staff)} คน\n\n")

    out.write("---------------------------------------------------------------\n")
    out.write(f" ⚡ รายชื่อพนักงานสถานีไฟฟ้า ในจังหวัดเพชรบุรี ({len(pb_sub_staff)} คน)\n")
    out.write("---------------------------------------------------------------\n\n")

    for p in pb_sub_staff:
        out.write(f"• ลำดับที่ {p['seq']:2s} | รหัส {p['emp_id']:7s} | {p['name']:25s} | ตำแหน่ง: {p['pos']:10s} | สังกัด: {p['dept']}\n")

    out.write("\n---------------------------------------------------------------\n")
    out.write(f" ❌ รายชื่อพนักงานสถานีไฟฟ้า นอกจังหวัดเพชรบุรี ({len(outside_sub_staff)} คน)\n")
    out.write("---------------------------------------------------------------\n\n")

    for p in outside_sub_staff:
        out.write(f"• ลำดับที่ {p['seq']:2s} | รหัส {p['emp_id']:7s} | {p['name']:25s} | ตำแหน่ง: {p['pos']:10s} | สังกัด: {p['dept']}\n")

print("Generated substation_pb_summary.txt successfully!")
