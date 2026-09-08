# Auditoria de docs — 2026-09-08

**Veredito:** documentação ampla e organizada, mas com inconsistências materiais que precisam de correção antes de servir como contrato de implementação. Foram encontrados oito achados: três de prioridade alta, quatro de prioridade média e um de prioridade baixa. Este veredito avalia o conteúdo documental atual; não reescreve o PASS histórico do Gauntlet nem constitui uma nova execução desse processo.

**Escopo e método:** inventário dos 39 arquivos Markdown de `docs/`, leitura cruzada dos documentos de especificação e ADRs, comparação da estrutura do blueprint com sua rastreabilidade, análise dos exemplos YAML e dos links locais. Os registros em `.agent/` e `.gauntlet/` foram consultados somente para conferir as alegações de encerramento e integridade. Não houve implementação, execução de ComfyUI, geração de mídia ou alteração dos documentos auditados. Revisão realizada por um único auditor nesta sessão, sem nova revisão independente por subagentes.

**Critérios usados:** consistência entre requisito e exemplo, fonte canônica dos campos, separação entre plano e observação, adequação dos oráculos aos cenários, coerência das fases, atualidade do status e navegabilidade. P1 significa corrigir antes de implementar o contrato afetado; P2 significa corrigir antes de usar a documentação para aceite ou planejamento da etapa afetada; P3 significa manutenção de navegação. As prioridades representam risco da futura implementação, não incidentes observados em produção. Todos os achados abaixo estão abertos.

**AUD-001 — P1: formatos incompatíveis para objetos declarados canônicos.**

