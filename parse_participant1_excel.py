import sys, zipfile, xml.etree.ElementTree as ET, re

path = r'd:\Kaeha\Participant (1).xlsx'

pos_keywords = [
    'ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
    'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
    'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ', 'ผปด', 'ชผ', 'ผสซ', 'ผคฟ',
    'ผบร', 'ชบช', 'ชชง', 'ชจก', 'นบช'
]

is_name = lambda s: bool(re.match(r'^(นาย|นาง|นางสาว)\s', s))

with zipfile.ZipFile(path, 'r') as z:
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for elem in tree.iter():
            if elem.tag.endswith('t'):
                ss.append(elem.text or '')

    sheet_xml = z.read('xl/worksheets/sheet1.xml')
    tree = ET.fromstring(sheet_xml)
    
    rows_dict = {}
    for row in tree.iter():
        if row.tag.endswith('row'):
            r_num = int(row.attrib.get('r'))
            row_vals = {}
            for c in row:
                r_ref = c.attrib.get('r')
                col_str = ''.join([ch for ch in r_ref if ch.isalpha()])
                v = ''
                t = c.attrib.get('t')
                for child in c:
                    if child.tag.endswith('v'):
                        v = child.text
                        if t == 's' and v.isdigit():
                            idx = int(v)
                            v = ss[idx] if idx < len(ss) else v
                row_vals[col_str] = v.strip()
            rows_dict[r_num] = row_vals

# Process rows 5 to 110
participants = []
for r in range(5, 110):
    curr = rows_dict.get(r, {})
    emp_id = curr.get('C', '')
    seq_str = curr.get('A', '')
    if not emp_id and not seq_str.isdigit():
        continue
    
    # Email is in Row r+1 Col B (or Row 5 Col B if r==5)
    if r == 5:
        email_candidate = curr.get('B', '')
        if '@' not in email_candidate:
            email_candidate = rows_dict.get(r+1, {}).get('B', '')
    else:
        email_candidate = rows_dict.get(r+1, {}).get('B', '')

    # Extract Name candidates
    name_cands = []
    for col in ['D', 'E', 'H', 'I']:
        val = curr.get(col, '')
        if is_name(val):
            name_cands.append(val)
    
    name = name_cands[0] if name_cands else ''

    # Extract Position candidates
    pos = ''
    for col in ['E', 'D', 'H', 'I']:
        val = curr.get(col, '')
        if not val or is_name(val) or val == '/': continue
        for k in pos_keywords:
            if val.startswith(k):
                pos = val.split(' ', 1)[0]
                break
        if pos: break

    # Extract Department candidates
    dept = curr.get('F', '')
    for col in ['H', 'I']:
        val = curr.get(col, '')
        if val and not is_name(val) and any(d in val for d in ['กฟจ', 'กฟส', 'กปบ', 'ฝปบ', 'กดส', 'ผจฟ', 'ฝสบ']):
            for k in pos_keywords:
                if val.startswith(k) and ' ' in val:
                    dept = val.split(' ', 1)[1]
                    break
            else:
                dept = val
            break

    participants.append({
        'row_in_excel': r,
        'seq': str(len(participants) + 1),
        'emp_id': emp_id,
        'name': name,
        'pos': pos,
        'dept': dept,
        'email': email_candidate,
        'raw': curr
    })

with open(r'd:\Kaeha\parsed_participant1_report.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total parsed participants: {len(participants)}\n\n")
    for p in participants:
        out.write(f"Seq {p['seq']:3s} | Row {p['row_in_excel']:3d} | ID:{p['emp_id']:7s} | Name:{p['name']:25s} | Pos:{p['pos']:12s} | Dept:{p['dept']:35s} | Email:{p['email']}\n")

print(f"Parsed {len(participants)} participants to parsed_participant1_report.txt successfully!")
