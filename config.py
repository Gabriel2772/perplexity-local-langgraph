"""Configuração local; importar este módulo não faz chamadas de rede."""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    model: str = "gemma4:e2b-it-qat"
    reasoning_model: str = "gemma4:e2b-it-qat"
    base_url: str = "http://localhost:11434"
    tavily_api_key: str = field(default="", repr=False)

    @classmethod
    def from_env(cls):
        load_dotenv(Path(__file__).parent / ".env")
        model = os.getenv("OLLAMA_MODEL", "gemma4:e2b-it-qat").strip()
        return cls(
            model=model,
            reasoning_model=os.getenv("REASONING_MODEL", model).strip() or model,
            base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip(),
            tavily_api_key=os.getenv("TAVILY_API_KEY", "").strip(),
        )


def create_graph(settings: Settings, *, max_queries=4, max_results=3):
    if not settings.tavily_api_key:
        raise ValueError("Preencha TAVILY_API_KEY no arquivo .env.")

    from langchain_ollama import ChatOllama
    from tavily import TavilyClient

    from graph import build_graph
    from schemas import QueryPlan

    if not settings.model or not settings.reasoning_model:
        raise ValueError("Informe os nomes dos modelos instalados no Ollama.")
    planner = ChatOllama(
        model=settings.reasoning_model,
        base_url=settings.base_url,
        temperature=0,
        num_ctx=16384,
        client_kwargs={"timeout": 180},
    ).with_structured_output(QueryPlan, method="json_schema")
    writer = ChatOllama(
        model=settings.model,
        base_url=settings.base_url,
        temperature=0.2,
        num_ctx=32768,
        client_kwargs={"timeout": 300},
    )
    return build_graph(
        planner,
        writer,
        TavilyClient(api_key=settings.tavily_api_key),
        max_queries=max_queries,
        max_results=max_results,
    )
