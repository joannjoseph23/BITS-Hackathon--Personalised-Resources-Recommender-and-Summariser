from extract import extract_text_from_ppt, extract_text_from_pdf

def get_texts():
    pdf_text = extract_text_from_pdf("/Users/nityareddy/Desktop/forking.pdf")
    #ppt_text = extract_text_from_ppt("/Users/nityareddy/Desktop/CS/5TH SEM/GIT/unit3,5")
    return pdf_text
