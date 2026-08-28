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

print('=== ALIGNMENT ANALYSIS ===')
# Let's inspect rows 5 to 35
for r in range(5, 36):
    r_curr = rows_dict.get(r, {})
    r_next = rows_dict.get(r+1, {})
    
    emp_curr = r_curr.get('C', '')
    emp_next = r_next.get('C', '')
    
    email_curr = r_curr.get('B', '')
    email_next = r_next.get('B', '')
    
    d_curr = r_curr.get('D', '')
    e_curr = r_curr.get('E', '')
    h_curr = r_curr.get('H', '')
    i_curr = r_curr.get('I', '')

    d_next = r_next.get('D', '')
    e_next = r_next.get('E', '')

    print(f"R{r:02d} | Curr Emp:{emp_curr:7s} | Next Emp:{emp_next:7s} | Next Email:{email_next:25s} | D_curr:{d_curr:25s} | E_curr:{e_curr}")
