import zipfile
import xml.etree.ElementTree as ET
import re
from xml.sax.saxutils import escape

DOCX_IN = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity].docx'
XLSX_IN = r'd:\Kaeha\Participant.xlsx'
DOCX_OUT = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity]_พร้อมรายชื่อ_ครบถ้วนถูกต้อง.docx'

is_name = lambda s: bool(re.match(r'^(นาย|นาง|นางสาว)\s', s))

pos_keywords = [
    'ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
    'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
    'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ', 'ผปด', 'ชผ', 'ผสซ', 'ผคฟ',
    'ผบร', 'ชบช', 'ชชง'
]

def match_email_to_name(email):
    if not email or '@' not in email: return ''
    prefix = email.split('@')[0].lower()
    
    if 'pakorn' in prefix or 'pearl' in email: return 'นาย ปกรณ์ ถาวร'
    elif 'worrapol' in prefix: return 'นาย วรพล พิทักษ์วงษ์โยธิน'
    elif 'santichai' in prefix: return 'นาย สันติชัย เกิดช้าง'
    elif 'suchada' in prefix: return 'นางสาว สุชาดา สุขนิรันดร์'
    elif 'chaiwut' in prefix: return 'นาย ชัยวุฒิ ศรีชะฎา'
    elif 'nongnuch' in prefix: return 'นาง นงนุช ตั้งประเสริฐ'
    elif 'rungrot' in prefix: return 'นาย รุ่งโรจน์ ช่วยอุระชน'
    elif 'prachaya' in prefix: return 'นาย ปรัชญา จีนขาวขำ'
    elif 'suriyun' in prefix: return 'นาย สุริยัณห์ ขาวเกลี้ยง'
    elif 'nisarut' in prefix: return 'นางสาว นิศารัตน์ โชคลาภ'
    elif 'wanlop.san' in prefix: return 'นาย วัลลภ แสงทอง'
    elif 'tawee' in prefix: return 'นาย ทวี เอมโอษฐ์'
    elif 'kantharat' in prefix: return 'นางสาว กรัณฑรัตน์ ภู่ทอง'
    elif 'suriya.boo' in prefix: return 'นาย สุริยา บุญลือ'
    elif 'wullop.sri' in prefix: return 'นาย วัลลภ ศรีวิโรจน์'
    elif 'thanachai' in prefix: return 'นาย ธนชัย รุ่งเรือง'
    elif 'tassanawalai' in prefix: return 'นางสาว ทัศนาวลัย ดังก้อง'
    elif 'wiroj' in prefix: return 'นาย วิโรจน์ เม่งพัด'
    elif 'pathay' in prefix: return 'นาย เพทาย ประเสริฐจิตร์'
    elif 'panuwat' in prefix: return 'นาย ภาณุวัฒน์ อุบลวรรณรัตน์'
    elif 'chanwad' in prefix: return 'นาย ชาญเวส รัตนสิทธิ์'
    elif 'wirat.jun' in prefix: return 'นาย วิรัตน์ จังโสพานิช'
    elif 'thanadeach' in prefix: return 'นาย ธนาเดช คงเจริญ'
    elif 'khwanruan' in prefix: return 'นางสาว ขวัญเรือน ชะเอมสินธิ์'
    elif 'poranis' in prefix: return 'นาย ปรนิส เนาวบุตร'
    elif 'kawitsara' in prefix: return 'นาง กวิสรา เอี่ยมเจริญศักดิ์'
    elif 'sakda' in prefix: return 'นาย ศักดา แก้วสุทัศน์'
    elif 'pranalee' in prefix: return 'นางสาว ประณาลี พันธุ์พำนัก'
    elif 'suphachai' in prefix: return 'นาย พลฐณัฏฐ์ ช่วยมิตร'
    elif 'chana' in prefix: return 'นาย ชนะ วรรณพุก'
    elif 'suriyan.lim' in prefix: return 'นาย สุริยัน ลิมปนิลชาติ'
    elif 'piman' in prefix: return 'นาย พิมาน รัตนมุง'
    elif 'puwanai' in prefix: return 'นาย ภูวนัย บุญมีผล'
    elif 'intarat' in prefix: return 'นาย อินทรัตน์ เนียเติม'
    elif 'nattasak' in prefix: return 'นาย ณัฏฐศักดิ์ เพริดพริ้ง'
    elif 'pininun' in prefix: return 'นาย พินิจนันท์ ญาตินุกูล'
    elif 'panya' in prefix: return 'นาย ปัญญา มาดี'
    elif 'sangnapa' in prefix: return 'นางสาว แสงนภา ผลไพบูลย์'
    elif 'warunee' in prefix: return 'นาง วารุณี รังศิโรภาส'
    elif 'chamni' in prefix: return 'นาย ชำนิ ยนต์พิทักษ์กิจ'
    elif 'danusorn' in prefix: return 'นาย ดนุสรณ์ สุขสุสินธุ์'
    elif 'watcharapong' in prefix: return 'นาย วัชรพงษ์ เวสสุวรรณ'
    elif 'wisanu' in prefix: return 'นาย วิษณุ ณ บางช้าง'
    elif 'pongthon' in prefix: return 'นาย พงศ์ธร ศิริโต'
    elif 'treesit' in prefix: return 'นาย ตรีสิทธิ์ อัฑฒพงษ์'
    elif 'natee' in prefix: return 'นาย นที แสงทอง'
    elif 'teerasak' in prefix: return 'นาย ธีรศักดิ์ สระศรี'
    elif 'ruckchart' in prefix: return 'นาย รักษ์ชาติ ประสานสกุล'
    elif 'kitisak' in prefix: return 'นาย กิติศักดิ์ เอิบอิ่ม'
    elif 'sompong' in prefix: return 'นาย สมพงษ์ จันทร์ชูกลิ่น'
    elif 'danupon' in prefix: return 'นาย ดนุพล จังธนสมบัติ'
    elif 'wachira' in prefix: return 'นาย วชิระ สีแดง'
    elif 'naris' in prefix: return 'นาย นริศ นวลมา'
    elif 'panitan' in prefix: return 'นาย ปณิธาน พึ่งธรรม'
    elif 'atchara' in prefix: return 'นางสาว อัจฉรา สงฉิม'
    elif 'sudarat' in prefix: return 'นางสาว สุดารัตน์ ทองน้อย'
    elif 'nawaporn' in prefix: return 'นางสาว นวพร ภู่สมบูรณ์'
    elif 'suwirat' in prefix: return 'นาย สุวิรัตน์ แสนสุข'
    elif 'treerapat' in prefix: return 'นาย ธีรภัทร ทองมาก'
    elif 'sasiwimon' in prefix: return 'นางสาว ศศิวิมล โชติมณีวัฒนา'
    elif 'nitad' in prefix: return 'นาย นิทัศน์ ปานณรงค์'
    elif 'patinya' in prefix: return 'นาย ปฏิณญา ชุณหมุกดา'
    elif 'suriya.iam' in prefix: return 'นาย สุริยา เอี่ยมอินทร์'
    elif 'ronnayut' in prefix: return 'นาย รณยุทธ อินทรสมบัติ'
    elif 'chanwit' in prefix: return 'นาย ชาญวิทย์ สกุลปักษ์'
    elif 'sarawut' in prefix: return 'นาย สราวุธ ช่วยมิตร'
    elif 'nattawat' in prefix: return 'นาย ณัฐวัฒน์ วรรณชัย'
    elif 'thaweechok' in prefix: return 'นาย ทวีโชค เปี่ยมอุดมลักษณ์'
    elif 'pitsanu' in prefix: return 'นาย พิษณุ แช่มช้อย'
    elif 'ruengsirl' in prefix: return 'นางสาว เรืองศิริ ทองชาติ'
    elif 'tinn' in prefix: return 'นาย ติณณ์ ศรีสมศักดิ์'
    elif 'watcharapon' in prefix: return 'นาย วัชรพล พิทยาพันธ์'
    elif 'tanawat' in prefix: return 'นาย ธนวัต อารีย์วงศ์'
    elif 'apiwat' in prefix: return 'นาย อภิวัฒน์ คนยืนยง'
    elif 'warat' in prefix: return 'นาย วรัษฐ์ กรเปรมสุขพงศ์'
    elif 'kritchet' in prefix: return 'นาย กฤษฎิ์เชษฐ์ รวยทรัพย์รชตะ'
    elif 'grissana' in prefix: return 'นาย กฤษณะ สมมารถ'
    elif 'thong.mun' in prefix: return 'นาย ทอง มั่นคง'
    elif 'wirat.suk' in prefix: return 'นาย วิรัตน์ สุขโต'
    elif 'boonsoom' in prefix: return 'นาย บุญสม นวนพลอย'
    elif 'sujittra' in prefix: return 'นางสาว สุจิตตรา พุ่มไสว'
    return ''

