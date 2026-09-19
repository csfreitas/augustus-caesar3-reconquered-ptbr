# Checklist de QA comunitário

Este roteiro valida a localização PT-BR sem exigir que cada participante conclua as 20 missões. Cada relato deve identificar exatamente o ambiente e o ponto testado para que resultados de instalações diferentes possam ser comparados.

## 1. Preparação segura

- use uma cópia de teste da instalação e da campanha; não altere sua instalação principal sem backup;
- use somente o Reconquered público correspondente ao `fileid=2243`;
- registre a versão ou commit do Augustus e a versão do pacote PT-BR;
- registre sistema operacional, arquitetura, origem do Caesar III (Steam, CD-ROM ou outra distribuição legítima), formato da campanha (diretório ou `.campaign`) e locale selecionado;
- não publique mapas, XMLs canônicos, músicas, vozes, imagens ou outros assets originais do Reconquered/Caesar III;
- não use nem anexe conteúdo obtido em canais privados de Tester.

Para a `v1.0.0-rc.3`, use a rota nativa documentada no [README](README.md) e o
Claudius `26e050892` ou build com suporte equivalente. Não basta a PR #1893
isolada. Instalações RC1/RC2 devem ser removidas com seus próprios instaladores
antes da migração; preserve todos os backups.

## 2. Verificação básica

- [ ] A campanha aparece na lista com o nome esperado.
- [ ] A missão inicia sem crash.
- [ ] O texto exibido está em PT-BR.
- [ ] Acentos e `ç` aparecem corretamente; problemas visuais de caracteres devem ser classificados como **glifo**, não como tradução.
- [ ] O log do Augustus não apresenta erro novo relacionado ao carregamento da localização.
- [ ] Na rota nativa, o log registra o carregamento dos overlays de mensagens e de mídia para a missão.

## 3. Briefing

- [ ] O texto do contexto histórico está completo.
- [ ] A fala PT-BR corresponde ao roteiro aprovado, ainda que o contexto histórico narrado possa ser uma adaptação mais curta.
- [ ] A voz e a música começam sem corte no início.
- [ ] A música permanece audível sem encobrir a voz.
- [ ] O personagem, a intenção e a pronúncia dos nomes estão coerentes.
- [ ] Ao iniciar a missão antes do fim, voz e música param imediatamente e não retornam depois.

## 4. Eventos durante a missão

Para cada evento, anote missão e UID.

- [ ] O texto PT-BR corresponde integralmente ao texto canônico, com apenas as correções históricas aprovadas.
- [ ] Quando houver fala planejada, o áudio correto inicia.
- [ ] Eventos durante o gameplay não recebem uma nova cama musical; permanece a música normal do jogo.
- [ ] Quando houver fanfarra, a fala começa depois dela, sem sobreposição nem corte.
- [ ] Ao fechar a mensagem durante a fanfarra, a fala pendente não começa posteriormente.
- [ ] Ao fechar durante a fala, o áudio para e não vaza para outra mensagem.
- [ ] Entradas deliberadamente sem voz, como `RC02/epithets`, permanecem somente textuais.

## 5. Vitória

- [ ] O texto de vitória está completo em PT-BR.
- [ ] A fala e a música corretas iniciam sem corte.
- [ ] A interpretação transmite satisfação, energia e reconhecimento pela missão cumprida.
- [ ] A música está mais presente que nos primeiros testes, mas não encobre palavras.
- [ ] Ao fechar a tela, voz e música param imediatamente.

A vitória ainda não possui aprovação funcional dentro do jogo e é uma prioridade do QA comunitário.

## 6. Fallback da rota nativa

Estes casos são opcionais e destinados a testadores técnicos. Preserve uma cópia do pacote antes de alterar qualquer fixture.

- [ ] Fala localizada ausente: usa fala canônica e mantém música localizada.
- [ ] Música localizada ausente: mantém fala localizada e usa música canônica.
- [ ] Entrada de mídia ausente: mantém texto PT-BR e usa mídia canônica.
- [ ] Companion inválido ou incompatível: mantém o overlay textual e ignora somente o companion de mídia.
- [ ] O mesmo comportamento ocorre em campanha por diretório e, quando suportado, em pacote `.campaign`.

## 7. Como relatar

Abra ou complemente a [issue comunitária de QA](https://github.com/csfreitas/reconquered-ptbr/issues/1) com:

```text
Pacote PT-BR:
Augustus (versão/commit):
Sistema/arquitetura:
Origem do Caesar III:
Formato da campanha: diretório | .campaign
Missão e UID:
Categoria: tradução | áudio | música | glifo | crash | instalação | outro
Passos para reproduzir:
Resultado esperado:
Resultado observado:
O problema se repete?:
Log relevante:
```

Capturas e pequenos registros produzidos pelo próprio testador são bem-vindos. Antes de anexar, confirme que não contêm assets originais redistribuíveis nem conteúdo privado.

## 8. Critério de aceite comunitário

Uma missão pode ser marcada como funcionalmente validada quando houver evidência do briefing, de todos os eventos alcançáveis e da vitória, com identificação do ambiente. Aprovação em Windows não implica aprovação nativa em Linux, macOS ou outras plataformas; esses resultados devem ser registrados separadamente.

Para a versão 1.0, a ausência de uma campanha completa jogada antes da publicação foi uma decisão explícita do projeto. Falhas descobertas pela comunidade serão corrigidas em candidatos posteriores, sem reclassificar retroativamente áudio não escutado como aprovado.
