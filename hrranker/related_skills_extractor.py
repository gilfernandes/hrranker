from langchain.chains import create_tagging_chain
from langchain.schema import HumanMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, HumanMessagePromptTemplate

from langchain.chains.openai_functions import (
    create_structured_output_chain,
)

from typing import List, Any

from hrranker.hr_model import related_skills_schema
from hrranker.config import cfg
from hrranker.log_init import logger

import asyncio

async def extract_related_skills(skill: str) -> List[Any]:

    prompt_msgs = [
        SystemMessage(
            content="You are a world class algorithm for extracting information in structured formats."
        ),
        HumanMessage(
            content=f"Which topics  and frameworks are related to {skill}? Can you please provide a list? For example."
        ),
        HumanMessagePromptTemplate.from_template("{input}"),
        HumanMessage(content="Tips: Make sure to answer in the correct format"),
    ]
    prompt = ChatPromptTemplate(messages=prompt_msgs)

    chain = create_structured_output_chain(related_skills_schema(skill), cfg.llm, prompt, verbose=True)

    res = await chain.arun(skill)
    logger.info(res)
    if 'related skills' in res:
        return res['related skills']
    else:
        keys = list(res.keys())
        if len(keys) > 0:
            return res[keys[-1]]
        else:
            logger.warn("Failed to return anything from related skills: %s", res)
            return []


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    asyncio.run(extract_related_skills("Tailwind CSS"))
    loop.run_forever()
    loop.close()
    
