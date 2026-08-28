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

# Map PEA branch abbreviations in Phetchaburi (กฟจ.พบ.)
# กฟจ.พบ. = การไฟฟ้าส่วนภูมิภาคจังหวัดเพชรบุรี
# กฟส.บลด. = การไฟฟ้าส่วนภูมิภาคสาขาบ้านลาด (อ.บ้านลาด จ.เพชรบุรี)
# กฟส.ชอ. = การไฟฟ้าส่วนภูมิภาคสาขาชะอำ (อ.ชะอำ จ.เพชรบุรี)
# กฟส.ขยย. = การไฟฟ้าส่วนภูมิภาคสาขาเขาย้อย (อ.เขาย้อย จ.เพชรบุรี)
# กฟส.บห. = การไฟฟ้าส่วนภูมิภาคสาขาบ้านแหลม (อ.บ้านแหลม จ.เพชรบุรี)
# กฟส.กกจ. = การไฟฟ้าส่วนภูมิภาคสาขาแก่งกระจาน (อ.แก่งกระจาน จ.เพชรบุรี)
# กฟส.ทย. = การไฟฟ้าส่วนภูมิภาคสาขาท่ายาง (อ.ท่ายาง จ.เพชรบุรี)

branch_info = {
    'กฟจ.พบ.': {'name_th': 'กฟจ.เพชรบุรี (การไฟฟ้าส่วนภูมิภาคจังหวัดเพชรบุรี - สำนักงานใหญ่จังหวัด)', 'district': 'อ.เมืองเพชรบุรี', 'count': 0, 'members': []},
    'กฟส.บลด.': {'name_th': 'กฟส.บ้านลาด (การไฟฟ้าส่วนภูมิภาคสาขาบ้านลาด)', 'district': 'อ.บ้านลาด', 'count': 0, 'members': []},
    'กฟส.ชอ.': {'name_th': 'กฟส.ชะอำ (การไฟฟ้าส่วนภูมิภาคสาขาชะอำ)', 'district': 'อ.ชะอำ', 'count': 0, 'members': []},
    'กฟส.ขยย.': {'name_th': 'กฟส.เขาย้อย (การไฟฟ้าส่วนภูมิภาคสาขาเขาย้อย)', 'district': 'อ.เขาย้อย', 'count': 0, 'members': []},
    'กฟส.บห.': {'name_th': 'กฟส.บ้านแหลม (การไฟฟ้าส่วนภูมิภาคสาขาบ้านแหลม)', 'district': 'อ.บ้านแหลม', 'count': 0, 'members': []},
    'กฟส.กกจ.': {'name_th': 'กฟส.แก่งกระจาน (การไฟฟ้าส่วนภูมิภาคสาขาแก่งกระจาน)', 'district': 'อ.แก่งกระจาน', 'count': 0, 'members': []},
    'กฟส.ทย.': {'name_th': 'กฟส.ท่ายาง (การไฟฟ้าส่วนภูมิภาคสาขาท่ายาง)', 'district': 'อ.ท่ายาง', 'count': 0, 'members': []},
}

other_depts = {}

for p in participants:
    dept = p['dept']
    matched_pb = False
    
    # Check if contains กฟจ.พบ. or any Phetchaburi branch code
    if 'กฟจ.พบ.' in dept or any(b in dept for b in branch_info.keys()):
        for b_code, info in branch_info.items():
            if b_code in dept:
                info['count'] += 1
                info['members'].append(p)
                matched_pb = True
                break
        if not matched_pb and 'กฟจ.พบ.' in dept:
            branch_info['กฟจ.พบ.']['count'] += 1
            branch_info['กฟจ.พบ.']['members'].append(p)
            matched_pb = True
            
    if not matched_pb:
        other_depts[dept] = other_depts.get(dept, 0) + 1

print("--- PHETCHABURI BRANCHES SCAN SUMMARY ---")
total_pb = sum(b['count'] for b in branch_info.values())
print(f"Total participants from Phetchaburi Province (กฟจ.พบ. & Branches): {total_pb} / {len(participants)}")
print()

for b_code, info in branch_info.items():
    print(f"[{b_code}] {info['name_th']} ({info['district']}) : {info['count']} คน")
    for m in info['members']:
        print(f"   - ลำดับ {m['seq']:2s} | รหัส {m['emp_id']} | {m['name']} ({m['pos']}) | สังกัด: {m['dept']}")
    print()

print("--- OTHER OFFICES (e.g. Regional Office / Sector Office) ---")
for d, c in other_depts.items():
    print(f" - {d}: {c} คน")
