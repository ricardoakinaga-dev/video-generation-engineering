# Auditoria de docs — terceira revisão — 2026-09-08

**Resultado:** as cinco pendências da [segunda revisão](AUDIT-docs-2026-09-08-r2.md) foram corrigidas no escopo reportado. A inspeção adicional identificou dois problemas P2 na passagem de geração para revisão de artefatos. Não foi encontrado novo P1 no escopo desta auditoria. A documentação melhorou, mas ainda precisa dessas correções antes de implementar a fronteira pós-geração.

P2 significa inconsistência que deve ser corrigida antes de implementar ou aceitar a etapa afetada. As consequências descritas são riscos da futura implementação, não falhas executadas em ComfyUI.

**Escopo:** inventário e checagem estrutural dos 39 Markdown; comparação por hash com a revisão anterior, identificando 14 documentos modificados; leitura cruzada das correções com contratos, continuidade, estado, execução, roadmap, patterns e critérios de aceite. Os documentos inalterados também permanecem cobertos pelas inspeções anteriores, sem presumir que essas inspeções provem perfeição. Foram consultados os registros locais de remediação. A revisão foi realizada por um único auditor, sem subagentes, execução de modelos, mídia ou nova rodada Gauntlet. A abordagem de evidência e prioridades segue a skill `engineering-framework` já utilizada nesta conversa.

**Fechamento das pendências da revisão anterior.**

| Achado | Situação no escopo apontado | Verificação |
|---|---|---|
| AUD-001 — perfil/campos internos | CORRIGIDO | Os objetos CapabilityProfile completos dos dois documentos são iguais após parse; `omissions` existe no nível canônico nos dois exemplos. |
| AUD-002 — canais e valores de QA no lifecycle | CORRIGIDO | PAT-STATE-CARRY agora distingue os canais; o passo 10 escreve QA em ArtifactObservation.status e lifecycle em shot.lifecycle_status. O novo problema AUD-010 trata outra condição dessa tabela. |
| AUD-005 — duração fracionária | CORRIGIDO | Requisitos, visão e tabela de cena usam intervalos contínuos com limites explícitos: `0 < t ≤ 30`, `30 < t ≤ 45`, `45 < t < 60`, `60 ≤ t < 90`, `90 ≤ t ≤ 120`. |
| AUD-006 — probes de perfil na Fase 1 | CORRIGIDO | Adaptação e execução agora permitem planos nas Fases 1/2 e remetem ativação de perfil/preflight aos gates posteriores. |
| AUD-009 — coerção de ignição | CORRIGIDO | Ignição tem enum textual declarado; não há valores booleanos implícitos como `off` nos 44 blocos YAML. |

O fechamento é documental. Não significa que exista uma implementação de roteamento por duração, de agregação de QA ou de continuidade que tenha sido executada nesta auditoria. AUD-003, AUD-004, AUD-007 e AUD-008 mantêm as correções centrais registradas na segunda revisão; a observação editorial sobre os forbidden_behaviors de G-004 continua de baixa prioridade e não foi promovida a um novo bloqueador.

**AUD-010 — P2 — NOT_RUN não distingue um shot ainda não gerado de um artefato aguardando QA.**

