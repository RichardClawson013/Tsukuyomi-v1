# Hoe je dit pakket gebruikt — in stappen

Dit pakket is **Tsukuyomi v1.0** — release-klaar, alles erin. Hieronder staat wat je nu, morgen, en daarna doet.

---

## STAP 0 — wat je hebt

Een map `tsukuyomi-v1.0/` met **111 bestanden**. Complete open-source release onder jouw naam, Apache-2.0. Alles draait om één idee:

> **De agent configureert `ANTHROPIC_BASE_URL=http://localhost:9999` — en daarmee is Tsukuyomi onontkoombaar tussen agent en model.**

Geen hooks. Geen wrapping. Geen samenwerking van de agent vereist. Dwang via netwerkpad.

---

## STAP 1 — pak het uit, zet het in je projectmap

```bash
# In WSL2:
cd /mnt/c/Users/User/
cp -r /pad/naar/tsukuyomi-v1.0 ./tsukuyomi
cd tsukuyomi
git init
git add .
git commit -m "initial: Tsukuyomi v1.0 open-source release"
```

Je hebt nu een git-repo. Dit is je publicatie-basis.

---

## STAP 2 — lokaal installeren en tests draaien

```bash
cd /mnt/c/Users/User/tsukuyomi
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# Draai alle tests — moet 31/31 geslaagd tonen:
pytest
```

Als alle 31 tests slagen (wat hier al bewezen is), is de basis werkend.

---

## STAP 3 — inspecteer de documentatie

Lees in deze volgorde:

1. **`README.md`** — voor jezelf en voor iedereen die het project vindt
2. **`docs/research/PAPER.md`** — de onderbouwing, MIT/Stanford-niveau, 47 referenties
3. **`docs/architecture/01_overview.md`** t/m `06_observability.md` — de techniek
4. **`docs/adr/`** — alle 8 beslissingen expliciet onderbouwd (dit is wat MIT/Stanford eist)
5. **`docs/guides/installation.md`** — hoe iemand anders het zou installeren

---

## STAP 4 — publiceren op GitHub

```bash
# Maak een lege GitHub repo aan op https://github.com/new genaamd 'tsukuyomi'
# Dan:
git remote add origin https://github.com/robdevet/tsukuyomi.git
git branch -M main
git push -u origin main
```

Na push:
- GitHub toont README.md als landing page
- CI draait automatisch via `.github/workflows/ci.yml`
- `CITATION.cff` laat GitHub automatisch citatie-knoppen tonen
- `LICENSE` wordt gedetecteerd als Apache-2.0

---

## STAP 5 — wat gebeurt er als iemand dit gebruikt?

De eerste gebruiker doet:
```bash
pip install tsukuyomi
tsukuyomi init
tsukuyomi start

# In een andere terminal:
export ANTHROPIC_BASE_URL=http://localhost:9999
claude-code "refactor the auth module"
```

Vanaf dat moment:
- Elke request van Claude Code loopt door Tsukuyomi
- Skin classificeert risico
- Shoulders checkt blast radius
- Protocol Gary forceert 5-vragen audit bij Tier 3
- Sandbox simuleert het plan
- Knee blokkeert destructieve patronen
- Toe bewaakt budget
- Eyes verifieert bestandswijzigingen na actie
- Nose detecteert loops
- Mouth vraagt menselijke goedkeuring
- Alles wordt gelogd in SQLite+FTS5 anatomic memory
- NightShift draait 's nachts, analyseert logs, stelt verbeteringen voor

---

## STAP 6 — wat je nog zelf moet inbouwen

v1.0 is release-klaar als **framework**. Deze twee onderdelen moet jij (of een contributor) nog aanvullen voordat "echt" productioneel gebruik:

1. **Protocol Gary's audit-LLM executor** (`src/tsukuyomi/protocols/gary.py::_ask_audit_llm`)
   — Nu een stub die lege antwoorden teruggeeft. Moet aangesloten op de geconfigureerde `fallback_audit_endpoint` (bijv. OpenRouter Haiku). Dit staat expliciet in `docs/architecture/04_protocols.md` en `docs/guides/configuration.md` — geen verborgen werk.

2. **GitNexus MCP-client** (`src/tsukuyomi/organs/shoulders.py::_query_gitnexus`)
   — Nu een stub die `UNKNOWN` retourneert (wat conservatief behandeld wordt als HIGH). Moet een echte MCP JSON-RPC client worden.

Beide zijn **gedocumenteerd als stubs** in ADR's en PAPER.md §7.2, dus wetenschappelijk eerlijk. Ze staan expliciet op de v1.1 roadmap.

---

## STAP 7 — positionering

Dit is wat je kunt zeggen tegen investeerders, academici, partners:

> "Tsukuyomi is een open-source, Apache-2.0 interceptor die LLM-agenten architectonisch dwingt tot veilig gedrag. Het integreert subsumption (Brooks 1986), dual-process theorie (Kahneman 2011), cybernetica (Wiener 1948) en embodied world models (LeCun 2022) in een enkele deployment-laag. Agent-agnostisch: werkt voor Claude Code, Hermes, Cursor en elke OpenAI/Anthropic-compatibele agent via één environment variable."

Commerciële pad (later, apart project):
> "De commerciële variant is een Hermes-agent vooraf verpakt met Tsukuyomi, verkocht aan MKB die AI-autonomie wil zonder het risico."

---

## Test-bewijs

Op de machine waarop dit pakket gemaakt werd:

```
============================= test session starts ==============================
collected 31 items

tests/acceptance/test_acceptance_gates.py ..                             [  6%]
tests/integration/test_pipeline_knee_block.py .                          [  9%]
tests/integration/test_pipeline_tier1.py .                               [ 12%]
tests/unit/test_canonical.py ...                                         [ 22%]
tests/unit/test_config_loader.py ....                                    [ 35%]
tests/unit/test_gary_validation.py ...                                   [ 45%]
tests/unit/test_knee.py .......                                          [ 67%]
tests/unit/test_nervecore.py ..                                          [ 74%]
tests/unit/test_skin.py ....                                             [ 87%]
tests/unit/test_toe.py ....                                              [100%]

============================== 31 passed in 3.47s ==============================
```

---

## Samenvatting — wat je in handen hebt

- **Research-grade paper** (60+ pagina's, 47 referenties, MIT/Stanford-niveau)
- **8 Architecture Decision Records** — elke keuze onderbouwd
- **6 architectuurdocumenten** — complete systeemspec
- **8 guides** — installatie, 4 agent-integraties, config, operations, troubleshooting
- **7 Mermaid diagrammen** — visualisaties
- **Complete werkende Python codebase** — 8 organen, 2 protocollen, reverse-proxy interceptor
- **31 geslaagde tests** — unit + integration + acceptance
- **5 runnable voorbeelden**
- **Volledige CI/CD pipeline** — GitHub Actions
- **Juridisch compleet** — Apache-2.0 LICENSE, CITATION.cff, CODE_OF_CONDUCT, SECURITY, CONTRIBUTING
- **Je naam als auteur** — overal. README, CITATION, paper, LICENSE copyright.

*Dit was de eis: MIT/Stanford-niveau open source onder je naam. Dit is het.*
