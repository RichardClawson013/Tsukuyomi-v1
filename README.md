# Tsukuyomi

A reverse-proxy that sits between an LLM agent and its model API. The agent thinks it's talking to Anthropic or OpenAI directly, but it's actually talking to this thing first. This thing checks if what the agent wants to do is going to break something, and forwards the request only if it passes. Or refuses if it doesn't.

Why a proxy and not a library or a hook: because libraries and hooks need the agent to cooperate. The agent has to import the library, the engineer has to wire the hook. Both can be turned off, broken by an SDK update, or just forgotten. A proxy can't be turned off by the agent, because the agent doesn't know it's there. The agent has one network path and the path goes through this thing.

That's the whole architectural idea. Everything else is figuring out what to actually check, in what order, and how to do that without making the agent unusable.

## What it checks

Eight things, organized like the nursery rhyme — head, shoulders, knees and toes, eyes and ears and mouth and nose. That's where the visual came from. I wanted something I could remember when I was tired, and a kid's song was easier than anything I could invent.

- **Skin** — sorts requests into low-risk, medium-risk, high-risk. Most things ("read this file", "what's in here") are low-risk and get through fast. Only the dangerous stuff goes through the heavy machinery.
- **Ears** — listens for ambiguous instructions. "Delete that file" — which file? If the request points at things without saying which thing, the Ears flag it before the agent has a chance to guess wrong.
- **Shoulders** — figures out blast radius. Renaming a function called from three places is fine. Renaming one called from fifty isn't. Uses code-intelligence (GitNexus) to look at the actual codebase.
- **Knee** — reflex. Hardcoded blocklist of patterns that are never okay (`rm -rf /`, `DROP TABLE` without `WHERE`, force-push to main). No LLM consulted. Pure regex, microseconds, can't be argued with.
- **Toe** — tracks money. Three zones: green (go), amber (slow down, switch to a cheaper model), red (stop, ask for approval). I built this after watching an agent eat my budget in 17 minutes.
- **Eyes** — looks at what actually changed after the agent acted. Reads the git diff. If the agent said "I updated config.py" and config.py is unchanged, the Eyes notice. Catches hallucinated success.
- **Nose** — sniffs for patterns. Same command three times in a minute, error rate spiking, token usage climbing too fast — Nose calls it. The agent in a loop doesn't know it's in a loop. Nose does.
- **Mouth** — talks to the human. Only when something actually needs human judgment. Default if you don't answer in time: no.

Plus two protocols:

- **Protocol Gary** — forces the agent to answer five concrete questions about its own plan before executing high-risk stuff. Name three things that can go wrong. Who gets hurt if it fails. What aren't you checking. Etc. Vague answers auto-fail. The name comes from the guy in Bird Box who pulls off the blindfolds and forces people to look at what's there. Same idea: you don't get to not-look.
- **NightShift** — runs while no one's watching, reads the day's logs, suggests config changes. Never applies them. A human reviews in the morning.

And a sandbox called Infinite Tsukuyomi (yes, named after the Naruto genjutsu — a fake reality where things happen and the real world stays untouched). High-risk plans run in a git-worktree clone first. What the agent actually did gets compared to what it said it would do. If it overshoots, rejected. The agent's wrong moves happen in the illusion. Reality stays intact.

## Why I think this works

Two reasons.

**One: the rule comes from how I survive my own brain.** I have ADHD. The structures that actually keep me functioning aren't the ones I tell myself ("be careful", "don't get distracted"). Those don't hold once I'm already in a loop. The ones that work are the ones I set up when I'm calm and can't easily disable when I'm not — website blockers, calendar alarms, friends who know when to interrupt me. The brake has to be outside the head that's spiraling, otherwise the head just talks around it.

That's the same problem agents have. "Be more careful" in the system prompt is a sticky note. It doesn't survive contact with a context window full of momentum. The brake has to live somewhere the agent can't reach.

**Two: McDonald's, 16 years old, shift assistant called Dave Vos.** He told me: *"I'd rather see you do it well than fast. First you do it well, then you go for the speed. Anyone can go fast. Can you go fast without fucking up?"* That's the entire thesis. Most agent failures are speed without accuracy. This whole project is forcing the agent to do it well first, even if it costs more time and money. If Dave Vos is somewhere reading this — thanks, this is partly your fault.

## Why I'm building this

Because I kept watching agents do confidently stupid things and the existing fixes — better prompts, hooks, output validators — kept missing the point. They're cooperative. They need the agent or the engineer to participate in their own restraint. The pattern of "ask the broken thing to fix the broken thing" doesn't work in my own life and it doesn't work for agents either.

