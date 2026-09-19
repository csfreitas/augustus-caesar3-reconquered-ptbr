# Cobertura de tradução — v1.0.0-rc.3, 19/09/2026

Estado: **pré-release técnica; não instalada no perfil principal durante esta preparação**.
Esta cobertura não significa aprovação linguística/visual das 20 missões.

## Conteúdo preservado e acrescentado

| Superfície | Cobertura verificada | Limite |
|---|---|---|
| Mensagens personalizadas | 198/198 UIDs e campos textuais; corrigidos resíduos ingleses, destaques e 19 referências do ícone de instruções | Presença de campo não prova tradução completa; revisão de sentido e contexto em jogo continua pendente |
| Falas e músicas | Referências às 197 falas e dez músicas existentes preservadas | Nenhuma regravação ou nova validação auditiva nesta rodada |
| Seleção de campanha/missões/cenários | 62 campos em `campaign.xml`: 2 da campanha, 20 títulos, 20 nomes e 20 descrições | Requer o suporte integrado no Claudius `26e050892` ou equivalente |
| Identidades alternativas de cenário | Sete aliases em mensagens e mídia, mais seis imperiais: 20 cópias geradas | Não renomeia cenários, XMLs canônicos ou saves |
| Nomes personalizados do mapa imperial | 12 grafias localizadas em 54 ocorrências nas 20 missões; 26 arquivos incluindo seis aliases SAVE | 21 grafias mantidas conforme o original PT-BR, incluindo três conflitos agora resolvidos; 85 outras grafias aguardam revisão; requer o suporte integrado no Claudius `26e050892` ou equivalente |
| Lista esquerda de campanhas | O build integrado permite exibir o nome localizado | Identidade do diretório/pacote preservada; não renomear a campanha. QA visual integral da RC3 ainda pendente |

Os aliases corrigem a diferença entre nomes usados pelos arquivos de mensagens e
os caminhos de cenário do `Settings.xml` público:

| Origem dos overlays | Nome procurado pelo cenário |
|---|---|
| RC08 Mediolanum | RC08 Mediolanum SAVE |
| RC10 Carthago | RC10 Carthago SAVE |
| RC11 Tarsus | RC11 Tarsus SAVE |
| RC13 Valentia | RC13 Valencia |
| RC14 Lutetia | RC14 Lutetia SAVE |
| RC17 Londinium | RC17 Londinium SAVE |
| RC19 Lindum | RC19 Lindum SAVE |

O perfil de QA já tinha aliases preparados localmente; faltava transportá-los ao
pacote. As cópias são byte-idênticas aos overlays de origem deste repositório e
verificadas por `generate_scenario_aliases.py --check`.

## Decisões de tradução

- Identidades `file`, `first-scenario`, UIDs, datas, eras e progressão preservadas.
- Nomes seguem a terminologia existente: Óstia, Brundisium, Capua, Tarentum,
  Siracusa, Carthago, Caesarea, entre outros. Não foi reaplicada uma nova política
  de exônimos a mensagens já aprovadas.
- Os títulos da seleção foram traduzidos a partir dos próprios títulos canônicos;
  não foram substituídos indiscriminadamente pelo título do briefing, que pode ter
  outro sentido.
- Separador dos nomes usa hífen ASCII. Travessão U+2014 é codificável em Windows-1252,
  mas não possui glifo na fonte padrão/PT; codificação válida não prova exibição.
- Continuação de 19/09, incluindo terminologia: alterações pontuais em 93 campos
  das mensagens, preservando os 198 UIDs, a estrutura dos campos, números e
  referências de voz/música. A auditoria
  encontrou 60 ocorrências de palavras inglesas na lista de regressão e 195
  marcações `@` fora do padrão seguro; ambas as contagens foram zeradas.
- Nomes imperiais acrescentados conforme terminologia existente: Roma, Óstia,
  Crotona, Veios, Siracusa, Mileto, Tarso, Valentia e Damasco. As três traduções
  preparadas em 18/09 continuam: Ruínas de Cartago, Extremo Oriente e Muralha de Adriano.

## Lacunas que exigem continuação

