from langchain import PromptTemplate
from langchain.schema import Document
from langchain.chains import create_tagging_chain_pydantic, create_tagging_chain
from typing import List

from hrranker.extract_data import extract_data
from hrranker.config import cfg
from hrranker.hr_model import (
    CandidateInfo,
    NameOfCandidateResponse,
    NumberOfYearsResponse,
    NumberOfYearsResponseWithWeight,
    create_skill_schema,
    sort_candidate_infos,
)
from hrranker.log_init import logger

import asyncio

import chainlit

SKILL_TEMPLATE = PromptTemplate.from_template(
    "Based on the following text, how many years does this person have in {technology}.? " + 
    "And tell whether this person has experience in {technology}." +
    "If a person has experience in {technology} but you cannot figure out the years reply with 1.\n\n"
)
SKILLS = [
    "Wordpress",
    "Programming in PHP",
    "Programming in Javascript",
    "CSS",
    "Programming in Rust",
    "Programming in OCaml",
]
WEIGHTS = [3, 2, 1, 1, 1, 1]


async def process_docs(
    docs: List[Document],
    skills: List[str] = SKILLS,
    weights: List[int] = WEIGHTS,
    cl_msg: chainlit.Message = None,
) -> List[CandidateInfo]:
    candidate_infos: List[CandidateInfo] = []
    for doc in docs:
        chain = create_tagging_chain_pydantic(NameOfCandidateResponse, cfg.llm)
        try:
            name_of_candidate_response = await chain.arun(doc)
            logger.info(f"Response: {name_of_candidate_response}")
            if cl_msg:
                await cl_msg.stream_token(
                    f"Processing {name_of_candidate_response.name}\n\n"
                )
            number_of_year_responses: List[NumberOfYearsResponseWithWeight] = []
            process_skills(doc, number_of_year_responses, skills, weights)
            candidate_info = CandidateInfo(
                name_of_candidate_response=name_of_candidate_response,
                number_of_years_responses=number_of_year_responses,
                source_file=doc.metadata["source"],
            )
            candidate_infos.append(candidate_info)
        except Exception as e:
            logger.error(f"Could not process {doc.metadata['source']} due to {e}")
    return candidate_infos


def process_skills(
    doc,
    number_of_year_responses,
    skills: List[str] = SKILLS,
    weights: List[int] = WEIGHTS,
):
    page_content = doc.page_content
    for skill, weight in zip(skills, weights):
        # Create skill schema dynamically
        schema, has_skill_field, number_of_years_field = create_skill_schema(skill)
        chain = create_tagging_chain(schema, cfg.llm)
        # Combine the CV with a question
        doc.page_content = SKILL_TEMPLATE.format(technology=skill) + page_content
        # Run the chain
        number_of_years_response_json = chain.run(doc)
        # Extract the results
        number_of_years = (
            0
            if number_of_years_response_json[number_of_years_field] == None
            else number_of_years_response_json[number_of_years_field]
        )
        has_skill = (
            False
            if not number_of_years_response_json[has_skill_field]
            else number_of_years_response_json[has_skill_field]
        )
        number_of_years_response = NumberOfYearsResponse(
            has_skill=has_skill, number_of_years_with_skill=number_of_years, skill=skill
        )
        number_of_year_responses.append(
            NumberOfYearsResponseWithWeight(
                number_of_years_response=number_of_years_response,
                score_weight=weight,
            )
        )
        logger.info(f"Response: {number_of_years_response}")


async def main():
    path = cfg.doc_location
    docs = extract_data(path)
    logger.info(f"Read {len(docs)} documents")

    candidate_infos = await process_docs(docs)
    candidate_infos = sort_candidate_infos(candidate_infos)

    logger.info("")
    for candidate_info in candidate_infos:
        logger.info(candidate_info)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
