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

print(f"Total participants parsed from MD: {len(participants)}")

# Categorize by Office / Branch
office_map = defaultdict(list)

for p in participants:
    dept = p['dept']
    if 'กฟส.บปง.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาบ้านโป่ง (กฟส.บปง.)'
    elif 'กฟส.จบง.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาจอมบึง (กฟส.จบง.)'
    elif 'กฟส.ปทอ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาปากท่อ (กฟส.ปทอ.)'
    elif 'กฟส.พธร.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาโพธาราม (กฟส.พธร.)'
    elif 'กฟส.สนผ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาสวนผึ้ง (กฟส.สนผ.)'
    elif 'กฟส.นปม.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาบางแพ (กฟส.นปม.)'
    elif 'กฟส.บ้านคา' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาบ้านคา (กฟส.บ้านคา)'
    elif 'กฟส.ดตก.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขาดำเนินสะดวก (กฟส.ดตก.)'
    elif 'กฟส.กรญ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคสาขากาญจนบุรี (กฟส.กรญ.)'
    elif 'กฟจ.รบ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคจังหวัดราชบุรี (สำนักงานใหญ่จังหวัด กฟจ.รบ.)'
    elif 'กฟจ.พบ.' in dept: key = 'การไฟฟ้าส่วนภูมิภาคจังหวัดเพชรบุรี (กฟจ.พบ.)'
    else: key = 'ส่วนกลางเขต / ฝ่ายบริหาร / กองต่าง ๆ (กฟต.1)'
    
    office_map[key].append(p)

with open(r'd:\Kaeha\office_breakdown_a2vtui.txt', 'w', encoding='utf-8') as out:
    out.write("===============================================================\n")
    out.write(f" สรุปสาขาการไฟฟ้าของผู้เข้าร่วมประชุม 106 คน (จาก tableConvert.com_a2vtui.md)\n")
    out.write("===============================================================\n\n")

    for key, members in sorted(office_map.items(), key=lambda x: len(x[1]), reverse=True):
        out.write(f"📌 {key} — ({len(members)} คน)\n")
        out.write("-" * 63 + "\n")
        for m in members:
            out.write(f"   • ลำดับที่ {m['seq']:3s} | รหัส {m['emp_id']:7s} | {m['name']:25s} | ตำแหน่ง: {m['pos']:12s} | สังกัดย่อย: {m['dept']}\n")
        out.write("\n")

print("Generated office_breakdown_a2vtui.txt successfully!")
