# Security

Find something security-sensitive? Email me, don't open a public issue for it.

- rob@droogdoc.info
- umakemedo@proton.me

Either one works. I read both.

## What to expect

No bug bounty. No security team. No incident response playbook. I'm one person and I'm not a security professional. Realistically what happens when a report lands is: I read it, try to understand it, and point Cursor or Claude Code at fixing it. That's the extent of my toolkit. I don't have a network of security people to tap.

If what you found needs someone who actually knows security to evaluate, I'll tell you that and ask before I loop anyone else in. I'd rather be upfront about not knowing than pretend I do.

## What helps

Tell me:

- What you found.
- How to reproduce it, if you can.
- What you think the impact is.
- Whether you have an idea how to fix it. Not required, just useful if you do.

Clear writing beats security jargon. I won't follow acronyms I haven't Googled yet.

## What counts as security-relevant to me

- An agent reaching its model provider without going through the Tsukuyomi pipeline while Tsukuyomi is supposedly active.
- Getting the Knee (regex blocklist) to ignore patterns it's supposed to catch.
- Credentials (API keys, user secrets) ending up in logs or memory somewhere they shouldn't.
- Escaping the sandbox during plan simulation.
- SQL injection or memory corruption in the anatomic memory database.
- Prompt injection that reliably gets past Protocol Gary's audit validation.

## What's probably not a security issue

- General code messiness. Normal issue, not security.
- Stuff documented as "not done yet" in `docs/research/PAPER.md` section 7.2 or in the ADRs. That's known.
- Misconfigurations that reduce safety. Operator error, not a vulnerability. Happy to help configure it correctly, but don't file it as security.

## Coordinated disclosure

If you found something serious and want to give me time to fix it before publishing — that's good form, thanks. Email me first and we'll figure out a timeline together. I won't commit to industry-standard windows because I can't always hit them. What I can do is tell you honestly what's realistic and stick to that.

---

rob@droogdoc.info · umakemedo@proton.me
