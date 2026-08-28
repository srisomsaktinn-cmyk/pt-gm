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

# Position prefixes common in PEA
pos_prefixes = ('ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
                'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
                'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ')

def separate_pos_dept(text, default_dept):
    text = text.strip()
    if not text or text == '/':
        return '', default_dept
    
    # Check if text is pure position like 'รฝ.', 'ผจก.กฟส.11.ฉ', 'พชง.7'
    # If text contains department keywords like 'กฟต', 'กฟจ', 'กฟส', 'ฝสบ', 'กปบ', 'ฝปบ'
    if any(k in text for k in ['กฟต', 'กฟจ', 'กฟส', 'ฝสบ', 'กปบ', 'ฝปบ', 'กดส']):
        # If it starts with a position code like 'ผบง. กฟส.บลด. กฟจ.พบ. กฟต.1 สายงาน (ต)'
        for pref in pos_prefixes:
            if text.startswith(pref):
                # Split at first space if available
                parts = text.split(' ', 1)
                pos = parts[0]
                dept = parts[1] if len(parts) > 1 else default_dept
                return pos, dept
        # Otherwise it's a department name
        return '', text
    else:
        # It's a position name
        return text, default_dept

parsed = []
for r in range(5, 87):
    curr = rows_dict.get(r, {})
    seq = curr.get('A', '')
    emp_id = curr.get('C', '')
    d = curr.get('D', '')
    e = curr.get('E', '')
    f = curr.get('F', '')
    h = curr.get('H', '')
    i = curr.get('I', '')
    
    if not emp_id and not seq:
        continue

    default_dept = f or 'ฝสบ.(ต1) กฟต.1 สายงาน (ต)'
    
    # 1. Determine Name
    if is_name(e):
        name = e
        # Position & Dept are in H or I
        pos1, dept1 = separate_pos_dept(h, default_dept)
        pos2, dept2 = separate_pos_dept(i, default_dept)
        pos = pos1 or pos2
        dept = dept1 if dept1 != default_dept else (dept2 if dept2 != default_dept else default_dept)
    else:
        name = d
        pos1, dept1 = separate_pos_dept(e, default_dept)
        pos2, dept2 = separate_pos_dept(h, default_dept)
        pos = pos1 or pos2
        dept = dept1 if dept1 != default_dept else (dept2 if dept2 != default_dept else default_dept)

    parsed.append({
        'row': r,
        'emp_id': emp_id,
        'name': name,
        'pos': pos,
        'dept': dept
    })

print(f'Total parsed: {len(parsed)}')
for p in parsed:
    print(f"R{p['row']:02d} | Emp: {p['emp_id']:8s} | Name: {p['name']:30s} | Pos: {p['pos']:15s} | Dept: {p['dept']}")
