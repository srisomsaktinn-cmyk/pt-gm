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

pos_keywords = ['ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
                'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
                'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ', 'ผปด', 'ชผ', 'นรค']

is_name = lambda s: bool(re.match(r'^(นาย|นาง|นางสาว)\s', s))

with open(r'd:\Kaeha\pos_analysis.txt', 'w', encoding='utf-8') as out:
    for r in range(5, 87):
        curr = rows_dict.get(r, {})
        emp_id = curr.get('C', '')
        if not emp_id: continue
        
        # Check current, prev, next rows for any position keyword
        found_pos = []
        for offset in [0, 1, -1, 2, -2]:
            rd = rows_dict.get(r + offset, {})
            for col in ['E', 'H', 'I', 'F', 'D']:
                val = rd.get(col, '')
                if not val or val == '/' or is_name(val): continue
                for k in pos_keywords:
                    if k in val:
                        pos_code = val.split()[0] if ' ' in val else val
                        found_pos.append(f"Row{r+offset} Col{col}: '{val}' -> [{pos_code}]")
                        break

        out.write(f"Seq {r-4:2d} | Row {r:02d} | Emp: {emp_id:7s} | Matches:\n")
        if found_pos:
            for fp in found_pos:
                out.write(f"   - {fp}\n")
        else:
            out.write("   - NONE FOUND NEARBY\n")

print("Analysis written to pos_analysis.txt!")
