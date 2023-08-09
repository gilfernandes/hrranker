
from langchain.schema import Document
import chainlit as cl
from asyncer import asyncify

from hrranker.plot.hr_rank_plot import create_barchart
from hrranker.related_skills_extractor import extract_related_skills
from hrranker.candidate_ranker_langchain import process_docs, sort_candidate_infos
from hrranker.log_init import logger
from hrranker.config import cfg
from hrranker.hr_model import CandidateInfo
from hrranker.pdf_conversion_client import extract_text_from_pdf

from typing import List, Any, Optional

from pathlib import Path

MAX_FILES = 20
TIMEOUT = 1200

KEY_EXTENDED_SKILLS = 'extended_skills'


@cl.on_chat_start
async def init():
    while True:
        skills = await gather_elements(
            "Please enter the list of skills as a comma separated list, like e.g: `Wordpress, Programming in PHP, Programming in Javascript, CSS, Programming in SQL`",
            "skills",
            None,
        )
        skills = await related_skills(skills)
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


def split_skills(input: str) -> List[str]:
    return [s.strip() for s in input["content"].split(",")]

async def gather_elements(content: str, item_name: str, previous_elements: List[Any]):
    items = None
    while not items:
        res = await cl.AskUserMessage(
            content=content, timeout=TIMEOUT, raise_on_timeout=False
        ).send()
        if res:
            items = split_skills(res)
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
                content=f"Your selected {item_name} are: \n- {joined_str}",
            ).send()

    return items


@cl.action_callback("action_button")
async def on_action(action):
    skill: str = action.value
    extended_skills = cl.user_session.get(KEY_EXTENDED_SKILLS)
    extended_skills.append(skill)
    await cl.Message(content=f"Added {skill}").send()
    # Remove the action button from the chatbot user interface
    # await action.remove()
    


async def related_skills(skills: List[str]) -> str:
    extended_skills = [] + skills
    cl.user_session.set(KEY_EXTENDED_SKILLS, extended_skills)
    for skill in skills:
        related_skills = await extract_related_skills(skill)
        actions = []
        for i, related_skill in enumerate(related_skills):
            # Sending an action button within a chatbot message
            actions.append(
                cl.Action(
                    name="action_button", 
                    label=related_skill,
                    value=related_skill, 
                    description=f"{i}. {related_skill}"
                )
            )
        await cl.Message(content=f"Extra skills for \"{skill}\"", actions=actions).send()
        while True:
            res = await cl.AskUserMessage(
                content="Would you like to include any extra skills? Enter 'ok' to continue.", timeout=TIMEOUT, raise_on_timeout=False
            ).send()
            if 'content' in res and res['content'].lower() == 'ok':
                break

    await cl.Message(content=f"Current skills: {', '.join(extended_skills)}").send()
    extended_skills = list(dict.fromkeys(extended_skills))
    return extended_skills


async def handle_rankings(skills: List[str], weights: List[int]):
    files = []
    docs: List[Document] = []
    file_names = ""

    # Wait for the user to upload a file
    while not files:
        files = await cl.AskFileMessage(
            content="Please upload multiple pdf files with the CV of a candidate!",
            accept=["application/pdf"],
            max_files=MAX_FILES,
            timeout=TIMEOUT,
        ).send()

        if files is not None:
            file_names += "\n- ".join([f"{f.name}" for f in files])

            await process_file_extraction(docs, files)

            res = await cl.AskUserMessage(
                content=f"You have uploaded {len(docs)} documents. Any more documents? (y/n)",
                timeout=TIMEOUT,
                raise_on_timeout=False,
            ).send()

            if res is None:
                await cl.Message(
                    content=f"Process failed. Please restart.",
                ).send()
                files = None
            elif res["content"].lower() in ["n", "no", "nope"]:
                break
            else:
                files = None

    await process_ranking_with_files(skills, weights, file_names, docs)


