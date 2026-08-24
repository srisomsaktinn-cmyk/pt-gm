import zipfile
import xml.etree.ElementTree as ET
import re

with zipfile.ZipFile(r'd:\Kaeha\Participant.xlsx', 'r') as z:
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

is_name = lambda s: bool(re.match(r'^(นาย|นาง|นางสาว)\s', s))
pos_keywords = ['ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
                'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
                'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ', 'ผปด']

def extract_pos_dept(curr):
    e = curr.get('E', '')
    f = curr.get('F', '')
    h = curr.get('H', '')
    i = curr.get('I', '')
    
    pos = ''
    dept = f or 'ฝสบ.(ต1) กฟต.1 สายงาน (ต)'

    for c in [e, h, i]:
        if not c or c == '/' or is_name(c): continue
        for k in pos_keywords:
            if c.startswith(k):
                pos = c.split(' ', 1)[0]
                break
        if pos: break
    
    if not pos:
        for c in [e, i]:
            if c and c != '/' and not is_name(c) and len(c) <= 15 and not any(d in c for d in ['กฟต', 'กฟจ', 'กฟส', 'ฝสบ', 'กปบ', 'ฝปบ']):
                pos = c
                break

    for c in [h, i]:
        if c and not is_name(c) and any(d in c for d in ['กฟส', 'กฟจ', 'กปบ', 'ฝปบ', 'กดส', 'ผจฟ']):
            for k in pos_keywords:
                if c.startswith(k) and ' ' in c:
                    dept = c.split(' ', 1)[1]
                    break
            else:
                dept = c

    return pos, dept

participants = []
for r in range(5, 87):
    curr = rows_dict.get(r, {})
    emp_id = curr.get('C', '')
    d = curr.get('D', '')
    e = curr.get('E', '')
    h = curr.get('H', '')
    i = curr.get('I', '')
    
    if not emp_id: continue

    # Determine Name for row r
    if is_name(e):
        name = e
    elif is_name(d):
        name = d
    elif is_name(i):
        name = i
    elif is_name(h):
        name = h
    else:
        name = ''

    pos, dept = extract_pos_dept(curr)

    participants.append({
        'row': r,
        'seq': str(len(participants) + 1),
        'emp_id': emp_id,
        'name': name,
        'pos': pos,
        'dept': dept
    })

with open(r'd:\Kaeha\direct_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total Participants: {len(participants)}\n\n")
    for p in participants:
        f.write(f"R{p['row']:02d} | Seq: {p['seq']:2s} | Emp: {p['emp_id']:8s} | Name: {p['name']:30s} | Pos: {p['pos']:12s} | Dept: {p['dept']}\n")

print("Generated direct_report.txt successfully!")