Evidência: [continuity-engine.md](../../docs/continuity-engine.md#algorithm), linha 66; [contracts.md](../../docs/contracts.md#status-vocabulary), linhas 56–67; [comfyui-execution.md](../../docs/comfyui-execution.md#8-artifact-collection-and-provenance), linhas 117–130.

A primeira linha da nova tabela de efeitos sobre o shot associa “No artifact or NOT_RUN observation” à instrução de manter o shot `PLANNED/READY`. Porém `NOT_RUN` também é a condição normal de QA quando um arquivo já foi gerado e ainda não foi inspecionado. O próprio exemplo de execução apresenta simultaneamente `generation_status: GENERATED` e `validation_status: NOT_RUN`.

**Caso que expõe a inconsistência:** o runtime termina a geração; o shot entra em GENERATED; a inspeção ainda não começou e sua observação está NOT_RUN. A tabela manda manter PLANNED/READY, embora o estado factual seja GENERATED ou REVIEW. Durante uma execução RUNNING sem artefato disponível, a alternativa “No artifact” também não basta para determinar PLANNED/READY.

**Impacto:** uma implementação literal pode regredir o estado de produção e perder a distinção entre trabalho não iniciado, geração em curso e mídia aguardando QA. Isso pode provocar nova geração indevida ou apresentar progresso incorreto. Não foi observado esse comportamento em um runtime: a evidência é a contradição entre as instruções.

**Correção proposta:** separar as condições de ausência de artefato, geração em curso e artefato existente sem avaliação. NOT_RUN deve atualizar a informação de QA sem, por si só, alterar o lifecycle. O lifecycle deve conservar o estado determinado pelos eventos de produção.

**Critério de encerramento:** os casos `(PLANNED, sem artefato)`, `(RUNNING, sem saída ainda)` e `(GENERATED, artefato existente, QA NOT_RUN)` preservam estados diferentes; iniciar a revisão permite REVIEW; somente evidência de aceite permite ACCEPTED. Nenhum deles é normalizado automaticamente para PLANNED/READY por ausência de QA.

Responsável sugerido: dono de continuidade/estado. Confiança alta na inconsistência textual; consequência de runtime não executada.

**AUD-011 — P2 — O objeto de coleta ComfyUI é chamado ArtifactObservation, mas não segue esse contrato.**

Evidência: [comfyui-execution.md](../../docs/comfyui-execution.md#8-artifact-collection-and-provenance), linhas 112–130; [contracts.md](../../docs/contracts.md#observation-contract-artifactobservation), linhas 439–461; [domain-model.md](../../docs/domain-model.md#entity-catalogue), linhas 40–41.

Os documentos usam a mesma chave YAML `artifact_observation` para dois formatos distintos:

| Contrato canônico de observação | Exemplo de coleta ComfyUI |
|---|---|
| `id`, `shot_id`, `artifact_ref` | `artifact_id`, `media.uri` |
| `observed_at`, `procedure`, `checks` | Sem campos correspondentes |
| `status`, `limitations`, `repair_route` | `generation_status`, `validation_status`, `runtime` |

A comparação após parse encontrou zero campos de primeiro nível em comum. Parte da diferença é conceitual: coleta de um artefato e observação de qualidade são registros diferentes no modelo de domínio. O exemplo de execução se parece com um registro de GenerationArtifact, mas não o identifica assim nem documenta uma projeção para ArtifactObservation.

**Impacto:** o consumidor orientado pelo contrato não encontra `ArtifactObservation.status` no objeto produzido pelo exemplo de execução e não consegue associar procedimento, shot e resultado de QA. Metadados de coleta podem ser confundidos com observação de qualidade. O exemplo mantém NOT_RUN, portanto não está alegando que a mídia passou; o defeito é a interface documental incompatível.

**Correção proposta:** identificar o registro de coleta pelo conceito correto e produzir uma ArtifactObservation separada quando a avaliação existir; alternativamente, documentar uma projeção explícita que preserve todas as informações necessárias sem inventar observações. Campos não aplicáveis antes da execução precisam de semântica definida.

**Critério de encerramento:** um exemplo completo mostra a sequência coleta → registro de artefato → QA → observação vinculada. Os dois registros são distintos, seus campos correspondem aos contratos e a ausência de inspeção não fabrica procedimento, timestamp ou PASS. Um consumidor do contrato consegue obter o estado de QA pelo caminho declarado.

Responsáveis sugeridos: donos de execução e contratos. Confiança alta; divergência de campos reproduzida no coletor desta auditoria. Este achado amplia a revisão para o objeto de observação na integração e não reabre a paridade de CapabilityProfile corrigida em AUD-001.

**Verificação executada.**

| Procedimento | Resultado atual | Limite |
|---|---|---|
| Inventário e hashes | 39 documentos; 14 modificados desde r2; manifest individual preservado | Não certifica o histórico de origem |
| Parse seguro de YAML | 44 blocos; zero erros de sintaxe; zero booleanos implícitos não escritos como true/false | Não é validação de schema nem de comportamento |
| Links Markdown locais | 377 referências; zero destinos de arquivo/âncora ausentes | Não inclui URIs em YAML nem validação online; slugs seguem a aproximação GitHub descrita no coletor |
| IDs de requisitos em traceability | 79/79 presentes: 66 R-* e 13 NFR-* | Presença não prova adequação ou execução de todos os evals |
| Paridade integral de CapabilityProfile | Igualdade após parse: true | Não comprova suporte dos modelos nem instalação local |
| Omissões do prompt canônico | Campo de primeiro nível presente nos dois exemplos | Não executa um compilador |
| Exemplo canônico de QA | Agregado PARTIAL e checagem PARTIAL preservados | Não é teste exaustivo do agregador |
| Comparação de ArtifactObservation | Nove campos do exemplo canônico ausentes no exemplo de coleta | Reprodução estrutural que fundamenta AUD-011 |

O [coletor r3](../docs-2026-09-08-r3/check_docs.py) reutiliza as verificações estruturais do coletor r2 sem alterar os resultados anteriores. A [evidência JSON](../docs-2026-09-08-r3/evidence.json) registra versão do Python/PyYAML, horário, resultados e hashes dos documentos. Reproduza a partir da raiz:

```bash
python3 audit-artifacts/docs-2026-09-08-r3/check_docs.py
```

A saída é evidência de inspeção, não um PASS automático. A avaliação de lifecycle em AUD-010 foi feita por comparação explícita das regras e dos casos; não existe um motor implementado que tenha sido executado para essa conclusão.

**Limitações e próximo passo:** não houve revalidação online de todas as fontes externas, geração de mídia, execução ComfyUI, prova de qualidade visual/sonora ou novo Gauntlet. O escopo documental não exige tais execuções. Recomenda-se corrigir AUD-010 e AUD-011 antes de implementar coleta/revisão, mantendo os fechamentos anteriores e os relatórios históricos. Nenhum documento de `docs/` ou controle `.agent/.gauntlet` foi alterado nesta auditoria.