async def process_file_extraction(docs: List[Document], files: List[str]):

    await cl.Message(content="Extracting text from files ...\n\n").send()
    for i, file in enumerate(files):
        file_path = await asyncify(write_to_temp_folder)(file=file)
        extracted_text = await asyncify(extract_text_from_pdf)(pdf=file_path)
        if extracted_text is not None:
            docs.append(Document(page_content=extracted_text, metadata={'source': file_path.absolute()}))
            await cl.Message(
                content=f"{i + 1}. {file.name}.\n\n"
            ).send()
            logger.info("Processed %s", file_path)
        else:
            await cl.Message(
                content=f"Failed to extract {file.name}.\n\n"
            ).send()


async def process_ranking_with_files(skills, weights, file_names, docs):
    msg = cl.Message(content="")
    await msg.stream_token(
        f"### Processing \n\n- {file_names}. \n\nYou have currently **{len(docs)}** files.\n\n"
    )

    candidate_infos = await process_docs(docs, skills, weights, msg)
    candidate_infos: List[CandidateInfo] = sort_candidate_infos(candidate_infos)

    barchart_image = create_barchart(candidate_infos)
    elements = [
        cl.Image(
            name="image1",
            display="inline",
            path=str(barchart_image.absolute()),
            size="large",
        )
    ]

    barchart_message = cl.Message(content="## Results", elements=elements)
    await barchart_message.send()

    await display_candidates(candidate_infos)


def write_to_temp_folder(file) -> Path:
    temp_doc_location = cfg.temp_doc_location
    new_path = temp_doc_location / (file.name)
    logger.info(f"new path: {new_path}")
    with open(new_path, "wb") as f:
        f.write(file.content)
    return new_path


def ranking_generator(candidate_infos: List[CandidateInfo]):
    for i, condidate_info in enumerate(candidate_infos):
        personal_data = condidate_info.name_of_candidate_response
        source_file = Path(condidate_info.source_file)
        yield i, condidate_info, personal_data, source_file


async def display_candidates(candidate_infos: List[CandidateInfo]):

    ranking_text = "## Ranking\n\n"
    for i, condidate_info, personal_data, source_file in ranking_generator(candidate_infos):
        personal_data = condidate_info.name_of_candidate_response
        source_file = Path(condidate_info.source_file)
        ranking_text += f"{i + 1}. Name: **{personal_data.name}**"
        ranking_text += f" *{source_file.name}*\n\n"

    randking_message = cl.Message(content=ranking_text)
    await randking_message.send()

    await cl.Message(content="## Breakdown\n\n").send()

    for i, condidate_info, personal_data, source_file in ranking_generator(candidate_infos):
        pdf_element = create_pdf(source_file)
        personal_data = condidate_info.name_of_candidate_response
        source_file = Path(condidate_info.source_file)
        ranking_text = ""
        ranking_text += f"{i + 1}. Name: **{personal_data.name}**, Email: {personal_data.email}, Experience: {personal_data.years_of_experience}, points: {condidate_info.score}\n\n"
        ranking_text += f"*{source_file}*\n\n"
        for nyr in condidate_info.number_of_years_responses:
            number_of_years_response = nyr.number_of_years_response
            ranking_text += f"  - Skill: {number_of_years_response.skill}, years: {number_of_years_response.number_of_years_with_skill}\n"
        breakdown_list = []
        for nyr in condidate_info.number_of_years_responses:
            number_of_years_response = nyr.number_of_years_response
            breakdown_list.append(f"{number_of_years_response.number_of_years_with_skill} * {nyr.score_weight}")
        breakdown_text = " + ".join(breakdown_list)
        await cl.Message(content=f"{ranking_text}\n\n{condidate_info.score} = {breakdown_text} + {personal_data.years_of_experience}", elements=[pdf_element]).send()



def create_pdf(source_file: Path) -> Optional[cl.File]:
    return cl.File(
        name=source_file.name, display="inline", path=str(source_file.absolute())
    )