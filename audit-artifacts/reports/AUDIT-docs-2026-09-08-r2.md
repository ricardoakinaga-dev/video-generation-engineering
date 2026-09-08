# Auditoria de docs — segunda revisão — 2026-09-08

**Veredito:** as correções melhoraram a documentação, mas a declaração de encerramento integral dos oito achados ainda é excessiva. Quatro achados anteriores estão corrigidos no escopo observado, quatro têm resíduos, e um novo problema foi reproduzido. Permanecem cinco achados abertos: um P1, três P2 e um P3. Não foi observado incidente de runtime; os riscos são de especificação e da futura implementação.

Esta revisão sucede o [relatório original](AUDIT-docs-2026-09-08.md), que permanece preservado. Foram inventariados 39 documentos, dos quais 18 diferem do inventário histórico do Gauntlet. A auditoria combina leitura cruzada das correções e de seus documentos dependentes, verificações estruturais de toda a pasta e consulta dos registros de remediação em `.agent/verification.jsonl`. Não houve modificação de `docs/` ou dos registros históricos, implementação da Skill, execução de ComfyUI ou nova revisão por subagentes.

**Situação dos achados anteriores.** “Corrigido” nesta tabela significa confirmado por inspeção documental ou pelo procedimento indicado, não aprovação de uma implementação ainda inexistente.

| ID | Situação nesta revisão | Evidência de fechamento ou resíduo |
|---|---|---|
| AUD-001 | PARCIAL — P1 | Os campos principais de shot/profile foram alinhados; formatos internos, identidade da revisão do perfil e posição de `omissions` ainda divergem. |
| AUD-002 | PARCIAL — P2 | A inicialização e a travessia PLAN_ONLY foram especificadas; o pattern de herança permanece incompatível e o algoritmo mistura resultado de QA com ciclo de vida do shot. |
| AUD-003 | CORRIGIDO no caso reportado | O exemplo agora contém agregado PARTIAL e checagem obrigatória PARTIAL; há regra que impede PASS para checagem obrigatória incompleta. |
| AUD-004 | CORRIGIDO no defeito central dos oráculos | G-004 agora verifica conversa e G-006 verifica contato/posse; o mapeamento de Dialogue Director foi corrigido. Há limpeza editorial residual indicada ao fim deste relatório. |
| AUD-005 | PARCIAL — P3 | MUST versus orientativo foi reconciliado; faltam intervalos coerentes para durações fracionárias. A prioridade caiu porque a regra canônica agora é clara. |
| AUD-006 | PARCIAL — P2 | A fila e o roadmap separam corretamente as fases, mas os documentos de adaptação e execução ainda remetem probes/runtime à Fase 1. |
| AUD-007 | CORRIGIDO no defeito de status histórico | README, índice e relatório reconhecem o finish anterior e sua obsolescência para o conteúdo modificado. Existem registros de remediação; o alcance de seu PASS é revisto pelos achados atuais. |
| AUD-008 | CORRIGIDO | As 12 âncoras foram ajustadas; a checagem atual dos links Markdown locais não encontrou destinos ausentes. |

**AUD-001 — P1 — As representações canônicas continuam divergentes em campos internos.**

