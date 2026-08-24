import zipfile
import xml.etree.ElementTree as ET

with zipfile.ZipFile(r'd:\Kaeha\Participant.xlsx', 'r') as z:
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
        for elem in tree.iter():
            if elem.tag.endswith('t'):
                ss.append(elem.text or '')

    sheet_xml = z.read('xl/worksheets/sheet1.xml')
    tree = ET.fromstring(sheet_xml)
    
    rows = []
    for r in tree.iter():
        if r.tag.endswith('row'):
            r_num = int(r.attrib.get('r'))
            row_dict = {}
            for c in r:
                r_ref = c.attrib.get('r')
                col_letter = ''.join([ch for ch in r_ref if ch.isalpha()])
                v = ''
                t = c.attrib.get('t')
                for child in c:
                    if child.tag.endswith('v'):
                        v = child.text
                        if t == 's' and v.isdigit():
                            idx = int(v)
                            v = ss[idx] if idx < len(ss) else v
                row_dict[col_letter] = v.strip()
            rows.append((r_num, row_dict))

print('=== RAW EXCEL COLUMNS (ROWS 4 to 35) ===')
for r_num, rd in rows:
    if 4 <= r_num <= 35:
        a = rd.get('A', '')
        b = rd.get('B', '')
        c = rd.get('C', '')
        d = rd.get('D', '')
        e = rd.get('E', '')
        f = rd.get('F', '')
        g = rd.get('G', '')
        h = rd.get('H', '')
        i = rd.get('I', '')
        j = rd.get('J', '')
        print(f"R{r_num:02d} | A:{a:3s} | B:{b:22s} | C:{c:8s} | D:{d:25s} | E:{e:25s} | F:{f:25s} | H:{h:25s} | I:{i}")
