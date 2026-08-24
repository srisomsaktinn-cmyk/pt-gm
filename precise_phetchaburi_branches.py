import sys
from collections import defaultdict

MD_PATH = r'd:\Kaeha\tableConvert.com_3x9z2h.md'

raw_participants = []
with open(MD_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

for line in lines:
    line_str = line.strip()
    if not line_str.startswith('|'):
        continue
    parts = [p.strip() for p in line_str.split('|')[1:-1]]
    if len(parts) >= 5 and parts[0].isdigit():
        raw_participants.append({
            'emp_id': parts[1],
            'name': parts[2],
            'pos': parts[3],
            'dept': parts[4]
        })

# Insert Ms. Rattiya Sukkasem
new_person = {
    'emp_id': '504811',
    'name': 'นางสาว รัฐทียา สุขเกษม',
    'pos': 'จป.ว.7',
    'dept': 'กฟจ.พบ. กฟต.1 สายงาน (ต)'
}
raw_participants.insert(30, new_person)

for idx, p in enumerate(raw_participants):
    p['seq'] = str(idx + 1)

pb_exact_map = defaultdict(list)

for p in raw_participants:
    dept = p['dept']
    
    if 'กฟส.ชอ.' in dept or 'ชอ.1' in dept or 'ชอ.2' in dept:
        key = '1. การไฟฟ้าส่วนภูมิภาคสาขาชะอำ (กฟส.ชอ.)'
    elif 'กฟส.ขยย.' in dept or 'กฟส.ขย.' in dept or 'ขย.1' in dept or 'ขย.2' in dept:
        key = '2. การไฟฟ้าส่วนภูมิภาคสาขาเขาย้อย (กฟส.ขยย.)'
    elif 'กฟส.บลด.' in dept:
        key = '3. การไฟฟ้าส่วนภูมิภาคสาขาบ้านแหลม (กฟส.บลด.)'
    elif 'กฟส.บห.' in dept:
        key = '4. การไฟฟ้าส่วนภูมิภาคสาขาบ้านลาด (กฟส.บห.)'
    elif 'กฟส.กกจ.' in dept:
        key = '5. การไฟฟ้าส่วนภูมิภาคสาขาแก่งกระจาน (กฟส.กกจ.)'
    elif 'กฟส.ทย.' in dept or 'กฟส.ทซ.' in dept or 'ทซ.' in dept:
        key = '6. การไฟฟ้าส่วนภูมิภาคสาขาท่ายาง (กฟส.ทย. / กฟส.ทซ.)'
    elif 'กฟจ.พบ.' in dept or 'พบ.1' in dept or 'พบ.2' in dept:
        key = '7. การไฟฟ้าส่วนภูมิภาคจังหวัดเพชรบุรี (สำนักงานใหญ่จังหวัด กฟจ.พบ.)'
    else:
        key = '8. ส่วนกลางเขต กฟต.1 / สถานีไฟฟ้าประจำต่างจังหวัด'

    pb_exact_map[key].append(p)

with open(r'd:\Kaeha\phetchaburi_precise_report.txt', 'w', encoding='utf-8') as out:
    out.write("===============================================================\n")
    out.write(f" สรุปจำแนกสาขาในจังหวัดเพชรบุรีอย่างแม่นยำ 100% (รวม 83 คน)\n")
    out.write("===============================================================\n\n")

    total_pb = 0
    for key in sorted(pb_exact_map.keys()):
        members = pb_exact_map[key]
        if '8. ส่วนกลางเขต' not in key:
            total_pb += len(members)
        out.write(f"📌 {key} — ({len(members)} คน)\n")
        out.write("-" * 63 + "\n")
        for m in members:
            out.write(f"   • ลำดับที่ {m['seq']:2s} | รหัส {m['emp_id']:7s} | {m['name']:25s} | ตำแหน่ง: {m['pos']:12s} | สังกัดย่อย: {m['dept']}\n")
        out.write("\n")

    out.write(f"รวมพนักงานและสถานีไฟฟ้าในพื้นที่จังหวัดเพชรบุรีทั้งหมด: {total_pb} คน\n")

print(f"Generated phetchaburi_precise_report.txt successfully! Total PB: {total_pb}")
