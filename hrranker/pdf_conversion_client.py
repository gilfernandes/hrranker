import requests
from pathlib import Path
import json

from hrranker.config import cfg
from hrranker.extract_data import convert_pdf_to_document

from hrranker.log_init import logger

from typing import Optional

def extract_text_from_pdf(pdf: Path) -> Optional[str]:
    if not pdf.exists():
        raise Exception(f"File {pdf} does not exist.")
    pdf_parse_text = ""
    if cfg.use_parser:
        try:
            pdf_parse_text = convert_pdf_to_document(pdf).page_content
        except Exception as e:
            logger.exception("Could not parse pdf")
    with open(pdf, 'rb') as file:
        multipart_form_data = {
            'file': (pdf.name, file)
        }
        response = requests.post(cfg.remote_pdf_server, files=multipart_form_data)
        if response.status_code == 200:
            json_response = json.loads(response.content)
            extracted_text = json_response['extracted_text']
            if cfg.use_parser:
                return f"{extracted_text}\n\n{pdf_parse_text}"
            else:
                return extracted_text
        logger.warn("Could not extract PDf content due to %s", response)
        return None
    

if __name__ == "__main__":
    for doc in cfg.doc_location.glob("*.pdf"):
        logger.info("Document: %s", doc)
        extracted_text = extract_text_from_pdf(doc)
        logger.info(extracted_text)
        logger.info("")