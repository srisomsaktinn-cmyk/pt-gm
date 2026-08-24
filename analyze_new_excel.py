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

with open(r'd:\Kaeha\new_excel_analysis.txt', 'w', encoding='utf-8') as out:
    out.write("=== FLAT CELL DUMP FOR ALL ROWS (Participant (1).xlsx) ===\n\n")
    for r in range(5, 111):
        curr = rows_dict.get(r, {})
        if not curr: continue
        seq = curr.get('A', '')
        b = curr.get('B', '')
        c = curr.get('C', '')
        d = curr.get('D', '')
        e = curr.get('E', '')
        f = curr.get('F', '')
        g = curr.get('G', '')
        h = curr.get('H', '')
        i = curr.get('I', '')
        j = curr.get('J', '')
        out.write(f"Row {r:3d} | Seq:{seq:3s} | ColC(ID):{c:7s} | ColD:{d:25s} | ColE:{e:20s} | ColF:{f:25s} | ColH:{h:30s} | ColI:{i:30s} | ColB(Email):{b}\n")

print("Generated new_excel_analysis.txt successfully!")
