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

is_name = lambda s: bool(re.match(r'^(นาย|นาง|นางสาว)\s', s))

# Extract all names and map them to their email or surrounding row
pos_keywords = ['ผจก', 'รจก', 'หผ', 'รก', 'รฝ', 'พชง', 'นทน', 'วศก', 'ชชง', 'ชบช', 
                'ผบง', 'ผบค', 'ผปบ', 'ผปร', 'ผกส', 'หป', 'ผจฟ', 'จป', 'นรค', 'พคค',
                'พบช', 'นบท', 'ผมต', 'วศ', 'ชช', 'หจ', 'ผปด']

def match_name_for_row(r):
    curr = rows_dict.get(r, {})
    email = curr.get('B', '').lower()
    prefix = email.split('@')[0] if '@' in email else ''
    
    # Check current row, prev row, next row
    candidates = []
    for r_offset in [0, -1, 1, -2, 2]:
        rd = rows_dict.get(r + r_offset, {})
        for col in ['D', 'E', 'H', 'I']:
            val = rd.get(col, '')
            if is_name(val) and val not in candidates:
                candidates.append(val)

    if not candidates:
        return ''

    # Transliteration match logic
    if 'pakorn' in prefix or 'pearl' in email:
        return 'นาย ปกรณ์ ถาวร'
    elif 'worrapol' in prefix:
        return 'นาย วรพล พิทักษ์วงษ์โยธิน'
    elif 'santichai' in prefix:
        return 'นาย สันติชัย เกิดช้าง'
    elif 'suchada' in prefix:
        return 'นางสาว สุชาดา สุขนิรันดร์'
    elif 'chaiwut' in prefix:
        return 'นาย ชัยวุฒิ ศรีชะฎา'
    elif 'nongnuch' in prefix:
        return 'นาง นงนุช ตั้งประเสริฐ'
    elif 'rungrot' in prefix:
        return 'นาย รุ่งโรจน์ ช่วยอุระชน'
    elif 'prachaya' in prefix:
        return 'นาย ปรัชญา จีนขาวขำ'
    elif 'suriyun' in prefix:
        return 'นาย สุริยัณห์ ขาวเกลี้ยง'
    elif 'nisarut' in prefix:
        return 'นางสาว นิศารัตน์ โชคลาภ'
    elif 'wanlop.san' in prefix:
        return 'นาย วัลลภ แสงทอง'
    elif 'tawee' in prefix:
        return 'นาย ทวี เอมโอษฐ์'
    elif 'kantharat' in prefix:
        return 'นางสาว กรัณฑรัตน์ ภู่ทอง'
    elif 'suriya.boo' in prefix:
        return 'นาย สุริยา บุญลือ'
    elif 'wullop.sri' in prefix:
        return 'นาย วัลลภ ศรีวิโรจน์'
    elif 'thanachai' in prefix:
        return 'นาย ธนชัย รุ่งเรือง'
    elif 'tassanawalai' in prefix:
        return 'นางสาว ทัศนาวลัย ดังก้อง'
    elif 'wiroj' in prefix:
        return 'นาย วิโรจน์ เม่งพัด'
    elif 'pathay' in prefix:
        return 'นาย เพทาย ประเสริฐจิตร์'
    elif 'panuwat' in prefix:
        return 'นาย ภาณุวัฒน์ อุบลวรรณรัตน์'
    elif 'chanwad' in prefix:
        return 'นาย ชาญเวส รัตนสิทธิ์'
    elif 'wirat.jun' in prefix:
        return 'นาย วิรัตน์ จังโสพานิช'
    elif 'thanadeach' in prefix:
        return 'นาย ธนาเดช คงเจริญ'
    elif 'khwanruan' in prefix:
        return 'นางสาว ขวัญเรือน ชะเอมสินธิ์'
    elif 'poranis' in prefix:
        return 'นาย ปรนิส เนาวบุตร'
    elif 'kawitsara' in prefix:
        return 'นาง กวิสรา เอี่ยมเจริญศักดิ์'
    elif 'sakda' in prefix:
        return 'นาย ศักดา แก้วสุทัศน์'
    elif 'pranalee' in prefix:
        return 'นางสาว ประณาลี พันธุ์พำนัก'
    elif 'suphachai' in prefix:
        return 'นาย พลฐณัฏฐ์ ช่วยมิตร' # or สุภชัย
    elif 'chana' in prefix:
        return 'นาย ชนะ วรรณพุก'
    elif 'suriyan.lim' in prefix:
        return 'นาย สุริยัน ลิมปนิลชาติ'
    elif 'piman' in prefix:
        return 'นาย พิมาน รัตนมุง'
    elif 'puwanai' in prefix:
        return 'นาย ภูวนัย บุญมีผล'
    elif 'intarat' in prefix:
        return 'นาย อินทรัตน์ เนียเติม'
    elif 'nattasak' in prefix:
        return 'นาย ณัฏฐศักดิ์ เพริดพริ้ง'
    elif 'pininun' in prefix:
        return 'นาย พินิจนันท์ ญาตินุกูล'
    elif 'panya' in prefix:
        return 'นาย ปัญญา มาดี'
    elif 'sangnapa' in prefix:
        return 'นางสาว แสงนภา ผลไพบูลย์'
    elif 'warunee' in prefix:
        return 'นาง วารุณี รังศิโรภาส'
    elif 'chamni' in prefix:
        return 'นาย ชำนิ ยนต์พิทักษ์กิจ'
    elif 'danusorn' in prefix:
        return 'นาย ดนุสรณ์ สุขสุสินธุ์'
    elif 'watcharapong' in prefix:
        return 'นาย วัชรพงษ์ เวสสุวรรณ'
    elif 'wisanu' in prefix:
        return 'นาย วิษณุ ณ บางช้าง'
    elif 'pongthon' in prefix:
        return 'นาย พงศ์ธร ศิริโต'
    elif 'treesit' in prefix:
        return 'นาย ตรีสิทธิ์ อัฑฒพงษ์'
    elif 'natee' in prefix:
        return 'นาย นที แสงทอง'
    elif 'teerasak' in prefix:
        return 'นาย ธีรศักดิ์ สระศรี'
    elif 'ruckchart' in prefix:
        return 'นาย รักษ์ชาติ ประสานสกุล'
    elif 'kitisak' in prefix:
        return 'นาย กิติศักดิ์ เอิบอิ่ม'
    elif 'sompong' in prefix:
        return 'นาย สมพงษ์ จันทร์ชูกลิ่น'
    elif 'danupon' in prefix:
        return 'นาย ดนุพล จังธนสมบัติ'
    elif 'wachira' in prefix:
        return 'นาย วชิระ สีแดง'
    elif 'naris' in prefix:
        return 'นาย นริศ นวลมา'
    elif 'panitan' in prefix:
        return 'นาย ปณิธาน พึ่งธรรม'
    elif 'atchara' in prefix:
        return 'นางสาว อัจฉรา สงฉิม'
    elif 'sudarat' in prefix:
        return 'นางสาว สุดารัตน์ ทองน้อย'
    elif 'nawaporn' in prefix:
        return 'นางสาว นวพร ภู่สมบูรณ์'
    elif 'suwirat' in prefix:
        return 'นาย สุวิรัตน์ แสนสุข'
    elif 'treerapat' in prefix:
        return 'นาย ธีรภัทร ทองมาก'
    elif 'sasiwimon' in prefix:
        return 'นางสาว ศศิวิมล โชติมณีวัฒนา'
    elif 'nitad' in prefix:
        return 'นาย นิทัศน์ ปานณรงค์'
    elif 'patinya' in prefix:
        return 'นาย ปฏิณญา ชุณหมุกดา'
    elif 'suriya.iam' in prefix:
        return 'นาย สุริยา เอี่ยมอินทร์'
    elif 'ronnayut' in prefix:
        return 'นาย รณยุทธ อินทรสมบัติ'
    elif 'chanwit' in prefix:
        return 'นาย ชาญวิทย์ สกุลปักษ์'
    elif 'sarawut' in prefix:
        return 'นาย สราวุธ ช่วยมิตร'
    elif 'nattawat' in prefix:
        return 'นาย ณัฐวัฒน์ วรรณชัย'
    elif 'thaweechok' in prefix:
        return 'นาย ทวีโชค เปี่ยมอุดมลักษณ์'
    elif 'pitsanu' in prefix:
        return 'นาย พิษณุ แช่มช้อย'
    elif 'ruengsirl' in prefix:
        return 'นางสาว เรืองศิริ ทองชาติ'
    elif 'tinn' in prefix:
        return 'นาย ติณณ์ ศรีสมศักดิ์'
    elif 'watcharapon' in prefix:
        return 'นาย วัชรพล พิทยาพันธ์'
    elif 'tanawat' in prefix:
        return 'นาย ธนวัต อารีย์วงศ์'
    elif 'apiwat' in prefix:
        return 'นาย อภิวัฒน์ คนยืนยง'
    elif 'warat' in prefix:
        return 'นาย วรัษฐ์ กรเปรมสุขพงศ์'
    elif 'kritchet' in prefix:
        return 'นาย กฤษฎิ์เชษฐ์ รวยทรัพย์รชตะ'
    elif 'grissana' in prefix:
        return 'นาย กฤษณะ สมมารถ'
    elif 'thong.mun' in prefix:
        return 'นาย ทอง มั่นคง'
    elif 'wirat.suk' in prefix:
        return 'นาย วิรัตน์ สุขโต'
    elif 'boonsoom' in prefix:
        return 'นาย บุญสม นวนพลอย'
    elif 'sujittra' in prefix:
        return 'นางสาว สุจิตตรา พุ่มไสว'

    # Fallback to candidates
    return candidates[0] if candidates else ''

