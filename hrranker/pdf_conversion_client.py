import requests
from pathlib import Path
import json

from hrranker.config import cfg

from hrranker.log_init import logger

from typing import Optional

def extract_text_from_pdf(pdf: Path) -> Optional[str]:
    if not pdf.exists():
        raise Exception(f"File {pdf} does not exist.")
    with open(pdf, 'rb') as file:
        multipart_form_data = {
            'file': (pdf.name, file)
        }
        response = requests.post(cfg.remote_pdf_server, files=multipart_form_data)
        if response.status_code == 200:
            json_response = json.loads(response.content)
            return json_response['extracted_text']
        logger.warn("Could not extract PDf content due to %s", response)
        return None
    

if __name__ == "__main__":
    for doc in cfg.doc_location.glob("*.pdf"):
        logger.info("Document: %s", doc)
        extracted_text = extract_text_from_pdf(doc)
        logger.info(extracted_text)
        logger.info("")