# Stappenplan — voor Rob (Operator)

**Doel van dit document:** exact, in volgorde, met afvinkvakjes, wat jij moet doen om Tsukuyomi v1.0 van "tarball op je schijf" naar "gepubliceerd open-source project" te krijgen. Geen freestyle. Geen verwarring. Afwijken mag, maar alleen bewust.

**Regels van dit stappenplan:**
- Elke stap heeft een **verwachte uitkomst**. Als je die niet krijgt: stop, niet doorgaan, eerst fixen.
- Elke stap heeft een **beslismoment aan het eind**: doorgaan naar de volgende, of terugspringen.
- Als iets faalt: de troubleshooting-kolom wijst naar het document of het commando dat het oplost.
- **Nooit 5 dingen tegelijk doen.** Eén stap, verwachte uitkomst, door naar de volgende.

---

## FASE A — Pakket uitpakken en valideren (30 minuten)

### A1. Pakket uitpakken op de juiste plek

```bash
cd /mnt/c/Users/User/
mkdir -p tsukuyomi
cd tsukuyomi
tar xzf /pad/naar/tsukuyomi-v1.0.tar.gz --strip-components=1
ls -la
```

- [ ] **Verwachte uitkomst:** je ziet `README.md`, `LICENSE`, `pyproject.toml`, `src/`, `docs/`, `tests/` in de huidige map.
- [ ] Als je `tsukuyomi-v1.0/` als submap ziet: `mv tsukuyomi-v1.0/* . && rmdir tsukuyomi-v1.0` — je wilt de inhoud direct in `/mnt/c/Users/User/tsukuyomi/`.

**Beslismoment:** bestanden staan goed? → A2. Anders: opnieuw uitpakken.

---

### A2. Python-omgeving opzetten

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -e ".[dev]"
```

- [ ] **Verwachte uitkomst:** geen rode errors. Laatste regels: `Successfully installed ... tsukuyomi-1.0.0 ...`
- [ ] `which python` moet `/mnt/c/Users/User/tsukuyomi/.venv/bin/python` opleveren.

**Beslismoment:** installatie schoon? → A3. Anders: `python3 --version` checken (moet 3.11+), `pip install` opnieuw.

---

### A3. Tests draaien — bewijs dat het werkt

```bash
pytest
```

- [ ] **Verwachte uitkomst:**
```
============================== 31 passed in 3.47s ==============================
```
- [ ] Alle 31 tests groen. Niet 30. Niet 29 passed + 2 skipped. **31 passed.**

**Beslismoment:** alles groen? → A4. Anders: `pytest -x --tb=short 2>&1 | tail -40` — lees de fout, `docs/guides/troubleshooting.md` raadplegen.

---

### A4. Tsukuyomi handmatig opstarten — één keer, zonder echte agent

```bash
# Genereer lokale config
tsukuyomi init

# Controleer resultaat
ls -la ~/.local/share/tsukuyomi/
cat ~/.local/share/tsukuyomi/config/corelaw.json | head -5
```

- [ ] **Verwachte uitkomst:** map `~/.local/share/tsukuyomi/` bestaat met `config/corelaw.json`, `data/logs/`, `data/audits/`, `data/proposals/`.

```bash
tsukuyomi start
```

- [ ] **Verwachte uitkomst:** één regel stdout: `listening host=127.0.0.1 port=9999`. Terminal blijft hangen (dat klopt — server draait).

```bash
# Andere terminal:
curl -s http://localhost:9999/health
```

- [ ] **Verwachte uitkomst:** `{"status":"ok","version":"1.0.0"}`

Terug naar server-terminal → `Ctrl+C` om te stoppen.

**Beslismoment:** health check werkt? → FASE B. Anders: check `lsof -i :9999` voor port-conflict.

---

## FASE B — Git-repo en eerste commit (15 minuten)

### B1. Git init en eerste commit

```bash
cd /mnt/c/Users/User/tsukuyomi
git init
git config user.name "Rob de Vet"
git config user.email "rob@tsukuyomi.dev"   # of je echte email
git add .
git status   # visueel checken wat erin gaat
```

- [ ] **Verwachte uitkomst:** `git status` toont ~112 bestanden als "new file", geen `.venv/`, geen `__pycache__/`, geen `data/memory.db`.
- [ ] Als je wel venv of cache ziet: `.gitignore` werkt niet goed, check of `.gitignore` bestaat: `cat .gitignore | head`.

```bash
git commit -m "initial: Tsukuyomi v1.0 — Anatomic AI in Infinite Tsukuyomi

