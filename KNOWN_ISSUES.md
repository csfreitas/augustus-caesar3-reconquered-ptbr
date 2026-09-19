# Limitações conhecidas — v1.0.0-rc.3

- Requer Claudius `26e0508921bcb1c01166fc683a59fb1917fa2426` ou suporte equivalente
  conjunto a mensagens, mídia nativa, metadados e nomes imperiais. Não basta a
  PR #1893 isolada nem o Claudius alpha.1; não inclui executável.
- O instalador aceita somente os hashes do baseline público Reconquered
  `fileid=2243`. Uma atualização da campanha exige reconciliação, não simples
  troca dos hashes para contornar a validação.
- RC1/RC2 e instalações experimentais devem ser removidas com o instalador da
  mesma versão/família, preservando os backups. A RC3 usa somente a rota nativa.
- No Windows, use caminhos curtos. Não alteramos o registro global para habilitar
  caminhos longos. Uma recusa de segurança deve ser investigada antes de repetir.
- QA integral das 20 missões continua pendente. Aprovação de testes automatizados
  não comprova gameplay, layout, glifos nem compatibilidade entre distribuições.
- O QA histórico Windows SDL2 cobriu seleção, briefing, eventos RC01, interrupção
  de voz e fanfarra e campanha `.campaign`. Não equivale a uma nova aprovação
  integral desta RC3. Vitória e outras plataformas permanecem no QA comunitário.
- `Ç`, `Ã` e `Õ` podem apresentar problemas em fontes/telas específicas;
  QA-FONT-01 continua separado da revisão dos textos.
- `deno.png`, referenciada pela fonte inglesa de RC03, não foi encontrada no
  baseline local examinado. Não foi substituída por outra imagem arbitrariamente.
- `coins.png` em RC13 contém inglês desenhado. Não foi localizada nem é
  redistribuída por este pacote. O inventário visual dos assets não é exaustivo.
- Foram localizadas 54 ocorrências imperiais; 85 outras grafias ainda aguardam
  revisão editorial. Veja [TERMINOLOGY.md](TERMINOLOGY.md).
- Falas e músicas não foram regravadas. Ajustes recentes de terminologia podem
  divergir do áudio existente; isso requer revisão auditiva, não está aprovado
  automaticamente pelo hash. `RC02/epithets` é deliberadamente apenas texto.
- As músicas são derivadas das prévias MP3 fornecidas pela EasyMusic e entregues
  em WAV após ajuste de nível; uma futura fonte WAV oficial poderá substituí-las.
- A instalação deve ser preparada em computador com Python. Não foi validado o
  uso desta RC3 em Android, Nintendo Switch ou PS Vita.

Cobertura e evidências históricas: [TRANSLATION_COVERAGE.md](TRANSLATION_COVERAGE.md).
Para novos relatos, use [COMMUNITY_QA_CHECKLIST.md](COMMUNITY_QA_CHECKLIST.md).
