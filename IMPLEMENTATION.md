# Implementação — 8 de setembro de 2026 (R2)

A skill está implementada em [.agents/skills/video-generation-engineering](.agents/skills/video-generation-engineering/SKILL.md), com direção semântica pelo agente e ferramentas determinísticas para planejamento, continuidade, compatibilidade, execução, proveniência, montagem e qualidade audiovisual. Pode ser usada neste projeto pela IDE ou pelo terminal com `$video-generation-engineering`.

## Entrega

- Entrada concisa, metadados de descoberta e nove referências carregadas conforme a tarefa.
- Tratamento de exemplo completo, contratos JSON, propagação de estado, DAG, timelines, conflitos, câmera, diálogo, áudio, restrições e compilação de prompts estruturados.
- Descoberta e preflight de grafos ComfyUI, vinculação explícita de entradas/parâmetros, submissão autorizada, consulta pelo mesmo ID, coleta e registros imutáveis com SHA-256.
- Negociação por perfil e evidência: perfil local H3 confirmado no escopo testado; Wan 2.2 e Hailuo API candidatos. Adaptador Hailuo com preparação e transporte testado sem chamadas pagas.
- Validação de observações, scorecard de 14 dimensões, transições com dois artefatos observados, re-anchor, contato físico com sete fases canônicas, ownership/vehicle-state, diálogo/áudio em canais separados, causalidade, adaptação diferencial, reparo orçamentado, FFmpeg/ffprobe, montagem e folhas de contato.
- Ladder LF-001..LF-004 com fixtures estruturais; `validate_long_form_case` falha fechado para PASS declaratório e exige tentativas, artefatos, observações, transições e assembly hash-bound.
- QA mecânico de mídia separado de QA semântico, ladder de 10–120 segundos, níveis de maturidade, gates independentes e relatório de release sem promoção indevida de evidência.
- Suíte de regressão e integração, avaliação de uso por outro agente, rastreabilidade e evidências reproduzíveis.

O pacote usa Python 3.10+ e biblioteca padrão. FFmpeg e ffprobe nativos são necessários para os comandos de mídia. Não inclui pesos de modelos. [ADR-011](docs/adr/ADR-011-skill-implementation-and-evidence.md) registra as decisões de implementação; [README](README.md) contém os comandos de uso.

## Verificação

| Procedimento executado | Resultado e limite |
|---|---|
| Suíte Python | 120 testes passaram, sem falhas ou skips: planejamento, mutações inválidas, contratos de qualidade, HTTP local simulado, API paga simulada, proveniência e mídia sintética real |
| Validação de Skill | `quick_validate.py` passou e `compileall` passou para scripts, testes e ferramentas |
| Pacote | ZIP R1 com CRC válido; cópia para diretório temporário externo executou help, prepare, validate e compile |
| Revisão independente de código | Oito problemas corrigidos com regressões; auditorias fresh sucessivas fecharam vínculos de evidência, deriva e orçamento no escopo revisado |
| Uso independente | Respostas efetivas para 12 cenários principais e 17 adversariais; revisão de oito respostas após problemas observados; G-004 passou prepare/validate/compile |
| ComfyUI instalado | H3 T2V e H3 R2V foram observados localmente com runtime, nós, workflow, modelo, dispositivo, tentativa e artefato hash-bound; T2V é confirmado apenas no escopo exato e R2V permanece `PARTIAL` após inspeção semântica |
| QA de mídia | Artefatos locais passaram checks mecânicos de integridade, alinhamento, decode, preto e freeze; isso não aprova identidade, física, emoção, continuidade ou lip-sync |
| Mídia gerada | H3 T2V: MP4 H.264, 384×224, 124 quadros, 24 FPS, 5,167 s, AAC estéreo 32 kHz. H3 R2V: MP4 coletado de 832×480, 124 quadros, 24 FPS; retenção veterinária/identidade declarada falhou semanticamente |

Os erros encontrados durante a construção incluíram validação de perfil candidato e tolerância de duração, seleção de FFmpeg via wrapper Flatpak, estados desconhecidos, inconsistências de parâmetros e promoção indevida de tentativas. Foram corrigidos antes do resultado final. As respostas e falhas iniciais da avaliação de uso foram preservadas.

