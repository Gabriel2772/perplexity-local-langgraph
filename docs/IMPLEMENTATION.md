# Escopo e verificação

## Escopo

Completar o esboço com o fluxo indicado no vídeo: planejamento, pesquisa paralela e compilação. Manter Ollama e Tavily, acrescentar Streamlit e preservar `garph.py` como import de compatibilidade. Não publicar `.env`, não afirmar equivalência linha a linha com material não recuperado e não criar funcionalidades fora do projeto de pesquisa.

## Plano de execução

- [x] Inspecionar arquivos e identificar referência e conta GitHub.
- [x] Escrever cenários de teste para o fluxo e observar ausência da implementação.
- [x] Implementar estados, prompts e grafo com dependências injetáveis.
- [x] Criar configuração e interface, incluindo mensagens de erro e download.
- [x] Documentar comandos PowerShell, limitações e atribuição.
- [x] Verificar testes, instalação e conteúdo a publicar.


## Critérios

Não perder resultados de workers paralelos; não gerar síntese sem evidência; limitar consultas e resultados; manter falhas de pesquisa visíveis sem imprimir exceções com credenciais; criar serviços apenas ao pesquisar; manter `.env` fora do commit. Testes externos simulados não devem ser descritos como validação real de inferência.

## Resultado da verificação

Instalação pelo Poetry, poetry check, nove testes e Ruff concluídos com sucesso em Python 3.12. Construção dos clientes ChatOllama e Tavily verificada sem chamadas externas.

A chave Tavily enviada estava vazia e o servidor Ollama do usuário não está disponível neste ambiente. Inferência real e busca autenticada não foram executadas. O ambiente de teste usa proxy SOCKS e precisou de socksio para construir os clientes; isso não é necessário em uma instalação comum sem esse proxy.
