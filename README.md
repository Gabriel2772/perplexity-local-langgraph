# Pesquisa com IA local — LangGraph + Ollama

Aplicação de pesquisa na web com planejamento por LLM, consultas paralelas no Tavily e resposta em português com fontes. Interface em Streamlit, executada no computador do usuário.

Projeto de **Gabriel Amaral** para pesquisa na web com modelos de linguagem locais.

## Executar no Windows / PowerShell

Requisitos: Python 3.11–3.14, Git, Poetry 2 e [Ollama](https://ollama.com/download). Python 3.12 é a versão usada na verificação deste projeto.

```powershell
git clone https://github.com/Gabriel2772/perplexity-local-langgraph.git
cd perplexity-local-langgraph
poetry install
Copy-Item .env.example .env
notepad .env
```

Preencha `TAVILY_API_KEY` com sua chave do [Tavily](https://www.tavily.com/). Se você já tem um `.env` com essa chave, copie seu arquivo para a pasta do projeto e acrescente as configurações opcionais abaixo. Não substitua um `.env` já configurado pelo exemplo.

Confirme os modelos instalados:

```powershell
ollama list
```

O nome `gemma4:e2b-it-qat` foi preservado do código inicial enviado. **A disponibilidade dessa tag e a inferência com ela não foram verificadas neste ambiente.** Configure `OLLAMA_MODEL` e `REASONING_MODEL` com o nome exato de um modelo instalado no seu Ollama. O planejador precisa funcionar com saída JSON estruturada; a qualidade depende do modelo.

Se ainda não tiver modelo, escolha uma tag disponível no [catálogo oficial do Ollama](https://ollama.com/library) e use `ollama pull NOME_DO_MODELO`. O comando é um exemplo: substitua `NOME_DO_MODELO` pela tag escolhida.

Abra o aplicativo Ollama. Se o servidor não estiver rodando, execute `ollama serve` em outro terminal. Em seguida:

```powershell
poetry run streamlit run app.py
```

Acesse `http://localhost:8501`. Não é necessário `poetry shell`, zsh ou ativar manualmente o ambiente virtual. No Linux/macOS, use `cp .env.example .env` no lugar de `Copy-Item`.

## Como funciona

1. O planejador transforma a pergunta em até quatro consultas, configuráveis na interface.
2. `Send` cria uma tarefa de pesquisa para cada consulta. Até quatro buscas podem executar simultaneamente.
3. Cada pesquisador consulta Tavily. Um reducer (`operator.add`) reúne os resultados sem sobrescrever outros pesquisadores.
4. O compilador remove URLs repetidas, numera as fontes e solicita uma resposta ao modelo local.
5. A interface mostra a resposta, as consultas, os trechos recuperados, eventuais falhas e um botão para baixar o Markdown.

Os pesquisadores realizam a recuperação; o planejador e o compilador usam LLM. Não há treinamento de redes neurais, banco vetorial ou memória persistente entre perguntas. Cada envio inicia uma nova pesquisa.

## Arquivos

| Arquivo | Responsabilidade |
| --- | --- |
| `app.py` | Interface Streamlit e acompanhamento da pesquisa |
| `graph.py` | Grafo, distribuição paralela, busca e síntese |
| `garph.py` | Compatibilidade com o nome original do arquivo |
| `schemas.py` | Plano estruturado e estados do grafo |
| `prompts.py` | Instruções de planejamento e síntese |
| `config.py` | Leitura do `.env` e construção dos clientes |
| `tests/` | Testes com serviços externos simulados e Streamlit AppTest |
| `poetry.lock` | Dependências resolvidas pelo Poetry |

## Configuração

| Variável | Uso |
| --- | --- |
| `TAVILY_API_KEY` | Obrigatória para pesquisa real; nunca versionar |
| `OLLAMA_BASE_URL` | Padrão `http://localhost:11434` |
| `OLLAMA_MODEL` | Modelo da resposta final |
| `REASONING_MODEL` | Modelo do planejador; usa o mesmo modelo se omitida |

As dependências `langchain` e `langchain-openai` do esboço foram retiradas: esta versão usa `langchain-ollama` e não oferece integração OpenAI. `tavily-python` foi adicionado para a busca. `package-mode = false` permite usar Poetry sem criar um pacote Python instalável.

## Testes

```powershell
poetry run pytest -q
poetry run ruff check .
```

Os testes executam o grafo real do LangGraph com planejador, escritor e buscador simulados. Cobrem agregação paralela, limites de consultas, plano vazio, falha parcial, ausência de evidência, entrada vazia, URLs inválidas e inicialização da interface. Eles não comprovam a qualidade factual das respostas nem substituem um teste com Ollama e Tavily reais.

## Limitações e solução de problemas

- **Não é totalmente offline:** a geração é local, mas Tavily recebe as consultas e requer internet. O uso da API está sujeito ao plano/créditos da sua conta.
- **Trechos, não leitura integral:** a resposta usa os trechos retornados pela busca. As referências numéricas não garantem que uma afirmação esteja correta. Confira as fontes originais.
- **Modelo indisponível:** compare o nome configurado com `ollama list` e verifique se o Ollama está aberto.
- **Falha no planejador:** confirme o suporte à saída estruturada e teste um modelo com melhor capacidade de seguir JSON. Não há fallback silencioso para respostas inventadas.
- **Sem resultados / busca indisponível:** confira chave, créditos e conexão do Tavily. A aplicação não gera uma resposta factual quando não há fontes utilizáveis.
- **Memória e demora:** o planejador solicita contexto de 16 mil tokens e o escritor de 32 mil. Isso pode exigir bastante RAM/VRAM; reduza consultas/resultados ou ajuste `num_ctx` em `config.py` conforme seu hardware.
- **Privacidade:** `.env` é ignorado pelo Git. Só `.env.example`, sem chave, deve ser publicado. Não habilite tracing externo sem avaliar quais dados serão enviados.
- **Uso local:** esta aplicação não tem autenticação e não foi preparada para exposição pública como serviço. Repositório público não significa aplicativo hospedado.

## Referências

- [LangGraph: workflows e workers](https://docs.langchain.com/oss/python/langgraph/workflows-agents)
- [Integração ChatOllama](https://docs.langchain.com/oss/python/integrations/chat/ollama)
- [Tavily Python SDK](https://docs.tavily.com/sdk/python/reference)
