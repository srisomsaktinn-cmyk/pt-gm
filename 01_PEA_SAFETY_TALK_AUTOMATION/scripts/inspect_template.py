import zipfile
import xml.etree.ElementTree as ET

docx_path = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity].docx'
with zipfile.ZipFile(docx_path, 'r') as z:
    xml_bytes = z.read('word/document.xml')
    tree = ET.fromstring(xml_bytes)
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    tbl = tree.find('.//w:tbl', ns)
    rows = tbl.findall('w:tr', ns)
    sample_row = rows[1]
    
    with open(r'd:\Kaeha\sample_row.xml', 'w', encoding='utf-8') as f:
        f.write(ET.tostring(sample_row, encoding='utf-8').decode('utf-8'))

print('Saved sample_row.xml!')
