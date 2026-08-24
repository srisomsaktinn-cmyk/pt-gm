import zipfile

docx_path = r'd:\Kaeha\แบบฟอร์มกิจกรรม PEA safety talk [Cybersecurity].docx'
with zipfile.ZipFile(docx_path, 'r') as z:
    raw_xml = z.read('word/document.xml').decode('utf-8')

tbl_start = raw_xml.find('<w:tbl>')
tbl_end = raw_xml.find('</w:tbl>') + len('</w:tbl>')

tbl_xml = raw_xml[tbl_start:tbl_end]

with open(r'd:\Kaeha\raw_table.xml', 'w', encoding='utf-8') as f:
    f.write(tbl_xml)

print(f"Table XML length: {len(tbl_xml)} chars")
