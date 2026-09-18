from streamlit.testing.v1 import AppTest


def test_app_opens_and_rejects_blank_question():
    app = AppTest.from_file("../app.py").run()
    assert not app.exception
    assert app.title[0].value == "Pesquisa com IA local"
    next(b for b in app.button if b.label == "Pesquisar").click().run()
    assert "Digite uma pergunta" in app.warning[0].value
    assert not app.exception


def test_missing_key_shows_actionable_message(monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "")
    app = AppTest.from_file("../app.py").run()
    app.text_area[0].set_value("O que é LangGraph?")
    next(b for b in app.button if b.label == "Pesquisar").click().run()
    assert "TAVILY_API_KEY" in app.error[0].value
    assert not app.exception