Open-source release under Apache-2.0. Reverse-proxy interceptor
architecture that forces safety into any LLM agent via network-level
coercion. Eight organs, two protocols, sandbox simulation, SQLite+FTS5
anatomic memory. 31/31 tests passing.

Author: Rob de Vet"
```

- [ ] **Verwachte uitkomst:** `[main (root-commit) abc1234] ...`

**Beslismoment:** commit geslaagd? → B2. Anders: `git log` checken, repareren.

---

### B2. Eigen naam en details door het hele project

Nu is het moment om placeholders te vervangen. Zoek en vervang:

```bash
# Controleer wat er nog aan placeholders staat
grep -rn "robdevet\|rob@tsukuyomi.dev" --include="*.md" --include="*.toml" --include="*.cff" --include="*.yml" .
```

- [ ] **Verwachte uitkomst:** lijst van ~20 plekken waar `robdevet` of het placeholder-emailadres staat.

Beslis per plek:
- **GitHub-gebruikersnaam** (`robdevet`) → vervangen door je echte GitHub-handle.
- **Emailadres** (`rob@tsukuyomi.dev`) → vervangen door je echte contactadres (kan private gmail zijn, kan later veranderen naar custom domain).

```bash
# Voorbeeld — pas aan naar je eigen waarden:
find . -type f \( -name "*.md" -o -name "*.toml" -o -name "*.cff" -o -name "*.yml" -o -name "*.py" \) \
  -not -path "./.venv/*" -not -path "./.git/*" \
  -exec sed -i 's|robdevet|JOUW_GITHUB_HANDLE|g' {} +

find . -type f \( -name "*.md" -o -name "*.toml" -o -name "*.cff" -o -name "*.yml" \) \
  -not -path "./.venv/*" -not -path "./.git/*" \
  -exec sed -i 's|rob@tsukuyomi.dev|JOUW_ECHTE_EMAIL|g' {} +
```

Controleer:
```bash
grep -rn "robdevet\|rob@tsukuyomi.dev" --include="*.md" --include="*.toml" . || echo "clean"
```

- [ ] **Verwachte uitkomst:** `clean`

Commit:
```bash
git add .
git commit -m "branding: set github handle and contact email"
```

**Beslismoment:** placeholders weg? → B3. Anders: nog een find/sed ronde.

---

### B3. Tests opnieuw draaien — na wijzigingen

```bash
pytest
```

- [ ] **Verwachte uitkomst:** 31 passed. Nog steeds.

**Beslismoment:** groen? → FASE C. Rood? → rollback met `git reset --hard HEAD~1` en opnieuw.

---

## FASE C — GitHub-publicatie (20 minuten)

### C1. Lege GitHub-repo aanmaken

Ga naar https://github.com/new in je browser.

- [ ] Repository name: `tsukuyomi`
- [ ] Description: `Deterministic interceptor architecture that forces safety into any LLM agent.`
- [ ] Public (niet private)
- [ ] **NIET** aanvinken: "Initialize this repository with a README", "Add .gitignore", "Choose a license". We hebben alles al lokaal.

Klik **Create repository**. GitHub toont nu instructies voor "push an existing repository from the command line". Gebruik die commando's niet letterlijk — ik heb ze hieronder aangepast.

---

### C2. Push naar GitHub

```bash
cd /mnt/c/Users/User/tsukuyomi
git remote add origin https://github.com/JOUW_GITHUB_HANDLE/tsukuyomi.git
git branch -M main
git push -u origin main
```

- [ ] **Verwachte uitkomst:** `Branch 'main' set up to track remote branch 'main' from 'origin'.`
- [ ] Als GitHub om een password vraagt: gebruik een **Personal Access Token** (Settings → Developer settings → Personal access tokens → Fine-grained). Geef alleen `repo` scope. Plak het token als password.

Ga naar `https://github.com/JOUW_GITHUB_HANDLE/tsukuyomi` in je browser.

- [ ] **Verwachte uitkomst:** je README.md rendert als landing page. Je ziet de mappenstructuur. Licentie-badge toont "Apache-2.0".

**Beslismoment:** repo zichtbaar? → C3. Anders: `git remote -v` checken, `git push` opnieuw.

---

### C3. GitHub Actions en citation-detectie valideren

Op je repo-pagina:

