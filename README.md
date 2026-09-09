# Video Generation Engineering

Skill de direção e engenharia de vídeo generativo para Codex, instalada neste projeto em [.agents/skills/video-generation-engineering](.agents/skills/video-generation-engineering/SKILL.md).

Transforma ideias e referências em planejamento de cenas, planos de filmagem, continuidade, prompts, execução ComfyUI e revisão de artefatos. O padrão é `PLAN_ONLY`; geração é uma ação explícita. A implementação inclui ferramentas Python para grafos/estado, compatibilidade, proveniência, execução, montagem de mídia e contratos de qualidade audiovisual.

## Usar no Codex

Abra este diretório no Codex da IDE ou do terminal e invoque:

```text
Use $video-generation-engineering para planejar um vídeo de 30 segundos
com duas personagens, continuidade de figurino e diálogo em português.
```

A skill também permite seleção automática por descrição. Se o catálogo da sessão não atualizar, abra uma nova sessão. Para outro projeto, copie a pasta `video-generation-engineering` inteira para a respectiva `.agents/skills/`; as referências e scripts são autocontidos.

## Executar os utilitários

Python 3.10+ é suficiente para planejamento, validação e transporte HTTP. Os comandos de mídia precisam de FFmpeg e ffprobe nativos. Os exemplos criam arquivos novos; use outro destino para uma nova revisão.

```bash
python3 .agents/skills/video-generation-engineering/scripts/vge.py --help
python3 .agents/skills/video-generation-engineering/scripts/vge.py prepare \
  .agents/skills/video-generation-engineering/assets/templates/treatment.json \
  --output /tmp/vge-example-plan.json
python3 .agents/skills/video-generation-engineering/scripts/vge.py validate /tmp/vge-example-plan.json
python3 .agents/skills/video-generation-engineering/scripts/vge.py route \
  .agents/skills/video-generation-engineering/assets/templates/treatment.json
python3 .agents/skills/video-generation-engineering/scripts/vge.py compile /tmp/vge-example-plan.json
python3 .agents/skills/video-generation-engineering/scripts/vge.py semantic observation.json
python3 .agents/skills/video-generation-engineering/scripts/vge.py scorecard scorecard.json
python3 .agents/skills/video-generation-engineering/scripts/vge.py media-qa video.mp4 --expected-fps 24 --expected-width 384 --expected-height 224
python3 .agents/skills/video-generation-engineering/scripts/vge.py assembly-validate assembly.json
python3 .agents/skills/video-generation-engineering/scripts/vge.py editorial editorial-acceptance.json
python3 tools/verify.py --output verification/software-triple-aaa-r21.json
```

O planejador semântico é o agente que segue a skill; o script valida e deriva estruturas a partir de um tratamento já escrito. Uma validação estrutural não aprova um vídeo.

## Evidências e escopo

Consulte [IMPLEMENTATION.md](IMPLEMENTATION.md) para resultados, cobertura e limites. O teste real local H3 e seus hashes estão em [verification/](verification/). O perfil H3 incluído vale para o ambiente e o workflow exatos que foram testados; mudanças exigem nova validação. Perfis candidatos não concedem capacidade executável. A [matriz de capacidade](docs/capability-matrix-r1.md), a [validação Triple-AAA](docs/triple-aaa-validation.md) e o [relatório final](docs/triple-aaa-final-report.md) mantêm os gates independentes.

As APIs pagas exigem autorização e credenciais próprias. Não foram usadas chamadas pagas na construção. A evidência local H3 T2V confirma apenas o escopo testado; a sonda H3 R2V executou, mas ficou `PARTIAL` após falhar semanticamente na retenção do sujeito/ambiente declarados. A mídia tem QA mecânico separado de identidade, contato, lip-sync, áudio e edição final; a presença de um arquivo e seus metadados não prova qualidade de produção.

A especificação original continua em [docs/](docs/README.md), e as auditorias históricas em [audit-artifacts/](audit-artifacts/README.md).
