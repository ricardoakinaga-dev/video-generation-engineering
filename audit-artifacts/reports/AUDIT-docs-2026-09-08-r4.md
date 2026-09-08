# Auditoria de docs — quarta revisão — 2026-09-08

**Resultado:** os dois achados da terceira revisão estão corrigidos no escopo reportado. A nova revisão encontrou uma lacuna P2 na proveniência do contrato de coleta. Não foi identificado novo P1 no escopo inspecionado. A estrutura documental está consistente nas verificações executadas; a fronteira de execução ainda precisa explicitar como relaciona o arquivo produzido à execução que o originou.

P2 significa corrigir antes de implementar ou aceitar a etapa afetada. Este relatório não declara uma falha observada em produção, nem substitui o histórico de aprovação do Gauntlet.

**Escopo e método.** Inventário dos 39 arquivos Markdown, comparação com os hashes da [terceira revisão](AUDIT-docs-2026-09-08-r3.md), leitura das correções e dos contratos consumidores, verificação de YAML/links/IDs e comparação dos exemplos completos após parse. Dez documentos mudaram desde r3. Os demais foram cobertos pelos checks globais e pelas inspeções anteriores conforme seus hashes, sem presumir que inspeção anterior prove ausência de todos os defeitos. Os registros de remediação em `.agent/verification.jsonl` foram consultados. A revisão segue a abordagem de evidência da skill `engineering-framework` já aplicada nesta conversa.

Foi uma auditoria por um único agente, sem subagentes, runtime, mídia, revalidação online de todas as fontes ou novo Gauntlet. Os documentos de `docs/`, os controles de processo e os relatórios anteriores foram preservados.

**Revalidação dos achados pendentes.**

| ID | Resultado | Evidência atual |
|---|---|---|
| AUD-010 — NOT_RUN e lifecycle | CORRIGIDO no caso reportado | A tabela de continuidade distingue planejamento sem artefato, RUNNING sem saída, GENERATED aguardando QA e REVIEW com QA pendente. NOT_RUN não determina regressão para PLANNED/READY. |
| AUD-011 — coleta versus observação | CORRIGIDO no caso reportado | Coleta agora usa GenerationArtifact; os registros pendente e executado de ArtifactObservation têm os campos canônicos. O pendente possui procedimento/timestamp nulos e checks vazios; o executado contém procedimento, timestamp e PARTIAL. |

Não foi detectada regressão nos controles anteriores verificados: igualdade integral de CapabilityProfile, posição canônica de `omissions`, ignição textual, links do sumário e separação entre QA e lifecycle permanecem consistentes. Essas constatações se limitam à documentação e aos exemplos; não são testes de uma Skill ou adapter implementado.

**AUD-012 — P2 — O contrato de coleta não materializa a proveniência exigida.**