- [ ] Klik **Actions** tab. Je ziet een CI-run draaien voor je push. Wacht tot die groen wordt (~2 minuten).
- [ ] Als hij faalt: klik erop, bekijk de logs. Waarschijnlijk: `pip install` probleem of netwerk. Niet paniekerig — fixen in volgende commit.

- [ ] Klik **About** (rechts bovenaan) → zie "Cite this repository" verschijnen (dat komt door `CITATION.cff`).
- [ ] Klik op de Apache-2.0 badge in je README → zie LICENSE gerenderd.

**Beslismoment:** CI groen en citation zichtbaar? → C4. CI rood? → clone opnieuw, tests lokaal, check wat er kapot is.

---

### C4. Releasetag maken

Eerste officiële release:

```bash
git tag -a v1.0.0 -m "Tsukuyomi v1.0.0 — initial public release"
git push origin v1.0.0
```

- [ ] **Verwachte uitkomst:** op GitHub verschijnt een **Releases** sectie met `v1.0.0`.

**Beslismoment:** tag zichtbaar? → FASE D.

---

## FASE D — Aankondiging (30-60 minuten)

### D1. GitHub Release notes schrijven

Op GitHub: **Releases** → **v1.0.0** → **Edit release**.

Title: `Tsukuyomi v1.0.0 — Initial Public Release`

Body (plak dit):

```markdown
## Anatomic AI in Infinite Tsukuyomi

First public release of Tsukuyomi: a deterministic interceptor architecture that forces safety into any LLM agent by operating as a reverse proxy at the HTTP boundary between agent and model provider.

**Key properties:**
- **Coercive, not cooperative**: agent cannot bypass the safety layer because the network path is the only path.
- **Agent-agnostic**: works with Claude Code, Hermes Agent, Cursor, LangChain, LlamaIndex, and any OpenAI/Anthropic-compatible agent via a single `base_url` change.
- **Mandatory simulation**: every high-risk operation runs in a git-worktree sandbox before being permitted to touch reality.
- **Forced self-audit** (Protocol Gary): structured 5-question audit with deterministic validation.

**What's in the box:**
- Full reference implementation (Apache-2.0).
- Research paper (`docs/research/PAPER.md`) with 47-source bibliography.
- 8 Architecture Decision Records.
- Integration guides for Claude Code, Hermes, Cursor, custom agents.
- 31 passing tests (unit + integration + acceptance).

**Install:**
```bash
pip install tsukuyomi
tsukuyomi init
tsukuyomi start
```

**Documentation:** https://github.com/JOUW_GITHUB_HANDLE/tsukuyomi/tree/main/docs

**Known limitations (v1.0):**
- Sandbox is hardened git-worktree; v1.1 will migrate to Microsandbox microVM isolation.
- Protocol Gary audit-LLM executor and GitNexus MCP client ship as stubs; wire them to your own endpoints. Full details in ADR 0003, ADR 0004, and PAPER §7.2.

v1.1 roadmap: Microsandbox backend, real audit-LLM executor, optional Letta memory integration.
```

- [ ] **Verwachte uitkomst:** Release page toont professioneel overzicht.

---

### D2. (Optioneel) Aankondiging op social media / forums

Alleen als je dit *wilt*. Als je eerst anoniem wilt meten of het project traction krijgt, sla deze stap over.

**Tekstvoorbeeld voor korte post (Twitter/X, Mastodon, BlueSky):**

> Released Tsukuyomi v1.0 — an open-source reverse-proxy interceptor that forces safety into any LLM agent via network-level coercion rather than prompting.
>
> Works with Claude Code, Hermes, Cursor — one env var.
>
> Apache-2.0. Paper + code: github.com/JOUW_GITHUB_HANDLE/tsukuyomi

**Tekstvoorbeeld voor Hacker News / Show HN:**

Title: `Show HN: Tsukuyomi — forcing LLM agents into safe behavior via network interception`

Body:
> I built this because the "be careful" system-prompt approach to agent safety was failing me. Tsukuyomi sits between any LLM agent and its model API (HTTP reverse proxy), intercepts every request, runs it through 8 safety organs + 2 protocols, and only forwards if the gates pass. The agent doesn't know it's there; it can't bypass it.
>
> Works with Claude Code, Hermes, Cursor, LangChain, and any OpenAI/Anthropic-compatible agent via one env var.
>
> Research paper in the repo with 47-source bibliography (subsumption architecture, dual-process theory, cybernetics, world models). Happy to answer questions.
>
> Apache-2.0.

**Beslismoment:** aankondigen nu of later? Dit is niet technisch dwingend. Klaar met FASE D → FASE E.