def get_participants(path):
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

    name_to_pos_map = {}
    for r_num, rd in rows_dict.items():
        for col in ['D', 'E', 'H', 'I']:
            val = rd.get(col, '')
            if is_name(val):
                for p_col in ['E', 'H', 'I']:
                    p_val = rd.get(p_col, '')
                    if p_val and not is_name(p_val) and p_val != '/':
                        for k in pos_keywords:
                            if p_val.startswith(k):
                                code = p_val.split(' ', 1)[0]
                                name_to_pos_map[val] = code

    def extract_pos_smart(r, name):
        for r_offset in [0, 1, -1, 2, -2]:
            rd = rows_dict.get(r + r_offset, {})
            for col in ['E', 'H', 'I']:
                val = rd.get(col, '')
                if not val or val == '/' or is_name(val): continue
                for k in pos_keywords:
                    if val.startswith(k):
                        return val.split(' ', 1)[0]
                    elif f" {k}" in val:
                        parts = val.split()
                        for p in parts:
                            if any(p.startswith(kw) for kw in pos_keywords):
                                return p

        if name in name_to_pos_map:
            return name_to_pos_map[name]

        return ''

    def extract_dept(curr):
        f = curr.get('F', '')
        h = curr.get('H', '')
        i = curr.get('I', '')
        for c in [h, i]:
            if c and not is_name(c) and any(d in c for d in ['กฟส', 'กฟจ', 'กปบ', 'ฝปบ', 'กดส', 'ผจฟ']):
                for k in pos_keywords:
                    if c.startswith(k) and ' ' in c:
                        return c.split(' ', 1)[1]
                return c
        return f or 'ฝสบ.(ต1) กฟต.1 สายงาน (ต)'

    participants = []
    for r in range(5, 87):
        curr = rows_dict.get(r, {})
        emp_id = curr.get('C', '')
        seq = curr.get('A', '')
        if not emp_id and not seq: continue
        
        real_email = curr.get('B', '') if r == 5 else rows_dict.get(r+1, {}).get('B', '')
        name = match_email_to_name(real_email)
        
        if not name:
            prev_i = rows_dict.get(r-1, {}).get('I', '')
            cands = [c for c in [curr.get('E',''), curr.get('D',''), curr.get('I',''), prev_i] if is_name(c)]
            name = cands[0] if cands else ''

        pos = extract_pos_smart(r, name)
        dept = extract_dept(curr)

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
    participants = get_participants(XLSX_IN)
    print(f"Total participants: {len(participants)}")

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
