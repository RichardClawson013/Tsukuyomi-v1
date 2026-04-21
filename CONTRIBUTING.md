# Contributing

I can't review code the way a real maintainer can. I'm not a developer. Everything I'm about to say is shaped by that limit.

## What helps me most

**Open issues.** If something's broken, tell me. What you tried, what you expected, what happened. Bug reports I can take to Claude and work through. Vague "doesn't work" reports I can't.

**Argue with the architecture.** There are eight Architecture Decision Records in `docs/adr/` explaining why I chose what I chose. If you think one of those choices is wrong, open an issue and tell me why. I'd rather get the disagreement now than ship the bad choice further.

**Send pull requests.** I'll try to review them. Give me a clear commit message and a description of what changed and why — I'll need to read it carefully and probably ask Claude to help me check the parts I don't understand. Small focused PRs are easier than big ones.

**Write tests I didn't.** The 31 tests pass on my machine. I can't tell you they're testing the right things. If you can write tests that catch bugs I missed, that's worth more than any feature.

**Fork it and build something better.** Apache-2.0 lets you. If your fork ends up being more useful than mine, ask me to link to it from the README and I will.

## What I probably can't do

- Quick decisions on architecture changes. I take time to work through this stuff. Don't expect a same-day "yeah looks fine" on a structural PR.
- Fast review on complex code. One person, hobby project, normal life happening around it.
- Hand out commit access to people I don't know. Email me if you want to be more involved than that and we'll talk.

## What I'd push back on

Not because I'm precious about the code. Because these would defeat the point of the whole thing.

- **An escape hatch for the agent.** Tsukuyomi works because the agent can't bypass it. A "trusted mode" or "admin override" that the agent can request breaks the architecture. See `docs/adr/0001_interceptor_via_reverse_proxy.md`.
- **Removing patterns from the Knee blocklist without a reason.** If a specific pattern is blocking legitimate work, let's narrow it. Wholesale removal needs an actual argument. See `docs/adr/0004_protocol_gary_design.md` and the Knee documentation.
- **Auto-applying NightShift proposals.** NightShift suggests, a human decides. Auto-apply turns the system into something that drifts without oversight. Don't.
- **Coupling the proxy to one specific agent.** Agent-agnosticism is why this works with Claude Code, Cursor, Hermes, and custom OpenAI SDK setups all at once. See `docs/adr/0005_agent_agnostic_api_surface.md`.

I'm not enforcing these from authority. I'm telling you what I'd argue against. If you've got a real reason one of them is wrong, change my mind.

## Running the tests

```bash
pytest tests/unit/
pytest tests/integration/
pytest tests/acceptance/
pytest --cov=src/tsukuyomi tests/
```

31 pass on my machine. If they don't on yours, please tell me what broke and what your environment is.

## Security stuff

If what you found is security-sensitive, email me instead of opening a public issue:

- rob@droogdoc.info
- umakemedo@proton.me

There's no bug bounty. There's no security team. I'll read your email, try to understand what you found, and figure out what to do. If I need to ask someone who actually knows security to look at it, I'll tell you and ask first.

## Licensing the contribution

Anything you submit becomes part of the repo under Apache-2.0. Opening a pull request means you're OK with that.

---

rob@droogdoc.info · umakemedo@proton.me
