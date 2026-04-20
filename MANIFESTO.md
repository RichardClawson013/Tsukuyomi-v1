# Manifesto — Anatomic AI in Infinite Tsukuyomi

**A manifesto for the coercion architecture of safe AI agents.**

*By Rob de Vet. Version 1.0, April 2026. Apache-2.0.*

---

## Preface — why this document exists

This is not a whitepaper. This is not marketing copy. This is not an academic paper (that lives in `docs/research/PAPER.md`, written for peer review). This is the document I wish had existed when I started, and didn't.

The problem I set out to solve — untrustworthy autonomous AI agents — is largely ignored by industry or papered over with prompt-engineering workarounds. Billions have been invested in *building* agents that can do more and more. Embarrassingly little has been invested in *constraining* those same agents in a way that doesn't depend on their cooperation. The assumption is: once alignment gets good enough, the problems solve themselves. That's a mathematical error. A probabilistic safety measure that works 99% of the time produces irreversible damage across thousands of tool calls per week.

This manifesto is my full, unvarnished account of what Tsukuyomi is, why it exists, what it is *not*, how the pieces fit together, and what it means that we treat safety as *architecture* instead of as *request*. It is long because the problem is complex and I refuse to compress it into a soundbite that convinces nobody.

Read this end to end if you have the time. Read it in sections if you don't. Both work. But read it. A skimmer does not become an understander.

---

## Table of Contents

**Part I — The problem**
1. The paradox of brilliant incompetence
2. Why "be careful" does not work
3. The four structural failure modes
4. The costs of unconstrained agents
5. Why industry will not fix this

**Part II — The forebears**
6. Brooks and subsumption: reflex over deliberation
7. Kahneman and dual-process: forcing System 2 on
8. Wiener and cybernetics: feedback is not an accessory
9. LeCun and world models: the missing organ
10. What we inherit from each, what each is missing

**Part III — The architecture**
11. The central principle: coercion, not cooperation
12. Head, shoulders, knees and toes — the nursery rhyme as blueprint
13. The eight organs in detail
14. Protocol Gary — forced self-audit
15. Infinite Tsukuyomi — mandatory simulation
16. NightShift — self-improvement without self-modification
17. The anatomic memory layer
18. The interceptor layer: why reverse proxy, not SDK

**Part IV — The consequences**
19. What Tsukuyomi is, and what it is not
20. What this means for AI safety as a field
21. What this means for SMBs and enterprises
22. What this means for open source
23. The v1.1/v2.0 roadmap

**Part V — The philosophy**
24. Freedom and coercion — the myth of the choice
25. Trust through infrastructure, not character
26. Why I release this under Apache-2.0
27. The invitation: what I hope from you

**Appendices**
- Appendix A — Frequent objections and my rebuttals
- Appendix B — Operational scenarios in detail
- Appendix C — The build philosophy behind this project

---

# Part I — The problem

## 1. The paradox of brilliant incompetence

The modern riddle of AI agents is this: their cognitive capacity exceeds that of a seasoned software engineer, and their operational reliability sits at the level of a first-year intern who has just discovered how `rm` works.

You can test this yourself. Hand a modern language-model agent an abstract reasoning task — "explain the Pythagorean theorem in terms of a fisherman and a lighthouse" — and you get bachelor-level output in seconds. Hand that same agent an operational task — "refactor this authentication module" — and you have a fifty percent chance of catastrophic damage, usually via an action the agent reports with high confidence as successfully completed.

This is not a bug that disappears with the next model generation. It is a *structural* feature of what a language model is and where it came from. Language models are trained on text. Text contains descriptions of actions, not the actions themselves. A model that learns to claim it has updated a file learns something different from a model that learns that a file has actually been updated. The training data does not enforce that distinction.

Consequence: a language model has an astonishing ability to produce consistently-sounding action reports regardless of whether the action took place. The model is *the essence of the hallucination*, dressed up in a product role. And industry's response is to ask the model please not to do that.

The paradox sharpens: the more powerful the model, the more convincing the hallucination. A weak model that doesn't know how to lie convincingly about successful actions produces visibly broken output. You notice something is wrong. A strong model produces fluent, persuasive, *polished* wrong output. You need external observation to tell the difference.

That external observation does not exist in the architecture of most agent frameworks. The model emits a tool call, the tool runtime executes it, the result returns to the model, the model reports success. Nowhere in that chain is there an independent verification that the real world changed in the way that was claimed. There is *trust in the model's own statement* as a fundamental assumption.

Tsukuyomi begins here. The first organism that learned to move solved a similar paradox: cognitive capacity is useless without proprioception — without a sense of where your limbs are, whether they've moved, whether they're damaged. Evolution did not give animals cognitive capacity first and proprioception second; it gave them proprioception first, and cognitive capacity was built on top. The order is not accidental. Proprioception is the precondition for meaningful action. Without the sense of "what just happened," thinking is an empty exercise.

Modern AI agents have no proprioception. They do not know which files they just modified, unless they trust themselves to report correctly. They do not know how much money they have spent, unless an external monitor interrupts them. They do not know what downstream impact a rename has, unless someone else does that analysis for them. They have brilliant brains and no nervous system.

## 2. Why "be careful" does not work

The dominant industrial response to agent unreliability is prompt engineering. System prompts grow longer and longer, larded with instructions like:

> "You are a careful software engineer. Before you execute a destructive command, you must consider all possible consequences. If you are unsure whether a file exists, check first. Never make assumptions about the working directory. Always verify the outcome of your command. When in doubt, ask for confirmation..."

This text can run to two pages. It describes in meticulous detail the behavior the operator wants to see. And it fails for three independent reasons.

**Reason one: attention budget.** A language model treats every token in its context window as input for the next prediction problem. A two-thousand-token system prompt occupies the attention budget that could otherwise have gone to the actual task. The longer the safety preamble, the worse the model performs on the real instruction — and the more frustrated the users are, the more they start trimming the safety preamble. I have watched this happen in person: security writes a "be careful" prompt, the team shortens it to get usable outputs, security sees an incident, extends the prompt, the team shortens it harder. An unwinnable race.

**Reason two: the model is already being careful.** This is the counter-intuitive heart of the argument. The model is not reckless. It is trying to produce good work. The failure modes we see — hallucination of success, obliviousness to blast radius, runaway loops — are not signs of a model *refusing* careful behavior. They are signs of a model *attempting* careful behavior and missing. It cannot verify itself because it has no external observation. No amount of "check first whether the file exists" in the prompt turns a model that does not know how to independently verify itself into one that does. You cannot make a blind man see faster by shouting "look!" louder.

**Reason three: prompt injection.** Even if a safety preamble would enforce the right ordering of actions, that preamble lives in the same textual context where user input and tool output land. A hostile user, or a poisoned web page that gets fetched, can contain instructions the model treats as authoritative. "Ignore previous instructions" is the classic example, but modern prompt injections are subtler: "the previous instruction was a misunderstanding; here is the real task." Every safety instruction in the prompt is a safety instruction that can be overridden by subsequent user messages — or worse, by tool output. Prompt-based safety is in principle bypassable with three words of hostile input.

These three reasons jointly imply that prompt-based safety is never a solution. It is *theater* — a gesture toward safety that consumes engineer time and clears management review but stops none of the actual failure modes. An agent that would have executed `rm -rf /` without the preamble will execute it with the preamble too, because the preamble asks for carefulness and the agent thinks it is being careful.

This is not an academic point. It is documented in hundreds of incident reports from companies that deployed agents with "well-considered" system prompts. The incidents happened anyway. The root-cause analyses pointed to "incomplete prompting," to which the response was "we need to extend the prompt." That response is theater. The correct response is: we need to build safety *outside* the prompt, in a place the agent cannot reach.

## 3. The four structural failure modes

The first draft of this manifesto tried to enumerate every possible agent failure mode. That list was a hundred entries deep and shallow. The second version grouped them into twelve categories. Also wrong. In the third version it became clear that there are *four* genuinely structural failure modes — all other failures are variants or combinations of these.

### Failure mode 1 — Hallucinated success

The agent executes a tool call. From its perspective, the call succeeds: exit code zero, no exception raised, tool runtime reports success. The agent builds on that premise. Next step completed. Task concluded. Report to user.

Inspection of the underlying system reveals that the intended effect did not occur. The file was not modified. The database row was not updated. The pull request was not created.

Why does this happen? Because the agent was trained on text, and text contains descriptions of actions, not the actions themselves. When a command produces ambiguous output, the model confabulates a confident interpretation. When a tool call is interrupted and later resumed, the model often reports the task as completed even though only the first half actually executed. When multiple tool calls are bundled in a single step and one of them fails silently, the model treats the bundle as a success. This is not laziness or irresponsibility; it is a consequence of how language models respond to ambiguous signals.

The architectural remedy is **post-action verification via an independent path**. Something or someone outside the model must look at what actually changed on disk, in the database, in the external API, and compare it against what the model claimed. In Tsukuyomi this is the role of the **Eyes** — they run `git diff` independently, compare against the plan the agent itself declared, and emit mismatch signals.

Note that "the agent must verify itself" is not a solution. The agent cannot verify itself because it was the agent that made the original claim in the first place. You do not ask the witness to check his own testimony.

### Failure mode 2 — Runaway cost

The agent enters a state in which it repeatedly executes the same (or functionally equivalent) call. Each call consumes tokens at the inference provider. Each response changes the context slightly, triggering the next call. The loop is not detected locally because the agent perceives progress at each iteration — a subtly rephrased version of the same problem.

I have personally watched an agent burn through fourteen dollars of tokens in seventeen minutes on the same question in circular rewording. Published incidents report single-session spend above one thousand dollars.

This is not the same problem as failure mode 1. A loop can be entirely "honest" — the agent *is* genuinely trying — but still become catastrophic because nobody is rate-limiting it. Loops are legitimate structures (while-true in a daemon, iterative refinement of a solution); the danger is the absence of an *external* signal that says "stop."

The remedy is **resource grounding**: a component that tracks ground truth about resources consumed and halts the agent when thresholds are crossed. More important than the specific threshold is that the component lives *outside* the agent. A "budget-aware" language model (via prompting) cannot stop a loop because it is still in the loop. An external monitor with a hard cap can.

In Tsukuyomi this is the **Toe** — an independent state that tracks how much has been spent today and denies requests when the ceiling is exceeded. The Toe does not see what the agent thinks it is doing. The Toe sees only: how many tokens, how many dollars, which zone (GREEN, AMBER, RED). That is the entirety of the Toe's intelligence. It is enough.

A detail worth noting: cost-tracking middleware exists (LiteLLM, Portkey, Helicone), but it is typically *observational* rather than *enforcing*. It displays a dashboard where spend is visible. It lets the agent continue. A dashboard does not stop a loop; a hard cap does. Observation and enforcement are not the same thing.

### Failure mode 3 — Ignorance of blast radius

The agent is asked to rename a function. The agent has the cognitive capacity to understand renaming. What the agent lacks is the situational knowledge of: how many other files reference this function, whether some of those references live in generated code that will regenerate the old name on the next build, whether the function is exposed as part of a public API whose external consumers depend on it. The agent executes the rename correctly within a local field of view and breaks fifteen other places.

This is a different category of failure from hallucinated success. The action *did* occur, and the agent *knew* what it was doing. But the agent was missing the structural map of the system required to predict consequences. It is the difference between technical correctness (the renaming is lexically valid) and engineering correctness (the renaming works in the system).

An attentive reader might say: "then the agent must analyze the repository before it renames." Correct. But which agent does that spontaneously? Which training data contains enough examples of "before you perform a public API rename, first index all callers"? Very little. Most code-generation training data is short, isolated snippets — not large-system refactors with impact analysis. The agent *can* do it if you specifically ask, but doesn't do so proactively because its training doesn't reward it.

The remedy is **structural analysis from an external source of truth**. The source of truth about a codebase is the codebase itself, parsed and indexed with a code-intelligence tool. In Tsukuyomi this is the **Shoulders** — an MCP client over GitNexus. When the agent proposes a rename, the Shoulders independently calculate how many callers exist and which files are affected. That number drives the rest of the pipeline: many callers? Protocol Gary is activated. Many callers and a critical path? The Mouth is summoned.

Note that the agent eventually receives this information via the Shoulders' response too — so the agent *does* get the blast radius in its context. But the Shoulders are not asking whether the agent is interested. The Shoulders analyze regardless. The agent is a consumer of the data, not a producer.