**Evidência:** [requirements.md](../../docs/requirements.md#model-adaptation-and-execution), linha 110, requisito R-EXE-04; [comfyui-execution.md](../../docs/comfyui-execution.md#5-local-and-cloud-boundaries), linhas 81–89; [contracts.md](../../docs/contracts.md#artifact-collection-contract-generationartifact), linhas 443–469; [exemplo de coleta](../../docs/comfyui-execution.md#8-artifact-collection-and-provenance), linhas 114–136.

R-EXE-04 exige preservar versão do modelo/perfil, identidade do workflow, entradas, seeds/parâmetros quando disponíveis e proveniência da saída. A seção de execução detalha a obrigação de preservar versões de modelo/nós, hashes de entrada e saída e identificador de prompt/fila quando retornado.

O novo contrato GenerationArtifact contém `id`, `shot_id`, caminho do arquivo, horário, estado de geração, metadados de mídia, progresso de revisão e um objeto `runtime` limitado a `provider`, `endpoint` e `workflow_hash`. Não há hash do conteúdo da saída, versão/referência do perfil, identificação da execução nem uma referência a um registro imutável que contenha os parâmetros e entradas usados. O `shot_id` identifica o plano, mas não distingue tentativas de geração do mesmo shot.

**Caso que expõe a lacuna:** gerar duas tentativas do mesmo shot com seeds ou versões de modelo diferentes e usar o mesmo caminho de saída. O formato documentado não define como descobrir, a partir de um artefato coletado, quais parâmetros/entradas produziram seus bytes, nem como detectar que o conteúdo apontado pelo caminho foi substituído depois da revisão. Os IDs distintos de artefato podem identificar registros, mas o vínculo desses registros com os bytes e a tentativa concreta precisa ser especificado.

**Impacto:** proveniência incompleta, recuperação e reprodução ambíguas, e dificuldade de demonstrar que a observação ainda corresponde ao arquivo disponível. Trata-se de uma lacuna de especificação; não se afirma que arquivos foram sobrescritos nesta sessão.

**Correção proposta:** definir onde os dados obrigatórios de execução são persistidos e como GenerationArtifact os referencia. Uma opção é uma referência imutável a uma tentativa de execução contendo perfil/modelo/nós, workflow, entradas e parâmetros, mais hash do conteúdo coletado. O responsável pode escolher outro formato, desde que preserve a mesma rastreabilidade. Declarar como valores desconhecidos são representados e em que etapa impedem o aceite. Os placeholders atuais são exemplos de Fase 0; sua substituição por valores reais não resolve, sozinha, os campos e relações ausentes.

**Critério de encerramento:** um exemplo de duas tentativas do mesmo shot permite recuperar separadamente os dados usados em cada geração e identificar os bytes associados a cada observação. Alterar o conteúdo no mesmo caminho deve ser detectável e exigir revalidação da evidência aplicável. O exemplo deve satisfazer a lista de proveniência já exigida pela documentação, sem depender de um vínculo implícito pelo nome do arquivo.

Responsáveis sugeridos: donos de contratos e execução. Confiança alta na ausência dos campos/relações documentados; comportamento da futura implementação não executado. AUD-012 complementa a revisão da coleta e não reabre a separação de tipos corrigida em AUD-011.

**Resultados reproduzíveis.**

| Verificação | Resultado | Limite |
|---|---|---|
| Inventário e manifest | 39 Markdown; dez alterações em relação a r3; hashes individuais registrados | Snapshot da auditoria, não aprovação independente do histórico |
| Parse seguro YAML | 48 blocos; zero erros de sintaxe; zero booleanos implícitos não escritos como true/false | Sintaxe não comprova semântica de todos os campos |
| Links Markdown locais | 378 referências; zero destinos de arquivo/âncora ausentes | Exclui URIs dentro de YAML e disponibilidade externa; convenção de slugs descrita no coletor |
| Requisitos em traceability | 79/79 presentes: 66 R-* e 13 NFR-* | Presença textual não prova execução ou qualidade de todos os evals |
| CapabilityProfile completo | Igualdade após parse entre contrato e adaptação | Não comprova suporte real do modelo |
| GenerationArtifact completo | Igualdade após parse entre contrato e execução | Igualdade entre dois exemplos não comprova suficiência de proveniência; AUD-012 |
| ArtifactObservation de execução | Nenhum campo canônico ausente nos registros pendente e executado | Inspeção dos exemplos, não execução de QA |
| Prompt canônico | `omissions` no nível canônico nos dois exemplos | Não é execução do compilador |
| BLUEPRINT | Hash preservado: `62c04a55fe991a8f094db47d661ab6fa70fbe20e26f0adbfda402eba78f6fc1d` | Comparação com o baseline local; anexo original não reapresentado |

O [coletor r4](../docs-2026-09-08-r4/check_docs.py) reutiliza os checks estruturais de r2 e acrescenta a inspeção da separação entre coleta e QA. O [JSON de evidência](../docs-2026-09-08-r4/evidence.json) preserva versões das ferramentas, horário, resultados e hashes. Para reproduzir na raiz:

```bash
python3 audit-artifacts/docs-2026-09-08-r4/check_docs.py
```

A saída do coletor não é um veredito automático. O cenário de duas tentativas em AUD-012 é uma análise do contrato, não um teste de geração realizado. Os antigos coletores/evidências foram preservados para comparação histórica.

**Próximo passo:** completar a relação artefato–execução–evidência em AUD-012 antes de implementar ou aceitar coleta de runtime. Os demais achados encerrados mantêm seu histórico. Não há necessidade de executar geração real para corrigir esta lacuna documental; essa execução pertence à validação posterior da implementação.