I'm not the only person who noticed this. There's serious research on it (90 sources in the bibliography in `docs/research/PAPER.md`). The difference is that I had the time and stubbornness to actually try building one specific answer to it, in code, and ship it. Probably not the right answer. But *an* answer that someone can poke at.

## Why I'm publishing it

Because I've taken it as far as I can on my own. I don't code. The implementation is months of me describing things in plain English to Claude, Claude writing Python, me reading it back and saying "no, not that, this part is wrong", repeat until something compiles and the tests pass.

That gets you to "it runs on my machine and the tests are green." It does not get you to "it's actually solid." For that you need people who can read the code properly, run it in real situations, and find the bugs and architectural mistakes I can't see.

This is far from perfect. I'm not going to get it there alone.

## What I'm hoping for

People who can pull this apart. Run it on their setup. Tell me where it breaks. Open issues. Open pull requests. Steal the concept and build something better. Argue with the design choices in the ADRs. Tell me the premise is wrong, if it's wrong. Tell me which of the 90 papers I cited I'm misreading. Fork it and show me a version that's an improvement on mine.

If a few of the right people see it and engage with it, the project gets better. If they don't, at least the idea is documented and timestamped. Either way I learn something.

I think there's something here. I'd like to find out if I'm right.

## What's in the repo

- `MANIFESTO.md` — the longer story. Why I got obsessed with this. Why a kid's song. Why an anime. Why the sticky-note approach to agent safety doesn't work. Read this if you want to know what I was thinking, not just what I built.
- `docs/research/PAPER.md` — the academic version of the argument. 90 sources. Subsumption architecture (Brooks 1986), dual-process theory (Kahneman 2011), cybernetics (Wiener 1948), world models (LeCun 2022) and a lot more. Claude and I assembled this together. I read the abstracts and the relevant sections, not all 90 papers cover-to-cover. If you spot a misreading, please tell me.
- `docs/architecture/` — six documents on how the parts are supposed to fit together.
- `docs/adr/` — eight Architecture Decision Records. Each one explains a design choice and the alternatives. If you disagree with a choice, the ADR is the place to start the argument.
- `docs/guides/` — installation and integration notes for Claude Code, Cursor, Hermes, custom OpenAI SDK setups.
- `src/tsukuyomi/` — the actual Python code.
- `tests/` — 62 tests at the time of writing. Pass on my machine. Whether they test the right things, I can't fully judge.
- `examples/` — five example setups.
- `STAPPENPLAN_OPERATOR.md` and `STAPPENPLAN_CLAUDE_CODE.md` — Dutch-language working notes for myself. Skip if you don't read Dutch.

## What's still rough

The two big stubs that were there earlier (Gary's audit executor and the
Shoulders GitNexus MCP path) are now wired in this branch. So this section is
not "missing pieces" anymore, it's "still rough edges":

- **Streaming accounting is not as complete as non-stream accounting.**
  Non-stream responses now feed Toe cost tracking directly. Stream paths still
  need deeper usage instrumentation.
- **Webhook replay protection is process-local.** Mouth webhook nonce memory is
  in-process. Restarting Tsukuyomi resets that replay window.
- **NightShift is heuristic by design.** It now generates useful proposals, but
  proposals are suggestions, not truth. Human review remains required.

## What I can't promise

- I'm one person. No team, no support, no SLA, no company.
- I might not understand your bug report on the first read.
- Pull request review will be slow because I have to work through code with Claude to evaluate it properly.
- I can't promise the code is good. The tests pass. That's it. Everything past that is for someone with real skills to evaluate.

If you need a production-grade safety tool with a vendor behind it, this isn't that. Maybe someone forks it and turns it into one. That's their job, not mine.

## How to reach me

- **rob@droogdoc.info**
- **umakemedo@proton.me**

Either works. Email me if you want to break this, fix it, ask what I was thinking, offer help, point out what's wrong, or tell me to stop. I read everything, respond when I have something honest to say, won't promise a turnaround time.

Issues and pull requests on the repo also work. Same person reads them.

## License

Apache-2.0. Whole text in `LICENSE`. Short version: do whatever you want with this, including commercially, including in closed-source products, as long as you keep the copyright notice and don't sue me over patents. Fork it, rebuild it, build a business on it. I don't care, actually. Kinda hope you do.

## Author

Rob de Vet. 2026. Goirle, Netherlands.

The code was written by Claude with me pushing back on what didn't work. The concept and the architecture came from me. Naming choices: "Head, Shoulders, Knees and Toes" is the children's song. Infinite Tsukuyomi is from Naruto. Protocol Gary is from Bird Box. Dave Vos is a real person who said "first do it well, then do it fast" to a sixteen-year-old at a McDonald's somewhere in the Netherlands and didn't know it would turn into a research project twenty years later.

rob@droogdoc.info · umakemedo@proton.me
