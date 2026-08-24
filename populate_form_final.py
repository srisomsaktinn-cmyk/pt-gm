import zipfile
import xml.etree.ElementTree as ET
import re
import copy

DOCX_PATH = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity].docx'
XLSX_PATH = r'd:\Kaeha\Participant.xlsx'
OUTPUT_PATH = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity]_พร้อมรายชื่อ_ถูกต้อง.docx'

def match_email_to_name(email):
    if not email or '@' not in email:
        return ''
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

def parse_xlsx(path):
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

    is_name = lambda s: bool(re.match(r'^(นาย|นาง|นางสาว)\s', s))
    pos_keywords = ['ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
                    'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
                    'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ', 'ผปด']

    def extract_pos_dept(curr):
        e = curr.get('E', '')
        f = curr.get('F', '')
        h = curr.get('H', '')
        i = curr.get('I', '')
        
        pos = ''
        dept = f or 'ฝสบ.(ต1) กฟต.1 สายงาน (ต)'

        for c in [e, h, i]:
            if not c or c == '/' or is_name(c): continue
            for k in pos_keywords:
                if c.startswith(k):
                    pos = c.split(' ', 1)[0]
                    break
            if pos: break
        
        if not pos:
            for c in [e, i]:
                if c and c != '/' and not is_name(c) and len(c) <= 15 and not any(d in c for d in ['กฟต', 'กฟจ', 'กฟส', 'ฝสบ', 'กปบ', 'ฝปบ']):
                    pos = c
                    break

        for c in [h, i]:
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
        emp_id = curr.get('C', '')
        d = curr.get('D', '')
        e = curr.get('E', '')
        h = curr.get('H', '')
        i = curr.get('I', '')
        
        if not emp_id and not seq: continue

        # Email for row r is in B_{r+1} (due to 1-row export shift starting row 6)
        if r == 5:
            real_email = curr.get('B', '')
        else:
            real_email = rows_dict.get(r+1, {}).get('B', '')

        name = match_email_to_name(real_email)
        
        # Fallback if email lookup fails
        if not name:
            prev_i = rows_dict.get(r-1, {}).get('I', '')
            cands = [c for c in [e, d, i, prev_i] if is_name(c)]
            name = cands[0] if cands else ''

        pos, dept = extract_pos_dept(curr)

        participants.append({
            'seq': str(len(participants) + 1),
            'emp_id': emp_id,
            'name': name,
            'pos': pos,
            'dept': dept
        })

    return participants

def update_docx(docx_in, docx_out, participants):
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    ET.register_namespace('w', ns['w'])
    
    with zipfile.ZipFile(docx_in, 'r') as zin:
        xml_content = zin.read('word/document.xml')
        tree = ET.fromstring(xml_content)
        
        tbl = tree.find('.//w:tbl', ns)
        if tbl is None:
            raise ValueError('Table not found in Word document!')

        rows = tbl.findall('w:tr', ns)
        sample_row = rows[1]

        # Clear existing template rows
        for r in rows[1:]:
            tbl.remove(r)

        def set_cell_text(tc, text):
            p = tc.find('w:p', ns)
            if p is None:
                p = ET.SubElement(tc, f"{{{ns['w']}}}p")
            
            for child in list(p):
                if child.tag.endswith('r'):
                    p.remove(child)
            
            r_elem = ET.SubElement(p, f"{{{ns['w']}}}r")
            
            rPr = ET.SubElement(r_elem, f"{{{ns['w']}}}rPr")
            rFonts = ET.SubElement(rPr, f"{{{ns['w']}}}rFonts")
            rFonts.set(f"{{{ns['w']}}}ascii", "TH Sarabun PSK")
            rFonts.set(f"{{{ns['w']}}}hAnsi", "TH Sarabun PSK")
            rFonts.set(f"{{{ns['w']}}}cs", "TH Sarabun PSK")
            
            sz = ET.SubElement(rPr, f"{{{ns['w']}}}sz")
            sz.set(f"{{{ns['w']}}}val", "32") # 16 pt
            szCs = ET.SubElement(rPr, f"{{{ns['w']}}}szCs")
            szCs.set(f"{{{ns['w']}}}val", "32")

            t_elem = ET.SubElement(r_elem, f"{{{ns['w']}}}t")
            t_elem.text = text

        for p_data in participants:
            new_tr = copy.deepcopy(sample_row)
            tcs = new_tr.findall('w:tc', ns)
            
            if len(tcs) >= 6:
                set_cell_text(tcs[0], p_data['seq'])
                set_cell_text(tcs[1], p_data['emp_id'])
                set_cell_text(tcs[2], p_data['name'])
                set_cell_text(tcs[3], p_data['pos'])
                set_cell_text(tcs[4], p_data['dept'])
                set_cell_text(tcs[5], '')
            
            tbl.append(new_tr)

        updated_xml = ET.tostring(tree, encoding='utf-8', xml_declaration=True)

    with zipfile.ZipFile(docx_in, 'r') as zin:
        with zipfile.ZipFile(docx_out, 'w', zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                if item.filename == 'word/document.xml':
                    zout.writestr(item.filename, updated_xml)
                else:
                    zout.writestr(item.filename, zin.read(item.filename))

    print(f'Successfully updated Word document: {docx_out}')

if __name__ == '__main__':
    participants = parse_xlsx(XLSX_PATH)
    print(f'Total participants processed: {len(participants)}')
    update_docx(DOCX_PATH, OUTPUT_PATH, participants)
