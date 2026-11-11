# Contributing

Thanks for making the kit better! Ideas, fixes and new redaction rules are all welcome.

- **Never include anything from your own home** in an issue or PR: no exports, entity
  lists, screenshots with names, tokens or MCP URLs. Make a minimal made-up example instead.
- **Tools** (`tools/`) must stay read-only against Home Assistant, work on every install
  type (skip Supervisor-only parts gracefully), and keep zero dependencies beyond PyYAML
  and Node 22+.
- **Redaction:** a new secret pattern needs a rule in `tools/check_secrets.py` *and*, if
  it can be redacted automatically, in `tools/redact.py`. Add a test case to the PR description.
- **Agent rules** (`AGENTS.md`, skills): keep them short and generic. Home-specific
  facts belong in `docs/home.md` of the user's own repo.
- **Vendored skills** are pinned upstream copies — fix them upstream, then refresh with
  `tools/update_skills.sh`.

Before opening a PR:

```bash
python3 tools/check_secrets.py && python3 tools/validate.py
```
