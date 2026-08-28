import sys
from collections import defaultdict

MD_PATH = r'd:\Kaeha\tableConvert.com_a2vtui.md'

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
            'seq': parts[0],
            'emp_id': parts[1],
            'name': parts[2],
            'pos': parts[3],
            'dept': parts[4]
        })

print(f"Total participants: {len(participants)}")

# Let's inspect every department string carefully!
with open(r'd:\Kaeha\detailed_dept_check.txt', 'w', encoding='utf-8') as out:
    for p in participants:
        out.write(f"Seq {p['seq']:3s} | ID:{p['emp_id']:7s} | {p['name']:25s} | Pos:{p['pos']:12s} | Dept:{p['dept']}\n")

# Let's categorize every branch explicitly by identifying sub-branch strings first!
# Notice: In PEA hierarchy, a sub-branch often includes its parent office in the string!
# E.g. "กฟส.สนผ. กฟส.จบง. กฟจ.รบ." means "กฟส.สวนผึ้ง (สังกัด กฟส.จอมบึง)"
# "กฟส.บ้านคา กฟส.จบง." means "กฟส.บ้านคา (สังกัด กฟส.จอมบึง)"
# "กฟส.นปม. กฟส.บปง." means "กฟส.บางแพ (สังกัด กฟส.บ้านโป่ง)"
# "กฟส.ดตก. กฟส.จบง." means "กฟส.ดำเนินสะดวก (สังกัด กฟส.จอมบึง)"
# "กฟส.กรญ. กฟส.บปง." means "กฟส.กรพะโดน/กาญจนบุรี (สังกัด กฟส.บ้านโป่ง)"

sub_branch_map = defaultdict(list)

for p in participants:
    dept = p['dept']
    
    # Check specific sub-branches first!
    if 'กฟส.สนผ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาย่อยสวนผึ้ง (กฟส.สนผ.)'
    elif 'กฟส.บ้านคา' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาย่อยบ้านคา (กฟส.บ้านคา)'
    elif 'กฟส.นปม.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาย่อยบางแพ (กฟส.นปม.)'
    elif 'กฟส.ดตก.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาดำเนินสะดวก (กฟส.ดตก.)'
    elif 'กฟส.กรญ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขา/จุดบริการ (กฟส.กรญ.)'
    elif 'กฟส.บปง.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาบ้านโป่ง (กฟส.บปง.)'
    elif 'กฟส.จบง.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาจอมบึง (กฟส.จบง.)'
    elif 'กฟส.ปทอ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาปากท่อ (กฟส.ปทอ.)'
    elif 'กฟส.พธร.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาโพธาราม (กฟส.พธร.)'
    elif 'กฟจ.รบ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคจังหวัดราชบุรี (สำนักงานใหญ่จังหวัด กฟจ.รบ.)'
    elif 'กฟจ.พบ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคจังหวัดเพชรบุรี (กฟจ.พบ.)'
    else: key = 'ส่วนกลางเขต / ฝ่ายบริหาร / กองต่าง ๆ (กฟต.1)'
    
    sub_branch_map[key].append(p)

with open(r'd:\Kaeha\full_branch_report_accurate.txt', 'w', encoding='utf-8') as out:
    out.write("===============================================================\n")
    out.write(f" สรุปการแบ่งสาขาและสาขาย่อยอย่างละเอียด (รวม 106 คน)\n")
    out.write("===============================================================\n\n")

    total_check = 0
    for key, members in sorted(sub_branch_map.items(), key=lambda x: len(x[1]), reverse=True):
        total_check += len(members)
        out.write(f"📌 {key} — ({len(members)} คน)\n")
        out.write("-" * 63 + "\n")
        for m in members:
            out.write(f"   • ลำดับที่ {m['seq']:3s} | รหัส {m['emp_id']:7s} | {m['name']:25s} | ตำแหน่ง: {m['pos']:12s} | สังกัดย่อย: {m['dept']}\n")
        out.write("\n")
    
    out.write(f"\nรวมทั้งสิ้น: {total_check} คน\n")

print(f"Generated full_branch_report_accurate.txt successfully! Total checked: {total_check}")
