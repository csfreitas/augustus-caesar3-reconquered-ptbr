# Reconquered PT-BR — v1.0.0-rc.3

Pré-release comunitária da tradução brasileira de 20 missões do Reconquered.
**É um candidato técnico: a revisão completa das missões dentro do jogo ainda
está pendente. Não é uma versão oficial do Reconquered ou do Augustus.**

## For translators working on other languages

See the **[English translator guide](docs/TRANSLATORS_GUIDE.md)** for compatible
Claudius downloads, locale configuration, text/metadata/imperial-name XML,
narration and music, packaging, installation, removal and validation.
The PT-BR installer below is not a generic installer for other languages.

## Compatibilidade obrigatória

Use **Claudius no commit `26e0508921bcb1c01166fc683a59fb1917fa2426` ou um
build que incorpore suporte equivalente** a mensagens localizadas, mídia nativa,
metadados de campanha/cenários e nomes imperiais de apresentação.
O commit de referência está no [fork do Augustus](https://github.com/csfreitas/augustus/commit/26e0508921bcb1c01166fc683a59fb1917fa2426).

Download compatível para Windows x64: [Claudius v0.1.0-alpha.2](https://github.com/csfreitas/augustus/releases/tag/claudius-v0.1.0-alpha.2).
O ZIP Windows inclui os assets correspondentes; leia os pré-requisitos e avisos
de perfil compartilhado antes de executar. Extrair em outra pasta não isola os saves.

A PR #1893 isolada e o Claudius `v0.1.0-alpha.1` não bastam para o conjunto desta
RC3. Não foi estabelecida compatibilidade completa com o Augustus estável.
Este pacote não inclui o executável do jogo.

Também são necessários:

- Python **3.11 ou superior** para executar o instalador;
- campanha pública Reconquered correspondente ao baseline `fileid=2243` e aos
  hashes canônicos registrados nos planos deste pacote;
- os quatro volumes abaixo, extraídos juntos;
- cópia de teste da campanha e espaço para os áudios, staging e backups.

Reserve pelo menos 4 GB para pacote extraído, arquivos instalados e cópia de
recuperação, além do espaço dos arquivos originais a preservar e dos ZIPs.
Não se presume compatibilidade com versões futuras do Reconquered. A origem do
Caesar III (CD-ROM, Steam, GOG etc.) não substitui a validação do baseline e do
build. Outras plataformas ainda precisam de validação dentro do jogo.

## O que mudou desde a RC2

- 62 campos de apresentação: nome/descrição da campanha e títulos, nomes e
  descrições das 20 missões/cenários;
- aliases para nomes de cenário `SAVE` e `RC13 Valencia`, sem renomear mapas ou saves;
- 54 ocorrências de nomes no mapa imperial localizadas, com guarda de ID/nome-fonte;
- correções de resíduos ingleses, terminologia, destaques e ícones das instruções;
- instalação nativa que **não modifica os XMLs canônicos** da campanha.

São **82 XMLs próprios de localização**, 198 mensagens, **197 falas e dez músicas**.
As gravações existentes foram preservadas; não houve regravação nesta RC3.
Detalhes e lacunas: [cobertura](TRANSLATION_COVERAGE.md),
[terminologia](TERMINOLOGY.md) e [limitações conhecidas](KNOWN_ISSUES.md).

## Downloads e preparação

Na [release RC3](https://github.com/csfreitas/augustus-caesar3-reconquered-ptbr/releases/tag/v1.0.0-rc.3),
baixe e extraia os quatro ZIPs na **mesma pasta**:

1. `Reconquered-PTBR-v1.0.0-rc.3-core.zip`;
2. `Reconquered-PTBR-v1.0.0-rc.3-music.zip`;
3. `Reconquered-PTBR-v1.0.0-rc.3-voices-RC01-RC10.zip`;
4. `Reconquered-PTBR-v1.0.0-rc.3-voices-RC11-RC20.zip`.

Todos usam a raiz `Reconquered-PTBR-v1.0.0-rc.3`. Os downloads automáticos
**Source code** do GitHub não contêm os áudios e não formam o pacote instalável.
`CHECKSUMS.sha256` permite conferir os ZIPs; `RELEASE_MANIFEST.json` registra os
arquivos distribuídos. O instalador também valida os hashes de todos os áudios.

No Windows, escolha caminhos curtos tanto para o pacote quanto para a cópia da
campanha. Caminhos excessivamente longos são recusados; o instalador não altera
as configurações globais do Windows. Não aponte inicialmente para o perfil principal.

## Instalação nativa

Feche o jogo antes de instalar ou remover o pacote. Execute uma operação por vez,
sem outro instalador/desinstalador ativo para a mesma campanha.
Abra um terminal dentro da pasta extraída. Windows:

```powershell
.\Install-Reconquered-PTBR-Media.ps1 -CampaignDirectory "C:\C3-QA\Reconquered Campaign"
```

Alternativa direta com Python 3.11+, inclusive no Linux/macOS:

```sh
python3 reconquered_ptbr_native_media.py install "/caminho/para/Reconquered Campaign"
python3 reconquered_ptbr_native_media.py verify "/caminho/para/Reconquered Campaign"
```

No Windows, pode usar `py -3` em lugar de `python3` se o Python Launcher estiver
instalado. Confira a versão selecionada antes de executar.
O atalho Unix `sh install-reconquered-ptbr-media.sh "/caminho/para/Reconquered Campaign"`
chama o mesmo instalador nativo.

O instalador verifica o baseline e o payload antes de instalar localização e
áudios próprios. Mantém backup dos arquivos substituídos e registro de recuperação.
Preserve esses registros e a pasta do pacote enquanto a instalação estiver ativa.
A cópia de recuperação dos áudios ocupa aproximadamente 1 GB e é mantida mesmo
após a desinstalação; não a apague enquanto precisar recuperar uma operação.
Selecione português brasileiro no jogo.

## Desinstalação e recuperação

```powershell
.\Uninstall-Reconquered-PTBR-Media.ps1 -CampaignDirectory "C:\C3-QA\Reconquered Campaign"
```

```sh
python3 reconquered_ptbr_native_media.py uninstall "/caminho/para/Reconquered Campaign"
```

Arquivos anteriores são restaurados e os arquivos acrescentados pelo pacote são
removidos. Alterações posteriores do usuário não devem ser sobrescritas: a
operação recusa divergências para permitir inspeção. Não apague os manifestos ou
backups para contornar uma recusa.

Se uma operação interrompida deixar registro pendente, preserve tudo. Confirme
primeiro que o jogo e todos os instaladores/desinstaladores estão fechados; a
recuperação não detecta processos ativos. Só então use a recuperação explícita:

```sh
python3 reconquered_ptbr_native_media.py recover "/caminho/para/Reconquered Campaign"
```

## Migração de RC1/RC2 ou instalação experimental anterior

Não extraia a RC3 por cima da pasta do instalador antigo. Faça backup e mantenha
o pacote antigo disponível. **Primeiro desinstale usando o pacote e a mesma
família de instalador que realizou a instalação anterior**: PowerShell com seu
desinstalador PowerShell, ou Python com seu desinstalador Python. Os formatos de
manifesto legados são diferentes. A rota antiga podia modificar os XMLs canônicos;
a desinstalação precisa restaurá-los a partir de seus próprios backups.

Uma instalação nativa experimental anterior também deve ser removida com o
instalador correspondente antes da RC3. Em caso de divergência, pare e preserve
os arquivos para análise. Não remova manualmente os registros de instalação.

A RC3 recusa instalações anteriores ainda ativas e baseline divergente. Somente
depois da restauração e validação, instale a RC3 pela rota nativa acima.

## Escopo e contribuição

Não distribuímos mapas, saves, perfis, XMLs canônicos, imagens, vídeos ou áudio
original do Reconquered/Caesar III. Veja [LICENSE-NOTICE.md](LICENSE-NOTICE.md).
O módulo `reconquered_ptbr_media.py` acompanha o pacote como dependência do
instalador; **não use sua rota legada para instalar a RC3**.

Testes automatizados e validação de hashes não substituem a revisão visual,
auditiva e contextual das 20 missões. Use o [checklist de QA](COMMUNITY_QA_CHECKLIST.md).
O repositório mantém suas próprias suítes e CI; os ZIPs de consumo não precisam
dos testes ou geradores, exceto módulos importados pelo instalador. Os áudios são
distribuídos apenas como assets da release.
Contribuições: [CONTRIBUTING.md](https://github.com/csfreitas/augustus-caesar3-reconquered-ptbr/blob/main/CONTRIBUTING.md).
