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

with open(r'd:\Kaeha\all_cells_flat.txt', 'w', encoding='utf-8') as out:
    for r in range(5, 87):
        curr = rows_dict.get(r, {})
        c = curr.get('C', '')
        b = curr.get('B', '')
        d = curr.get('D', '')
        e = curr.get('E', '')
        f = curr.get('F', '')
        h = curr.get('H', '')
        i = curr.get('I', '')
        out.write(f"R{r:02d} | B:{b:25s} | C:{c:7s} | D:{d:25s} | E:{e:20s} | H:{h:30s} | I:{i}\n")

print("Dumped all_cells_flat.txt!")
