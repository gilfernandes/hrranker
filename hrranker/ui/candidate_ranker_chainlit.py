from hrranker.plot.hr_rank_plot import create_barchart
from langchain.schema import Document
import chainlit as cl


from hrranker.candidate_ranker_langchain import process_docs, sort_candidate_infos
from hrranker.log_init import logger
from hrranker.extract_data import convert_pdf_to_document
from hrranker.config import cfg
from hrranker.hr_model import CandidateInfo

from typing import List, Any

from pathlib import Path

MAX_FILES = 10
TiMEOUT = 300


def write_temp_file(file) -> Document:
    temp_doc_location = cfg.temp_doc_location
    new_path = temp_doc_location / (file.name)
    logger.info(f"new path: {new_path}")
    with open(new_path, "wb") as f:
        f.write(file.content)
    return convert_pdf_to_document(new_path)


@cl.on_chat_start
async def init():
    while True:
        skills = await gather_elements(
            "Please enter the list of skills as a comma separated list, like e.g: `Wordpress, Programming in PHP, Programming in Javascript, CSS, Programming in SQL`",
            "skills",
            None,
        )
        weights = await gather_elements(
            f"Please enter the list of ({len(skills)}) weights as a comma separated list, like e.g: `4, 3, 2, 1, 1`",
            "weights",
            skills,
        )

        weights = [int(i) for i in weights]

        if len(skills) == len(weights):
            break
        else:
            await cl.Message(
                content=f"The length of the skill and weights do not match. Please make sure that the length of the skills and weights match, so that we can score the CVs.",
            ).send()

    await handle_rankings(skills, weights)


async def gather_elements(content: str, item_name: str, previous_elements: List[Any]):
    items = None
    while not items:
        res = await cl.AskUserMessage(
            content=content, timeout=TiMEOUT, raise_on_timeout=False
        ).send()
        if res:
            items = [s.strip() for s in res["content"].split(",")]
            if previous_elements and len(items) != len(previous_elements):
                await cl.Message(
                    content=f"The weights and the skills do not have the same length.",
                ).send()
                continue
            items_strings = []
            if previous_elements:
                for i, p in enumerate(previous_elements):
                    items_strings.append(f"{items[i]} ({p})")
            else:
                items_strings = items
            joined_str = "\n- ".join(items_strings)
            await cl.Message(
                content=f"Your {item_name} are: \n- {joined_str}",
            ).send()

    return items


async def handle_rankings(skills: List[str], weights: List[int]):
    files = []

    # Wait for the user to upload a file
    while not files:
        files = await cl.AskFileMessage(
            content="Please upload a pdf file with the CV of a candidate!",
            accept=["application/pdf"],
            max_files=MAX_FILES,
            timeout=TiMEOUT,
        ).send()

        if files is not None:
            file_names = "\n- ".join([f"{f.name}" for f in files])
            docs = [write_temp_file(file) for file in files]

            msg = cl.Message(content="")
            await msg.stream_token(
                f"### Processing \n\n- {file_names}. \n\nYou have currently **{len(docs)}** files.\n\n"
            )

            candidate_infos = await process_docs(docs, skills, msg)
            candidate_infos: List[CandidateInfo] = sort_candidate_infos(candidate_infos)

            ranking_text = await execute_candidates(candidate_infos)

            barchart_image = create_barchart(candidate_infos)
            elements = [
                cl.Image(
                    name="image1",
                    display="inline",
                    path=str(barchart_image.absolute()),
                    size="large",
                )
            ]

            result_message = cl.Message(content=ranking_text, elements=elements)
            await result_message.send()


async def execute_candidates(candidate_infos: List[CandidateInfo]):
    ranking_text = "## Ranking\n\n"
    for i, condidate_info in enumerate(candidate_infos):
        personal_data = condidate_info.name_of_candidate_response
        source_file = Path(condidate_info.source_file)
        ranking_text += f"{i + 1}. Name: {personal_data.name}, Email: {personal_data.email}, points: {condidate_info.score}\n\n"
        ranking_text += f"*{source_file.stem}*\n\n"
        for nyr in condidate_info.number_of_years_responses:
            number_of_years_response = nyr.number_of_years_response
            ranking_text += f"  - Skill: {number_of_years_response.skill}, years: {number_of_years_response.number_of_years_with_skill}\n"

    return ranking_text
