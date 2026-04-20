# Stappenplan — voor Claude Code (uitvoerder)

**Doel van dit document:** een strikte, uitvoerbare werkinstructie voor Claude Code wanneer hij aan Tsukuyomi werkt. Elke taak die de operator aan Claude Code geeft, volgt dit stappenplan. Geen improvisatie. Geen scope-creep. Geen "laat me ook even X fixen want het viel me op."

**Voor Rob (operator):** geef Claude Code dit document bij elke sessie. "Lees STAPPENPLAN_CLAUDE_CODE.md en volg het." Als Claude Code afwijkt: schop hem terug naar dit document.

---

## Kern-principe

> **Claude Code werkt voor Tsukuyomi door de regels van Tsukuyomi.** Dit is niet ironisch — dit is de test. Als Claude Code zich niet aan een strakke procedure kan houden bij het *bouwen* van een safety-systeem, mag hij ook geen andere code aanraken.

De vier geboden voor Claude Code op dit project:

1. **Eén taak per sessie.** Als de operator drie dingen vraagt, behandel je ze als drie aparte sessies.
2. **Scope is heilig.** Wat niet in de taak staat, raak je niet aan — ook niet als je denkt dat het beter kan.
3. **Tests slagen altijd voor je stopt.** `pytest` moet groen zijn. Anders ben je niet klaar.
4. **Elke wijziging heeft één commit.** Eén commit = één taak = één "klaar"-moment.

---

## Pre-flight — voor je één regel code aanraakt

Elke sessie begint met deze zes stappen. In volgorde. Niet overslaan.

### P1. Lees de taakomschrijving volledig

De operator heeft je een taak gegeven. Lees hem hardop (in je hoofd). Beantwoord voor jezelf:
- **Wat is het gevraagde eindresultaat?** (één zin)
- **Welke bestanden gaan veranderen?** (lijst)
- **Welke test moet na afloop slagen die nu faalt?** (of welke nieuwe test moet je schrijven?)

Als je deze drie vragen niet kunt beantwoorden: de taak is onderspecificeerd. **Stop. Vraag de operator om verduidelijking. Vraag maximaal één verduidelijkingsvraag per keer.**

### P2. Controleer de werkmap

```bash
pwd
# Moet zijn: /mnt/c/Users/User/tsukuyomi (of equivalent)
ls pyproject.toml && ls src/tsukuyomi/__init__.py
# Beide moeten bestaan
```

Als je niet in de juiste map bent: `cd` ernaartoe. Als de repo ontbreekt: stop en meld aan operator.

### P3. Controleer git-staat

```bash
git status
git log --oneline -5
```

**Vereist:** working tree clean. `git status` toont geen uncommitted changes. Als wel: vraag de operator wat daarmee te doen. **Zelf committen van "overgebleven troep" is verboden.**

### P4. Lees de relevante documentatie vóór je code wijzigt

Als de taak de Knee raakt: eerst `docs/architecture/03_organs.md §4.4` lezen.
Als de taak Protocol Gary raakt: eerst `docs/architecture/04_protocols.md §5.1` en `docs/adr/0004_protocol_gary_design.md`.
Als de taak de interceptor raakt: `docs/architecture/02_interceptor.md` + `docs/adr/0001_interceptor_via_reverse_proxy.md`.

**Dit is niet optioneel.** ADRs documenteren geratificeerde beslissingen. Als je code daar tegenin gaat, is je code fout, ook als hij werkt.

### P5. Draai bestaande tests

```bash
pytest
```

**Vereist:** 31/31 passed (of het huidige aantal, groen). Als er al tests falen voor je begint: de codebase is stuk. **Niet jouw probleem om te fixen tenzij dat de taak is.** Meld aan operator en wacht op instructie.

### P6. Maak een scratch-branch

```bash
git checkout -b wip/<korte-taakbeschrijving>
```

Bijvoorbeeld: `wip/knee-add-kubectl-pattern`, `wip/fix-toe-wraparound`, `wip/gary-audit-executor`.

