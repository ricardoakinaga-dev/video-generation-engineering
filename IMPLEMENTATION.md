# Implementação — 9 de setembro de 2026 (R3)

A skill está implementada em [.agents/skills/video-generation-engineering](.agents/skills/video-generation-engineering/SKILL.md), com direção semântica pelo agente e ferramentas determinísticas para planejamento, continuidade, compatibilidade, execução, proveniência, montagem e qualidade audiovisual. Pode ser usada neste projeto pela IDE ou pelo terminal com `$video-generation-engineering`.

## Entrega

- Entrada concisa, metadados de descoberta e nove referências carregadas conforme a tarefa.
- Tratamento de exemplo completo, contratos JSON, propagação de estado, DAG, timelines, conflitos, câmera, diálogo, áudio, restrições e compilação de prompts estruturados.
- Descoberta e preflight de grafos ComfyUI, incluindo dynamic-combo aninhado com chaves pontilhadas, vinculação explícita de entradas/parâmetros, guard fail-closed de dispositivo/VRAM livre, submissão autorizada, consulta pelo mesmo ID, coleta e registros imutáveis com SHA-256.
- Negociação por perfil e evidência: perfil local H3 confirmado no escopo testado; Wan 2.2 e Hailuo API candidatos. Adaptador Hailuo com preparação e transporte testado sem chamadas pagas.
- Validação de observações, scorecard de 14 dimensões, transições com dois artefatos observados, re-anchor, contato físico com sete fases canônicas, ownership/vehicle-state, diálogo/áudio em canais separados, causalidade, adaptação diferencial, reparo orçamentado, FFmpeg/ffprobe, montagem e folhas de contato.
- Gate de estado canônico contra contradições de porta/movimento/assento, iluminação/tempo, câmera, diálogo e estado declarado; adaptação exige esse estado e seleção de negativos é limitada ao risco real da cena.
- Oráculos de QA agora são específicos à reivindicação: áudio para áudio, multi-frame/sequence/transition para temporal/lip-sync/continuidade e HUMAN para editorial; maturidade exige registros atuais com evidência hash-bound.
- Ladder LF-001..LF-004 com fixtures estruturais; `validate_long_form_case` falha fechado para PASS declaratório e exige tentativas, artefatos, observações, transições e assembly hash-bound. A execução local A003 acrescenta evidência real `PARTIAL` para LF-001 S01 sem promover o caso completo.
- PASS de long-form agora exige referências canônicas hash-bound, ordem integral de shots, todos os pares adjacentes, IDs de observação imutáveis, manifesto de assembly estrito, QA de mídia atual e aceite editorial humano separado.
- QA mecânico de mídia separado de QA semântico, ladder de 10–120 segundos, níveis de maturidade, gates independentes e relatório de release sem promoção indevida de evidência.
- Suíte de regressão e integração, avaliação de uso por outro agente, rastreabilidade e evidências reproduzíveis.

O pacote usa Python 3.10+ e biblioteca padrão. FFmpeg e ffprobe nativos são necessários para os comandos de mídia. Não inclui pesos de modelos. [ADR-011](docs/adr/ADR-011-skill-implementation-and-evidence.md) registra as decisões de implementação; [README](README.md) contém os comandos de uso.

## Verificação

