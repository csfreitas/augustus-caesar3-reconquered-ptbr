# Como contribuir

Obrigado por testar a localização brasileira do Reconquered.

## Relatos de teste

Siga o [checklist de QA comunitário](COMMUNITY_QA_CHECKLIST.md). Abra uma issue e informe missão, UID/evento, versão do Augustus, origem da instalação, locale, resultado esperado e resultado observado. Screenshots são bem-vindos; não anexe assets originais da campanha.

## Sugestões de tradução

- preserve intenção e contexto do texto público atual;
- diferencie texto oficial, comentário público do autor e dicas gerais de Augustus;
- use o Caesar III original PT-BR como referência terminológica;
- cidades presentes no `c3.eng` devem manter a grafia ali usada, como `Brundisium`, `Capua` e `Tarentum`;
- sinalize correções históricas separadamente;
- não altere decisões aprovadas silenciosamente.

## Conteúdo proibido

- material de canais privados de Tester;
- mapas, músicas, imagens, vídeos ou vozes originais do Reconquered;
- arquivos completos do Caesar III;
- imitação deliberada de voz real existente.

Ao enviar uma contribuição, você declara que possui direito de fornecê-la ao projeto para avaliação e inclusão. A licença definitiva do projeto ainda será definida antes de uma versão estável.

## Companions de mídia nativa

Não edite manualmente os 20 arquivos em `Reconquered Campaign/localization/pt-BR/media/`. Altere os planos aprovados e execute:

```sh
python3 generate_native_media_overlays.py
python3 generate_native_media_overlays.py --check
python3 generate_scenario_aliases.py
python3 generate_scenario_aliases.py --check
```

Cada UID precisa existir no overlay textual correspondente. Somente nomes simples de arquivo são aceitos; diretórios, prefixos de drive e travessia de caminho são proibidos. A mídia deve ser criação própria ou possuir autorização de distribuição comprovável.

Os sete aliases de cenário em `messages/` e `media/` também são gerados. Edite o
overlay de origem e regenere os aliases; não mantenha traduções independentes das
mesmas mensagens. `SCENARIO_ALIASES` documenta apenas as diferenças de nomes da
campanha suportada, sem mudar arquivos canônicos ou lógica no Augustus.

Os seis aliases imperiais `SAVE` também são cópias dos overlays de origem. O
overlay imperial de RC13 já usa a chave `Valencia` diretamente. Preserve IDs e
nomes-fonte de `empire/`: somente o conteúdo de `<name>` é apresentação traduzida.

## Destaques nos textos

Use `@0palavra` para destacar palavras, inclusive termos latinos. Uma quantidade
destacada precisa de espaço, por exemplo `@0 32`: `@032` seria interpretado como
ID de link e consumiria o número. Preserve os comandos `@H`, `@L`, `@P`, `@G26`
e `@G[nome.png]`. Prefixos como `@Honorum` ou `@Geoponica` colidem com comandos
de título/imagem; use `@0Honorum` e `@0Geoponica`.

Os testes de mensagens detectam essas colisões, resíduos ingleses conhecidos e
a referência antiga incorreta ao ícone de instruções. Não são um classificador
completo de idioma nem substituem a revisão linguística.

## Metadados de apresentação

Edite `Reconquered Campaign/localization/pt-BR/campaign.xml` para títulos, nomes e
descrições. Preserve literalmente as chaves `first-scenario` e `file`, inclusive
os sufixos `SAVE` e a grafia `RC13 Valencia`: não são texto a traduzir. Nomes
exibidos podem usar a terminologia aprovada sem alterar essas identidades.

Execute `python3 -m unittest discover -s tests -v` e os dois geradores com `--check`.
Os testes estruturais não substituem inspeção das fontes, layout e contexto em jogo.
