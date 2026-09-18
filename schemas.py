"""Estados do grafo e contrato de saída estruturada do planejador."""

import operator
from typing import Annotated, TypedDict

from pydantic import BaseModel, Field


class QueryPlan(BaseModel):
    queries: list[str] = Field(default_factory=list, description="Consultas de busca distintas")


class QueryResult(BaseModel):
    title: str = ""
    url: str
    resume: str = ""


class ResearchResult(TypedDict):
    query: str
    sources: list[dict]
    warning: str


class ReportState(TypedDict, total=False):
    user_input: str
    queries: list[str]
    research_results: Annotated[list[ResearchResult], operator.add]
    sources: list[dict]
    warnings: list[str]
    final_response: str


class ResearchState(TypedDict):
    query: str
