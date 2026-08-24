import zipfile
import xml.etree.ElementTree as ET
import re

def get_phonetic_score(email, thai_name):
    if not email or not thai_name:
        return -100
    parts = email.split('@')[0].lower().split('.')
    e_first = parts[0] if len(parts) > 0 else ''
    e_last = parts[1] if len(parts) > 1 else ''
    
    clean_t = re.sub(r'^(นาย|นาง|นางสาว)\s*', '', thai_name).strip()
    t_parts = clean_t.split()
    t_first = t_parts[0] if len(t_parts) > 0 else ''
    t_last = t_parts[1] if len(t_parts) > 1 else ''
    
    score = 0
    cons_map = [
        (['b'], ['บ']), (['p', 'ph'], ['ป','พ','ภ','ผ']), (['t', 'th'], ['ท','ธ','ต','ถ']),
        (['c', 'ch'], ['ช','ฉ','จ']), (['s'], ['ส','ศ','ษ']), (['k', 'kh'], ['ก','ข','ค']),
        (['m'], ['ม']), (['n'], ['น','ณ']), (['r'], ['ร']), (['l'], ['ล']),
        (['w'], ['ว']), (['j'], ['จ']), (['d'], ['ด']), (['f'], ['ฟ']), (['h'], ['ห','ฮ']),
        (['y'], ['ญ','ย']), (['g'], ['ก'])
    ]
    
    if e_first and t_first:
        for en_list, th_list in cons_map:
            if any(e_first.startswith(en) for en in en_list) and t_first[0] in th_list:
                score += 20
                break
                
    if e_last and t_last:
        for en_list, th_list in cons_map:
            if any(e_last.startswith(en) for en in en_list) and t_last[0] in th_list:
                score += 20
                break

    return score

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
all_thai_names = set()
for r in rows_dict.values():
    for v in r.values():
        if is_name(v):
            all_thai_names.add(v)

pos_keywords = ['ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
                'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
                'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ', 'ผปด']

def extract_pos(cell_str):
    if not cell_str or cell_str == '/' or is_name(cell_str):
        return ''
    for k in pos_keywords:
        if cell_str.startswith(k):
            parts = cell_str.split(' ', 1)
            return parts[0]
    if len(cell_str) <= 15 and not any(d in cell_str for d in ['กฟต', 'กฟจ', 'กฟส', 'ฝสบ', 'กปบ', 'ฝปบ', 'สายงาน']):
        return cell_str
    return ''

def extract_dept(cell_f, cell_h, cell_i):
    for c in [cell_h, cell_i]:
        if c and not is_name(c) and any(d in c for d in ['กฟส', 'กฟจ', 'กปบ', 'ฝปบ', 'กดส', 'ผจฟ']):
            for k in pos_keywords:
                if c.startswith(k) and ' ' in c:
                    return c.split(' ', 1)[1]
            return c
    return cell_f

records = []
for r in range(5, 87):
    curr = rows_dict.get(r, {})
    seq = curr.get('A', '')
    email = curr.get('B', '')
    emp_id = curr.get('C', '')
    d = curr.get('D', '')
    e = curr.get('E', '')
    f = curr.get('F', '')
    h = curr.get('H', '')
    i = curr.get('I', '')
    
    if not emp_id and not seq:
        continue

    if email and '@' in email:
        name = max(all_thai_names, key=lambda n: get_phonetic_score(email, n))
    else:
        name = d if is_name(d) else (e if is_name(e) else '')

    pos = extract_pos(e) or extract_pos(h) or extract_pos(i)
    dept = extract_dept(f, h, i)

    records.append({
        'row': r,
        'seq': str(len(records) + 1),
        'emp_id': emp_id,
        'name': name,
        'pos': pos,
        'dept': dept
    })

print(f'Extracted {len(records)} participants:')
for p in records:
    print(f"R{p['row']:02d} | Seq:{p['seq']:3s} | Emp: {p['emp_id']:8s} | Name: {p['name']:30s} | Pos: {p['pos']:12s} | Dept: {p['dept']}")
