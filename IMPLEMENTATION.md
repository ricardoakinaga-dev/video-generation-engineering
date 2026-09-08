# Implementação — 8 de setembro de 2026

A skill está implementada em [.agents/skills/video-generation-engineering](.agents/skills/video-generation-engineering/SKILL.md), com direção semântica pelo agente e ferramentas determinísticas para planejamento, continuidade, compatibilidade, execução, proveniência e montagem. Pode ser usada neste projeto pela IDE ou pelo terminal com `$video-generation-engineering`.

## Entrega

- Entrada concisa, metadados de descoberta e nove referências carregadas conforme a tarefa.
- Tratamento de exemplo completo, contratos JSON, propagação de estado, DAG, timelines, conflitos, câmera, diálogo, áudio, restrições e compilação de prompts estruturados.
- Descoberta e preflight de grafos ComfyUI, vinculação explícita de entradas/parâmetros, submissão autorizada, consulta pelo mesmo ID, coleta e registros imutáveis com SHA-256.
- Negociação por perfil e evidência: perfil local H3 confirmado no escopo testado; Wan 2.2 e Hailuo API candidatos. Adaptador Hailuo com preparação e transporte testado sem chamadas pagas.
- Validação de observações, critérios pendentes, dispensas específicas, reparo de planos dependentes, FFmpeg/ffprobe, montagem e folhas de contato.
- Suíte de regressão e integração, avaliação de uso por outro agente, rastreabilidade e evidências reproduzíveis.

O pacote usa Python 3.10+ e biblioteca padrão. FFmpeg e ffprobe nativos são necessários para os comandos de mídia. Não inclui pesos de modelos. [ADR-011](docs/adr/ADR-011-skill-implementation-and-evidence.md) registra as decisões de implementação; [README](README.md) contém os comandos de uso.

## Verificação

| Procedimento executado | Resultado e limite |
|---|---|
| Suíte Python | 102 testes passaram, sem falhas ou skips: planejamento, mutações inválidas, HTTP local simulado, API paga simulada, proveniência e mídia sintética real |
| Pacote | Metadados válidos, referências internas verificadas; cópia para diretório temporário externo executou help, prepare e compile |
| Revisão independente de código | Oito problemas corrigidos com regressões; nova inspeção não encontrou bloqueador concreto no escopo revisado |
| Uso independente | Respostas efetivas para 12 cenários principais e 17 adversariais; revisão de oito respostas após problemas observados; G-004 passou prepare/validate/compile |
| ComfyUI instalado | Há evidência local datada de inferência H3 e coleta; a suíte atual mantém essa evidência separada dos testes offline e exige nova execução após mudanças de runtime/workflow |
| Mídia gerada | MP4 H.264, 384×224, 124 quadros, 24 FPS, 5,167 s, AAC estéreo 32 kHz; inspeção de oito quadros não equivale a aprovação audiovisual completa |

Os erros encontrados durante a construção incluíram validação de perfil candidato e tolerância de duração, seleção de FFmpeg via wrapper Flatpak, estados desconhecidos, inconsistências de parâmetros e promoção indevida de tentativas. Foram corrigidos antes do resultado final. As respostas e falhas iniciais da avaliação de uso foram preservadas.

Evidências: [verificação final do pacote](verification/software-final-r3.json), [portabilidade](verification/portable-package.json), [revisão técnica](verification/independent-code-review.json), [uso inicial](verification/forward-review.md), [revisão de uso](verification/forward-review-r2.md) e [verificação documental](verification/docs-final.json). A revisão de uso R2 reutilizou o contexto do avaliador; não é uma segunda avaliação independente dos 29 casos.

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

O planejamento de 60 e 90 segundos recebeu avaliação de decomposição e continuidade; os limites contínuos até 120 segundos têm testes estruturais. Não foi produzido e aprovado um filme completo de 60–120 segundos. As respostas longas do avaliador são tratamentos editoriais, não ScenePlan JSON integralmente validado. Tempos de atuação e decisões criativas continuam sujeitos ao projeto concreto.

Não foram executadas chamadas pagas, uploads externos, geração de fala aprovada, lip-sync ou encadeamento first/last-frame. Esses modos permanecem bloqueados enquanto não houver evidência e entradas adequadas. O adaptador de API não produz sozinho proveniência completa equivalente à do runtime local. A inspeção de quadros demonstra apenas consistência visual ampla; áudio, física fina, identidade, emoção e montagem editorial ainda precisam dos procedimentos indicados pela skill.

O preflight genérico verifica tipos, links, opções e limites conhecidos do inventário; semânticas internas de nós customizados continuam pertencendo ao runtime. Mudanças de hardware ou parâmetros não herdam o sucesso do teste local.

A entrega está pronta para planejamento e para o fluxo local comprovado. Uma certificação universal “AAA” não pode ser deduzida desses testes; qualidade final precisa ser demonstrada em cada produção.

## Distribuição

O [ZIP autocontido](dist/video-generation-engineering.zip) contém somente a pasta da skill. [Manifesto de distribuição](verification/distribution-final-r3.json) registra os arquivos e o hash do ZIP. Para outro projeto, extraia a pasta em `.agents/skills/`. Não é necessário copiar `docs/`, testes ou evidências históricas.
