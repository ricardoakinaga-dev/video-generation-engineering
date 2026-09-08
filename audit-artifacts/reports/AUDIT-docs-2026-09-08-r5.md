# Auditoria de docs — quinta revisão — 2026-09-08

**Resultado:** AUD-012, a pendência da [quarta revisão](AUDIT-docs-2026-09-08-r4.md), foi corrigido no escopo reportado. A documentação agora especifica tentativa de execução, hashes dos artefatos e vínculo de QA aos bytes inspecionados. Foi encontrado um novo achado P2 de consistência entre os exemplos dessa tentativa. Não foi identificado novo P1 no escopo inspecionado.

P2 significa corrigir antes de reutilizar os exemplos como contrato/fixture de implementação. Não representa um incidente observado em produção.

**Escopo e método.** Inventário dos 39 Markdown, comparação com os hashes de r4, leitura cruzada das alterações de proveniência e dos documentos consumidores, parse de todos os exemplos YAML, resolução dos links Markdown locais e presença dos requisitos na rastreabilidade. Doze documentos mudaram desde r4. As inspeções anteriores foram aproveitadas para o conteúdo inalterado, sem presumir ausência absoluta de outros defeitos. A auditoria segue a abordagem de evidência da skill `engineering-framework` já aplicada nesta conversa.

Esta revisão foi realizada por um único agente, sem subagentes, execução de ComfyUI, geração de mídia, revalidação online de todas as fontes ou novo Gauntlet. `docs/`, os registros de controle e os relatórios anteriores foram preservados.

**Revalidação de AUD-012 — CORRIGIDO no escopo reportado.**

