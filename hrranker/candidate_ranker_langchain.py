from langchain import PromptTemplate
from langchain.schema import Document
from langchain.chains import create_tagging_chain_pydantic
from typing import List

from hrranker.extract_data import extract_data
from hrranker.config import cfg
from hrranker.hr_model import (
    CandidateInfo,
    NameOfCandidateResponse,
    NumberOfYearsResponse,
    NumberOfYearsResponseWithWeight,
    sort_candidate_infos,
)
from hrranker.log_init import logger

SKILL_TEMPLATE = PromptTemplate.from_template(
    "Based on the following text, how many years does this person have in {technology}.? And tell whether this person has experience with {technology}.\n\n"
)
SKILLS = ["Wordpress", "PHP", "Javascript", "CSS"]
WEIGHTS = [3, 2, 1, 1]


def process_docs(
    docs: List[Document], skills: List[str] = SKILLS
) -> List[CandidateInfo]:
    candidate_infos: List[CandidateInfo] = []
    for doc in docs:
        chain = create_tagging_chain_pydantic(NameOfCandidateResponse, cfg.llm)
        name_of_candidate_response = chain.run(doc)
        logger.info(f"Response: {name_of_candidate_response}")
        number_of_year_responses: List[NumberOfYearsResponseWithWeight] = []
        process_skills(doc, number_of_year_responses, skills)
        candidate_info = CandidateInfo(
            name_of_candidate_response=name_of_candidate_response,
            number_of_years_responses=number_of_year_responses,
            source_file=doc.metadata["source"],
        )
        candidate_infos.append(candidate_info)
    return candidate_infos


def process_skills(
    doc,
    number_of_year_responses,
    skills: List[str] = SKILLS,
    weights: List[int] = WEIGHTS,
):
    for skill, weight in zip(skills, weights):
        chain = create_tagging_chain_pydantic(NumberOfYearsResponse, cfg.llm)
        # Combine the CV with a question
        doc.page_content = SKILL_TEMPLATE.format(technology=skill) + doc.page_content
        number_of_years_response = chain.run(doc)
        number_of_year_responses.append(
            NumberOfYearsResponseWithWeight(
                number_of_years_response=number_of_years_response,
                score_weight=weight,
            )
        )
        logger.info(f"Response: {number_of_years_response}")


if __name__ == "__main__":
    path = cfg.doc_location
    docs = extract_data(path)
    logger.info(f"Read {len(docs)} documents")

    candidate_infos = process_docs(docs)
    candidate_infos = sort_candidate_infos(candidate_infos)

    logger.info("")
    for candidate_info in candidate_infos:
        logger.info(candidate_info)
