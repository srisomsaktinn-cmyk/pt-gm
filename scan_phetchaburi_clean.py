import re

MD_PATH = r'd:\Kaeha\tableConvert.com_3x9z2h.md'

with open(MD_PATH, 'r', encoding='utf-8') as f:
    lines = f.readlines()

participants = []
for line in lines:
    line_str = line.strip()
    if not line_str.startswith('|'):
        continue
    parts = [p.strip() for p in line_str.split('|')[1:-1]]
    if len(parts) >= 5 and parts[0].isdigit():
        participants.append({
            'seq': parts[0],
            'emp_id': parts[1],
            'name': parts[2],
            'pos': parts[3],
            'dept': parts[4]
        })

# Map PEA office/branch codes in Phetchaburi Province (กฟจ.พบ. & branches under กฟจ.พบ.)
# กฟจ.พบ. = การไฟฟ้าส่วนภูมิภาคจังหวัดเพชรบุรี (กฟจ.)
# กฟส.บลด. = การไฟฟ้าส่วนภูมิภาคสาขาบ้านลาด (กฟส.บ้านลาด)
# กฟส.ชอ. = การไฟฟ้าส่วนภูมิภาคสาขาชะอำ (กฟส.ชะอำ)
# กฟส.ขยย. = การไฟฟ้าส่วนภูมิภาคสาขาเขาย้อย (กฟส.เขาย้อย)
# กฟส.บห. = การไฟฟ้าส่วนภูมิภาคสาขาบ้านแหลม (กฟส.บ้านแหลม)
# กฟส.กกจ. = การไฟฟ้าส่วนภูมิภาคสาขาแก่งกระจาน (กฟส.แก่งกระจาน)
# กฟส.ทย. = การไฟฟ้าส่วนภูมิภาคสาขาท่ายาง (กฟส.ท่ายาง)

branches_def = [
    ('กฟจ.พบ.', 'การไฟฟ้าส่วนภูมิภาคจังหวัดเพชรบุรี (สำนักงานจังหวัด / อ.เมืองเพชรบุรี)', 'กฟจ.พบ.'),
    ('กฟส.บลด.', 'การไฟฟ้าส่วนภูมิภาคสาขาบ้านลาด (อ.บ้านลาด)', 'กฟส.บลด.'),
    ('กฟส.ชอ.', 'การไฟฟ้าส่วนภูมิภาคสาขาชะอำ (อ.ชะอำ)', 'กฟส.ชอ.'),
    ('กฟส.ขยย.', 'การไฟฟ้าส่วนภูมิภาคสาขาเขาย้อย (อ.เขาย้อย)', 'กฟส.ขยย.'),
    ('กฟส.บห.', 'การไฟฟ้าส่วนภูมิภาคสาขาบ้านแหลม (อ.บ้านแหลม)', 'กฟส.บห.'),
    ('กฟส.กกจ.', 'การไฟฟ้าส่วนภูมิภาคสาขาแก่งกระจาน (อ.แก่งกระจาน)', 'กฟส.กกจ.'),
    ('กฟส.ทย.', 'การไฟฟ้าส่วนภูมิภาคสาขาท่ายาง (อ.ท่ายาง)', 'กฟส.ทย.'),
]

branch_results = {code: {'name': name, 'count': 0, 'members': []} for code, name, _ in branches_def}
regional_office_count = 0
regional_members = []

for p in participants:
    dept = p['dept']
    matched_branch = False
    
    # Check if specific branch code exists in dept
    for code, name, _ in branches_def:
        if code in dept:
            branch_results[code]['count'] += 1
            branch_results[code]['members'].append(p)
            matched_branch = True
            break

    if not matched_branch:
        regional_office_count += 1
        regional_members.append(p)

with open(r'd:\Kaeha\phetchaburi_summary.txt', 'w', encoding='utf-8') as out:
    out.write("===============================================================\n")
    out.write(" สรุปการสแกนผู้เข้าร่วมประชุม: หน่วยงานการไฟฟ้าในจังหวัดเพชรบุรี\n")
    out.write("===============================================================\n\n")

    total_pb = sum(b['count'] for b in branch_results.values())
    out.write(f"จำนวนผู้เข้าร่วมทั้งหมด: {len(participants)} คน\n")
    out.write(f"- สังกัดการไฟฟ้าในจังหวัดเพชรบุรี (กฟจ.พบ. และ กฟส.สาขาต่างๆ): {total_pb} คน\n")
    out.write(f"- สังกัดหน่วยงานระดับเขต/ฝ่ายบริหาร (ฝสบ.(ต1), กปบ.(ต1), ผจฟ.1 ฯลฯ): {regional_office_count} คน\n\n")

    out.write("---------------------------------------------------------------\n")
    out.write(" รายชื่อสาขาการไฟฟ้าในจังหวัดเพชรบุรี ที่มีผู้ลงทะเบียนเข้าร่วม\n")
    out.write("---------------------------------------------------------------\n\n")

    idx = 1
    for code, name, _ in branches_def:
        b_data = branch_results[code]
        if b_data['count'] > 0:
            out.write(f"{idx}. [{code}] {name}\n")
            out.write(f"   จำนวนผู้ลงทะเบียน: {b_data['count']} คน\n")
            out.write("   รายชื่อผู้เข้าร่วม:\n")
            for m in b_data['members']:
                out.write(f"     • ลำดับที่ {m['seq']:2s} | รหัส {m['emp_id']:7s} | {m['name']:25s} | ตำแหน่ง: {m['pos']:12s} | สังกัดย่อย: {m['dept']}\n")
            out.write("\n")
            idx += 1

    out.write("---------------------------------------------------------------\n")
    out.write(" รายชื่อสาขาการไฟฟ้าในจังหวัดเพชรบุรี ที่ไม่มีผู้ลงทะเบียนเข้าร่วม\n")
    out.write("---------------------------------------------------------------\n\n")

    for code, name, _ in branches_def:
        b_data = branch_results[code]
        if b_data['count'] == 0:
            out.write(f" • [{code}] {name}\n")

    out.write("\n===============================================================\n")

print("Generated phetchaburi_summary.txt successfully!")
