import sys

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

print("=== ALL PARTICIPANTS WITH 'ชอ' IN DEPT ===")
chaam_list = []
for p in raw_participants:
    if 'ชอ' in p['dept'] or 'ชะอำ' in p['dept']:
        chaam_list.append(p)

print(f"Found {len(chaam_list)} participants:")
for c in chaam_list:
    print(f"Seq {c['seq']:2s} | ID:{c['emp_id']:7s} | {c['name']:25s} | Pos:{c['pos']:12s} | Dept:{c['dept']}")