def extract_pos(curr):
    e = curr.get('E', '')
    h = curr.get('H', '')
    i = curr.get('I', '')
    
    for c in [e, h, i]:
        if not c or c == '/' or is_name(c):
            continue
        for k in pos_keywords:
            if c.startswith(k):
                return c.split(' ', 1)[0]
        if len(c) <= 15 and not any(d in c for d in ['กฟต', 'กฟจ', 'กฟส', 'ฝสบ', 'กปบ', 'ฝปบ']):
            return c
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

results = []
for r in range(5, 87):
    curr = rows_dict.get(r, {})
    seq = curr.get('A', '')
    emp_id = curr.get('C', '')
    if not emp_id and not seq:
        continue
        
    name = match_name_for_row(r)
    pos = extract_pos(curr)
    dept = extract_dept(curr)

    results.append({
        'row': r,
        'seq': str(len(results) + 1),
        'emp_id': emp_id,
        'name': name,
        'pos': pos,
        'dept': dept
    })

with open(r'd:\Kaeha\perfect_report.txt', 'w', encoding='utf-8') as f:
    f.write(f"Total Participants: {len(results)}\n\n")
    for p in results:
        f.write(f"ลำดับ {p['seq']:2s} | รหัส: {p['emp_id']:8s} | ชื่อ-สกุล: {p['name']:30s} | ตำแหน่ง: {p['pos']:12s} | สังกัด: {p['dept']}\n")

print("Generated perfect_report.txt successfully!")