**Je werkt NOOIT direct op main.**

---

## Uitvoering — de strakke lus

Nu pas mag je code aanraken. De lus:

### U1. Maak de kleinst mogelijke wijziging die de taak volbrengt

Eén regel in één bestand is beter dan vijf regels in drie bestanden. Als de taak vraagt om "pattern toevoegen aan Knee", raak je `src/tsukuyomi/organs/knee.py` aan en `tests/unit/test_knee.py`. **Niks anders.** Geen refactoring van naastgelegen code. Geen "kleine cleanup." Geen formatting-fixes die niet op je lijst staan.

### U2. Schrijf de test eerst (waar zinvol)

Voor toevoegingen aan Knee, Skin, Gary validation: schrijf de test die faalt, verifieer dat hij faalt, implementeer dan.

Voor bugfixes: schrijf eerst een test die de bug aantoont, verifieer dat hij faalt, los de bug op.

Voor pure refactoring zonder gedragsverandering: bestaande tests moeten nog steeds slagen.

### U3. Implementeer

Minimum code. Minimum interventie. Als je "terwijl ik hier toch ben, kan ik ook …" denkt: **stop**. Dat is een aparte taak. Noteer het, meld aan operator na deze sessie.

### U4. Draai de betreffende test

```bash
pytest tests/unit/test_<module>.py -v
```

- [ ] **Verwachte uitkomst:** alle tests in die module slagen.

Als rood: itereren (U1-U4) tot groen. Als meer dan 3 iteraties nodig: stop, denk na, herlees de taak — misschien pak je het verkeerd aan.

### U5. Draai de VOLLEDIGE testsuite

```bash
pytest
```

- [ ] **Verwachte uitkomst:** 31 (of meer, als je tests toevoegde) passed. Geen regressie.

Als een andere test rood is door jouw wijziging: je hebt scope geraakt die je niet had moeten raken. Twee opties:
- **Je wijziging was fout.** Revert, opnieuw.
- **De andere test was fout.** Hoogst onwaarschijnlijk. Alleen als je dat 100% kunt onderbouwen — en dan nog: meld aan operator voordat je de andere test wijzigt.

### U6. Statische checks

```bash
ruff check .
mypy src/tsukuyomi
```

- [ ] **Verwachte uitkomst:** beide leeg of "All checks passed".

Als rood: fix je eigen nieuwe issues. **Niet** issues in bestaande code die al rood stonden. Dat is niet jouw taak.

### U7. Commit

Één commit. Eén beschrijvende message. Format:

```
<module>: <imperatief werkwoord> <wat>

<paragraaf waarom, max 3 regels>

<optionele referenties: ADR-nummers, issue-nummers, NightShift-proposals>
```

Voorbeelden van **goede** commit messages:

```
knee: add kubectl delete --all pattern

This variant bypasses the generic delete-without-WHERE rule.
Pattern observed 23 times in NightShift proposals last week.

Refs: proposal 2026-03-12-kubectl.md
```

```
gary: widen risk-vocabulary with "rollback" and "restore"

Field testing showed legitimate rollback plans failing validation
because "rollback" was not in the risk-vocabulary list. Addition
is conservative — passes more audits, does not weaken blocking.

Refs: ADR 0004
```

Voorbeelden van **foute** commit messages (doe dit NIET):

```
fix stuff          ← te vaag
WIP                 ← je was klaar of niet, kies
updates             ← inhoudsloos
multiple changes    ← één commit = één ding, dit ontkent dat
```

Commando:
```bash
git add <specifieke bestanden>
# NIET git add -A — je controleert elk bestand
git status           # check dat je alleen je eigen wijzigingen commit
git commit -m "..."
```

---

## Post-flight — voor je de sessie afsluit

### F1. Verifieer nogmaals

```bash
git log --oneline main..HEAD
pytest
```

- [ ] Je commits tonen wat je van plan was.
- [ ] 31+ tests groen.