1. **Mapa imperial:** 54 ocorrências já estão preparadas em
   `localization/pt-BR/empire/`, com aliases dos seis cenários SAVE. Os pares
   ID/nome dos seis saves do perfil QA foram comparados com os MAPX e coincidem;
   isso não comprova compatibilidade com versões futuras. O suporte do motor usa
   getters exclusivos de apresentação e só aplica a tradução quando o nome-fonte
   confere; nomes canônicos usados na lógica de comércio e seleção não são alterados.
   Os conflitos `Lutetia`/`Lutécia`, `Massilia`/`Massília` e `Pergamum`/`Pérgamo`
   foram resolvidos pela regra aprovada: conservar o original Caesar III PT-BR.
   Também foram alinhados Valentia e Caesarea. Utica permanece uma decisão
   editorial provisória, não uma grafia comprovada no arquivo original.
   Ver [TERMINOLOGY.md](TERMINOLOGY.md), incluindo edifícios e limites de áudio.
   Variantes como `Syacusae` e `Tarsum` continuam canônicas até confirmação.
2. **Referências de imagens:** corrigidas as 19 referências do ícone de instruções
   para `c3_instructions_icon.png`, propagadas aos aliases. `deno.png` de RC03
   continua ausente no perfil QA e nas cópias locais examinadas em
   `references/zip-baseline` e `references/incoming`; exige identificação do
   asset correto. A referência já existe na fonte inglesa de RC03. Não foi
   substituída por `coins.png`, usado separadamente em RC13.
3. **Texto em imagens/vídeos:** `coins.png` foi inspecionada em 19/09 e contém
   inglês desenhado (título e descrições das moedas); ainda não foi localizada.
   Não houve inventário visual exaustivo. As três
   amostras inspecionadas (`workshop.png`, `Proper_Roman_Colony.png` e
   `c3_instructions_icon.png`) são gráficos sem texto a traduzir. Não presumir que
   isso vale para todos os assets; não redistribuir conteúdo original.
4. **Glifos e layout:** validação visual permanece necessária; QA-FONT-01 segue na
   trilha independente da PR #1906. O candidato precisa reunir as correções antes
   do QA detalhado das missões pelo usuário.

Não foi comprovada uma lacuna de variáveis textuais no HUD deste baseline: os
20 mapas inventariados são versão 18, sem o campo de apresentação introduzido
posteriormente. Isso não equivale a suporte de tradução para mapas futuros.

## Validação reproduzível

Rodada atual de 19/09: **20 testes Python aprovados**, 20 aliases e 20 companions
válidos. Pacote com 82 arquivos de localização. Auditoria contra o Git anterior:
198 UIDs e todos os números preservados nos 93 campos alterados; única troca de
referência gráfica foi o ícone de instruções. Novas regressões cobrem palavras
destacadas, números que poderiam ser consumidos como links e nomes imperiais com
guarda de fonte/ID. Inclui regressões de terminologia e da distinção entre templos
grandes e Santuários em RC20. A instalação/desinstalação testada continua sintética.

```sh
python3 generate_native_media_overlays.py --check
python3 generate_scenario_aliases.py --check
python3 -m unittest discover -s tests -v
```

Resultados de 18/09, anteriores à continuação textual: dez testes Python aprovados;
20 companions de origem e 14 aliases conferidos. A regressão de metadados falhava antes pela ausência do
arquivo e por rejeição do novo payload pelo instalador; passou após as correções.
O teste de instalação usa arquivos sintéticos, verifica falha sem gravações quando
faltam metadados e restaura um overlay anterior sem modificar Settings, save ou XML
canônico. Não instalou o pacote no perfil principal.

Validação adicional local com os módulos C reais de campanha, XML, encoding e ZIP:
dois casos (pasta e `.campaign`), 422 verificações, zero falhas. Conferiu os 62
campos, 20 missões/cenários e identidades preservadas. Usa cenários sintéticos e
não demonstra renderização, leitura completa dos saves reais, áudio ou gameplay.

A preparação da RC3 acrescenta testes de segurança e recuperação do instalador.
Os resultados finais ficam registrados nas notas da release e no CI do repositório;
as contagens acima descrevem a rodada de conteúdo anterior a essas correções.
O QA visual/auditivo integral deste candidato ainda não foi executado.
Esta RC3 usa exclusivamente a rota nativa; os wrappers também chamam essa rota.
O módulo legado permanece somente como dependência compartilhada e não deve ser
usado para instalar o payload ampliado.