Evidências: [verificação Triple-AAA do software](verification/software-triple-aaa-r16.json), [manifesto de distribuição](verification/distribution-triple-aaa-r2.json), [crítica independente R6](verification/triple-aaa-independent-critic-r6.md), [QA mecânico H3 T2V](verification/media-qa-h3-t2v-r1.json), [QA mecânico H3 R2V](verification/h3-r2v-media-qa.json), [observação semântica R2V](verification/h3-r2v-semantic-observation.json), [scorecard de continuidade R2V](verification/h3-r2v-continuity-scorecard.json), [matriz de capacidade](docs/capability-matrix-r1.md), [ladder long-form](docs/long-form-validation.md) e [relatório final](docs/triple-aaa-final-report.md). As auditorias históricas continuam preservadas e não são reutilizadas como veredito atual.

Para repetir as verificações locais:

```bash
python3 tools/verify.py
python3 -m unittest discover -s tests -v
```

Esses comandos não submetem geração nem invocam provedores externos. `tools/verify.py --output caminho-novo.json` grava relatório com comandos/testes e hashes do pacote.

## Vídeo e execução real

[Abrir amostra gerada](verification/media/final/art_2898879072af4739b673efe71fafcc7e.mp4) · [folha de contato](verification/media/h3-contact-sheet.jpg).

A primeira inferência levou aproximadamente 36,95 segundos na RTX 3060 de 12 GB. O teste final foi uma submissão deliberada para verificar o código final, com a fila livre e o mesmo workflow; o ComfyUI reutilizou seus nós em cache. Portanto, houve uma inferência observada e uma integração adicional com cache, não duas inferências independentes.

O SHA-256 do vídeo é `623f04987e1401623f6bb9e31c6823b23e56694719681d081e7484303538d124`. [Histórico final](verification/h3-final-history.json), [artefato coletado](verification/h3-final-artifacts.json), [metadados](verification/h3-final-media-probe.json) e [observação inicial PARTIAL](verification/h3-observation.json) mantêm a proveniência. O perfil incluído expira em 15/09/2026 e exige nova validação se runtime, modelos ou workflow mudarem.

## Cobertura e limites de aceitação

Os [79 requisitos têm responsáveis de implementação e referências de evidência](verification/requirements-coverage.json). Esse mapeamento não representa 79 aprovações de qualidade de produção. A especificação separa julgamento semântico, contratos estruturais, capacidade do runtime e observações da mídia; a entrega mantém essa separação.

O planejamento de 45 e 90 segundos recebeu fixtures explícitos de decomposição, Scene Bible, continuidade e recovery; os limites contínuos até 120 segundos têm testes estruturais. Não foi produzido e aprovado um filme completo de 45–120 segundos. As respostas longas do avaliador são tratamentos editoriais, não ScenePlan JSON integralmente validado. Tempos de atuação e decisões criativas continuam sujeitos ao projeto concreto.

Não foram executadas chamadas pagas, uploads externos, geração de fala aprovada, lip-sync ou encadeamento first/last-frame. Esses modos permanecem bloqueados enquanto não houver evidência e entradas adequadas. A ladder LF-001/LF-002/LF-003 está bloqueada e LF-004 não foi executada. O adaptador de API não produz sozinho proveniência completa equivalente à do runtime local. A inspeção de quadros demonstra apenas o resultado observado da sonda R2V e não substitui áudio, física fina, identidade, emoção ou montagem editorial.

O preflight genérico verifica tipos, links, opções e limites conhecidos do inventário; semânticas internas de nós customizados continuam pertencendo ao runtime. Mudanças de hardware ou parâmetros não herdam o sucesso do teste local. O verificador de long-form rejeita referências declaradas que não resolvem para bytes e registros aceitos.

A entrega está pronta para planejamento e para o fluxo local comprovado. Uma certificação universal “AAA” não pode ser deduzida desses testes; qualidade final precisa ser demonstrada em cada produção.

## Distribuição

O [ZIP autocontido R2](dist/video-generation-engineering-triple-aaa-r2.zip) contém somente a pasta da skill, sem pesos de modelo. [Manifesto de distribuição](verification/distribution-triple-aaa-r2.json) registra os arquivos, o hash do ZIP e a validação externa. Para outro projeto, extraia a pasta em `.agents/skills/`. Não é necessário copiar `docs/`, testes ou evidências históricas.