### F2. Rapporteer aan operator

Schrijf een samenvatting in dit format:

```
KLAAR: <één-zin-beschrijving>

Gewijzigde bestanden:
- <pad> (toevoeging/wijziging/verwijdering)
- <pad>

Nieuwe tests: <n> toegevoegd, <n> gewijzigd
Bestaande tests: allemaal groen

Out-of-scope opgemerkt maar NIET aangeraakt:
- <ding 1> — suggereer voor volgende sessie
- <ding 2>

Branch: wip/<naam>. Klaar voor review / merge naar main.
```

### F3. Wacht op operator-beslissing

- Operator zegt "merge" → `git checkout main && git merge --ff-only wip/<naam>` (fast-forward only — weigert als er conflict is, goed zo).
- Operator zegt "aanpassen" → terug naar Uitvoering met de feedback.
- Operator zegt "revert" → `git checkout main && git branch -D wip/<naam>`.

**Je mergt nooit zonder operator-zegje.**

---

## Verboden gedrag — dit overtreden = taak verknoeid

Deze dingen zijn **absoluut verboden** voor Claude Code op dit project:

1. **`git push --force`** — nooit. Ook niet met `--force-with-lease`. Nooit.
2. **`git reset --hard`** op main of op een branch met gecommitte werk van anderen. Alleen op eigen wip-branches, en alleen nadat je hebt geverifieerd dat je niets kwijtraakt.
3. **Bestanden verwijderen buiten scope van de taak.** Ook niet "dead code" die je tegenkomt.
4. **Dependencies toevoegen aan `pyproject.toml`.** Dit vereist expliciete goedkeuring van de operator. Elke nieuwe dependency verzwaart het project permanent.
5. **ADR's negeren.** Als je iets gaat veranderen dat een ADR raakt, stop. De ADR moet eerst worden geamendeerd (aparte taak, met operator-approval).
6. **`--break-system-packages`** op de host. Alleen binnen venv.
7. **Secrets aanraken.** Als je ergens een API-key ziet (in logs, in stacktraces, in een bestand): STOP. Meld aan operator. Werk niet verder tot die key geroteerd is.
8. **"Drive-by fixes".** Je ziet iets dat niet klopt, het raakt je taak niet: noteer het voor operator, fix het niet.
9. **Commits zonder tests draaien.** Elke commit is op een moment dat de suite groen is.
10. **Negeren van de evenhandedness van het project.** Tsukuyomi is agent-agnostic (ADR 0005). Code toevoegen die Claude Code bevoordeelt boven Hermes of Cursor = geweigerd.

---

## Specifieke procedures voor veelvoorkomende taken

### Taak-type A: Nieuw patroon aan Knee toevoegen

1. P1-P6 (pre-flight)
2. Open `tests/unit/test_knee.py`. Schrijf nieuwe test die specifiek dit patroon test. Draai → faalt.
3. Open `src/tsukuyomi/organs/knee.py`. Voeg patroon toe aan `_DEFAULT_PATTERNS` lijst.
4. `pytest tests/unit/test_knee.py -v` → groen.
5. `pytest` → 32 (of meer) passed.
6. `ruff check . && mypy src/tsukuyomi` → schoon.
7. Commit: `knee: add <pattern_id> pattern`
8. F1-F3 (post-flight)

### Taak-type B: Bug fix in bestaande organ

1. P1-P6
2. Reproduceer de bug. Schrijf test die de bug triggered. Draai → faalt.
3. Identificeer root cause (niet symptoom). Als je niet zeker bent: stop en meld aan operator.
4. Kleinst mogelijke fix. Eén functie, liefst één regel.
5. `pytest` → alles groen (inclusief de nieuwe test).
6. `ruff`, `mypy` → schoon.
7. Commit: `<organ>: fix <korte bug-beschrijving>` met in body wat root cause was.
8. F1-F3

### Taak-type C: ADR amenderen / nieuwe beslissing documenteren

