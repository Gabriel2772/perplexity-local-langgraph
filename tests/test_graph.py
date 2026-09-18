from types import SimpleNamespace

import pytest

from graph import build_graph


class Planner:
    def __init__(self, queries):
        self.queries = queries

    def invoke(self, messages):
        return SimpleNamespace(queries=self.queries)


class Writer:
    def invoke(self, messages):
        # Echo the evidence: assertions below check the real graph's aggregation.
        return SimpleNamespace(content=messages[-1][1])


class Search:
    def search(self, query, **kwargs):
        if query == "fail":
            raise RuntimeError("secret must never appear in output")
        if query == "empty":
            return {"results": []}
        return {
            "results": [
                {"title": query, "url": f"https://example.org/{query}", "content": query},
                {"title": "Shared", "url": "https://example.org/shared", "content": "shared"},
            ]
        }


def run(queries, text="Compare A e B", **kwargs):
    return build_graph(Planner(queries), Writer(), Search(), **kwargs).invoke(
        {"user_input": text}, config={"max_concurrency": 4}
    )


def test_parallel_workers_are_aggregated_and_sources_deduplicated():
    result = run(["A", "B"])
    assert len(result["research_results"]) == 2
    assert len(result["sources"]) == 3
    assert "https://example.org/A" in result["final_response"]
    assert "https://example.org/B" in result["final_response"]


def test_query_count_is_bounded_and_duplicates_removed():
    result = run([" A ", "a", "", "B", "C"], max_queries=2)
    assert result["queries"] == ["A", "B"]


def test_empty_plan_falls_back_to_original_question():
    assert run([])["queries"] == ["Compare A e B"]


def test_one_failed_search_keeps_other_sources_without_leaking_errors():
    result = run(["A", "fail"])
    assert result["sources"]
    assert result["warnings"]
    assert "secret" not in str(result)


def test_no_evidence_does_not_generate_an_answer():
    class MustNotRun:
        def invoke(self, _):
            raise AssertionError("Writer must not run without evidence")

    result = build_graph(Planner(["empty"]), MustNotRun(), Search()).invoke(
        {"user_input": "Pergunta"}
    )
    assert "Não encontrei fontes" in result["final_response"]


def test_blank_question_rejected():
    with pytest.raises(ValueError, match="pergunta"):
        run(["A"], text="   ")


def test_unsafe_urls_are_excluded():
    class UnsafeSearch:
        def search(self, **kwargs):
            return {"results": [{"url": "javascript:alert(1)", "content": "bad"}]}

    result = build_graph(Planner(["A"]), Writer(), UnsafeSearch()).invoke(
        {"user_input": "Pergunta"}
    )
    assert result["sources"] == []
