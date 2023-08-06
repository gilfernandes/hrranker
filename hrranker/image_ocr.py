from pathlib import Path
from typing import List

from langchain.schema import Document

from hrranker.log_init import logger
from hrranker.config import cfg

from pdf_image_ocr.image_ocr import convert_img_to_text

def convert_pdf_to_doc(pdf: Path) -> List[Document]:
    pdf_content = convert_img_to_text(pdf)
    new_document = Document(page_content=pdf_content, metadata={'source': pdf.absolute()})
    return new_document


if __name__ == "__main__":
    doc_location = cfg.test_doc_location
    logger.info("Starting using %s", doc_location)
    for doc in doc_location.glob("*.pdf"):
        logger.info("Processing %s", doc)
        document = convert_pdf_to_doc(doc)
        logger.info("Extracted document: %s", document)
        break