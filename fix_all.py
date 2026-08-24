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

def extract_pos_and_dept(cell_e, cell_f, cell_h, cell_i):
    pos = ''
    dept = cell_f
    
    # Check E, H, I for position codes
    for c in [cell_e, cell_h, cell_i]:
        if not c or c == '/' or is_name(c):
            continue
        
        # Check if it starts with position keyword
        for k in pos_keywords:
            if c.startswith(k):
                parts = c.split(' ', 1)
                pos = parts[0]
                if len(parts) > 1 and any(d in parts[1] for d in ['กฟ', 'ฝ่าย', 'กอง', 'ฝสบ', 'กปบ', 'ฝปบ']):
                    dept = parts[1]
                break
        if pos:
            break

    # If position still not found, check short text in E or I
    if not pos:
        for c in [cell_e, cell_i]:
            if c and c != '/' and not is_name(c) and len(c) <= 12 and not any(d in c for d in ['กฟต', 'กฟจ', 'กฟส', 'ฝสบ']):
                pos = c
                break

    # Check for specific department in H or I
    for c in [cell_h, cell_i]:
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

    # Name matching logic
    prev_i = rows_dict.get(r-1, {}).get('I', '').strip()
    cands = [c for c in [d, e, i, prev_i] if is_name(c)]
    
    name = ''
    if email and '@' in email:
        name = max(all_thai_names, key=lambda n: get_phonetic_score(email, n))
    elif cands:
        name = cands[0]

    pos, dept = extract_pos_and_dept(e, f, h, i)

    participants.append({
        'seq': str(len(participants) + 1),
        'emp_id': emp_id,
        'name': name,
        'pos': pos,
        'dept': dept
    })

# Save report to text file
with open(r'd:\Kaeha\report_extracted.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total Participants: {len(participants)}\n\n")
    for p in participants:
        out.write(f"ลำดับ {p['seq']:2s} | รหัส: {p['emp_id']:7s} | ชื่อ-สกุล: {p['name']:30s} | ตำแหน่ง: {p['pos']:10s} | สังกัด: {p['dept']}\n")

print("Report saved to d:\\Kaeha\\report_extracted.txt")
