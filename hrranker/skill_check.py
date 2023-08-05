from typing import List

import re


def find_whole_word(w):
    return re.compile(r"\b({0})\b".format(w), flags=re.IGNORECASE).search


def skill_check(doc: str, keywords: List[str]) -> bool:
    content = doc.lower()
    matches = False
    for keyword in keywords:
        if find_whole_word(keyword)(content):
            matches = True
            break
    return matches


if __name__ == "__main__":
    from hrranker.config import cfg
    from hrranker.extract_data import extract_data

    test_doc_location = cfg.test_doc_location
    docs = extract_data(test_doc_location, "Bharat")
    assert len(docs) == 1
    page_content = docs[0].page_content
    matches = skill_check(page_content, ["Figma"])
    assert matches
    matches = skill_check(page_content, ["Adobe XD"])
    assert matches
    matches = skill_check(page_content, ["Rust"])
    assert not matches
