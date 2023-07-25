from pathlib import Path
import enum
from typing import List, Any, Dict, Optional

from pydantic import BaseModel, Field

from hrranker.log_init import logger


class NameOfCandidateResponse(BaseModel):
    name: str = Field(
        ...,
        description="the name of the candidate if available in the text",
    )
    email: str = Field(
        ...,
        description="the email address of the candidate if available in the text",
    )
    age: int = Field(
        ...,
        description="the age of the candidate if available in the text",
    )
    gender: str = Field(
        ...,
        description="describes whether the candidate is male or female. It can e empty if this is not clear from the text.",
        enum=["female", "male", "unknown"],
    )


class NumberOfYearsResponse(BaseModel):
    has_experience: bool = Field(
        ...,
        description="describes whether the candidate has experience in the current skill",
    )
    numberOfYears: int = Field(
        ...,
        description="describes how many years of experience the candidate has in the current skill",
    )
    skill: str


class NumberOfYearsResponseWithWeight(BaseModel):
    number_of_years_response: NumberOfYearsResponse
    score_weight: int


class CandidateInfo:
    name_of_candidate_response: NameOfCandidateResponse
    number_of_years_responses: List[NumberOfYearsResponseWithWeight]
    source_file: str
    score: int

    def __init__(
        self,
        name_of_candidate_response: NameOfCandidateResponse,
        number_of_years_responses: List[NumberOfYearsResponseWithWeight],
        source_file: Path,
    ):
        self.name_of_candidate_response = name_of_candidate_response
        self.number_of_years_responses = number_of_years_responses
        self.source_file = source_file
        self.calculate_score()

    def calculate_score(self):
        score = 0
        for number_of_years_response in self.number_of_years_responses:
            nyr = number_of_years_response.number_of_years_response
            if nyr.has_experience:
                score += nyr.numberOfYears * number_of_years_response.score_weight
        self.score = score

    def __repr__(self) -> str:
        return f"Name: {self.name_of_candidate_response.name}, score: {self.score}, source_file: {self.source_file}"


def sort_candidate_infos(candidate_infos: List[CandidateInfo]):
    return sorted(candidate_infos, key=lambda x: x.score, reverse=True)


name_of_candidate_response_schema = NameOfCandidateResponse.schema()
number_of_years_response_schema = NumberOfYearsResponse.schema()

number_of_years_description = (
    "Get user answer or reply with 0 for the number of years and 'unknown' for skill"
)

questions_schemas: List[Any] = [
    {
        "question": "Which is the name, age and gender of the candidate?",
        "schema": name_of_candidate_response_schema,
        "class": NameOfCandidateResponse,
        "description": "Get user answer or reply with 0 for age or 'unknown' for name and gender if you do not know",
    },
    {
        "question": "How many years of experience with Wordpress does this candidate have?",
        "schema": number_of_years_response_schema,
        "class": NumberOfYearsResponse,
        "description": number_of_years_description,
        "year_weight": 3,
    },
    {
        "question": "How many years of experience with PHP development does this candidate have?",
        "schema": number_of_years_response_schema,
        "class": NumberOfYearsResponse,
        "description": number_of_years_description,
        "year_weight": 2,
    },
    {
        "question": "How many years of experience with Javascript development does this candidate have?",
        "schema": number_of_years_response_schema,
        "class": NumberOfYearsResponse,
        "description": number_of_years_description,
        "year_weight": 1,
    },
]


def parse_name_of_candidate_json(res: Dict) -> NameOfCandidateResponse:
    name = res.get("name")
    age = res.get("age")
    gender = res.get("gender")
    if (
        name is not None
        and age is not None
        and gender is not None
        and type(age) == int
        and type(gender) == str
    ):
        return NameOfCandidateResponse(name=name, age=age, gender=gender)
    return None


def parse_number_of_year_response_json(
    res: Dict, question_schema: Dict
) -> NumberOfYearsResponse:
    has_experience = res.get("has_experience")
    numberOfYears = res.get("numberOfYears")
    skill = res.get("skill")
    response = NumberOfYearsResponse(
        has_experience=has_experience, numberOfYears=numberOfYears, skill=skill
    )
    return response


if __name__ == "__main__":
    logger.info(name_of_candidate_response_schema)
    logger.info(number_of_years_response_schema)
    name_of_candidate_response = {
        "name": "Angadisseril Vadackathil",
        "age": 31,
        "gender": "Unknown",
    }
    ncr = NameOfCandidateResponse(age=25, name="John Doe", gender=Gender.MALE)
    nyr = NumberOfYearsResponse(has_experience=True, numberOfYears=3, skill="PHP")
    nyr_with_score = NumberOfYearsResponseWithWeight(
        number_of_years_response=nyr, score_weight=2
    )
    nyr_with_scores = [nyr_with_score]
    candidate_info = CandidateInfo(
        name_of_candidate_response=ncr, number_of_years_responses=nyr_with_scores
    )
    logger.info(f"score: {candidate_info.score}")
