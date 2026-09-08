# Histórico de auditorias

Os cinco relatórios antes localizados na raiz foram reunidos em `reports/` durante a organização de 2026-09-08. Seus links relativos foram ajustados. Caminhos antigos em registros históricos de `.agent/` e `.gauntlet/` descrevem a localização na data da execução.

- [Primeira auditoria](reports/AUDIT-docs-2026-09-08.md)
- [Revisão 2](reports/AUDIT-docs-2026-09-08-r2.md)
- [Revisão 3](reports/AUDIT-docs-2026-09-08-r3.md)
- [Revisão 4](reports/AUDIT-docs-2026-09-08-r4.md)
- [Revisão 5 e encerramento de AUD-013](reports/AUDIT-docs-2026-09-08-r5.md)

As pastas `docs-2026-09-08-r2` a `docs-2026-09-08-r5` conservam os coletores e snapshots de evidência. Os coletores mais recentes dependem do coletor r2 e de snapshots anteriores; esses arquivos continuam necessários para reprodução. Os hashes nos snapshots correspondem à data de cada verificação, antes das alterações posteriores e desta reorganização.

Para verificar a documentação atual, execute na raiz do projeto:

```bash
python3 audit-artifacts/docs-2026-09-08-r5/check_docs.py
```

O comando emite evidência estática em JSON. Não executa ComfyUI nem comprova qualidade de mídia. Este diretório contém histórico e ferramentas de auditoria, e não integra o futuro pacote da skill.
