"""Planejamento -> pesquisadores paralelos (Send) -> síntese com fontes."""

import json
import re
from datetime import date
from urllib.parse import urlsplit, urlunsplit

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from prompts import PLANNER_PROMPT, WRITER_PROMPT
from schemas import QueryResult, ReportState, ResearchState


def safe_url(value: str) -> str | None:
    try:
        parsed = urlsplit(value.strip())
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return None
        if parsed.username or parsed.password:
            return None
        return urlunsplit(parsed._replace(fragment=""))
    except (ValueError, AttributeError):
        return None


def markdown_text(value: str) -> str:
    return re.sub(r"([\\`*_{}\[\]<>()#!|])", r"\\\1", value.replace("\n", " "))


def build_graph(planner, writer, search_client, *, max_queries=4, max_results=3):
    """Injeta serviços externos para testar o grafo sem usar APIs ou modelos reais."""
    if not 1 <= max_queries <= 8 or not 1 <= max_results <= 5:
        raise ValueError("Use 1–8 consultas e 1–5 resultados por consulta.")

    def create_queries(state: ReportState):
        question = state.get("user_input", "").strip()
        if not question or len(question) > 4000:
            raise ValueError("Digite uma pergunta entre 1 e 4000 caracteres.")
        try:
            plan = planner.invoke(
                [
                    ("system", PLANNER_PROMPT.format(today=date.today(), max_queries=max_queries)),
                    ("human", question),
                ]
            )
            raw = plan.queries
        except Exception:
            # Do not silently hide a disconnected model or malformed structured output.
            raise RuntimeError("Falha no planejador. Verifique o modelo e a saída JSON.") from None
        queries, seen = [], set()
        for query in raw:
            query = query.strip()[:400]
            if query and query.casefold() not in seen:
                queries.append(query)
                seen.add(query.casefold())
            if len(queries) == max_queries:
                break
        return {"queries": queries or [question[:400]]}

    def spawn_researchers(state: ReportState):
        return [Send("research", {"query": query}) for query in state["queries"]]

    def research(state: ResearchState):
        sources, warning = [], ""
        try:
            response = search_client.search(
                query=state["query"],
                max_results=max_results,
                search_depth="basic",
                include_answer=False,
                include_raw_content=False,
                timeout=30,
            )
            for item in response.get("results", [])[:max_results]:
                url = safe_url(item.get("url", ""))
                content = item.get("content") or ""
                if url and content.strip():
                    sources.append(
                        QueryResult(
                            title=(item.get("title") or url)[:250],
                            url=url,
                            resume=content[:2500],
                        ).model_dump()
                    )
            if not sources:
                warning = f"Sem fontes utilizáveis para: {state['query']}"
        except Exception:
            # Provider exception strings may contain headers/credentials. Never expose them.
            warning = f"Busca indisponível para: {state['query']}. Verifique Tavily e conexão."
        return {
            "research_results": [
                {
                    "query": state["query"],
                    "sources": sources,
                    "warning": warning,
                }
            ]
        }

    def write_report(state: ReportState):
        indexed = {result["query"]: result for result in state.get("research_results", [])}
        sources, seen, warnings = [], set(), []
        for query in state["queries"]:
            result = indexed[query]
            if result["warning"]:
                warnings.append(result["warning"])
            for source in result["sources"]:
                if source["url"] not in seen:
                    sources.append(source)
                    seen.add(source["url"])
        if not sources:
            return {
                "sources": [],
                "warnings": warnings,
                "final_response": "Não encontrei fontes utilizáveis. Tente outra pergunta ou verifique a API Tavily.",
            }
        evidence = [{"id": i, **s} for i, s in enumerate(sources, 1)]
        context = json.dumps(
            {"question": state["user_input"], "evidence": evidence, "search_warnings": warnings},
            ensure_ascii=False,
        )
        try:
            answer = writer.invoke([("system", WRITER_PROMPT), ("human", context)]).content
            if not isinstance(answer, str) or not answer.strip():
                raise ValueError("Empty response")
        except Exception:
            raise RuntimeError("Falha na síntese. Verifique o modelo e tente novamente.") from None
        # Strip thinking blocks and Markdown images before rendering model output.
        answer = re.sub(r"<think>.*?</think>", "", answer, flags=re.S).strip()
        answer = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", answer)
        invalid = [
            int(n) for n in re.findall(r"\[(\d+)\]", answer) if not 1 <= int(n) <= len(sources)
        ]
        if invalid:
            warnings.append("O modelo gerou referências inválidas; confira a resposta nas fontes.")
            answer = re.sub(
                r"\[(\d+)\]",
                lambda m: m[0] if 1 <= int(m[1]) <= len(sources) else "[referência inválida]",
                answer,
            )
        references = "\n".join(
            f"{i}. [{markdown_text(s['title'])}](<{s['url']}>)" for i, s in enumerate(sources, 1)
        )
        return {
            "sources": sources,
            "warnings": warnings,
            "final_response": f"{answer}\n\n### Fontes consultadas\n{references}",
        }

    builder = StateGraph(ReportState)
    builder.add_node("create_queries", create_queries)
    builder.add_node("research", research)
    builder.add_node("write_report", write_report)
    builder.add_edge(START, "create_queries")
    builder.add_conditional_edges("create_queries", spawn_researchers, ["research"])
    builder.add_edge("research", "write_report")
    builder.add_edge("write_report", END)
    return builder.compile()