Evidências: `docs/contracts.md:338`, `:352`, `:355`, `:469` e `:482`; `docs/model-adaptation.md:23`, `:41`, `:47`, `:79` e `:247`. [Contrato](../../docs/contracts.md#capability-contract-capabilityprofile) e [adaptação](../../docs/model-adaptation.md#1-capability-profile).

Ambos os perfis agora têm o mesmo `id: comfyui-wan22-native-v1` e `profile_revision: 1`, mas diferem em estrutura e conteúdo:

| Propriedade | contracts.md | model-adaptation.md |
|---|---|---|
| Modo TI2V na mesma revisão | Ausente | Presente |
| Limite de frames | `limits.frames`, objeto com `rule` | `limits.frame_count`, string |
| Evidência de camera_controls | Campo `evidence: PROPOSED` | Campo `status: UNKNOWN` |
| Omissões de CanonicalPromptView | `canonical_prompt_view.omissions` obrigatório na projeção normativa | Apenas `canonical_prompt_view.compiled_view.omissions` |

O teste de presença reproduziu `contract_has_top_level=true`, `adapter_has_top_level=false`. Isso não é apenas diferença de exemplos abreviados: a localização de um campo normativo mudou, e a mesma identidade/revisão de perfil apresenta conjuntos de modos distintos. Não há transformação explícita para esses casos. O fato de os perfis serem PROPOSED evita uma alegação de suporte executado, mas não resolve a incompatibilidade da representação.

**Impacto:** um consumidor futuro pode rejeitar o exemplo de compilação, perder o registro de omissões ou carregar capacidades diferentes para a mesma revisão, dependendo do documento usado. **Responsável sugerido:** dono de contratos/adaptação. **Correção:** manter uma representação completa canônica; usar projeções identificadas e mapeadas quando necessário; evitar dados contraditórios sob a mesma revisão. **Encerramento:** os campos internos têm o mesmo tipo/caminho e o perfil identificado tem conteúdo compatível; o compilador preserva `omissions` no local normativo. Confiança alta.

**AUD-002 — P2 — A correção de continuidade não chegou a todos os consumidores.**

Evidências: `docs/continuity-engine.md:52`, `:60` e `:90`; `docs/pattern-library.md:31`; `docs/contracts.md:56`. [Algoritmo](../../docs/continuity-engine.md#algorithm), [patterns](../../docs/pattern-library.md#core-patterns) e [ciclo de vida](../../docs/contracts.md#status-vocabulary).

O algoritmo agora permite herdar estado planejado validado em PLAN_ONLY. O pattern `PAT-STATE-CARRY` ainda exige, sem qualificação de canal, que somente estado de saída aceito seja herdado. Um planejamento que combine o pattern e o novo algoritmo recebe regras diferentes para a mesma fronteira.

Além disso, o passo 10 manda marcar o **shot** como `PASS`, `PARTIAL`, `FAIL` ou `BLOCKED`. O contrato reserva esses valores à observação; o ciclo de vida do shot usa `PLANNED`, `READY`, `RUNNING`, `GENERATED`, `REVIEW`, `ACCEPTED`, `REGEN_REQUIRED`, `REJECTED` e `SUPERSEDED`. Se o passo pretendia atualizar apenas o resultado de QA do shot, esse campo precisa ser identificado.

**Impacto:** a herança depende da referência carregada, e seguir literalmente o passo 10 produz um status não reconhecido pelo contrato de shot. **Responsável sugerido:** dono de continuidade/patterns. **Correção:** alinhar a regra do pattern por canal e separar resultado da observação de transição de lifecycle. **Encerramento:** o plano de dois shots funciona também com PAT-STATE-CARRY selecionado; uma observação PARTIAL permanece PARTIAL, enquanto o shot assume apenas um estado de lifecycle permitido. A falta original de inicialização foi corrigida. Confiança alta quanto à divergência textual; consequências de implementação não foram executadas.

**AUD-006 — P2 — Documentos de runtime ainda exigem trabalho na Fase 1.**

Evidências: `docs/model-adaptation.md:307`; `docs/comfyui-execution.md:147`; `docs/open-questions.md:9`; `docs/roadmap.md:35`, `:43` e `:49`. [Adaptação](../../docs/model-adaptation.md#9-open-questions-and-related-documents), [execução](../../docs/comfyui-execution.md#10-open-questions-and-related-documents) e [roadmap](../../docs/roadmap.md).

O roadmap foi corrigido: Fase 1 é esqueleto PLAN_ONLY, Fase 3 ativa perfis e Fase 4 integra o runtime. Porém a adaptação ainda exige um “Phase 1 profile probe”, e a execução diz que versão ComfyUI, inventário de nós, recursos, armazenamento e autoridade cloud permanecem abertos “until Phase 1”.

**Impacto:** um implementador que carregue a referência de adaptação/execução recebe pré-requisitos diferentes da fila canônica, com possibilidade de antecipar integração ou bloquear trabalho de esqueleto. **Responsável sugerido:** dono do roadmap e das referências de runtime. **Correção:** atualizar os consumidores para os gates específicos das Fases 3–5 e manter referência à fila única. **Encerramento:** nenhum documento exige probe de perfil na Fase 1; todas as referências concordam sobre a etapa em que cada evidência é necessária. Confiança alta. Não é necessário resolver os probes para fechar este defeito documental.

**AUD-009 — P2 — O parser usado na verificação muda o tipo do estado de ignição.**

Evidências: `docs/contracts.md:204`, `:220` e `:311`. [SceneBible](../../docs/contracts.md#scenebible) e [ContinuityState](../../docs/contracts.md#continuity-state). Problema novo nesta auditoria.

Com Python 3.12.3 e PyYAML 6.0.1, os três valores `ignition: off` sem aspas são resolvidos como booleano `False`. Nenhum erro de sintaxe é emitido. A documentação usa o nome de estado `off`, mas não especifica que ignição deve ser um booleano nem documenta essa conversão. O parser efetivamente usado pela auditoria anterior, portanto, não preserva o texto do estado.

Reprodução mínima: `yaml.safe_load('ignition: off')` retorna `{'ignition': False}`; com aspas no valor retorna uma string. O script desta revisão percorre os nós YAML e registra os três locais e a tag booleana, sem depender de uma busca textual aproximada.

**Impacto:** serialização subsequente gera `false`, e comparações com o estado textual `off` deixam de coincidir. É um problema de interoperabilidade de exemplos, não um erro observado em um motor de vídeo. **Responsável sugerido:** dono dos contratos. **Correção:** definir explicitamente o tipo de ignição e preservá-lo em todos os exemplos, com string inequívoca ou campo booleano declarado. **Encerramento:** o parser adotado produz o tipo contratual esperado e um ciclo de parse/serialização preserva o estado. Confiança alta para o comportamento reproduzido; não se presume o comportamento de todos os parsers YAML.

**AUD-005 — P3 — As faixas resumidas deixam lacunas para segundos fracionários.**

Evidências: `docs/requirements.md:125`; `docs/scene-and-continuity.md:272` e `:279`; `docs/vision-and-scope.md:64`; `docs/phase-0-report.md:48`. [Requisitos](../../docs/requirements.md#long-form-and-modes) e [faixas](../../docs/scene-and-continuity.md#9-duration-profiles-30-60-90-and-120-seconds).

O requisito canônico diz `>30` e `>45`. Os resumos dizem que as estruturas começam em 31 e 46 segundos; a visão usa intervalos `31–45` e `46–59`. Para 30,5 segundos, a timeline é obrigatória pelo requisito, mas a tabela resumida não fornece faixa. O mesmo ocorre em 45,5 e 59,5 segundos. Não foi encontrada restrição de duração a inteiros ou regra de arredondamento.

**Impacto:** ambiguidade de leitura nos limites, com risco menor porque o requisito canônico agora resolve a decisão. **Responsável sugerido:** dono de requisitos/visão. **Correção:** expressar intervalos contínuos, por exemplo `30 < t ≤ 45`, `45 < t < 60` e `t ≥ 60`, ou declarar e justificar a discretização. **Encerramento:** 30, 30,5, 45, 45,5, 59,5 e 60 segundos têm classificação única e coerente em requisitos e resumos. Confiança alta quanto às lacunas textuais; não há comportamento implementado para testar.

**Observação editorial sem novo achado bloqueador:** `docs/failure-and-evals.md:124` mantém em G-004 os `forbidden_behaviors` “implicit ownership transfer” e “unvalidated contact claim”, embora os oráculos tenham sido corretamente substituídos por verificações de conversa. Recomenda-se limpar esse resíduo e explicitar requisitos de diálogo na lista do caso. Isso não mantém aberto o defeito central de AUD-004: contato/posse agora estão em um registro G-006 separado.

**Verificações desta revisão.**

| Procedimento | Resultado | Limite |
|---|---|---|
| Inventário e manifest SHA-256 | 39 documentos; hashes individuais registrados | O manifest descreve o snapshot desta auditoria, não um novo finish Gauntlet |
| YAML seguro | 45 blocos; zero erros de sintaxe | Três conversões implícitas `off` → booleano; sintaxe não prova compatibilidade de schema |
| Links Markdown locais, fora das cercas de código | 376 referências; zero destinos de arquivo/âncora ausentes | Slugs aproximam a convenção GitHub; não houve teste de publicação no navegador nem validação de URIs simbólicos dentro de YAML |
| Presença dos IDs de requisitos em traceability | 79/79: 66 R-* e 13 NFR-* | Presença textual não prova cobertura semântica ou execução de eval |
| Comparação dos exemplos de profile e prompt view | Divergências reproduzidas em JSON | Comparação estática de documentos, não teste de adapter |
| Exemplo de observação | Agregado PARTIAL; checagem obrigatória PARTIAL | Foi inspecionado o exemplo; não se alega implementação/teste exaustivo do agregador |
| Registros de remediação | Dois registros VER-20260908-AUDIT-DOCS-REMEDIATION* encontrados | PASS anterior não substitui a revalidação das propriedades que falharam nesta revisão |

O [script da auditoria](../docs-2026-09-08-r2/check_docs.py) e o [resultado com hashes](../docs-2026-09-08-r2/evidence.json) foram preservados. O script é um coletor de evidências, não um validador de planos da futura Skill, e sua saída não constitui um veredito automático. Para reproduzir, execute na raiz:

```bash
python3 audit-artifacts/docs-2026-09-08-r2/check_docs.py
```

**Limitações e próximo passo:** a revisão é documental, por um único auditor, sem revalidação online de todas as fontes externas, sem execução de mídia e sem novo Gauntlet. Esses limites não são defeitos da Fase 0. Corrigir primeiro AUD-001; depois alinhar continuidade, fases e tipos YAML, e finalizar as faixas de duração. O texto `REMEDIATED_VERIFIED` não deve ser interpretado como fechamento dos resíduos listados aqui. Os arquivos de especificação e o relatório anterior foram preservados.
