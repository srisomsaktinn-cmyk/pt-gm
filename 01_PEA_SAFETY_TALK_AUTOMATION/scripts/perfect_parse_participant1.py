import sys, zipfile, xml.etree.ElementTree as ET, re

path = r'd:\Kaeha\Participant (1).xlsx'

pos_keywords = [
    'ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
    'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
    'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ', 'ผปด', 'ชผ', 'ผสซ', 'ผคฟ',
    'ผบร', 'ชบช', 'ชชง', 'ชจก', 'นบช', 'นรค', 'พบค'
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

# Build name lookup from all cells
email_to_name_map = {}
for r_num, rd in rows_dict.items():
    if r_num < 5: continue
    email = rows_dict.get(r_num+1, {}).get('B', '') if r_num > 5 else rd.get('B', '')
    if '@' not in email:
        email = rd.get('B', '')
    
    names = [rd.get(c, '') for c in ['D', 'E', 'H', 'I'] if is_name(rd.get(c, ''))]
    if email and names:
        # Save last name found in row for this email
        email_to_name_map[email.lower().strip()] = names[-1]

print(f"Total unique email-to-name mappings found: {len(email_to_name_map)}")

participants = []
for r in range(5, 110):
    curr = rows_dict.get(r, {})
    emp_id = curr.get('C', '')
    seq_str = curr.get('A', '')
    if not emp_id and not seq_str.isdigit():
        continue
    
    email = rows_dict.get(r+1, {}).get('B', '') if r > 5 else curr.get('B', '')
    if '@' not in email:
        email = curr.get('B', '')
    
    name = email_to_name_map.get(email.lower().strip(), '')
    if not name:
        names = [curr.get(c, '') for c in ['E', 'H', 'I', 'D'] if is_name(curr.get(c, ''))]
        name = names[0] if names else curr.get('D', '')

    pos = ''
    for col in ['E', 'H', 'I']:
        val = curr.get(col, '')
        if not val or is_name(val) or val == '/': continue
        for k in pos_keywords:
            if val.startswith(k):
                pos = val.split(' ', 1)[0]
                break
            elif f" {k}" in val:
                parts = val.split()
                for p_str in parts:
                    if any(p_str.startswith(kw) for kw in pos_keywords):
                        pos = p_str
                        break
        if pos: break

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
        'seq': str(len(participants) + 1),
        'emp_id': emp_id,
        'name': name,
        'pos': pos,
        'dept': dept
    })

with open(r'd:\Kaeha\parsed_participant1_final.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total parsed participants from Participant (1).xlsx: {len(participants)}\n\n")
    for p in participants:
        out.write(f"Seq {p['seq']:3s} | ID:{p['emp_id']:7s} | Name:{p['name']:25s} | Pos:{p['pos']:12s} | Dept:{p['dept']}\n")

print(f"Successfully processed {len(participants)} participants!")