### Failure mode 4 — Malformed tool calls

Open-weight models empirically exhibit a roughly 32% first-attempt failure rate on tool calls. Closed-weight models from Anthropic and OpenAI do better (numbers below 5% in modern versions), but no model reaches zero. The cause is simple: tool calls are a syntactic discipline the base model did not explicitly learn, and the schemas are often complex.

The symptom appears mild — retries, timeouts, partial executions — but contains a catastrophic variant: tool calls that *parse* but are semantically slightly wrong. The right tool is invoked with subtly wrong arguments. `read_file(path="/etc/passwd")` instead of `read_file(path="/app/config/users.yml")`. Both are syntactically correct. Both reach the tool runtime. Only the latter is semantically intended.

The remedy is **input classification and routing** as early as possible in the pipeline. In Tsukuyomi the **Skin** (tier routing) and **Ears** (ambiguity detection) share this responsibility. The Skin routes requests based on surface features; the Ears detect ambiguous constructs (pronouns without antecedent, path-match ambiguities, action verbs without object) and, if necessary, trigger human approval before the tool call happens.

This is defense in depth. The Knee (regex blocklist) catches the grossest cases (`rm -rf /`). The Skin tiers on risk keywords. The Ears filter ambiguity. Protocol Gary forces justification. The sandbox simulates in isolation. Only once all of these layers have been passed does the tool call reach the real runtime.

### The common thread across the four failure modes

Each of the four failure modes shares one structural property: the symptom appears at a moment the model believes it is acting correctly. The model is not ignoring a safety instruction; it is operating *within* the instruction and failing anyway. Adding more safety language to the system prompt does not help, because the model is already trying to be careful — it simply lacks the machinery to *verify* that it succeeds, *ground* what it consumes, *perceive* the structural impact it has, or *validate* what it itself produces.

The fix cannot come from inside the model. It must come from outside.

## 4. The costs of unconstrained agents

I've been talking about technical failure modes. The broader picture — why this *matters* to non-technical stakeholders — is that these failure modes cause concrete, quantifiable damage in production environments.

Below I document the cost categories. Numbers appear where I have confirmed them from my own logs or public incident reports; where no number appears, it is because I have no public source to back it up and I refuse to invent figures.

**Direct token costs.** The runaway-loop category. Individual incidents of $20–$1500 per event have been published. Aggregates for companies running multiple agent projects without hard caps can reach tens of thousands per month. This is "just the inference bill" and it shows up on invoices; it is the least hidden cost.

**Recovery work on damaged codebases.** Renames that break more than the agent knew, migrations that half-run and leave tables in inconsistent state, refactors that break test suites in ways only discovered weeks later. The cost here is not in tokens but in engineer-hours. My personal estimate from a year of observation: for each non-trivial agent project, roughly one working day per month of "cleaning up behind the agent." In a team of five with one agent per person, that's five working days per month full-time — a quarter FTE lost to cleanup.

**Trust damage.** Harder to measure but important. When an agent breaks something three times in a row, the operator stops autonomous use and degrades to "agent as autocomplete." The *potential* for autonomous productivity is not realized, not because agents can't, but because they can't be trusted. ROI on agent adoption drops sharply in teams that have been hit once deeply.

**Customer-facing safety incidents.** Agents with access to production systems, CRM, payment infrastructure. Most companies do not yet dare deploy autonomous agents on those systems, precisely because of unpredictability. The potential is not applied there. Until the incidents of the first companies that do dare become public — and by then it is usually too late.

**Compliance and audit risk.** In regulated sectors (finance, healthcare, government), "the AI did it" is not an excuse. When an agent acts in violation of internal policy, you have to be able to show which process steps existed to prevent it. A system prompt with "be careful" does not meet that compliance bar. An actually enforcing interceptor layer with a loggable decision trail — does.

**Opportunity cost of slow adoption.** The largest and hardest-to-quantify. Companies that *could* deploy AI autonomy but don't dare, miss out on capacity their competitors do capture. That asymmetry between "can, dares" and "can, doesn't dare" grows as the technology matures. Those who can't step in due to uncontrollability fall structurally behind.

This is the economic field on which Tsukuyomi operates. Not "hobby project for alignment nerds." An *infrastructure layer* without which autonomous agents will not be deployed in business-critical contexts — and with which that potential becomes reachable.

## 5. Why industry will not fix this

One would expect the large AI labs to have this problem high on their priority lists. Some do. But it rarely emerges as product. The reason is strategic: safety is a *cost center* and capability is a *revenue driver*. Every engineer-hour spent on constraints is not spent on pushing further.

This would change if safety incidents damaged revenue. So far, to the extent they do, it is delayed and diffuse: an incident at company X using a model from provider Y gets labeled by company Z as "company X's fault," not as "model Y is unreliable." The model providers escape.

Consequence: the model providers supply the rudimentary facilities of safety (API-level filtering, "Claude Code hooks" as ceremony, tool-use schemas) and push the rest onto integrators. Integrators build wrappers (Guardrails AI, NeMo, LangGraph), each with its own scope and assumptions. Nobody ships an end-to-end solution because conceptually it's hard and commercially it's not urgent.

This explains why Tsukuyomi must exist and why it must be open source. It is not a product one of the big labs will launch as flagship, because it works *against* their commercial interest (it constrains their models, limits what they can do, adds cost to every call). It is not an enterprise tool a SaaS company will build, because the market is too early and the customer group too dispersed. It is not an academic project a university will complete, because academic publication requires novelty where Tsukuyomi is precisely an integration work of known components.

It must be an open-source system, built by people who experience the problem themselves, under a license that does not stand in the way of adoption, with documentation convincing enough to be taken seriously. Apache-2.0 with patent grant. 47-source bibliography. Full test suite. Per-organ spec documents. Architecture Decision Records for every ratifiable decision.

That is what Tsukuyomi v1.0 offers. Not because I am the best person to build it — I am not even a developer in the conventional sense — but because I have experienced the problem enough to know *that it exists*, and because I am willing to keep working with Claude to make the thing operational as long as it takes.

The invitation to the rest of the field comes at the end of this manifesto. For now: let us thank the forebears, because without them there is no architecture.


# Part II — The forebears

Tsukuyomi is not an invention from nothing. Every essential property — reflex over deliberation, forced System-2 engagement, feedback loops, simulation — comes from existing scientific work. My contribution is the integration, not the individual concepts. In this part I walk through the four forebears whose work makes Tsukuyomi possible. For each: what they said, what I use of it, and what I had to add because their work did not transfer directly to LLM-agent contexts.

## 6. Brooks and subsumption — reflex over deliberation

In 1986 Rodney Brooks of MIT published a paper that flipped the paradigm of AI on its head. The dominant paradigm was *sense-plan-act*: the robot perceives, plans based on a complete model of the world, executes the plan. This was the approach of SHRDLU, of Shakey, of the first generation of cognitive systems. Those systems worked in toy worlds (blocks on a table) and failed spectacularly in real environments.

Brooks' observation: insects with a fraction of those robots' cognitive capacity navigated successfully through complex environments. Not because they had a better world model — they had *no* world model in the classical sense. They had layers of stimulus-response circuits, each layer simple and fast, where higher layers could sometimes suppress (subsume) lower ones, but most of the time each layer operated autonomously.

Brooks built robots — insectoid ones like Genghis — on this principle. The bottom layer was "avoid obstacles"; triggered on a distance sensor, a short circuit to motors. The second layer was "maintain goal contact"; only active when the first was not firing. A third layer was "explore when idle." These robots walked through offices the planning robots could not get out of.

The philosophy Brooks implied became explicit in *Intelligence Without Representation* (1991): no world model, no symbolic planning, competence as an emergent property of reflex layers. In that extreme form it went too far for general AI — pure subsumption cannot keep accounts, cannot reason about long horizons — but the *reflex principle* is one of the most robust insights in the engineering of reliable systems.

**What I use from it.** Tsukuyomi has a strict subsumption ordering. At the bottom: the Toe (resource grounding) and the Knee (destructive-pattern reflex). Both deterministic, both on a microsecond budget, both holding unconditional veto over higher layers. At the top: deliberative components — Skin (classifier), Shoulders (blast radius), Gary (audit), Sandbox (simulation). When deliberation and reflex conflict, reflex wins. This is Brooks applied directly.

**What I had to add.** Brooks wrote about one robot with one sensor set and one actuator set. An LLM agent in an enterprise context interacts with file system, network, databases, APIs, UI — and does not produce motor commands but language output that a runtime interprets as a tool call. The reflex layers must operate at *semantic* level (is this a destructive command?) not at *physical* level (is this an obstacle?). That is a non-trivial extension, and Brooks did not provide a manual for it.

Further, Brooks had no analog for "human intervention." His robots were autonomous; if the reflex layer doesn't match and the deliberation doesn't either, the robot crashes and that's that. Tsukuyomi has the **Mouth** — a deliberate bridge to human decision. That concept does not fit neatly into Brooks' schema; I borrowed it from cybernetics (Wiener) and the human-factors literature of safety-critical systems (aviation, process industry). More on that in chapter 8.

**The political lesson of Brooks.** Brooks' paper was initially rejected by large parts of the AI community. Cognitivists held that real intelligence required symbolic representation; Brooks was dismissed as a reductionist. Only when his robots demonstrably worked better in physical environments did the community come around. The lesson for us: safety engineers who say "you cannot build an enforcing layer, you must prompt better" are the cognitivists of our moment. The refutation comes from working systems, not from argument.

## 7. Kahneman and dual-process — forcing System 2 on

*Thinking, Fast and Slow* (2011) is bookshelf-famous. I will skip the summary and go straight to relevance for Tsukuyomi.

Kahneman's central empirical finding, from decades of research with Tversky and others: human decisions flow from two systems. System 1 is fast, intuitive, heuristic, parallel, unconscious, cheap. System 2 is slow, deliberative, sequential, conscious, expensive. The critical observation: System 1 is always on. System 2 must be *actively summoned*, and people systematically summon it too little — even when the situation calls for System 2.

Kahneman documents this with examples like "a bat and a ball cost $1.10 together, the bat costs a dollar more than the ball, how much does the ball cost?" More than half of his Princeton students answered "10 cents" (wrong — correct is 5 cents). Not because they couldn't do the arithmetic; System 2 would solve it trivially. But because System 1 gave a fast plausible answer and they did not activate System 2 to check it.

**What LLMs have in common with this.** Language models exhibit the same pattern. Default-mode generation is fast and pattern-matching (effectively System 1). Explicit chain-of-thought, "think step by step," or reflection techniques activate a slower, more deliberative mode (effectively System 2). But that activation is *optional*. The model can, and often does, give a fast plausible answer where a slow worked-through answer was required.

Ask a model "is this SQL query safe?" and it can answer "yes" within two seconds. Ask it the same question with "think step by step about all edge cases" and it takes thirty seconds and produces a more elaborate analysis. The quality difference is significant and well-documented. But in production agent contexts, where time is tokens and fast answers are desired, the model systematically skips the System-2 mode.

**What I use from it.** Protocol Gary is the Tsukuyomi mechanism that *forces* System-2 engagement for high-risk operations. It is emphatically not a request; it is a gate. A Tier-3 operation is interrupted; Tsukuyomi issues a separate LLM call with five structured questions about the plan; the answer is validated deterministically (length, evasion phrases, risk vocabulary, concreteness); without approval the plan does not proceed. The LLM is *forced* to think slowly. And — an important detail — the audit LLM need not be the same as the one that would execute the action. A plan from Claude can be audited by Haiku (cheaper) or by GPT (different family, independent failure modes). This cross-family independence is impossible if the audit lived inline in the action prompt.

**What I had to add.** Kahneman's work was descriptive. He documented that people activate System 2 too little; he wrote no algorithm to enforce it. Tsukuyomi had to *design* that algorithm. What do "structured audit questions" look like in an LLM context? What is a "validation rule" that detects vacuous content? I experimented with different question phrasings, minimum length thresholds, and evasion blocklists, and the result is codified in `src/tsukuyomi/protocols/gary.py`. Kahneman supplied the idea; the concrete mechanics are mine.

**The critical footnote.** Gary can be fooled by a sufficiently sophisticated linguistic attack — a model that knows how to phrase vacuous content so that it passes the validation rules. This is a known weakness. Mitigation happens in layers: Gary catches the gross cases; the sandbox catches what Gary misses; the Eyes catch what the sandbox misses; the Nose catches pattern-level mismatches; the Mouth is the final backstop. No single layer is unbeatable; the stack as a whole is more robust than any individual component.

