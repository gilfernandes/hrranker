from hrranker.hr_model import (
    CandidateInfo,
    NameOfCandidateResponse,
    NumberOfYearsResponseWithWeight,
)
from hrranker.config import cfg

import matplotlib.pyplot as plt
import matplotlib
from matplotlib.pyplot import figure
from pathlib import Path
import numpy as np

import time

from typing import List


def create_barchart(candidate_infos: List[CandidateInfo]) -> Path:
    x_axis = [ci.name_of_candidate_response.name for ci in candidate_infos]
    y_axis = [ci.score for ci in candidate_infos]
    fig = figure(figsize=(18, 10), dpi=80)
    fig.subplots_adjust(bottom=0.2)
    font = {"size": 22}

    matplotlib.rc("font", **font)
    plt.bar(x_axis, y_axis)
    plt.title("Candidate Ranking")
    plt.xlabel("Candidate name")
    plt.ylabel("Score")
    plt.xticks(rotation=25)

    time_millis = round(time.time() * 1000)

    ranking_plot = cfg.temp_doc_location / f"{time_millis}_ranking.png"
    plt.savefig(ranking_plot)
    return ranking_plot


if __name__ == "__main__":
    name_of_candidate_response_1 = NameOfCandidateResponse(
        name="John Doe", age=40, gender="male", email="john@gmail.com"
    )
    number_of_years_responses: List[NumberOfYearsResponseWithWeight] = []
    candidate_info_1 = CandidateInfo(
        name_of_candidate_response=name_of_candidate_response_1,
        number_of_years_responses=number_of_years_responses,
        source_file="john.pdf",
    )
    candidate_info_1.score = 10

    name_of_candidate_response_2 = NameOfCandidateResponse(
        name="Mary Doe", age=40, gender="female", email="mary@gmail.com"
    )
    candidate_info_2 = CandidateInfo(
        name_of_candidate_response=name_of_candidate_response_2,
        number_of_years_responses=number_of_years_responses,
        source_file="mary.pdf",
    )
    candidate_info_2.score = 12

    candidate_infos: List[CandidateInfo] = [candidate_info_1, candidate_info_2]
    create_barchart(candidate_infos=candidate_infos)