O [contrato de execução](../../docs/contracts.md#execution-attempt-contract-executionattempt) passou a conter identificação da tentativa, referência do plano, perfil/modelo/runtime/nós/workflow, entradas, parâmetros, referências de progresso e campos desconhecidos explícitos. O [contrato de coleta](../../docs/contracts.md#artifact-collection-contract-generationartifact) contém `execution_attempt_ref` e `content_hash`. A [observação](../../docs/contracts.md#observation-contract-artifactobservation) identifica o artefato e registra `observed_content_hash`.

O exemplo de duas tentativas em [comfyui-execution.md](../../docs/comfyui-execution.md#8-artifact-collection-and-provenance) foi analisado após parse:

| Relação | Resultado |
|---|---|
| Tentativas identificadas | 2 |
| Artefatos identificados | 2 |
| Observações identificadas | 2 |
| Artefatos apontam para tentativas existentes | Sim |
| Observações apontam para artefatos existentes e hashes correspondentes | Sim |
| Hashes de saída distintos | 2 |
| Caminhos de saída distintos | 1, intencionalmente reutilizado |

A documentação também estabelece que divergência entre o hash atual e o registrado invalida a evidência aplicável e exige recolhimento/revalidação. Isso atende à lacuna anterior de identificação das tentativas e dos bytes. Foram conferidos dados e regras documentais; nenhum arquivo de vídeo foi produzido ou sobrescrito para testar um resolver real.

**AUD-013 — P2 — A mesma tentativa imutável tem inventários de entrada diferentes.**

**Evidência:** [contracts.md](../../docs/contracts.md#execution-attempt-contract-executionattempt), linhas 449–488; [comfyui-execution.md](../../docs/comfyui-execution.md#8-artifact-collection-and-provenance), linhas 150–173.

Os dois exemplos declaram `id: attempt_shot_002_001`, `attempt_index: 1`, `shot_id: shot_002` e `execution_plan_ref: exec_scene_001_rev1`. A comparação dos objetos completos encontrou diferença somente em `inputs`:

| Exemplo | Entradas declaradas |
|---|---|
| Contrato canônico | `ref_mara_portrait` como identity_reference e `anchor:shot_004:last_frame` como temporal_anchor |
| Cenário de duas tentativas em ComfyUI | Somente `ref_mara_portrait` como identity_reference |

Não há indicação de que o segundo exemplo seja uma projeção parcial, outro namespace de fixture ou uma tentativa diferente. O contrato define a tentativa como proprietária do contexto concreto e imutável de uma submissão. A omissão da âncora temporal muda esse contexto, embora a identidade do registro permaneça igual.

**Impacto:** um consumidor que reúna os exemplos pode obter proveniência diferente para o mesmo ID. Uma validação de reprodução ou continuidade pode considerar uma âncora que o outro registro não declara. A paridade já confirmada de CapabilityProfile e GenerationArtifact não detecta esse problema no novo ExecutionAttempt.

**Reprodução:** o coletor r5 procura o mesmo ID nos dois exemplos, compara os campos após `yaml.safe_load` e registra `different_top_level_fields: ["inputs"]`. O contrato contém duas entradas; o cenário de execução contém uma. O resultado completo está no JSON de evidência.

**Correção proposta:** alinhar o inventário da mesma tentativa nos dois exemplos. Se os contextos distintos são intencionais, usar identidades de fixture distintas ou identificar explicitamente uma projeção com regra de resolução para o registro completo. Preservar o vínculo correto entre tentativa, artefato e observação.

**Critério de encerramento:** dois registros que identifiquem a mesma tentativa e revisão/contexto resolvem para o mesmo inventário de entradas e hashes. Uma mudança de âncora não pode desaparecer por substituição silenciosa de um registro pelo outro. Os testes de vínculos e hashes do cenário devem continuar consistentes após a correção.

Responsáveis sugeridos: donos de contratos e execução. Confiança alta na divergência de fixture reproduzida; não há comportamento de runtime observado. Este achado não reabre a ausência de proveniência de AUD-012: a relação agora existe, mas um exemplo duplicado ainda precisa ser reconciliado.

**Verificações globais e regressão.**

| Verificação | Resultado | Limite |
|---|---|---|
| Inventário e manifest | 39 documentos; 12 alterados desde r4; hashes individuais preservados | Snapshot desta inspeção |
| YAML seguro | 50 blocos; zero erros de sintaxe; zero booleanos implícitos não escritos como true/false | Não é validação completa de schema |
| Links Markdown locais | 381 referências; zero destinos de arquivo/âncora ausentes | Exclui referências dentro de YAML e disponibilidade externa; slugs seguem a convenção aproximada documentada no coletor |
| Requisitos em traceability | 79/79 presentes: 66 R-* e 13 NFR-* | Presença não prova execução ou adequação de todos os evals |
| CapabilityProfile completo | Igual nos dois documentos após parse | Não comprova capacidades de runtime |
| GenerationArtifact completo | Igual nos dois documentos após parse | A ligação a ExecutionAttempt requer também a consistência apontada em AUD-013 |
| CanonicalPromptView | `omissions` permanece no nível canônico nos dois exemplos | Não executa um compilador |
| Exemplo de QA | Agregado PARTIAL e checagem PARTIAL preservados | Inspeção de exemplo, não teste exaustivo do agregador |
| Proveniência relacional | Referências e hashes correspondem dentro do cenário de duas tentativas | Dados ilustrativos, sem artefatos reais |
| BLUEPRINT | Hash igual ao baseline: `62c04a55fe991a8f094db47d661ab6fa70fbe20e26f0adbfda402eba78f6fc1d` | Sem o anexo original para comparação independente |

Não foi detectada regressão nos controles anteriores verificados. Seus fechamentos permanecem limitados aos defeitos e evidências documentais registrados nas revisões anteriores.

O [coletor r5](../docs-2026-09-08-r5/check_docs.py) reutiliza os checks estruturais de r2 e acrescenta as comparações dos vínculos e das tentativas. O [JSON de evidência](../docs-2026-09-08-r5/evidence.json) registra horário, versões das ferramentas, resultados e hashes. Para reproduzir na raiz:

```bash
python3 audit-artifacts/docs-2026-09-08-r5/check_docs.py
```

A saída é evidência de inspeção, não um veredito automático de aceite. **Próximo passo:** reconciliar o inventário de entradas de AUD-013 e repetir a comparação da tentativa e seus vínculos. Não é necessária execução de vídeo para corrigir essa inconsistência documental.

## Encerramento de AUD-013 — 2026-09-08

**CORRIGIDO após a auditoria.** A âncora `anchor:shot_004:last_frame`, com o papel `temporal_anchor` e o hash do contrato canônico, foi incluída em `attempt_shot_002_001` no exemplo de ComfyUI. Os dois objetos completos agora são iguais após parse YAML (`different_top_level_fields: []`). Os vínculos entre tentativas, artefatos e observações, incluindo os hashes, continuam válidos.

O coletor r5 foi executado novamente: 39 documentos, 50 blocos YAML sem erros, 381 links locais válidos e 79 requisitos presentes na rastreabilidade. Somente `docs/comfyui-execution.md` mudou em relação ao snapshot r5. A [evidência posterior à correção](../docs-2026-09-08-r5/evidence-after-AUD-013-fix.json) foi salva separadamente; os resultados originais acima permanecem como histórico. Verificação estática, sem execução de runtime ou geração de mídia. O próximo passo indicado na auditoria foi concluído.
