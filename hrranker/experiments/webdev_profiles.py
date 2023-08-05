import asyncio
from hrranker.log_init import logger
from hrranker.config import cfg

from hrranker.candidate_ranker_langchain import (
    extract_data,
    process_docs,
    sort_candidate_infos,
)


async def main():
    path = cfg.test_doc_location
    docs = extract_data(path, "Ashwini_Sadamate")
    logger.info(f"Read {len(docs)} documents")
    skills = [s.strip() for s in "Adobe Xd, Figma, HTML, CSS".split(",")]
    candidate_infos = await process_docs(docs, skills=skills, weights=[3, 3, 2, 2])
    candidate_infos = sort_candidate_infos(candidate_infos)

    logger.info("")
    for candidate_info in candidate_infos:
        logger.info(candidate_info)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
