# HR Candidate Ranker

The idea of this project is to provide a rank for candidates based on their CVs for interviews for a position based on a specific set of questions.
IT provides a chat like web interface based on Chainlit.

It can be used 

## Installation

First create an environment with Conda:

```
# conda activate base
# conda remove -n langchain_hrranker --all
conda create -n langchain_hrranker python=3.11
conda activate langchain_hrranker
# pip install chainlit
pip install --force-reinstall \\wsl.localhost\Ubuntu\home\gilf\chainlit\src\dist\chainlit-0.6.1.1-py3-none-any.whl
pip install langchain
pip install pdfminer
pip install pypdfium2
pip install -U matplotlib
pip install -e .
pip install black

```

To install as a package, please use:

```bash
pip install -e .
```

## Run Chainlit

For development:
```
chainlit run ./hrranker/ui/candidate_ranker_chainlit.py --port 8082 -w
```

Normally:
```
chainlit run ./hrranker/ui/candidate_ranker_chainlit.py --port 8082
```