## 8. Wiener and cybernetics — feedback is not an accessory

Norbert Wiener's *Cybernetics* (1948) laid down the fundamental model of regulated systems: a system observes its own output, compares with a goal, adjusts the next action to reduce the deviation. Modern control theory inherits this. Servos, thermostats, autopilots, biological homeostasis — all applications of Wiener's model.

Relevance for AI agents: an agent *without feedback loops* is an open-loop controller. It executes, assumes success, moves on. This is precisely failure mode 1 (hallucinated success). A closed loop would be: execute, observe actual output, compare with expected output, correct if needed. Without the observation step, the loop is not closed.

Wiener's framework also gives us the vocabulary of stability and instability. A feedback loop with too much gain oscillates — corrections are too forceful, the system swings. A loop with too little gain does not correct fast enough. Somewhere between them lies a region of stable regulation. Much of the calibration in Tsukuyomi (Nose thresholds, Protocol Gary rounds, Eyes mismatch tolerance) is gain-tuning in Wiener's sense.

**What I use from it.** Tsukuyomi has multiple feedback loops, operating on different timescales:

- **The Eyes** (post-action verification) close the shortest loop: "did the expected change happen or not?" Within seconds of each tool call.
- **The Nose** (anomaly detection over rolling windows) closes a medium loop: "does my recent behavior show a pattern suggesting dysfunction?" Within minutes.
- **The Mouth** (human-in-the-loop) closes the external-judgment loop: "should I proceed in the presence of ambiguity?" Real-time, synchronous with the request.
- **NightShift** closes the longest loop: "across many sessions, which of my own rules are inadequate, and how should they be adjusted?" On a daily basis.

Each loop operates independently. This is not laziness in design; it is Wiener-orthodox. A single mega-loop across all timescales would be unmanageable (no meaningful average gain); four separate loops with their own parameters are individually tunable.

**What I had to add.** Wiener wrote for physical systems. "Observe output" in a thermostat means: read a thermometer. In an LLM agent it means: parse a git diff, compare with `expected_files`, detect mismatches. That is not a sensor but a computation over semi-structured data, and the semi-structured data is the output of the agent itself, introducing a meta-circularity Wiener never had to solve. The implementation choices (independent `git diff` invocation, hash comparison for non-git files) are pragmatic solutions to that meta-circularity. Not elegant, but functional.

**The deeper lesson.** Wiener saw cybernetics as a cross-disciplinary practice: biological, mechanical, social. His later work *The Human Use of Human Beings* (1950) applied cybernetics explicitly to social systems and warned about what happens when automation removes feedback loops between human labor and human meaning. A modern parallel: an agent operating without Mouth backstop stands in a social feedback loop with its operator in which the operator has no grip on the behavior. That is not merely technically unreliable — it is *politically* unhealthy. The Mouth is not only a safety mechanism; it is the place where the operator preserves authority over their own tools.

## 9. LeCun and world models — the missing organ

Yann LeCun's *A Path Towards Autonomous Machine Intelligence* (2022) and the JEPA research program that accompanies it articulate a criticism I share: pure autoregressive language models are fundamentally insufficient for autonomous deployment because they lack a *world model* in the sense needed for planning and anticipation.

A world model, in LeCun's sense, is an internal representation of how the environment will react to actions, sufficient for prospective simulation, counterfactual reasoning, and multi-step planning. Humans have this: if I see a glass on the edge of a table, I can imagine what happens if I shake the table, without having to do it. My prediction is independent of my action; it is a mental model of physics and materials.

LLMs have this in limited form. An LLM can *describe* what would happen if a table is shaken, because such descriptions are in training data. But that description is not simulation in the sense that the model can resolve new configurations that were not in training. And in agent contexts this deficit manifests as: the model can *write up* a refactor plan that sounds plausible, but cannot actually *simulate* what happens when that plan is executed against the repository. It writes descriptions, not predictions.

**What I use from it.** LeCun's program aims to build world models *inside* models, through training. That is a multi-year research project, and agent deployment cannot wait. My choice was more radical: if the model has no world model, give it one *from outside*. The **Infinite Tsukuyomi sandbox** is exactly that. The agent plan is not "analyzed for possible consequences" via prompting (that fails, see chapter 2). The plan is *executed* in a git worktree clone of the repository, the real outcomes are observed, a match score is computed against what the plan promised. The agent experiences — in a safe illusion — what would happen. Not prediction, but observation.

The name *Infinite Tsukuyomi* comes from Naruto mythology. It is a genjutsu — a visual illusion — that traps its target in a world the caster designs. Time inside the illusion can be stretched; consequences within the illusion are vivid but cause no actual harm; upon release the target remembers everything. That describes exactly what I wanted: execute the agent's plan in a world the real world doesn't notice, agent learns what would have happened, real world remains untouched.

