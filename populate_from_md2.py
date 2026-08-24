import zipfile
import re
from xml.sax.saxutils import escape

MD_PATH = r'd:\Kaeha\tableConvert.com_3x9z2h.md'
DOCX_IN = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity].docx'
DOCX_OUT = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity]_พร้อมรายชื่อ_3x9z2h.docx'

def parse_md(path):
    participants = []
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line_str = line.strip()
        if not line_str.startswith('|'):
            continue
        parts = [p.strip() for p in line_str.split('|')[1:-1]]
        if len(parts) >= 5:
            seq = parts[0]
            emp_id = parts[1]
            name = parts[2]
            pos = parts[3]
            dept = parts[4]
            
            if seq.isdigit():
                participants.append({
                    'seq': seq,
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
    participants = parse_md(MD_PATH)
    print(f"Parsed {len(participants)} participants directly from tableConvert.com_3x9z2h.md!")

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