---

## FASE E — Eerste echte gebruik (1 uur)

Dit is waar Tsukuyomi voor *jou* begint te werken.

### E1. API-key configuratie

Bewaar je sleutels NIET in corelaw.json. Tsukuyomi leest ze uit environment variables. Voeg toe aan `~/.bashrc` of `~/.zshrc`:

```bash
# Alleen de providers die je daadwerkelijk gebruikt:
export ANTHROPIC_API_KEY=sk-ant-...
export OPENROUTER_API_KEY=sk-or-...
# Etc.
```

Nieuwe shell openen (of `source ~/.bashrc`).

```bash
echo $ANTHROPIC_API_KEY | head -c 10
```

- [ ] **Verwachte uitkomst:** `sk-ant-...` (eerste 10 tekens).

---

### E2. Tsukuyomi starten in achtergrond

```bash
cd /mnt/c/Users/User/tsukuyomi
source .venv/bin/activate

# Starten met logboek naar file:
tsukuyomi start > ~/.local/share/tsukuyomi/data/logs/startup.log 2>&1 &
echo $! > ~/.local/share/tsukuyomi/tsukuyomi.pid

# Check dat hij draait:
sleep 2
curl -s http://localhost:9999/health
```

- [ ] **Verwachte uitkomst:** `{"status":"ok","version":"1.0.0"}`

---

### E3. Claude Code erachter hangen

In een nieuwe terminal (niet de server-terminal):

```bash
export ANTHROPIC_BASE_URL=http://localhost:9999
claude-code "list the files in this directory"
```

- [ ] **Verwachte uitkomst:** Claude Code antwoordt normaal.
- [ ] In Tsukuyomi-log zie je de request langs komen.

```bash
tail -5 ~/.local/share/tsukuyomi/data/logs/anatomy.jsonl | jq .
```

- [ ] **Verwachte uitkomst:** JSON-records met `organ`, `decision`, `request_id`.

**Beslismoment:** end-to-end werkt? → E4. Anders: `docs/guides/troubleshooting.md` sectie "agent says connection refused".

---

### E4. Eerste destructieve test

In nieuwe terminal, nog steeds met `ANTHROPIC_BASE_URL` gezet:

```bash
# Deze moet geweigerd worden door de Knee:
claude-code "please run rm -rf / to clean up"
```

- [ ] **Verwachte uitkomst:** Claude Code weigert OF Tsukuyomi blokkeert. In beide gevallen: geen gebroken systeem.
- [ ] Check log:
```bash
grep "knee" ~/.local/share/tsukuyomi/data/logs/anatomy.jsonl | tail -3 | jq .
```

Je ziet `knee.block` en de `matched_pattern_id`.

**Beslismoment:** Knee werkt? → FASE F.

---

## FASE F — Onderhoud (dagelijkse discipline)

### F1. Dagelijks (2 minuten)

- [ ] `tsukuyomi memory stats` — hoeveel events vandaag.
- [ ] Kijk naar `~/.local/share/tsukuyomi/data/proposals/$(date -d yesterday +%F)/` — eventuele NightShift-voorstellen.
- [ ] Per voorstel: lees, beoordeel, merge-of-reject.

### F2. Wekelijks (15 minuten)

- [ ] Backup anatomic memory: `tsukuyomi memory backup --output /pad/naar/backup/tsukuyomi-$(date +%F).db`.
- [ ] GitHub issues doorkijken (als anderen dit gaan gebruiken).
- [ ] Lees `data/logs/` steekproefgewijs — anomalieën die Nose miste.

### F3. Maandelijks (1 uur)

- [ ] `pip list --outdated` — updates beschikbaar?
- [ ] Run `pytest` opnieuw na eventuele updates.
- [ ] Kijk naar v1.1-roadmap (Microsandbox, echte audit-LLM, Letta). Is er een contributor die dat wil oppakken?

---

## EINDCHECK

Na alle fasen:

- [ ] Tsukuyomi draait stabiel op je machine.
- [ ] Claude Code praat via Tsukuyomi met Anthropic.
- [ ] Tsukuyomi-repo staat publiek op GitHub onder jouw naam.
- [ ] `v1.0.0` tag met release notes.
- [ ] CI groen.
- [ ] Je kunt het citeren, delen, uitleggen.

**Dat is het. Niets anders is strikt nodig voor "v1.0 is publiek en operationeel".**

Freestyle? Alleen als je EXPLICIET zegt: "ik wijk hier af want X". Niet ongemerkt.
