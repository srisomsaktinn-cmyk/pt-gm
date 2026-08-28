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

# Inspect all people under ผจฟ.
phajof_list = [p for p in participants if 'ผจฟ' in p['pos'] or 'ผจฟ' in p['dept']]

with open(r'd:\Kaeha\substation_analysis.txt', 'w', encoding='utf-8') as out:
    out.write("===============================================================\n")
    out.write(f" รายชื่อพนักงานกลุ่ม ผจฟ. (สถานีไฟฟ้า/งานปฏิบัติการ) ทั้งหมด {len(phajof_list)} คน\n")
    out.write("===============================================================\n\n")

    for p in phajof_list:
        out.write(f"ลำดับ {p['seq']:2s} | รหัส {p['emp_id']:7s} | {p['name']:25s} | ตำแหน่ง: {p['pos']:10s} | สังกัด: {p['dept']}\n")

print("Generated substation_analysis.txt successfully!")