Evidência: [contracts.md](../../docs/contracts.md#canonical-names-aliases-and-serialized-enums), linhas 67–83; exemplo de `ShotSpec` na linha 239; [scene-and-continuity.md](../../docs/scene-and-continuity.md#4-narrative-and-shot-graphs), linha 150; [model-adaptation.md](../../docs/model-adaptation.md#1-capability-profile), linha 21.

O mesmo objeto `shot` usa `id`, `duration_s`, `dependency_ids` e `start_state_ref` no contrato, mas `shot_id`, `duration_seconds`, `dependencies` e `in_state_ref` no documento de cena. O `capability_profile` usa `id` e `supports.modes` no contrato, mas `profile_id`, `modes` e `modalities` na adaptação. A tabela normativa de aliases resolve nomes de conceitos, não essas diferenças de campos. Não existe uma transformação documentada entre os formatos.

Impacto: duas implementações que sigam documentos diferentes não trocam os mesmos objetos; um validador baseado no contrato rejeitaria exemplos usados para orientar o planejador. A questão não é a ausência de um JSON Schema executável nesta fase, e sim a falta de uma representação semântica única ou de uma projeção explícita.

Correção proposta: o responsável por `contracts.md` deve escolher os campos canônicos e alinhar os exemplos, ou identificar cada exemplo alternativo como uma projeção e documentar o mapeamento completo. Encerramento: exemplos equivalentes produzem a mesma representação canônica, com IDs, duração, dependências e capacidades preservados; campos antigos são rejeitados ou convertidos por uma regra explícita.

**AUD-002 — P1: algoritmo de continuidade não define a propagação inicial em PLAN_ONLY.**

Evidência: [continuity-engine.md](../../docs/continuity-engine.md#algorithm), linhas 46–64; [contracts.md](../../docs/contracts.md#state-and-transition-invariants), linha 423; [contracts.md](../../docs/contracts.md#status-vocabulary), linhas 53–63.

O algoritmo manda ler o último estado aceito de cada dependência, e a regra de herança permite somente estado aceito. Ao mesmo tempo, o próprio documento admite `START_STATE` planejado, e o ciclo de vida de shot só chega a `ACCEPTED` após geração e revisão. Não está definido como aceitar um estado exclusivamente planejado, como iniciar o primeiro shot ou como selecionar o canal de estado em uma cadeia ainda não gerada.

Reprodução conceitual: solicitar um plano de dois shots dependentes sem artefatos. Para calcular o segundo, não existe saída observada/aceita do primeiro. Seguir literalmente a regra bloqueia o planejamento; promover a saída planejada a aceita sem distinguir o canal compromete a separação entre plano e observação.

Correção proposta: o responsável pela continuidade deve distinguir a travessia de planejamento, que propaga estados planejados validados como plano, da travessia de execução, que usa observações aceitas quando exigidas. Definir também o estado inicial e a invalidação dos dependentes. Encerramento: um caso PLAN_ONLY com dois shots produz o grafo completo sem alegar evidência de mídia; uma observação posterior contraditória invalida somente os estados dependentes apropriados.

**AUD-003 — P1: exemplo de observação aprova uma checagem parcial.**

Evidência: [contracts.md](../../docs/contracts.md#observation-contract-artifactobservation), linhas 399–419; [acceptance.md](../../docs/acceptance.md#gate-execution-contracts), regra de evidência e QG-09.

O exemplo `ArtifactObservation` tem `status: PASS`, mas sua única checagem, QG-09, tem `result: PARTIAL` e contato da mão ambíguo. QG-09 faz parte do `acceptance_ids` do shot ilustrado. Não há waiver nem regra que explique por que o resultado agregado passou. A leitura com PyYAML reproduziu exatamente `{"status": "PASS", "checks": ["PARTIAL"]}`.

Impacto: o exemplo pode ensinar o consumidor a aprovar um artefato cuja obrigação de contato não foi demonstrada. Não é um teste negativo identificado como tal.

Correção proposta: o responsável pelo contrato de observação deve corrigir o exemplo e definir a agregação de resultados obrigatórios, opcionais, não executados e dispensados. Se a intenção era indicar apenas que a inspeção executou, esse estado deve ter um campo distinto do resultado de qualidade. Encerramento: uma checagem obrigatória PARTIAL/FAIL/BLOCKED/NOT_RUN impede PASS global, salvo tratamento de dispensa formalmente especificado.

**AUD-004 — P2: G-004 aponta para oráculos de transferência de objeto, não de conversa.**

Evidência: [failure-and-evals.md](../../docs/failure-and-evals.md#3-evaluation-record), linhas 115–135; [golden-scenarios.md](../../docs/golden-scenarios.md), linha 75; [traceability.md](../../docs/traceability.md#1-blueprint-to-owner-map), linha 27, e seção 2, linha 65.

O registro `eval_G-004_v1` referencia G-004, a conversa entre dois colegas, mas exige `interaction.contact_points` e `state_delta.after.object_owner`. Esses oráculos pertencem ao cenário de transferência G-006. A primeira matriz de rastreabilidade também aponta Dialogue Director para G-006/G-007, enquanto o cenário dedicado é G-004; a matriz consolidada posterior já usa G-004/G-011.

Impacto: a presença dos IDs dá aparência de cobertura, mas uma conversa correta pode falhar por não possuir objeto transferido, e uma conversa com falas trocadas pode não ser rejeitada por esses oráculos.

Correção proposta: os responsáveis por avaliação e rastreabilidade devem alinhar cenário, requisito, oráculo e matrizes. Encerramento: G-004 verifica falante/ouvinte, intervalos, reação e articulação; G-006 verifica contato e posse; versões deliberadamente incorretas de ambos falham pelo motivo correspondente.

**AUD-005 — P2: limiares de duração são simultaneamente obrigatórios e apenas orientativos.**

Evidência: [requirements.md](../../docs/requirements.md#complexity-and-narrative-planning), linha 60, e [requirements.md](../../docs/requirements.md#long-form-and-modes), linha 125; [phase-0-report.md](../../docs/phase-0-report.md#modified), linha 48; [architecture.md](../../docs/architecture.md#planning-depth), linha 151.

R-PLAN-02 diz que os limiares são apenas padrões orientativos. R-LONG-01 impõe timeline acima de 30 segundos e Scene Bible, grafo e propagação acima de 45 segundos com MUST. O relatório diz que os limiares foram convertidos em sinais orientativos, enquanto a arquitetura admite panorama longo com menor profundidade.

Impacto: um panorama estático de 60 segundos pode receber estruturas obrigatórias ou ser simplificado, dependendo do documento usado. A exceção não está definida em termos normativos.

Correção proposta: o responsável pelos requisitos deve esclarecer se há mínimos obrigatórios por duração, com complexidade apenas elevando a profundidade, ou exceções explícitas e verificáveis. Encerramento: casos de 30, 31, 45, 46 e 60 segundos, inclusive estáticos e de alto risco, recebem decisões compatíveis entre requisitos, arquitetura, cenários e relatório.

**AUD-006 — P2: bloqueadores da Fase 1 exigem evidências previstas para fases posteriores.**

Evidência: [open-questions.md](../../docs/open-questions.md#blocking-before-phase-1-implementation), linhas 7–14; [roadmap.md](../../docs/roadmap.md#phase-1--skill-skeleton), linhas 25–55; [safety-boundaries.md](../../docs/safety-boundaries.md#open-questions), linha 78.

OQ-B-001 a OQ-B-004 exigem runtime/hardware, oráculos de mídia, autoridade de upload e perfis confirmados antes da implementação da Fase 1. O roadmap define a Fase 1 como esqueleto PLAN_ONLY, perfis na Fase 3 e integração opcional na Fase 4. O documento de segurança diz expressamente que decisões de política externa são necessárias antes da execução externa, não antes do design PLAN_ONLY.

Impacto: trabalho local de esqueleto pode ficar condicionado a hardware, consentimentos e probes que não utiliza. A possibilidade de aceitar explicitamente bloqueadores evita um impasse absoluto, mas obriga a abrir exceção a uma classificação documental imprecisa.

Correção proposta: o responsável pelo roadmap deve separar bloqueadores do esqueleto, da ativação de um perfil, da execução externa e do aceite de mídia. Encerramento: o mesmo pedido de esqueleto PLAN_ONLY tem os mesmos pré-requisitos no índice, roadmap, relatório e fila de decisões; probes e autorizações continuam obrigatórios na etapa em que são necessários.

**AUD-007 — P2: status de entrega não reflete o encerramento registrado.**

Evidência: [00-index.md](../../docs/00-index.md#status), linha 5; [README.md](../../docs/README.md#status), linha 9; [phase-0-report.md](../../docs/phase-0-report.md#review-evidence-and-repair-record), linhas 104–109; `.gauntlet/state.json` e último evento de `.gauntlet/history.jsonl`.

O índice descreve FINAL_CANDIDATE pendente de finish; o relatório ainda pede novo crítico final e termina descrevendo C6. O controle registra `status: FINISHED`, `phase: STOP` e evento `finish` com `verdict: PASS` em 2026-09-08T03:46:54Z, com C8 como crítico final aprovado. Os hashes dos 39 documentos coincidem com o inventário armazenado, portanto não há indicação de que a discrepância seja causada por edição posterior dos documentos nesta sessão.

Impacto: quem consulta apenas `docs/` não consegue determinar se o processo terminou e pode solicitar revisão ou conclusão já registradas. O histórico de aprovação existe; o achado é a apresentação desatualizada, não ausência dessa aprovação.

Correção proposta: o responsável pelo handoff deve tornar a indicação de status compatível com o controle e separar claramente relato histórico de estado atual. Como os documentos integram o fingerprint, uma atualização deve receber nova verificação aplicável; não se deve reescrever o histórico anterior para parecer que aprovou outro conteúdo. Encerramento: navegação e relatório permitem descobrir o encerramento vigente e suas limitações sem anunciar revisão pendente inexistente.

**AUD-008 — P3: as 12 entradas do sumário de cenários não correspondem às âncoras de GitHub.**

Evidência: [golden-scenarios.md](../../docs/golden-scenarios.md), linhas 27–40 e demais títulos G-002 a G-012.

O sumário usa `#g-001-simple-cinematic-portrait`, mas o título é `G-001 — Simple cinematic portrait`. Pela convenção de anchors do GitHub, a remoção do travessão e a conversão de cada espaço deixam `g-001--simple-cinematic-portrait`, com dois hífens. O padrão se repete nas 12 entradas; não existem âncoras explícitas que forneçam os destinos escritos no sumário.

Impacto: os atalhos falham em renderização compatível com GitHub. A constatação é específica a essa convenção: renderizadores que colapsam hífens podem se comportar de outra forma. A auditoria executou uma extração estática de slugs, não um navegador contra uma publicação GitHub deste projeto.

Correção proposta: alinhar os links ao renderizador escolhido ou usar âncoras explícitas estáveis. Encerramento: os 12 atalhos alcançam suas seções no renderizador adotado, com uma verificação que preserve espaços adjacentes à pontuação removida.

**Verificações executadas e resultados.**

| Verificação | Resultado | Limite da evidência |
|---|---|---|
| Inventário com `rg --files docs` e contagem de linhas | 39 Markdown; 5.888 linhas; 10 ADRs | Presença não prova completude semântica |
| Extração de cercas YAML e `yaml.safe_load` | 43 blocos; zero erros de sintaxe | Não valida schema nem invariantes; AUD-001/AUD-003 mostram a diferença |
| Links Markdown locais fora de blocos de código | 370 referências; zero destinos de arquivo ausentes; 12 divergências de âncora | Não verifica todos os URIs em strings YAML, nem disponibilidade de todos os links externos |
| IDs R-* e NFR-* extraídos de requirements e comparados com traceability | 66 R-* e 13 NFR-* presentes | Cobertura textual não prova que o oráculo é adequado; AUD-004 |
| Objetos YAML selecionados inspecionados após parse | Formatos divergentes de shot/profile e PASS com PARTIAL reproduzidos | Inspeção de exemplos, sem runtime implementado |
| SHA-256 dos documentos versus inventário de `.gauntlet/state.json` | Nenhuma divergência nos 39 documentos | Comparação com baseline local, não autenticação independente de seu histórico |
| SHA-256 de BLUEPRINT.md | `62c04a55fe991a8f094db47d661ab6fa70fbe20e26f0adbfda402eba78f6fc1d`, igual ao registro local | O anexo original não está disponível para provar igualdade independente com a origem |
| Controle de encerramento | Evento finish/PASS e estado FINISHED presentes | Aprovação histórica consultada, não reexecutada |
| `git status --short` | Indisponível: workspace não reconhecido como repositório Git | Integridade aferida pelos hashes locais |

**Amostragem de fontes externas.** O [tutorial oficial Wan2.2](https://docs.comfy.org/tutorials/video/wan/wan2_2) foi reaberto e mantém as famílias T2V/I2V/TI2V/FLF descritas no registro, sem comprovar instalação local. O [registro arXiv 2412.07750](https://arxiv.org/abs/2412.07750) confirma a discussão de consistência entre shots, mas a versão atual tem o título *Motion by Queries: Identity-Motion Trade-offs in Text-to-Video Generation*: a bibliografia deveria indicar a versão à qual seu título se refere. Para [LongDiff](https://openaccess.thecvf.com/content/CVPR2025/html/Li_LongDiff_Training-Free_Long_Video_Generation_in_One_Go_CVPR_2025_paper.html), a página oficial confirma os riscos de consistência temporal/detalhe e a proposta de geração longa em uma passagem; isso não basta, por si só, para provar a preferência arquitetural por um grafo de shots. O acesso direto ao PDF retornou 403 nesta consulta; o registro oficial e trechos indexados estavam acessíveis. A amostragem não certifica todo o catálogo externo nem todas as inferências de `research.md`.

**Pontos bem sustentados:** responsabilidade explícita dos documentos, separação conceitual entre intenção/plano/artefato, perfis ainda PROPOSED sem alegação de execução, cenários positivos e adversariais identificados, e manutenção da fronteira documental da Fase 0. Ausência de mídia gerada ou ComfyUI não foi tratada como defeito dessa fase.

**Próxima ação:** corrigir primeiro AUD-001 a AUD-003 nos contratos e exemplos relacionados; depois reconciliar avaliação, duração, fases, status e navegação. Reexecutar as verificações estruturais e os casos positivos/negativos afetados antes de aceitar a documentação como base de implementação. Nenhuma dessas correções foi aplicada nesta auditoria.
