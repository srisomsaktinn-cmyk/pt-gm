import sys, zipfile, xml.etree.ElementTree as ET

path = r'd:\Kaeha\Participant (1).xlsx'

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

with open(r'd:\Kaeha\new_excel_dump.txt', 'w', encoding='utf-8') as out:
    out.write(f"Total rows: {len(rows_dict)}\n")
    for r_num in sorted(rows_dict.keys()):
        out.write(f"Row {r_num:3d}: {rows_dict[r_num]}\n")

print(f"Dumped {len(rows_dict)} rows to new_excel_dump.txt successfully!")
