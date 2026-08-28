import zipfile
import re
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape

XLSX_IN = r'd:\Kaeha\Participant (1).xlsx'
DOCX_IN = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity].docx'
DOCX_OUT = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity]_การประชุมครั้งใหม่_105คน.docx'

pos_keywords = [
    'ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
    'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
    'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ', 'ผปด', 'ชผ', 'ผสซ', 'ผคฟ',
    'ผบร', 'ชบช', 'ชชง', 'ชจก', 'นบช', 'นรค', 'พบค'
]

is_name = lambda s: bool(re.match(r'^(นาย|นาง|นางสาว)\s', s))

def get_participants():
    with zipfile.ZipFile(XLSX_IN, 'r') as z:
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

    email_to_name_map = {}
    for r_num, rd in rows_dict.items():
        if r_num < 5: continue
        email = rows_dict.get(r_num+1, {}).get('B', '') if r_num > 5 else rd.get('B', '')
        if '@' not in email:
            email = rd.get('B', '')
        
        names = [rd.get(c, '') for c in ['D', 'E', 'H', 'I'] if is_name(rd.get(c, ''))]
        if email and names:
            email_to_name_map[email.lower().strip()] = names[-1]

    participants = []
    for r in range(5, 110):
        curr = rows_dict.get(r, {})
        emp_id = curr.get('C', '')
        seq_str = curr.get('A', '')
        if not emp_id and not seq_str.isdigit():
            continue
        
        email = rows_dict.get(r+1, {}).get('B', '') if r > 5 else curr.get('B', '')
        if '@' not in email:
            email = curr.get('B', '')
        
        name = email_to_name_map.get(email.lower().strip(), '')
        if not name:
            names = [curr.get(c, '') for c in ['E', 'H', 'I', 'D'] if is_name(curr.get(c, ''))]
            name = names[0] if names else curr.get('D', '')

        pos = ''
        for col in ['E', 'H', 'I']:
            val = curr.get(col, '')
            if not val or is_name(val) or val == '/': continue
            for k in pos_keywords:
                if val.startswith(k):
                    pos = val.split(' ', 1)[0]
                    break
                elif f" {k}" in val:
                    parts = val.split()
                    for p_str in parts:
                        if any(p_str.startswith(kw) for kw in pos_keywords):
                            pos = p_str
                            break
            if pos: break

        dept = curr.get('F', '')
        for col in ['H', 'I']:
            val = curr.get(col, '')
            if val and not is_name(val) and any(d in val for d in ['กฟจ', 'กฟส', 'กปบ', 'ฝปบ', 'กดส', 'ผจฟ', 'ฝสบ']):
                for k in pos_keywords:
                    if val.startswith(k) and ' ' in val:
                        dept = val.split(' ', 1)[1]
                        break
                else:
                    dept = val
                break

        participants.append({
            'seq': str(len(participants) + 1),
            'emp_id': emp_id,
            'name': name,
            'pos': pos,
            'dept': dept
        })

    return participants