| Procedimento executado | Resultado e limite |
|---|---|
| Suíte Python | 141 testes passaram na verificação final, sem falhas ou skips: planejamento, mutações inválidas, progressive-disclosure routing, metamorphic invariants, contratos de qualidade, HTTP local simulado, guard de recursos/VRAM, API paga simulada, proveniência, mídia sintética real, semantic QA, granular media QA e assembly lineage |
| Validação de Skill | `quick_validate.py` passou e `compileall` passou para scripts, testes e ferramentas |
| Pacote | ZIP R5 com 37 entradas/28 arquivos, CRC válido, SHA `2e2a4fa10a41f776f69810cb8115dd5e32f92c762e15d1ce6d2d68ffbe208840`, scans e smoke test em CWD externo; manifesto em `verification/distribution-triple-aaa-r5.json` |
| Revisão independente de código | Oito problemas corrigidos com regressões; auditorias fresh sucessivas fecharam vínculos de evidência, deriva e orçamento no escopo revisado |
| Critic pós-guard | R15/R16/R18 são históricos incompletos; R17 é uma rejeição histórica com alerta de mutação do worktree. Três tentativas R3 foram registradas como `INCOMPLETE`; nenhuma aceitação independente é reivindicada. |
| Uso independente | Respostas efetivas para 12 cenários principais e 17 adversariais; revisão de oito respostas após problemas observados; G-004 passou prepare/validate/compile |
| ComfyUI instalado | Preflight local validou os dois grafos H3 contra ComfyUI 0.34.0/911 nós; A001/A002 falharam com OOM sem produzir artefato e A003 concluiu S01 com MP4 real, QA mecânico `PASS` e semântica `PARTIAL`; o novo guard bloqueia submissões sem piso explícito de VRAM livre; o perfil histórico foi marcado `EXPIRED` após a correção do dynamic-combo e exige nova sonda antes de qualquer promoção; H3 R2V permanece `PARTIAL` após inspeção semântica |
| QA de mídia | Artefatos locais passaram checks mecânicos de integridade, alinhamento, decode, preto e freeze; isso não aprova identidade, física, emoção, continuidade ou lip-sync |
| Mídia gerada | H3 T2V histórico: MP4 H.264, 384×224, 124 quadros, 24 FPS, 5,167 s, AAC estéreo 32 kHz. LF-001 A003 S01: MP4 H.264, 384×224, 124 quadros, 24 FPS, 5,167 s, AAC estéreo 32 kHz, QA mecânico `PASS`, semântica `PARTIAL`. H3 R2V: MP4 coletado de 832×480, 124 quadros, 24 FPS; retenção veterinária/identidade declarada falhou semanticamente |

Os erros encontrados durante a construção incluíram validação de perfil candidato e tolerância de duração, seleção de FFmpeg via wrapper Flatpak, estados desconhecidos, inconsistências de parâmetros e promoção indevida de tentativas. Foram corrigidos antes do resultado final. As respostas e falhas iniciais da avaliação de uso foram preservadas.

Evidências: [guard de recursos e OOM LF-001](verification/comfyui-runtime-resource-boundary-20260909.json), [contexto de recursos A003](verification/comfyui-runtime-resource-context-20260909-a003.json), [tentativa OOM A001](artifacts/lf001_probe_20260909/attempt-001-oom.json), [tentativa OOM A002](artifacts/lf001_probe_20260909/attempt-002-oom.json), [evidência LF-001 A003](verification/long-form/LF-001-evidence-r2.json), [matriz R3](docs/capability-matrix-r3.md), [scorecard R3](docs/triple-aaa-scorecard-r3.md), [relatório R3](docs/triple-aaa-final-production-closure.md), [bar R3](docs/triple-aaa-quality-bar-r3.json) e os artefatos históricos de perfil, QA, critic e distribuição preservados em `verification/`. As auditorias históricas continuam preservadas e não são reutilizadas como veredito atual.

Para repetir as verificações locais:

```bash
python3 tools/verify.py
python3 -m unittest discover -s tests -v
```

Esses comandos não submetem geração nem invocam provedores externos. `tools/verify.py --output caminho-novo.json` grava relatório com comandos/testes e hashes do pacote.

## Vídeo e execução real

[Abrir amostra H3 histórica](verification/media/final/art_2898879072af4739b673efe71fafcc7e.mp4) · [folha de contato histórica](verification/media/h3-contact-sheet.jpg) · [abrir LF-001 S01 A003](artifacts/lf001_probe_20260909/attempt-003-output/f2fc193e_000.mp4) · [folha de contato A003](artifacts/lf001_probe_20260909/attempt-003-contact-sheet.jpg).

