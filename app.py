"""Execute com: poetry run streamlit run app.py"""

from dataclasses import replace

import streamlit as st

from config import Settings, create_graph

st.set_page_config(page_title="Pesquisa com IA local", page_icon="🔎", layout="centered")
st.title("Pesquisa com IA local")
st.caption("Pergunte, acompanhe as buscas e confira as fontes.")
settings = Settings.from_env()

with st.sidebar:
    st.header("Configuração")
    model = st.text_input("Modelo de resposta", value=settings.model)
    reasoning_model = st.text_input("Modelo de planejamento", value=settings.reasoning_model)
    max_queries = st.slider("Máximo de consultas", 1, 8, 4)
    max_results = st.slider("Resultados por consulta", 1, 5, 3)
    st.caption("Use o nome exato exibido por `ollama list`.")
    st.caption(
        "Ollama gera o texto localmente. Tavily recebe as consultas para pesquisar na internet."
    )
    if st.button("Limpar resultado"):
        st.session_state.pop("report", None)

with st.form("research_form"):
    question = st.text_area(
        "O que você quer pesquisar?",
        max_chars=4000,
        placeholder="Compare LangGraph e uma sequência simples de chamadas de LLM.",
    )
    submitted = st.form_submit_button("Pesquisar", type="primary")

if submitted:
    st.session_state.pop("report", None)
    if not question.strip():
        st.warning("Digite uma pergunta antes de pesquisar.")
    else:
        try:
            workflow = create_graph(
                replace(settings, model=model, reasoning_model=reasoning_model),
                max_queries=max_queries,
                max_results=max_results,
            )
            with st.status("Planejando pesquisa...", expanded=True) as status:
                latest = {}
                for state in workflow.stream(
                    {"user_input": question}, stream_mode="values", config={"max_concurrency": 4}
                ):
                    latest = state
                    if state.get("final_response"):
                        status.update(label="Pesquisa concluída", state="complete", expanded=False)
                    elif state.get("research_results"):
                        status.update(label="Consolidando fontes e preparando resposta...")
                    elif state.get("queries"):
                        status.update(label="Pesquisando na web...")
                        for query in state["queries"]:
                            st.write(f"• {query}")
                st.session_state["report"] = latest
        except (ValueError, RuntimeError) as exc:
            st.error(str(exc))
        except Exception:
            st.error(
                "Não foi possível concluir. Verifique Ollama, modelos, conexão e chave Tavily."
            )

if report := st.session_state.get("report"):
    for warning in report.get("warnings", []):
        st.warning(warning)
    st.markdown(report["final_response"])
    with st.expander("Consultas e trechos recuperados"):
        st.write(report["queries"])
        for source in report.get("sources", []):
            st.write(source["title"])
            st.caption(source["url"])
            st.text(source["resume"])
    st.download_button(
        "Baixar resposta em Markdown",
        report["final_response"],
        file_name="pesquisa.md",
        mime="text/markdown",
    )
