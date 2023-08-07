from langchain.chat_models import ChatOpenAI
from pathlib import Path
import os

import pytesseract

from dotenv import load_dotenv

load_dotenv()

from pdf_image_ocr.config import cfg as image_cfg


class Config:
    model = "gpt-3.5-turbo-0613"
    # model = 'gpt-4-0613'
    llm = ChatOpenAI(model=model, temperature=0)
    doc_location = Path(os.getenv("DOC_LOCATION"))
    test_doc_location = Path(os.getenv("TEST_DOCS"))
    openai_api_key = os.getenv("OPENAI_API_KEY")
    temp_doc_location = Path(os.getenv("TEMP_DOC_LOCATION"))
    remote_pdf_server = os.getenv('REMOTE_PDF_SERVER')

    if not temp_doc_location.exists():
        temp_doc_location.mkdir(parents=True)

    def __repr__(self) -> str:
        return f"""# Configuration

doc_location: {self.doc_location}
llm: {self.llm}
"""


cfg = Config()

if __name__ == "__main__":
    print(cfg)
    print(image_cfg)
    print(pytesseract.pytesseract.tesseract_cmd)