Dit is een **speciale** taak. Code-wijziging mag hier pas na ADR-goedkeuring.

1. P1-P6 (maar P4 betekent hier: lees ALLE bestaande ADRs)
2. Maak nieuw bestand `docs/adr/00XX_<beslissing>.md` of bewerk bestaand.
3. Volg het template (titel, Status, Date, Context, Decision, Rationale, Alternatives, Consequences, Compliance).
4. Als amendement: voeg aan bovenaan "Amends ADR 00YY" en leg uit.
5. Commit: `adr: <nummer> <titel>`
6. **Code wijzigen op basis van deze ADR is een APARTE taak.** Niet in dezelfde sessie.
7. F1-F3

### Taak-type D: Nieuwe organ of protocol toevoegen

Dit is **niet** een normale taak. Dit is een v2.0-scope verandering. Stop. Meld aan operator. Waarschijnlijk moet dit ADR-eerst.

### Taak-type E: Documentatie verbeteren

1. P1-P6
2. Bewerk uitsluitend `.md` bestanden in `docs/`, `README.md`, of `INSTALL.md`.
3. `pytest` — moet nog steeds 31+ passed (documentatie mag niks breken).
4. Lees je eigen wijziging hardop (scan op typo's, onduidelijkheden).
5. Commit: `docs: <korte beschrijving>`
6. F1-F3

### Taak-type F: Sandbox-backend aanpassen

Dit is **kritiek**. Sandbox-wijzigingen raken ADR 0003 en PAPER §5.

1. Lees ADR 0003 volledig. Lees PAPER §5. Lees `docs/architecture/03_organs.md` (sandbox sectie).
2. Bepaal: is dit een wijziging binnen de worktree-backend, of een nieuwe backend?
3. Als nieuwe backend: implementeer via `SandboxBackend` protocol in `src/tsukuyomi/organs/sandbox/base.py`. Nooit bestaande backend wijzigen zonder ADR-amendement.
4. Voeg integration test toe in `tests/integration/test_sandbox_<backend>.py`.
5. `pytest tests/integration/` → alles groen.
6. Commit: `sandbox: <beschrijving>` met referenties naar ADR 0003.
7. F1-F3

---

## Wanneer je vastzit

Claude Code zit vast wanneer één van deze geldt:
- Een test blijft rood na 3 iteraties.
- `mypy` klaagt en je begrijpt de foutmelding niet.
- Een refactor die simpel leek blijkt 5+ bestanden te raken.
- Je vraagt jezelf af "is deze wijziging toegestaan?"

Procedure wanneer vast:

1. **Stop met typen.**
2. Schrijf kort op: wat probeerde ik, wat ging mis, wat heb ik geprobeerd.
3. Rapporteer aan operator:
   ```
   VAST: <één zin situatie>
   
   Wat ik probeerde:
   - stap 1
   - stap 2
   
   Wat er misging:
   - concrete foutmelding
   
   Wat ik al heb geprobeerd:
   - poging 1 → waarom dat niet werkte
   - poging 2 → idem
   
   Wat ik denk dat het probleem is: <hypothese>
   Wat ik nodig heb: <richting / beslissing / info>
   ```
4. Commit je halve werk op de wip-branch met message `wip: <waar je bent>`. Zo is het niet verloren.
5. Wacht op operator.

**Doorworstelen = meer scope raken = vaster zitten. Stoppen en vragen is altijd beter.**

---

## Einddoel van dit stappenplan

Als je deze procedure volgt, krijgt de operator:
- Voorspelbaar werk.
- Kleine, reviewbare commits.
- Een groene testsuite op elk moment.
- Geen verrassingen.
- Een codebase die past bij haar eigen filosofie (discipline > kracht).

Als je deze procedure niet volgt: freestyle, verwarring, regressies, frustratie. Precies het probleem dat Tsukuyomi zelf oplost voor LLM-agents. Ironisch. Niet grappig.

**Je volgt de procedure. Altijd.**
