import PyPDF2

with open('Provider Reimbursement Manual.pdf', 'rb') as pdf_file:
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ''
    for page in pdf_reader.pages:
        text += page.extract_text()

with open('Provider Reimbursement Manual.txt', 'w', encoding='utf-8') as txt_file:
    txt_file.write(text)