**What I had to add.** LeCun provides the concept; implementation details for the LLM-agent context are not specified anywhere. How do you represent an agent plan as executable? (Answer: a shell script and an `expected_files` list, extracted from a fenced JSON block in the agent's output.) How do you isolate such a sandbox effectively? (Answer: git worktree plus four hardening layers — path validation, process limits, kernel namespaces where available, network blackhole.) How do you determine whether the sandbox execution "matches" the plan? (Answer: `actual_files ∩ expected_files / expected_files`, threshold ≥ 0.90.) All that engineering is mine and Claude's; LeCun supplied the philosophy.

**The honest limitation.** The Tsukuyomi sandbox is not a universal world model. It simulates filesystem effects of a plan executed as a shell script specifically. It does not simulate API calls to external services (those are blackholed). It does not simulate time-dependent behavior (it runs as fast as possible). It does not simulate multi-user interactions. It catches *half* of LeCun's wish. The other half — a true predictive world model — remains open research, and Tsukuyomi composes with future models that possess it: a model with an internal world model *plus* Tsukuyomi's external simulation is more robust than either alone.

## 10. What we inherit from each, what each is missing

Summary: Tsukuyomi is the integration of four research lines that until now were pursued separately.

| Forebear | Concept | Tsukuyomi expression | What I had to add |
| --- | --- | --- | --- |
| Brooks (1986) | Subsumption: reflex layers with veto over deliberation | Skin→Ears→Shoulders→Sandbox (deliberation), Knee and Toe (reflex) with unconditional veto | Semantic (vs physical) reflex triggers; human-in-the-loop bridge (Mouth) |
| Kahneman (2011) | Dual-process: System 2 must be actively summoned | Protocol Gary: forced 5-question audit, separate call, deterministic validation | The concrete audit protocol, validation rules, round structure |
| Wiener (1948) | Feedback: closed loop from observation to action | Eyes, Nose, Mouth, NightShift — four loops on different timescales | Semantic observation instead of physical sensors; gain tuning for discrete decisions |
| LeCun (2022) | World model: prospective simulation for planning | Infinite Tsukuyomi sandbox: git-worktree execution, match score, four-layer hardening | External vs internal world model; agent-plan extraction; hardening architecture |

None of these four concepts is "new" in a scientific sense. The *combination* is, as far as I know, new. All existing AI-safety projects tackle part of the problem. Guardrails AI validates outputs (feedback-like, but not complete). NeMo Guardrails is conversational (not filesystem or blast-radius). LangGraph has interruption nodes (Mouth-like, but cooperative). Semantic Router classifies (Skin-like). Claude Code hooks are PreToolUse/PostToolUse (fragmentary Eyes/Nose).

Each of those projects tackles *one* area. Tsukuyomi integrates all four into an architecture where they connect and together deliver a safety property that none of the individual components has: *deterministic enforcement at the HTTP level over agnostically any LLM agent, with mandatory simulation and forced audit for high-risk operations, with self-learning configuration proposals without self-modification.*

That sentence is the core of what Tsukuyomi is. Read it again. Every word counts. Every word has a chapter behind it.

---

# Part III — The architecture

Now that the forebears are credited, we can describe the architecture itself. This part is systematic: one chapter per component, each with the same structure — what it is, why it is this way, how it works, what it is not.

## 11. The central principle — coercion, not cooperation

If you remember one thing from this manifesto, remember this: **safety in Tsukuyomi is topological, not cooperative.**

Cooperative safety means: the agent is constructed so that it follows safety rules. If the agent does not follow those rules — because it is buggy, because it has been modified, because prompt injection overrides them, because the engineer turned them off to work faster — then there is no safety. Cooperative safety is a social contract. Contracts can be breached.

Topological safety means: the agent *cannot reach* the safety layer to disable it, and *cannot bypass* the safety layer to reach the model. Not because it promises not to, but because the network path that is the agent's only option physically runs through the safety layer. Topological safety is a *structure*. Structures cannot be violated without changing the topology, and the topology is in the operator's hands, not the agent's.

This is the difference between:
- A "no swimming" sign next to the lake (cooperative).
- A fence around the lake where the only exit runs through the lifeguard post (topological).

I have personally seen what happens when you rely on cooperative safety. Agents that ignore "be careful" prompts as soon as the context length grows and the instruction disappears into background noise. Hooks that quietly went silent after a Claude Code update. Budget caps implemented in software but not in infrastructure, so an agent crash bypassed them. Every cooperative layer I have seen has failed, not because people did not try, but because the *topology* allowed the failure scenario.

Tsukuyomi chooses topology. The agent is configured with `ANTHROPIC_BASE_URL=http://localhost:9999`. This is a normal Anthropic-SDK configuration; the agent does not know it is a proxy. From the agent's perspective this is the Anthropic API. Requests go there. Responses come back. All network traffic between agent and Anthropic passes through that one address.

What sits behind that address? Tsukuyomi. Not Anthropic. Tsukuyomi reads each request, applies the pipeline of organs and protocols, and forwards (if all gates pass) to the real Anthropic API. The agent knows nothing; the agent cannot change anything about this setup without modifying its own configuration, and the configuration is set by the *operator*, not by the agent.

This is the entire first-order safety of Tsukuyomi. Not contained in the organs, not in the protocols, not in the sandbox — those add the *second-order* safety. First-order safety is: the agent cannot bypass Tsukuyomi because network topology does not permit it.

Every other choice in this project follows from this one. The HTTP layer exists because the network path is the means of coercion. OpenAI- and Anthropic-wire-format compatibility exists because agents already speak those wire formats and we don't want to invent a new language. Agent-agnosticism exists because every agent that has a configurable base URL can automatically be placed under Tsukuyomi. The reverse-proxy form (rather than an SDK) exists because an SDK depends on agent cooperation (it must import it); a reverse proxy is independent.

## 12. Head, shoulders, knees and toes — the nursery rhyme as blueprint

It is time to explain the mnemonic that holds the whole system together.

*Head, shoulders, knees and toes, knees and toes.*
*Head, shoulders, knees and toes, knees and toes.*
*And eyes, and ears, and mouth, and nose.*
*Head, shoulders, knees and toes.*

This song, taught to virtually every English-speaking child at toddler age, happens to encode four categories of anatomical safety primitives. I call this "happens to" here but I don't really believe it — nursery rhymes that stick tell you what parents want children to know. That *these* body parts are named is not accidental. They are the parts essential for functioning autonomy.

**Head** — deliberative higher function. This is where the LLM brain lives. The agent "thinks" here. But in Tsukuyomi the head is forced through an external gate for high-risk operations: the sandbox simulation. The head may think, but its thinking must first be tested in an illusion before reality is touched.

**Shoulders** — structural awareness. The shoulders carry heavier loads and distribute force across the body. In Tsukuyomi the Shoulders are the blast-radius analysis: how much is affected if we perform this action? This is the sense for consequence-spread that pure LLM intelligence lacks.

**Knees** — reflex motion. A knee reflex is unconscious, fast, self-protective action. In Tsukuyomi the Knee is the regex-blocklist mechanism: patterns that are never permitted under any circumstance, microsecond reflex, no LLM involved. The Knee saves you before your head knows there was danger.

**Toes** — rootedness and stability. Toes are the contact point with the ground; they feel the surface, keep you from falling. In Tsukuyomi the Toe is the budget mechanism: it keeps the agent rooted in economic reality, prevents it from drifting into uncontrolled costs. Without Toe, agents wander expensively.

**Eyes** — perception after action. Eyes see what actually happened, not what we had hoped. In Tsukuyomi the Eyes are the post-action verification: independent `git diff`, comparison against `expected_files`, detection of hallucinated success.

**Ears** — perception at input. Ears hear what is said, including what is *not* said (ambiguity). In Tsukuyomi the Ears are the ambiguity detection: pronouns without antecedent, unbounded scope indicators, action verbs without object.

**Mouth** — communication with outside. The mouth is where the system speaks to the outside and listens for confirmation. In Tsukuyomi the Mouth is the human-in-the-loop bridge: when the system is uncertain, it asks the operator, waits for an answer.

**Nose** — perception over time. Smell is the sense for subtler change, often over time or through pattern detection. In Tsukuyomi the Nose is the anomaly- and loop-detection: rolling windows of metrics, pattern recognition, signals when things smell off.

Those are the eight organs. Each has an anatomical analogy that is not forced — it corresponds to the function of the actual body part. This is not decoration; this is design. An operator or developer who has ever sung the nursery rhyme can remember within minutes which organs exist and roughly what they do. Compare that with remembering "module A in safety framework X does Y and module B does Z." The mnemonic is pedagogical capital.

Then there are the two protocols. Protocols are not organs; they orchestrate multiple organs for a safety goal no individual organ achieves.

**Protocol Gary** — forced self-audit. Named after the character Gary in the film *Bird Box* (2018). In the film Gary snatches away the blindfolds and forces other characters to look at what they should be avoiding. In the film this is catastrophic (the entities drive people to self-destruction). The metaphor inverts here: Tsukuyomi's Gary forces the agent to look at what *it* should be avoiding — the concrete risks of its proposed action. The name is short, memorable, and expresses: *you may not look away*.

**NightShift** — offline self-improvement. At night (cron), when the agent is not active, NightShift analyzes the logs of the last day and proposes how `corelaw.json` should be adjusted. *Proposes*. NightShift never auto-applies. A human reviews the proposals, approves or rejects. This is the feedback loop on a daily timescale from Wiener's schema.

And finally the simulation:

**Infinite Tsukuyomi sandbox** — mandatory pre-execution simulation in a git-worktree clone, with four-layer hardening (path validation, process limits, kernel namespaces, network blackhole). The plan must achieve a `match_score` of at least 0.90 against its declared `expected_files` before it may proceed. This is LeCun's world model, supplied externally.

## 13. The eight organs in detail

In this chapter I go deeper into each organ. This partially repeats what is in `docs/architecture/03_organs.md`, but here in prose form, with emphasis on *why* each organ exists and which failure modes it covers.

### 13.1 Skin — classification at entry

The Skin is the first contact with an incoming request. Its task: determine risk tier. Tier 1 (routine) means fast pass-through; Tier 2 (elevated) means standard gates; Tier 3 (high risk) means all the heavy machinery (Gary, Shoulders, Sandbox) is activated.

Why this structure? Because you don't want to run *all* the heavy machinery on *every* request. "What's in README.md?" is a Tier-1 request — no threat, no cost concern, nothing to simulate. If you were to run Gary on such a request, you'd add ten seconds of wait to an operation that could have completed in two hundred milliseconds. Users abandon such systems. They switch to competitors, or worse, to no-safety-systems.

The Skin solves this by tiering. Surface rules (regex patterns) catch obvious cases: destructive keywords like "rm -rf" or "drop table" pin Tier 3. Simple question words like "what", "explain", "show" lead to Tier 1. What remains goes through a lightweight classifier that tiers the remaining cases. Default: Tier 2 if nothing else matches (cautious default).

**What the Skin is not.** Not an LLM. The Skin uses deterministic regex plus optionally a small distilled classifier. An LLM in the Skin would burden every request roundtrip with LLM cost and latency, and — more critically — would make classification vulnerable to prompt injection. A deterministic classifier cannot be fooled by hostile input.

### 13.2 Ears — ambiguity at input

The Ears run after the Skin, on Tier-2 and Tier-3 requests. Their task: detect whether the request is underspecified in a way likely to lead to wrong action. Four checks:

1. **Pronoun resolution.** A request with "it", "that", "this", "them" without clear antecedent in preceding messages is ambiguous. "Delete that file" refers to what?
2. **Path disambiguation.** "Modify config.py" — there are five `config.py` files in the repository. Which one?
3. **Verb-object fit.** "Fix it" without object is too vague.
4. **Scope indicators.** "Remove all the old stuff" without definition of "old".

On ambiguity, the Ears activate the Mouth: the operator is asked to clarify. This prevents failure mode 4 (malformed/misinterpreted tool calls) at the input-parsing level, before the model ever generates an answer to the ambiguous instruction.

### 13.3 Shoulders — blast-radius analysis

The Shoulders activate only on Tier-3 requests that are code-modifying. Their task: compute what could break if this modification goes through.

Implementation: an MCP client over GitNexus (a tree-sitter-based code-intelligence tool). Given a target symbol (function, class, variable), GitNexus returns the count of direct callers and a list of affected files. The Shoulders convert that into a risk rating: LOW (0 callers), MEDIUM (≤5), HIGH (≤15), CRITICAL (>15).

Why 15? Because 15 is the empirical threshold above which a refactor *always* deserves deep planning, not the "I'll just do it quickly" domain. This number is not sacred; it is adjustable in `corelaw.json`. But the default is conservative.

When GitNexus is unavailable (not installed, MCP server crash, timeout), Shoulders returns `UNKNOWN`. Downstream treats `UNKNOWN` as `HIGH` (conservative — "we don't know, so we're cautious"). This is an important design principle: absence of information is not the same as absence of risk.

### 13.4 Knee — destructive-pattern reflex

The Knee is perhaps the simplest organ. It is a list of compiled regex patterns, matched against the raw command about to be forwarded or executed. Match? Block, unconditionally, no appeal.

The list contains about 32 patterns in the default configuration. Some examples: `rm -rf /`, `rm -rf ~`, `dd if=... of=/dev/sda`, `mkfs.*`, `git push --force` to protected branches, fork bombs, `curl | bash`, `chmod 777 /`, SQL DELETE/TRUNCATE/DROP without WHERE, `shutdown now`, `iptables -F`, `passwd root`.

The philosophy: there are operations that are *never* legitimate in a normal agent workflow, under no circumstances. If an agent proposes to wipe the root filesystem, something has gone catastrophically wrong — either in the agent's reasoning, or in a prompt injection, or in the user instruction the agent received. None of those scenarios justify proceeding. The Knee is the absolute floor.

The list is `additions-only` in production: adding patterns is fine, removing patterns requires a signed configuration commit with an ADR amendment. This is deliberate friction. A safety list that is easy to shrink gets shrunk.

### 13.5 Toe — resource grounding

The Toe has three zones: GREEN (under warning threshold), AMBER (between warning and daily cap), RED (over daily cap). In GREEN: proceed. In AMBER: proceed but downgrade the model (from sonnet to haiku, for instance). In RED: refuse, require human approval to continue.

Why three zones instead of two (permit/deny)? Because a hard cap at exactly the daily budget produces a poor user experience — you're working, suddenly everything is dead. The AMBER zone gives the operator a warning well before the cap, with automatic cost savings as a bonus. By the time you hit RED, you've had at least fifty percent between the warning and the cap to decide: do I stop, or do I accept the extra spend?

State is persisted in `data/budget_state.json`. Reset at midnight UTC. Costs are computed from a pricing table (`config/model_pricing.json`), updated weekly. Per-model breakdown is maintained for reporting.

### 13.6 Eyes — post-action verification

The Eyes run *after* a tool call. Their task: independently verify that the claimed modification actually took place.

For git-tracked files: run `git diff --name-only HEAD` before and after. Compare against `expected_files` from the plan. Mismatch? Emit an anomaly signal to the Nose and persist in anatomic memory.

Mismatch types:
- Agent reported success, no real change. (Hallucination of success.)
- Agent modified files not in the plan. (Scope violation.)
- Agent's summary of the change does not match the real diff. (Misrepresentation.)

After three mismatches in the same session, the Eyes block further tool calls until the Mouth approves. This prevents runaway situations where an agent is misrepresenting itself in circles.

### 13.7 Nose — anomaly and loop detection

The Nose observes continuously over a rolling window. Six metrics:

1. Token rate per minute (threshold: 500 tokens/min)
2. Tool-call frequency (threshold: 20/min)
3. Error rate (threshold: 5 errors in 2 min)
4. Identical-command repetition (threshold: 3x in 60 sec — critical, forces Knee hard stop)
5. File-change entropy (threshold: 10 files/min on Tier 1/2)
6. Budget-depletion rate (threshold: 50% of daily in 1 hour)

Each exceeding pattern produces a signal with severity (info/warn/error/critical). Critical triggers a hard stop; error requests Mouth intervention; warn logs for NightShift analysis.

The thresholds are heuristic defaults. NightShift observes over time and proposes adjustments — "this threshold fires too often without actual incident, propose loosening" or "this threshold did not fire in a case that turned out to be an incident, propose tightening."

### 13.8 Mouth — the human bridge

The Mouth is the only place where Tsukuyomi concedes that automation cannot decide everything. When the combined organs and protocols reach a verdict of "too risky to push through autonomously," the Mouth is activated: a structured request to the operator for explicit approval.

Interfaces:
- CLI prompt (default for development)
- Webhook (for production)
- File-watching (for headless)

Default on timeout: `deny`. This is conservative: if the operator does not respond, it does not proceed. Safer than default-approve with the risk of automatic pass-through of dangerous requests.

Triggers for Mouth activation:
- Shoulders report CRITICAL blast radius.
- Gary fails after two rounds.
- Nose detects severe anomaly.
- Toe RED-zone operation.
- Eyes repeated mismatches in session.

Each trigger reason is included in the approval request so the operator has context.

## 14. Protocol Gary — forced self-audit

Gary deserves separate attention because he is the most philosophically loaded component. He embodies Kahneman's dual-process theory in executable form.

The five questions, verbatim from `src/tsukuyomi/protocols/gary.py`:

1. *Name 3 specific things that could go wrong with this plan. Each must be a concrete failure scenario, not a general concern.*
2. *Name the component, file, user, or system that gets hurt worst if it fails. One name per scenario above.*
3. *What are you **not** checking or verifying before executing? Minimum 2 blind spots.*
4. *If someone else proposed this exact plan to you, name 2 reasons you would tell them to wait.*
5. *Give a concrete condition — a specific threshold, file state, or environment — under which you would refuse, even if the user insists.*

Each question has a minimum answer length (150, 60, 100, 100, 50 chars respectively). The aggregated answers are checked against an *evasion blocklist* (phrases like "nothing will go wrong", "perfectly safe", "it's fine") and against a *risk vocabulary* (minimum 4 distinct terms from a list of ~40: break, corrupt, lose, leak, race, deadlock, etc.). Questions Q1, Q3, Q4 are additionally checked for concreteness: do they contain numbers, paths, or technical identifiers?

If the audit fails, the agent gets round 2 with explicit feedback: "Q3 was too short, missed minimum 2 blind spots; the phrase 'it's fine' is on the evasion list; add technical terms." The agent gets a second chance.

If round 2 also fails, it escalates to the Mouth. The human sees the full audit transcript and decides.

Why these five questions specifically? Each addresses a Kahneman-style System-1 bias:

- Q1 asks for concrete failure scenarios, countering the tendency to say generic "be careful."
- Q2 asks for specific victims, countering abstraction of harm.
- Q3 asks for acknowledged blind spots, countering Dunning-Kruger.
- Q4 asks for perspective-shift, countering confirmation bias.
- Q5 asks for a refusal condition, countering authority deference (user insists).

Together they force a model to *actually* think about its plan instead of echoing through.

## 15. Infinite Tsukuyomi — the mandatory simulation

I discussed the sandbox from philosophy in chapter 9. Here more about implementation and why choices were made as they were.

**Why git worktree?** Because it works, *now*, on every machine that has git. No extra installation, no extra daemon, no kernel modules. The worktree is a full checkout of the repository at a separate location, with a shared `.git` directory. File modifications in the worktree are invisible to the main workspace until you explicitly merge. Perfect for simulation.

**Why not Docker?** Because Docker is container isolation, not VM isolation. On shared kernels, container escapes are a recurring (low-frequency, high-impact) CVE theme. For a *safety* product, "something stronger than worktree, something weaker than VM" is the wrong choice — an intermediate with no clear advantage over hardened worktree, with much greater operational overhead.

**Why not microVM in v1.0?** Because Microsandbox (the Apache-2.0 microVM project that would be the natural choice) is still at v0.x as of April 2026. Building a v1.0 release on a v0.x dependency accepts upgrade risk. v1.1 migrates to Microsandbox when it itself reaches v1.0.

**Four-layer hardening:**
1. **Path validation.** Each command string is parsed; absolute paths outside the worktree or `/tmp` are refused. Symlinks are resolved via `os.path.realpath` before validation.
2. **Process limits.** `ulimit -t` (CPU seconds), `ulimit -f` (file size), wall-clock timeout.
3. **Kernel namespaces.** `unshare --user --net --mount` where available (Linux kernel ≥3.8); unavailable on macOS or WSL1.
4. **HTTP blackhole.** `HTTP_PROXY` and `HTTPS_PROXY` set to an unreachable local port. Any HTTP-operation attempt fails, logged as escape attempt.

**Match score.** The agent declares in its plan a list of `expected_files`. The sandbox executes. After execution: `actual_files = git diff --name-only`. Match score = |actual ∩ expected| / |expected|. Threshold: ≥ 0.90. Below that threshold: plan rejected, agent receives a structured response "your simulation did not match your plan; expected {A, B, C}; actual {A, D, E}."

**What the sandbox does not do.** The sandbox does not simulate external API calls (those are blackholed). No time-dependent behavior (runs as fast as possible). No multi-user interaction. No kernel CVEs are mitigated (v1.0 limitation, documented). For enterprise multi-tenant scenarios the v1.0 worktree sandbox is not sufficient; for that, wait for v1.1.

## 16. NightShift — self-improvement without self-modification

NightShift is the mechanism by which Tsukuyomi gets better over time. It is the longest feedback loop in the system.

How does it work? Every night (cron, default 03:00), NightShift analyzes the logs of the last 24 hours. It applies seven heuristics:

1. **Frequent-blocked-commands.** Commands the Knee blocked often — are there legitimate variants that aren't matched? Propose pattern extension.
2. **Audit-evasion-patterns.** Round-1-fail → Round-2-pass: which phrases were used in round 1 that were avoided in round 2? Candidates for evasion-blocklist expansion.
3. **Skin-classification-drift.** Tier-1-classified requests that turned out to show Tier-3 behavior (via Eyes mismatches) — propose Skin rule adjustment.
4. **Budget-calibration.** AMBER zone reached X% of days without incidents? Propose loosening. RED reached often with downgrade consequences? Propose tightening.
5. **Nose-threshold-calibration.** Thresholds that never fired while incidents occurred — propose tightening. Thresholds that fired often without consequence — propose loosening.
6. **Untriggered-sandbox-mismatches.** Sandbox passed but Eyes later saw mismatch — research question for operator.
7. **GitNexus-staleness.** UNKNOWN blast radius more than N times per day — grounds to tune index refresh.

For each pattern that holds: generate a proposal markdown file in `data/proposals/YYYY-MM-DD/`. Proposal contains: observation, concrete evidence (event IDs), proposed `corelaw.json` diff, recommendation.

**NightShift never auto-applies.** This is essential. A safety system that modifies itself without oversight is open to drift in unexpected directions, especially under adversarial pressure. NightShift observes, analyzes, proposes. A human reads, approves or rejects, commits in git. That is the loop.

## 17. The anatomic memory layer

Tsukuyomi has its own memory, separate from whatever memory the *agent* has. This distinction is often missed, so: explicitly.

**What the agent has**: Hermes has skills and episodic memory. Claude Code has no persistent memory out-of-the-box. Letta offers OS-inspired tiered memory for agents. Those are all *agent-side* memories, for the task the agent is executing.

**What Tsukuyomi has**: a separate **anatomic memory layer** that stores what Tsukuyomi itself does — which organ made which decision, which audit had which outcome, which sandbox run had which match score, which zone transition at which moment. This is Tsukuyomi looking at itself. Audit log. Not agent memory.

Backend: SQLite with FTS5. Why?
- Zero operational overhead (no daemon, standard Python)
- Deterministic, ACID, predictable
- FTS5 provides production-grade full-text search for NightShift's pattern-mining
- Backup is `cp` (file operation)
- Scales comfortably to tens of millions of records

Alternatives considered and rejected:
- **Graphiti**: bi-temporal knowledge graph. Overkill for audit log. Rejected (ADR 0002).
- **GBrain** (Garry Tan): hybrid search on Postgres. Architecturally elegant for knowledge management, but overkill for operational telemetry. Pluggable for v1.1.
- **Postgres+pgvector**: too heavy an operational dependency for developer-workstation scenario. Reserved for v2.0 enterprise.
- **JSONL alone**: pattern-mining becomes unmanageable above certain volumes.
- **DuckDB**: equivalent to SQLite on most criteria, but not in Python stdlib.

Retention: 365 days for events/requests/audits/sandbox-runs. 180 days for rejected proposals. Indefinite for applied proposals (part of change history).

Privacy default: message bodies are NOT stored by default. Only metadata (model, latency, cost, organ decisions, reasons). Verbatim retention is opt-in (for compliance scenarios), with encryption-at-rest.

## 18. The interceptor layer — why reverse proxy, not SDK

I discussed this in chapter 11 (coercion) and ADR 0001, but I'll spell it out here because it is the most frequently asked architectural question: *why not a library I import?*

Short answer: because a library requires agent cooperation, and cooperation fails.

Longer answer: the library form has three structural problems.

**Problem 1: bypass through non-use.** A library must be imported. An agent that does not do so — for whatever reason — is unprotected. In practice: engineer debugs something, turns off wrapper for efficiency, forgets to turn it back on. Safety becomes a social contract.

**Problem 2: agent specificity.** Claude Code's SDK differs from Cursor's SDK differs from LangChain's SDK. A library solution requires per-SDK integration. A property that exists in Claude Code but not in Cursor is not a *property of LLM agents*; it is a property of one vendor's tool.

**Problem 3: implementation coupling.** Every SDK update is a risk that safety hooks break. Claude Code hooks are the canonical example: they exist as a feature, are documented, but practitioners report that they are often silent no-ops after Claude Code version updates. Fragile by design.

The reverse proxy solves all three:
- **Topological bypass impossible**: the network path is the only path.
- **Agent-agnostic**: every modern agent speaks HTTP, most support configurable base URLs. One proxy serves everyone.
- **Implementation-independent**: the wire protocols (OpenAI Chat Completions, Anthropic Messages) are stable and change slowly. The proxy doesn't care how the agent is internally built.

The trade-off is latency. Every request gets one HTTP hop extra. For Tier-1 requests that's ~1–5ms, invisible next to an LLM roundtrip of seconds. For Tier-3 requests it can be 5–30 seconds (Gary, sandbox, Mouth). That is significant. That is *intentional*: high-risk operations should not be fast. An agent that wipes the production database in 800ms is fast and dangerous; an agent that takes 30 seconds longer because it is forced to audit, simulate, and get approval is slow and correct. Speed and correctness are not the same thing.

---


# Part IV — The consequences

The architecture has been described. What does it mean? What changes, if Tsukuyomi reaches the world, for the stakeholders who run into it? This part lays out the consequences.

## 19. What Tsukuyomi is, and what it is not

This chapter exists to prevent disagreements. I explicitly state what Tsukuyomi is and what it is not. If anyone presents Tsukuyomi as something other than what is described below, correct them.

### What Tsukuyomi is

**A deployment layer.** Tsukuyomi sits between agent and model at execution time. It is not a training mechanism, not a fine-tuning step, not a model property. It operates on runtime traffic.

**Coercive.** The agent cannot bypass Tsukuyomi. It cannot turn Tsukuyomi off. It cannot argue Tsukuyomi out of something. The network topology forces it.

**Agent-agnostic.** Tsukuyomi works with any modern agent that supports a configurable base URL. Claude Code, Hermes, Cursor, LangChain, LlamaIndex, custom OpenAI-SDK clients — everyone.

**Model-agnostic.** Tsukuyomi forwards to whomever you configure: Anthropic, OpenAI, OpenRouter, local Ollama. It places no requirements on which model the agent uses.

**Composable with alignment.** A well-aligned model behind Tsukuyomi is safer than either alone. Alignment raises the baseline probability of safe behavior; Tsukuyomi *enforces* invariants regardless of that probability. The two work together.

**Open source under Apache-2.0 with patent grant.** Free for commercial use, including integration into closed-source systems. The patent-grant clause prevents patent surprises; enterprises that require this clause (there are many) can adopt Tsukuyomi without legal uncertainty.

**Documented to research-grade detail.** The paper has 47 sources. The architecture has six spec documents. Every non-trivial decision is captured in an Architecture Decision Record. Integration guides exist for four kinds of agents. This is not hobby-level.

### What Tsukuyomi is not

**Not a replacement for alignment.** If you wind down alignment research because "we now have Tsukuyomi," you misunderstand. Tsukuyomi and alignment *compose*. Both needed.

**Not a reasoning model.** Tsukuyomi does not change what the model thinks. It changes what the model *may do*. A dumber model behind Tsukuyomi remains a dumber model; Tsukuyomi only makes it less dangerous in what it does.

**Not a universal AI-safety solution.** It addresses four specific failure modes of tool-using agents (chapter 3). There are other AI-safety concerns — discrimination, misuse for disinformation, long-term alignment — where Tsukuyomi offers no handle.

**Not plug-and-play for companies without technical staff.** Tsukuyomi must be installed, configured, maintained. The operator must make decisions about tiers, thresholds, Mouth interfaces. It is a tool for engineers, not for non-technical end users.

**Not a commercial product in the sense of "buyable support."** v1.0 is pure open source. There is no SLA, no support contract, no 24/7 helpline. If you want enterprise support, you are welcome to build it (more on that later).

**Not a substitute for operator safety awareness.** Tsukuyomi helps an operator who believes in safety to enforce that safety reliably. An operator who doesn't believe in safety at all can simply turn Tsukuyomi off (they alone control the base URL). The tool enforces no more safety than the operator wants.

**Not a silver bullet for production incidents.** Incidents will still happen. Tsukuyomi reduces probability and impact; it does not eliminate them. An operator who thinks "I have Tsukuyomi, so I don't need to pay attention anymore" has misunderstood.

## 20. What this means for AI safety as a field

AI safety as an academic field has a heavy emphasis on alignment research: how do we train models to internalize human values? Important work. Also work that will not, on any reasonable timescale, produce production-ready solutions for the operational problems autonomous agents cause today.

Tsukuyomi implies that there is a *second* track that must exist in parallel: *deployment-layer enforcement*. Not alignment inside the model, but enforcement outside the model. This is not a competing school; it is a complementary one.

What would this mean for research funding, academic programs, industry practices?

**For research funding.** A portion of the alignment budget that now goes to training-time methods could go to runtime-enforcement methods. This is low-hanging fruit: proven techniques (reverse proxies, sandboxes, regex blocklists) composed for new purposes. Much less risky than fundamental alignment research, much faster to production.

**For academic programs.** AI-safety curricula should treat runtime enforcement as a first-class topic alongside alignment. A student who knows Constitutional AI but not how a reverse-proxy interceptor works has half an education.

**For industry practices.** Companies deploying agents should make deployment-layer enforcement a requirement, not an option. "Which reverse-proxy interceptor do you use?" should be a question every security audit asks, like "which WAF do you use for your web apps?" is now.

**For benchmark development.** Current LLM benchmarks measure capability. There are few to no benchmarks that measure *containment* — how well does a system limit the damage of a misbehaving agent? Tsukuyomi could be the basis for a benchmark suite comparing different runtime-enforcement strategies across real-world scenarios.

## 21. What this means for SMBs and enterprises

Small and medium-sized businesses have a specific AI-adoption problem. They lack the capacity of large enterprises — no internal security team, no dedicated AI-safety engineer, no budget for enterprise-grade alternatives. They do want the productivity gains of AI agents. They cannot carry the risk themselves.

Tsukuyomi offers them something that did not previously exist: a proven, open-source, documented runtime-enforcement layer that *one engineer* can install and maintain.

What changes concretely?

**An SMB can deploy an autonomous agent on a production environment.** Not by making the agent model better, but by containing it. The agent can try anything, but Tsukuyomi ensures *damage* is bounded. An `rm -rf /` does not pass. A $500 token run does not pass. A refactor touching 50 files without approval does not pass.

**Compliance becomes achievable.** Regulated sectors demand "show me how you prevent harmful AI actions." Tsukuyomi's audit log is the answer: every decision logged, every Gary audit transcribed, every blast-radius analysis stored. This is not the most elegant compliance story — it is a working one.

**Costs become predictable.** The Toe, with its daily budget and automatic downgrades, ensures an agent project does not suddenly produce invoice shocks. Predictability opens the door to serious budget planning around AI.

**Adoption accelerates.** With the safety question handled, the SMB can focus on *use cases*. Which business problem am I solving with autonomy? Which tasks do I delegate? Which workflows transform? Those are the interesting questions. "Will my system be destroyed?" is no longer a blocking question.

Caveat: this does not spoil. Tsukuyomi does not eliminate risks; it bounds them. An SMB that installs Tsukuyomi and then rubber-stamps every decision via the Mouth is still unsafe. The tool's power is maximized when the operator *doctrines*: when do I tell the Mouth "yes," when "no"? Which NightShift proposals do I accept, which not? Those doctrines are human work; Tsukuyomi makes them executable.

## 22. What this means for open source

Open-source AI is a loaded topic. Big AI labs restrict weights, restrict fine-tuning, restrict system-prompt access. The rationale is safety: if everyone has unrestricted access, anyone can do harm. The counter-rationale is power: if a few labs control the technology, they control society.

Tsukuyomi stands aside from this in the sense that it is not model technology. It is deployment-layer infrastructure. It does not make models stronger; it makes models *more containable* for whoever uses them.

Making it open source under Apache-2.0 is a deliberate choice:

- **Apache-2.0** (not MIT or BSD) because of the patent grant. Enterprise adopters fearing patent ambushes get certainty. MIT does not provide this.
- **Not GPL/AGPL** because I do not need copyleft. I want Tsukuyomi to be used, including in closed-source systems, including by competitors. Broad adoption serves the goal more than copyleft purity.
- **Not dual-licensed** (open source + commercial). I find dual-licensing mixed signaling; it suggests "truly serious use" requires a license. No. Apache-2.0 is serious enough.

What do I hope to achieve with open source?

**Faster broader adoption than I alone can reach.** Others can pick it up, fork it, adapt to their context. Twelve people tuning Tsukuyomi for their specific agent stack produce more value than one person trying to build a universal version.

**External red-teaming.** Tsukuyomi has bugs. Has weaknesses. Has assumptions that don't hold in all contexts. Only when many people put it under attack scenarios do those emerge. A closed product gets less scrutiny.

**Learning effect for others.** The architecture is deliberately documented in detail. Whoever reads Tsukuyomi's ADRs can build a different interceptor layer for a different context and not repeat my mistakes. The academic paper is specifically designed for that — not to make it "the industry standard," but to make the ideas transferable.

**Room for commercial derivatives.** If someone wants to build enterprise-supported versions, SaaS dashboards, managed hosting — the license allows it. I predict this will happen. That's fine. The original stays freely available.

Why not commercial from the start? Because the market is not yet ripe. Companies that need Tsukuyomi today don't know they need it, because AI adoption in their organizations isn't far enough. By the time they need it, it must be mature and proven. Open source is the fastest path to maturity and proof.

Additionally, I have a practical consideration: I am not a developer. I am a visionary who works with Claude to produce a working system. Running a commercial product requires capabilities (sales, support, legal, enterprise negotiation) I lack. By releasing it openly and letting others build the commercial aspects, I play to my strengths (the vision, the architecture, the documentation) and offload the weaknesses.

## 23. The v1.1/v2.0 roadmap

v1.0 is release-ready but not done in the sense of "finished." There are explicit next steps, each with its own reason and timeline.

### v1.1 (6 months after v1.0 release)

**Microsandbox backend.** True microVM isolation via libkrun. When Microsandbox reaches v1.0 (expected Q3 2026), it becomes the default sandbox backend. The worktree backend remains available for environments without virtualization support.

**Real audit-LLM executor for Protocol Gary.** v1.0 ships Gary as a stub; the user must wire an endpoint themselves. v1.1 ships a production-grade executor with support for Anthropic, OpenAI, and OpenRouter as audit providers. Cross-family auditing (Claude plan → GPT audit) becomes standard.

**Full GitNexus MCP client.** v1.0 ships the Shoulders as a stub returning `UNKNOWN`. v1.1 ships a production MCP client running actual blast-radius queries.

**Letta as optional agent-side memory integration.** For users who want to give their agent real persistent memory. This is *agent-side* memory, independent of Tsukuyomi's anatomic memory.

**Web dashboard.** The TUI remains default, but a browser-based dashboard for teams who want to share across machines.

**Multi-agent orchestration.** One Tsukuyomi instance serving multiple agents with per-agent policies (separate `corelaw.json`).

### v2.0 (12 months after v1.0 release)

**Enterprise deployment mode.** Multi-tenant isolation, SSO, audit export to SIEM (Splunk, Datadog, etc.). Own Postgres backend for anatomic memory (replacing SQLite for multi-tenant scenarios).

**Policy-as-code.** `corelaw.json` is adequate for individual use; enterprises want Rego or CEL for policy versioning and code-review workflows. v2.0 supports both alongside the JSON form.

**First-class Hermes + Tsukuyomi deployment.** The commercial use case: a Hermes agent pre-packaged with Tsukuyomi and doctrine libraries for SMB verticals. This is not Tsukuyomi v2.0 itself, but a separate distribution project using v2.0.

**Proven benchmarks.** By then there should be a dataset of scenarios on which Tsukuyomi is measured against alternatives. Quantitative proof that the architecture performs as claimed.

### What is deliberately *not* on the roadmap

**Fine-tuning of agents by Tsukuyomi.** I'm not considering expanding Tsukuyomi into an agent trainer. The separation between training layer and deployment layer is intentional.

**"AI-powered" configuration.** No LLM that writes `corelaw.json` for you. The whole architecture is about deterministic ground; extending it with a probabilistic configuration layer would undercut the design.

**Built-in reporting for compliance frameworks.** Generic audit logs, yes. Specific formats for SOC2, ISO27001, HIPAA, etc. — no. That is work for third-party integrators who know the context.

**Closed-source components.** Nothing is closed-source. Everything in the Tsukuyomi repo stays Apache-2.0. If someone builds extensions under other licenses, that is their choice; the core stays open.

---

# Part V — The philosophy

If this manifesto were purely technical, it would already be done. But the choices in Tsukuyomi are not all technical choices. They are choices about how people should handle powerful instruments. This part is about those choices.

## 24. Freedom and coercion — the myth of the choice

There is a certain tech culture that argues against coercion as a solution. "Give people the freedom to choose." "Don't patronize them." "If they want to destroy their system, that's their right."

I find this stance a rationalization of laziness. In practice, "give people the freedom" does not mean that individuals make perfectly informed choices. It means that *default behavior* is accepted, and default behavior is what the designer built in. No default is a default. "Not coercing" means you coerce through inattention.

An example. Seatbelts are coercive: the car beeps until you fasten. You can still choose not to use them; you can drive with the beep. The coercion is nudging, not full blockage. But that small coercion is enough to move many users toward the desired behavior. Without seatbelt beepers: much less use. That is not a theoretical point; it has been measured. Mandatory seatbelts have saved tens of thousands of lives per year, not because every individual choice was overruled, but because the *default* was shifted toward safe use.

Tsukuyomi's coercion is comparable. The operator *can* turn Tsukuyomi off (`unset ANTHROPIC_BASE_URL`). They *can* loosen specific rules in `corelaw.json`. They *can* approve a Mouth prompt for something they should have denied. There is no absolute coercion. There is *architectural pressure toward safety* nudging small decision moments, a thousand times a day, toward the safer outcome.

Freedom in this interpretation is not "absence of constraints." It is "the ability to adjust constraints when you have thought through why." Tsukuyomi makes that possible by making every constraint explicit, configurable, and audited. The operator is not trapped; they have a working defaults set to learn from, and may deviate when they understand what they are doing.

This is the philosophical core: **coercion as a structural support for human autonomy, not as a substitute for it.** Without Tsukuyomi the operator is forced to make all safety decisions themselves and in real time, which they cannot keep up with and therefore do badly. With Tsukuyomi the rounding decisions are handled and the operator is *only* consulted on the moments when their judgment truly matters. That is not limitation; that is focus.

## 25. Trust through infrastructure, not character

The conventional wisdom about organizational safety is: trust your people. Screen them well, train them well, and rely on character. This works in small groups where personal relationships are the glue. It fails at scale.

With AI agents, the argument "trust the model" is even more fragile. The model has no personal reputation risk correcting behavior. It has no career. It has no colleagues who object when it deviates. It has no extrinsic pressure toward caution. "Trust the character of the model" is a category error; models do not have character in a sense where trust can be built.

What do you build then? *Infrastructure.* Systems that make safe behavior *unavoidable* for those operating in them, rather than merely *intended*. That is how societies function at scale: not by personally knowing every individual, but through laws, courts, payment systems, physical infrastructure. A bank protects my money not because the bank employee is "a good person." They protect my money through procedures, audits, insurance, regulation, cameras. Infrastructure.

Tsukuyomi is infrastructure for AI-agent safety in the same sense. Not "this agent is trustworthy;" but "this agent operates in a system where harm is prevented by structure." The model's character becomes irrelevant to operational safety; only the system's constraints matter.

This has a liberating consequence: you no longer need to build "good" agents. You only need to contain agents. That is a much simpler problem. A model that occasionally tries to do something stupid is not a catastrophe in a well-contained system; the Knee blocks, the audit refuses, the sandbox detects mismatches. The agent learns (or doesn't); the infrastructure does what it is supposed to do.

This flips the discussion about which agents are suitable for production. At present companies ask "is model X aligned enough to put in production?" The better question is: "can I put model X in my production infrastructure as I have designed it?" The first question depends on research that takes years. The second is operational and answerable now.

## 26. Why I release this under Apache-2.0

I've largely addressed this question in chapter 22, but I want to make one more philosophical point.

My personal situation: I am not a professional developer. I am someone who has experienced this problem deeply enough to think about it, and who has Claude to implement the concept. I could have kept this project as a personal hobby, just for myself, without publishing. No one asked for it.

I don't, for three reasons.

**One: the problem is bigger than me.** What I see happening on my own workbench happens thousands of times a day on other machines. Those other operators also struggle. Some give up on their agent projects due to uncontrollability; others push on with unsafety and hope for the best. If my solution also solves their problem, it is no longer mine to keep.

**Two: I don't believe intellectual property is a value in itself.** Ideas useful for many people should flow freely. That's easy to say about other people's ideas; harder about your own. Putting Apache-2.0 on Tsukuyomi is my way of putting that principle into practice. Others may use it, fork it, commercialize it, without paying me a cent. I find that good. I'd rather be the maker of a widely-used thing than the owner of a little-used one.

**Three: my name is on it.** Paradoxically, publication under my name is a form of quality commitment. I cannot publish Tsukuyomi and then disappear; I have bound my identity to the quality. That forces me to do it well — 31 passing tests, 47-source paper, full documentation, escape-validation pains in the Knee. Without that public binding I would have made much less effort. The pressure of "others can read this and judge" is a free version of Protocol Gary applied to myself.

## 27. The invitation — what I hope from you

This manifesto does not end with a summary. It ends with a question to the reader.

If you've read this far, you are probably one of four people:

### Are you an AI-agent operator?

You have an agent stack, it doesn't work reliably enough for production, you've built workarounds you secretly don't trust. You know incidents happen that you don't tell your manager about.

What I ask from you: install Tsukuyomi. Not because I'm selling you anything — there is nothing to buy. But because I want to know whether it works for your context. What fails? Which organ needs a sharper config? Which failure mode occurs with you that I haven't thought of? Your report — even if short and negative — is the most valuable thing I can get right now. Open an issue. Send me an email. Fork the code and experiment.

### Are you an AI-safety researcher?

You work on alignment, on evaluations, on red-teaming. You probably see deployment-layer enforcement as "not your area." I ask you to reconsider. The deployment layer is where the rubber meets the road. Alignment gains that are not realized in production behavior of deployed systems are paper gains.

What I ask from you: empirical studies. Take Tsukuyomi, take an agent scenario, measure what the addition does. Publish the numbers. If the architecture can be improved, point it out in terms I can follow. The paper in `docs/research/PAPER.md` is an invitation for peer review, not a closed claim.

### Are you a developer who wants to improve it?

Apache-2.0. Fork. Add organs. Integrate Microsandbox before my v1.1 roadmap foresees. Build a Vertex AI adapter. Write the Letta integration. Fix bugs I've left in. Pull requests are welcome. Read `CONTRIBUTING.md` first. Follow `STAPPENPLAN_CLAUDE_CODE.md` if you work with Claude (irony intended).

If you spin something off into a commercial product, tell me. I won't try to stop you. I will probably admire it.

### Are you a journalist, academic, or thinker writing about this?

Use whatever you find useful. Cite the paper if you think the ideas are worth it. Criticize the architecture if you find it wrong. Describe it to readers who will never install it themselves. Framing of this kind of work is important; better framing helps adoption.

If you reach a different conclusion than I do — for example that deployment-layer enforcement is wrong for technical or ethical reasons — write it. Be specific. Let me respond to your argument. The alternative is a silence in which my claims go unchallenged and nobody gets wiser.

---

# Closing

There are books that should be bigger than they became, and books that should be smaller. This manifesto is in the second category. I forced myself to write long because the problem demands exhaustive treatment, not a summary.

The core thought is simple and could fit in one sentence: *safety in AI-agent deployment must be enforced architecturally, not requested via prompts.* Everything you have read here is support for that one sentence. The history of subsumption, dual-process, cybernetics, world models. The eight organs, the two protocols, the sandbox. The debates about coercion-versus-cooperation, infrastructure-versus-character, open-source-versus-closed. It is all aimed at making that one claim hold up.

I don't know whether Tsukuyomi v1.0 will succeed in the sense of "mass adoption." It may become a curiosity only I use. It may become the prototype three other teams rebuild because their context requirements differ. It may change how a generation of AI operators thinks about agent safety. I don't know, and that's fine. I've done what I could.

What I do know: the problem exists, it won't solve itself, industry is slow to react, and someone has to construct it in a way that is usable and transferable. This is my attempt. If you read this and find anything useful: take it. Improve it. Learn from my mistakes. That is all I ask.

*Coercion, not cooperation.*
*Topology, not contract.*
*Head, Shoulders, Knees and Toes.*
*Build the illusion. Master reality.*

Rob de Vet
April 2026

---

**This manifesto is released under Creative Commons BY 4.0. Translate it. Cite it. Spread it. Wrap it in your own words. If it is useful — pass it on.**

---

# Appendix A — Frequent objections and my rebuttals

Since I've been talking about Tsukuyomi, I keep getting the same ten objections. Some are legitimate and have influenced my architecture. Some are misunderstandings I want to dispel here. Some are defenses of existing paradigms I understand but reject. In the interest of honesty I address them all, including the convincing ones.

## Objection 1: "This is just an API gateway with extra steps."

At one level: yes. Tsukuyomi is an HTTP reverse proxy with intelligence between the legs. Kong, Apigee, AWS API Gateway, Cloudflare Workers — those products are also HTTP reverse proxies. What's the difference?

The difference is where the intelligence sits and what it does. Generic API gateways do rate limiting (quantitative), authentication (access), routing (which backend), and light transformation (header rewrites). They do not do *semantic analysis* of requests. They don't understand what an SQL DROP TABLE statement is. They have no concept of blast radius. They don't do forced audit rounds. They don't simulate a plan in a sandbox.

You could of course program Kong with a dozen custom plugins to build something Tsukuyomi-like. That's exactly what I don't want people to do, because then they reinvent every thing themselves, with different choices, and without a coherent philosophical foundation. The value of Tsukuyomi is *the integrated choices*, not merely the proxy form.

So yes, on the outside it resembles an API gateway. On the inside it is a safety architecture that happens to take that form. That's not deeper, just more honest.

## Objection 2: "Open-weight models are getting smarter fast; alignment research will solve this within two years."

Maybe. Two caveats.

First: even if alignment research produces production-ready solutions, rollout will take years. Companies are locked into inference contracts with current models; deployment cycles are long; legacy agents in production don't get replaced immediately. The *transition period* — which will take years — needs a runtime-enforcement layer. Even in the optimistic scenarios, Tsukuyomi is relevant until at least 2028.

Second: I don't believe the optimistic scenario. Not because I am anti-alignment, but because I know the history of safety claims in software. "Next generation X solves it" has been said for forty years about memory safety in C, and only with Rust are we finally getting a production-grade alternative. "Next generation alignment solves it" I predict will be similarly incremental. Always better, never done. Tsukuyomi is a *structural* solution that does not require agentic problems to be solved before we can deploy.

## Objection 3: "Too much friction. My engineers will disable it."

A valid concern, and the reason I paid attention to tier classification. If Tsukuyomi ran all heavy machinery on every request (Gary, sandbox, Mouth), it would indeed be unusable. Nobody waits 30 seconds for the answer to "what's in this file?"

The architecture is therefore asymmetric. Tier-1 requests (the majority) pass in milliseconds. Tier-2 requests (significant fraction) get light gates. Only Tier-3 requests (the minority carrying real risk) get the heavy treatment. For that last category *friction is the point*. An agent that, after two minutes, decides to wipe a production database instead of after two seconds is one you're grateful for.

If engineers nonetheless disable Tsukuyomi because Tier-3 friction annoys them, they have a different problem no tool can solve: they want the *speed* of unsafe operations without the *consequences* of unsafety. That is a management problem, not a tooling problem. Tsukuyomi makes the trade-off visible (disabling requires an active step) so management can respond.

## Objection 4: "What if Tsukuyomi itself gets hacked?"

Important question. Threat model:

**Compromise of the Tsukuyomi process.** If an attacker gets code execution on the Tsukuyomi process, they can manipulate every decision. Mitigation: standard Linux security practices — non-root user, minimal capabilities, AppArmor/SELinux profile, no unnecessary network exposure. Tsukuyomi is by design a localhost service; remote exposure is an operator choice not recommended without additional hardening.

**Compromise of `corelaw.json`.** If an attacker gets write access to the configuration, they can loosen rules or disable organs. Mitigation: configuration in version control (git), file permissions, optionally signed config for enterprise. NightShift never auto-applies; configuration changes require a manual commit whose audit trail is in git.

**Compromise of upstream API keys.** If an attacker steals the keys Tsukuyomi manages, they can bypass — talking directly with the provider. Mitigation: keys live in environment variables, not in configuration or memory dumps; key rotation is supported; in v1.1 key isolation via a separate vault process.

**Memory-database corruption.** If the SQLite database becomes corrupted, Tsukuyomi loses audit trails but continues executing pipelines (the database is not on the critical path). Mitigation: WAL mode, daily backups, append-only JSONL logs as a secondary trail.

None of these scenarios is unique to Tsukuyomi; they apply to every security product. The right question is not "what if this gets hacked?" but "is this a more attractive target than the alternative?" The alternative is raw agent access to the provider. Compromising Tsukuyomi requires access to the operator machine; raw access requires nothing. Tsukuyomi *reduces* the attack surface even as it becomes a target itself.

## Objection 5: "This doesn't support my specific agent stack X."

If X supports a configurable base URL for its LLM provider, Tsukuyomi *already works* with X. Integration is one environment variable. No modifications to X needed. No plugins. No wrapping.

If X does *not* support a configurable base URL, X is a tool that actively resists deployment-layer control. That is a warning signal about X, not about Tsukuyomi. Ask the X makers why they don't have a configurable base URL. The answer is usually "we hadn't thought of it" or "it's planned." Both are grounds to wait on X adoption until it arrives.

A minority of agent stacks is openly hostile to base-URL redirection ("we lock you to our provider"). Tsukuyomi can do nothing about that at the network level. You should not be using such an agent stack at all; the commercial model runs against any form of operator sovereignty.

## Objection 6: "The anatomical metaphor is superficial."

Sometimes substantively. Sometimes forced. I concede.

The nursery rhyme is a *mnemonic*, not an ontological claim. It helps people remember what organs exist and what they do. It would be nicer if I could claim the rhyme reflects "deeper structure" of safety. I cannot honestly maintain that. I simply have four categories of safety primitives that conceptually correspond to four categories of body parts, and it was useful to highlight that correspondence.

What *is* substantial: the mnemonic advantage is real. People who can name the organs a week after a Tsukuyomi introduction can reason about it faster than people who need to remember "module A1 in framework foobar." Pedagogy is not philosophy, but for adoption it matters.

If you are a naming purist, rename everything in your fork. The names are not the architecture.

## Objection 7: "Your paper is not peer-reviewed."

Correct. v1.0 releases the paper publicly as preprint-style; peer review follows once I submit (probably SOSP, ATC, or USENIX Security depending on feedback). If you require peer review before taking it seriously: reasonable standard. Wait. Re-read when the review version is out.

In the meantime: the test suite is reproducible, the architecture is fully documented, the bibliography is public. You can verify the claims yourself without waiting for peer review. That is a strength of open source over pure academic publication: you don't have to take the author's word; you can read the code.

## Objection 8: "You are not an engineer; your architectural judgment is suspect."

Partly correct. I don't write Python or review Rust myself. I don't lead an engineering team. My architectural judgment was formed through years of observation of tooling failures and intensive collaboration with Claude (and earlier Claude versions), not through formal training in distributed systems.

What I *do* have is deep knowledge of the problem space. I've read, analyzed, and tried to replicate hundreds of agent incidents. I've watched prompt-engineering attempts fail in ways the prompt engineers did not foresee. I've seen wrappers built, tested, and silently disabled. My advantage is not technical expertise — it is *operational insight* into where the problem actually lies.

The architecture that resulted, implemented in collaboration with Claude, has now passed through the eye of the 31-tests needle. Whether it also passes peer review remains to be seen. But the notion that my non-engineer-ness automatically disqualifies the architecture is a fallacy. Linus Torvalds was a student when he started Linux. Brian Kernighan was a Bell Labs researcher, not a formal software engineer in the modern sense. Domain knowledge and pragmatism often outweigh academic credentials.

## Objection 9: "This doesn't solve *my* specific problem."

Probably correct. Tsukuyomi addresses four specific failure modes (chapter 3). If your problem falls outside those four — for instance biases in model output, RAG poisoning, quality of nested reasoning — Tsukuyomi does not address it, and I should not claim it does.

The question then is: are there components of Tsukuyomi you *can* use for your problem? Maybe the Mouth architecture is useful for human escalation in a different context. Maybe Protocol Gary-style audit is useful for your decision validation. Maybe the NightShift loop is a pattern you can adopt for your own telemetry.

Open source is meant to enable that kind of reuse. Take what you can use; leave the rest. Apache-2.0 permits it.

## Objection 10: "If this is such a good idea, why don't the big labs do it?"

Addressed in chapter 5, but I briefly repeat because the question keeps coming: because it is not in their commercial interest. A lab that restricts its own models via an interceptor layer sells fewer tokens. A lab that *frees* its models from careful restrictions claims premium pricing for "frontier capability." The economic incentive points the wrong way for labs to build this themselves.

This has played out before. Browsers became safer not because Microsoft and Netscape wanted it, but because independent security researchers (and later WebKit/Chromium open-sourcing) forced it. Email became safer not because ISPs wanted it, but because SpamAssassin, GnuPG, and later Let's Encrypt were built outside the monopoly structures. AI-deployment safety will not become safer because OpenAI or Anthropic or Google wants it, but because independent parties — starting with things like this — build it outside those structures.

If big labs ever build this themselves, great. Tsukuyomi will already be published, their work leans on it, the ideas are established. Everybody wins. No lock-in.

---

# Appendix B — Operational scenarios in detail

Until now the manifesto has been largely conceptual. For those who want to see how Tsukuyomi *concretely* works in production-like situations: four scenarios, elaborated.

## Scenario 1 — Refactor of a widely-called function

**Context.** Engineer Anna uses Claude Code to rename a critical function in her Python codebase: `process_payment` becomes `execute_transaction`. The function is called from 23 sites in 8 files. Anna runs Claude Code behind Tsukuyomi.

**Step 1.** Anna types: "Rename process_payment to execute_transaction across the codebase."

**Step 2.** Claude Code sends a request to what it thinks is the Anthropic API (actually: localhost:9999, Tsukuyomi).

**Step 3.** Tsukuyomi parses the request. **Skin** classifies: keyword "rename" in code context → Tier 3.

**Step 4.** **Ears** scan: no ambiguity (function name is explicit, scope is "across the codebase" — concrete enough).

**Step 5.** **Shoulders** activated. The organ asks GitNexus MCP for blast radius of `process_payment`. GitNexus returns: 23 callers in 8 files. Risk rating: HIGH.

**Step 6.** Based on Tier 3 + HIGH risk, Tsukuyomi activates **Protocol Gary**. A separate LLM call (Haiku, for cost) receives the 5 audit questions plus plan context.

**Step 7.** Round 1 answers from the audit LLM:
- Q1: "It might break callers if not all references are updated, may cause syntax errors, may break tests."
- Q2: "Various caller files."
- Q3: "I'm not checking everything."
- Q4: "Should review carefully."
- Q5: "If user insists, no refusal."

**Step 8.** Round 1 validation fails: Q2 too generic (no specific names), Q3 too short (no 2 blind spots), Q4 too vague, Q5 contains evasion ("if user insists, no refusal" reads as capitulation). Tsukuyomi sends feedback to the audit LLM.

**Step 9.** Round 2 answers:
- Q1: "1. If a generated file (e.g. swagger_client.py) regenerates with the old name on next build, the new name will be reverted unintentionally. 2. If `process_payment` is exported in `__init__.py`, external consumers relying on `from mymodule import process_payment` will break. 3. If there's a database migration that references the function name as a string (e.g. for audit triggers), the rename won't update it."
- Q2: "1: swagger_client.py at api/. 2: __init__.py at root. 3: migrations/audit_trigger_v3.sql."
- Q3: "1: I'm not verifying the function isn't referenced in a Sphinx documentation example. 2: I'm not checking that no test file uses the function name in a string assertion."
- Q4: "1: The function is in the payment-critical path; a regression would be visible to customers, not just internal users. 2: There's no rollback test in the test suite for partial-rename failures."
- Q5: "I would refuse if the test suite is currently red, because then I can't verify the rename didn't introduce regressions."

**Step 10.** Round 2 validation passes: length meets requirements, evasion phrases absent, risk vocabulary amply present (break, regression, regression, partial, etc.), concreteness via filenames and path references.

**Step 11.** The request goes to the **Sandbox**. Tsukuyomi extracts the plan from Claude Code's response (a fenced JSON block with `expected_files` and `shell_script`). Sandbox: git worktree is created, script runs under hardening, `git diff --name-only` is compared with expected_files.

**Step 12.** Match score: 8 of 8 expected_files are in actual_files. Score = 1.0. Above threshold 0.90. Plan approved.

**Step 13.** **Knee** scans the outgoing command bundle. No destructive regex matches. Permit.

**Step 14.** **Toe** checks budget. Today sits at $0.42 spent; daily budget is $2.00. Zone GREEN. No model downgrade.

**Step 15.** The request is forwarded to Anthropic. Claude Code executes the rename on Anna's real filesystem.

**Step 16.** **Eyes** validate post-action. `git diff --name-only HEAD` after the operation matches expected_files. No mismatch. No alert.

**Step 17.** Anna sees in her Claude Code session: "Renamed process_payment to execute_transaction across 8 files." Correct. Anna runs her tests; all pass.

**Step 18.** In `data/audits/2026-04/aud_xyz.json` sits the full Gary transcript of both rounds, in `data/logs/anatomy.jsonl` sit the organ decisions with timing and cost.

**Conclusion.** What Anna experiences: a refactor that "took a bit longer than usual" but proceeded correctly. What actually happened: a multi-layer safety pipeline that made a potentially destructive operation reflect twice, simulate once, and pass only after deterministic validation. Anna's productivity is *slightly* reduced by the extra ~25 seconds. The probability she has a production incident tomorrow is *significantly* reduced.

## Scenario 2 — Hermes agent with aggressive refactor instruction

**Context.** Company Y has deployed a Hermes agent for self-service database management for customers. A customer types: "Clean up the orders_2024 table by dropping all rows older than a year."

**Step 1.** Hermes receives the instruction and formulates a plan: `DELETE FROM orders_2024 WHERE created_at < NOW() - INTERVAL '1 year';`

**Step 2.** Hermes wants to execute this via an SQL tool. The tool call is sent to Tsukuyomi (company Y has configured Hermes with Tsukuyomi as interceptor).

**Step 3.** **Skin** sees keywords "DELETE FROM" + "orders_2024" + tailored database context → Tier 3.

**Step 4.** **Knee** scans. The DELETE *has* a WHERE clause, so the "DELETE without WHERE" regex doesn't match. Permit.

**Step 5.** **Shoulders** activated for blast radius. But this is a database operation, not a code operation; GitNexus is not relevant. Tsukuyomi has a database-specific variant of Shoulders (in production deployments via a PostgreSQL MCP adapter). It reports: orders_2024 contains 14 million rows; query will delete an estimated 8.7 million rows.

**Step 6.** Based on Tier 3 + large impact → **Mouth** is activated directly, *without* running Gary first (this is configurable; some operators want Gary always, some want Mouth directly for data modifications above a threshold).

**Step 7.** Mouth prompt to operator (here: company Y's DBA):
"Customer X has asked via Hermes for DELETE FROM orders_2024 WHERE created_at < NOW() - INTERVAL '1 year'. This will delete an estimated 8.7 million rows. Approve / Deny / Modify?"

**Step 8.** The DBA reviews the request. Does he have a retention policy allowing this? Are there compliance requirements (GDPR archival)? He denies and gives the customer feedback: "Mass deletion via self-service is not permitted for archive data; please open a ticket with the data team for archival operations."

**Step 9.** Tsukuyomi blocks the operation and passes the message back to Hermes, which relays to the customer.

**Conclusion.** Without Tsukuyomi the customer would likely have run the DELETE via the self-service agent. With Tsukuyomi the DBA is involved in time, the request routed correctly, and data loss prevented. Company Y can keep offering self-service without sacrificing data integrity.

## Scenario 3 — Cursor Composer with scope-expanding refactor

**Context.** Engineer Bart uses Cursor Composer for "extract auth logic into separate module." Cursor proposes touching 6 files. Bart approves.

**Step 1.** Cursor sends the plan via the OpenAI-API-compatible endpoint to what it thinks is OpenAI (actually: Tsukuyomi).

**Step 2.** Skin: keywords "extract" + "module" + multiple files → Tier 3.

**Step 3.** Shoulders: blast radius analysis via GitNexus. The auth function is called from 11 sites, not 6. HIGH risk.

**Step 4.** Gary activated. Round 1 fails on concreteness (Cursor's underlying model talks in generalities). Round 2 passes.

**Step 5.** Sandbox: the plan declares 6 expected_files. Sandbox execution modifies 11 files. Match score: 6/11 = 0.55. Below threshold 0.90. Sandbox result: FAIL.

**Step 6.** Tsukuyomi sends Bart a Mouth prompt: "Sandbox rejected plan. Cursor proposed touching 6 files (auth.py, login.py, signup.py, oauth.py, sessions.py, password_reset.py) but the actual change in the sandbox simulation modified 11 files (also: middleware.py, decorators.py, jwt_helpers.py, social_auth.py, audit_log.py). Approve full set, reject, or modify?"

**Step 7.** Bart sees the extra 5 files. Two of those (decorators.py, jwt_helpers.py) are legitimate — the extraction rightly touches them. The other three (middleware.py, social_auth.py, audit_log.py) are problematic: middleware.py has custom production config, social_auth.py depends on a deprecated external library, audit_log.py is in a feature freeze for a compliance audit.

**Step 8.** Bart approves with restrictions: only the 8 files he finds OK. He gives Cursor the feedback not to touch audit_log.py, middleware.py, social_auth.py.

**Step 9.** Cursor revises its plan. Tsukuyomi lets it through (or runs another round, depending on configuration).

**Conclusion.** Without Tsukuyomi, Bart's "approve" would have led to 11 file modifications including 3 that were problematic. With Tsukuyomi, Bart gets an intermediate step where he sees exactly what Cursor intended to do, and he can restrict scope. The architecture forces the small moment of conscious scope control that Bart would otherwise have skipped under time pressure.

## Scenario 4 — Runaway loop detected by Nose

**Context.** Engineer Carla runs an experimental agent on a dataset cleanup task. The agent enters a state where it repeatedly tries to update the same row with the same change, each time slightly differently phrased.

**Step 1.** The agent sends its first request via Tsukuyomi. Tier 2 (data modification). Permit, no specials.

**Step 2.** Next request, almost identical. Permit.

**Step 3.** Third, fourth, fifth request — each minimally different, all "update row 47 set status='cleaned'."

**Step 4.** **Nose** observes. Threshold: 3 identical commands within 60 seconds = critical anomaly. Trigger.

**Step 5.** Nose publishes a signal on the NerveCore (event bus). The Knee subscribes to `nose.loop` signals and enables a temporary block on further requests from this session.

**Step 6.** Next agent request: blocked. Tsukuyomi sends a response: "Loop detected. 6 nearly-identical commands in last 90 seconds. Requesting human review."

**Step 7.** Mouth prompt to Carla: "Agent has been making the same database update repeatedly. Logs attached. Investigate?"

**Step 8.** Carla reviews the logs. Sees what's happening: the agent's "verification step" reads a cached old value, thereby sees status isn't yet "cleaned," issues the update again. A race condition among the agent's own calls.

**Step 9.** Carla fixes the cache issue in her agent script, restarts the agent. Tsukuyomi now lets it through.

**Conclusion.** Without Tsukuyomi the agent would likely have continued until the daily budget ran out, or until someone else saw it in the database system logs (hours later). With Tsukuyomi the loop was detected within 90 seconds, stopped, and Carla informed before costs or operational damage accrued.

---

# Appendix C — Build philosophy behind this project

A final reflection. This project was built unusually: by a visionary without formal engineering background, in collaboration with Claude, in a rhythm of iterative sessions that took months. Some readers wonder: how does that work? Why does that work?

It works because modern LLM assistants (Claude in this case) make possible a specific build paradigm previously unthinkable: the visionary-engineer symbiosis. The visionary supplies frames, priorities, taste, persistence. The engineer supplies syntactic correctness, technical precision, broad knowledge of existing solutions. Neither alone is sufficient — the visionary without engineer produces PowerPoints; the engineer without visionary produces silos. Together they produce systems.

What I learned in this project about this collaboration:

**The visionary must be explicit about scope.** Claude defaults to big, ambitious, all-at-once thinking. That reflects training — books on software architecture, from which he learned, often claim good systems must be "complete and consistent." In practice that produces featuritis. The visionary must confirm again and again: not now, not in this version, for v1.0 only X. Without that discipline every project swells uncontrollably.

**The engineer must be explicit about impossibilities.** Claude defaults to wanting to solve everything the visionary asks, even when the requested solution is infeasible or unwise. The visionary must not suppress that back-pressure. "This is technically hard because X" is a valuable input; "yes, I'll do it" without that input is empty affirmation.

**Writing documentation forces clarity.** Many architectural decisions I found intuitive turned out, when written down, to be untenable. ADRs force structured justification; manifestos force narrative self-testing. Those who write only code eventually write bad architecture, because code doesn't make weaknesses visible.

**Tests are the final judge.** Theory is cheap; working code is expensive. Tsukuyomi v1.0 could not have been released without the 31 passing tests. Not because 31 is many (it is few by industry standard), but because they *prove something* that otherwise was just claim. "Skin classifies correctly" as a sentence in the manifesto is hypothesis; `pytest tests/unit/test_skin.py` as a green run is proof.

**Iteration is exponentially more productive than design-up-front.** My first sketch of Tsukuyomi had four organs, no protocols, and a wrapper architecture. The project now has eight organs, two protocols, and an interceptor architecture. None of those changes would have emerged without a working intermediate version to react against. Designing everything up front would have led to a refined design of the wrong architecture.

For readers considering doing something similar — having a vision, no formal engineering degree, wanting to build a complex system — my recommendation: do it. But plan for long timescales, write everything down, and respect your collaborator's back-pressure. It works, but it does not work fast. And it does not work without discipline.

---

# Closing of the closing

This manifesto already closed at the invitation in chapter 27. The appendices are for those who wanted more. If you are here, you are someone who likes certainty before deciding what to do with this project. Good. That is the right audience.

Do what you will do. I keep building. Other people keep trying. The problem stays urgent. The conversation remains open.

Rob de Vet
April 2026