O A003 é a primeira evidência local desta rodada que concluiu sem OOM: a proveniência canônica passou, a integridade mecânica passou e a inspeção semântica ficou `PARTIAL`. O vídeo cobre somente aproximação e pré-contato; não demonstra entrada no veículo, continuidade entre shots, reparo ou aceitação editorial.

A primeira inferência levou aproximadamente 36,95 segundos na RTX 3060 de 12 GB. O teste final foi uma submissão deliberada para verificar o código final, com a fila livre e o mesmo workflow; o ComfyUI reutilizou seus nós em cache. Portanto, houve uma inferência observada e uma integração adicional com cache, não duas inferências independentes.

O SHA-256 do vídeo é `623f04987e1401623f6bb9e31c6823b23e56694719681d081e7484303538d124`. [Histórico final](verification/h3-final-history.json), [artefato coletado](verification/h3-final-artifacts.json), [metadados](verification/h3-final-media-probe.json) e [observação inicial PARTIAL](verification/h3-observation.json) mantêm a proveniência. O perfil histórico expira em 15/09/2026 e a mudança atual do workflow já está registrada como `EXPIRED`; nova sonda é obrigatória antes de reutilizar sua capacidade.

## Cobertura e limites de aceitação

Os [79 requisitos têm responsáveis de implementação e referências de evidência](verification/requirements-coverage.json). Esse mapeamento não representa 79 aprovações de qualidade de produção. A especificação separa julgamento semântico, contratos estruturais, capacidade do runtime e observações da mídia; a entrega mantém essa separação.

O planejamento de 45 e 90 segundos recebeu fixtures explícitos de decomposição, Scene Bible, continuidade e recovery; os limites contínuos até 120 segundos têm testes estruturais. Não foi produzido e aprovado um filme completo de 45–120 segundos. As respostas longas do avaliador são tratamentos editoriais, não ScenePlan JSON integralmente validado. Tempos de atuação e decisões criativas continuam sujeitos ao projeto concreto.

Não foram executadas chamadas pagas, uploads externos, geração de fala aprovada, lip-sync ou encadeamento first/last-frame. Esses modos permanecem bloqueados enquanto não houver evidência e entradas adequadas. A ladder LF-001/LF-002/LF-003 continua bloqueada: A003 prova apenas o segmento S01. LF-004 não foi executada. O adaptador de API não produz sozinho proveniência completa equivalente à do runtime local. As inspeções de quadros demonstram somente os resultados observados dos artefatos locais e não substituem áudio, física fina, identidade, emoção ou montagem editorial.

O preflight genérico verifica tipos, links, opções e limites conhecidos do inventário; o `submit` local exige ainda dispositivo selecionado, piso de VRAM livre e margem explícitos, bloqueando antes do POST quando o snapshot não atende. Semânticas internas de nós customizados continuam pertencendo ao runtime, e nenhum snapshot garante que a inferência caberá. Mudanças de hardware ou parâmetros não herdam o sucesso do teste local. O verificador de long-form rejeita referências declaradas que não resolvem para bytes e registros aceitos.

A entrega está pronta para planejamento e para o fluxo local comprovado. Uma certificação universal “AAA” não pode ser deduzida desses testes; qualidade final precisa ser demonstrada em cada produção.

## Distribuição

O [ZIP autocontido R5](dist/video-generation-engineering-triple-aaa-r5.zip) contém somente a pasta da Skill, sem pesos de modelo, segredos ou mídia privada. O [manifesto R5](verification/distribution-triple-aaa-r5.json) registra CRC, SHA, scans e smoke externo. Para outro projeto, extraia a pasta em `.agents/skills/`; não é necessário copiar `docs/`, testes ou evidências históricas.