def make_row_xml(p):
    seq_esc = escape(p['seq'])
    emp_esc = escape(p['emp_id'])
    name_esc = escape(p['name'])
    pos_esc = escape(p['pos'])
    dept_esc = escape(p['dept'])

    row_xml = f'''<w:tr w:rsidR="00EA097E" w14:paraId="37666615" w14:textId="658E1503" w:rsidTr="00994662">
<w:tc><w:tcPr><w:tcW w:w="450" w:type="dxa"/></w:tcPr><w:p w14:paraId="1A9BF9AA" w14:textId="2BE69DAB" w:rsidR="00EA097E" w:rsidRDefault="00EA097E" w:rsidP="00554FC6"><w:pPr><w:spacing w:after="120"/><w:jc w:val="center"/><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK" w:hint="cs"/><w:sz w:val="32"/><w:szCs w:val="32"/><w:cs/></w:rPr><w:t>{seq_esc}</w:t></w:r></w:p></w:tc>
<w:tc><w:tcPr><w:tcW w:w="1813" w:type="dxa"/></w:tcPr><w:p w14:paraId="5F9D1CFA" w14:textId="77777777" w:rsidR="00EA097E" w:rsidRDefault="00EA097E" w:rsidP="00554FC6"><w:pPr><w:spacing w:after="120"/><w:jc w:val="center"/><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK"/><w:sz w:val="32"/><w:szCs w:val="32"/><w:cs/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK" w:hint="cs"/><w:sz w:val="32"/><w:szCs w:val="32"/><w:cs/></w:rPr><w:t>{emp_esc}</w:t></w:r></w:p></w:tc>
<w:tc><w:tcPr><w:tcW w:w="2410" w:type="dxa"/></w:tcPr><w:p w14:paraId="77468069" w14:textId="101FAEF9" w:rsidR="00EA097E" w:rsidRDefault="00EA097E" w:rsidP="00554FC6"><w:pPr><w:spacing w:after="120"/><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK" w:hint="cs"/><w:sz w:val="32"/><w:szCs w:val="32"/><w:cs/></w:rPr><w:t xml:space="preserve">{name_esc}</w:t></w:r></w:p></w:tc>
<w:tc><w:tcPr><w:tcW w:w="1559" w:type="dxa"/></w:tcPr><w:p w14:paraId="66B93C1F" w14:textId="77777777" w:rsidR="00EA097E" w:rsidRDefault="00EA097E" w:rsidP="00554FC6"><w:pPr><w:spacing w:after="120"/><w:jc w:val="center"/><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK" w:hint="cs"/><w:sz w:val="32"/><w:szCs w:val="32"/><w:cs/></w:rPr><w:t xml:space="preserve">{pos_esc}</w:t></w:r></w:p></w:tc>
<w:tc><w:tcPr><w:tcW w:w="1418" w:type="dxa"/></w:tcPr><w:p w14:paraId="6B445464" w14:textId="77777777" w:rsidR="00EA097E" w:rsidRDefault="00EA097E" w:rsidP="00554FC6"><w:pPr><w:spacing w:after="120"/><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:pPr><w:r><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK" w:hint="cs"/><w:sz w:val="32"/><w:szCs w:val="32"/><w:cs/></w:rPr><w:t xml:space="preserve">{dept_esc}</w:t></w:r></w:p></w:tc>
<w:tc><w:tcPr><w:tcW w:w="1417" w:type="dxa"/></w:tcPr><w:p w14:paraId="16C8F427" w14:textId="77777777" w:rsidR="00EA097E" w:rsidRDefault="00EA097E" w:rsidP="00554FC6"><w:pPr><w:spacing w:after="120"/><w:jc w:val="center"/><w:rPr><w:rFonts w:ascii="TH SarabunPSK" w:hAnsi="TH SarabunPSK" w:cs="TH SarabunPSK"/><w:sz w:val="32"/><w:szCs w:val="32"/></w:rPr></w:pPr></w:p></w:tc>
</w:tr>'''
    return row_xml

def process():
    participants = get_participants()
    print(f"Total participants for new meeting: {len(participants)}")

    with zipfile.ZipFile(DOCX_IN, 'r') as zin:
        raw_xml = zin.read('word/document.xml').decode('utf-8')

    tbl_start = raw_xml.find('<w:tbl>')
    tbl_end = raw_xml.find('</w:tbl>') + len('</w:tbl>')

    header_tr_end = raw_xml.find('</w:tr>', tbl_start) + len('</w:tr>')
    tbl_head = raw_xml[tbl_start:header_tr_end]

    rows_xml = [tbl_head]
    for p in participants:
        rows_xml.append(make_row_xml(p))

    rows_xml.append('</w:tbl>')

    new_tbl_xml = '\n'.join(rows_xml)
    new_doc_xml = raw_xml[:tbl_start] + new_tbl_xml + raw_xml[tbl_end:]

    with zipfile.ZipFile(DOCX_IN, 'r') as zin:
        with zipfile.ZipFile(DOCX_OUT, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == 'word/document.xml':
                    zout.writestr(item.filename, new_doc_xml.encode('utf-8'))
                else:
                    zout.writestr(item.filename, zin.read(item.filename))

    print(f"Successfully generated docx: {DOCX_OUT}")

if __name__ == '__main__':
    process()
