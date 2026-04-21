# Install

How to get this running on your machine.

## What you need

- Python 3.11 or newer.
- Git.
- A terminal you can paste commands into. I built and tested this on Windows with WSL2 (Ubuntu). It probably works on Linux and macOS the same way. I don't know about plain Windows without WSL — I haven't tried.
- Disk space: small, well under 100 MB.

## Get the code

```bash
git clone https://github.com/RichardClawson013/Tsukuyomi.git
cd Tsukuyomi
```

## Set up a Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate    # Linux / macOS / WSL
# or on Windows:  .venv\Scripts\activate
```

## Install the package and its dev dependencies

```bash
pip install -e ".[dev]"
```

If this fails, the most common cause is having a Python older than 3.11. Check with `python3 --version`.

## Run the tests

```bash
pytest
```

You should see something like `31 passed`. If a test fails on your machine but passes on mine, open an issue and tell me what failed and what your environment is.

## Try starting it

```bash
tsukuyomi init
tsukuyomi start
```

The `init` command creates a config directory with a default config file. The `start` command launches the proxy and it should print one line saying it is listening on port 9999.

In another terminal, check it's alive:

```bash
curl http://localhost:9999/health
```

You should get `{"status":"ok","version":"1.0.0"}` back. If you don't, something went wrong starting it. Check the terminal where `tsukuyomi start` is running.

## Point an agent at it

If you use Claude Code:

```bash
export ANTHROPIC_BASE_URL=http://localhost:9999
claude-code "list the files here"
```

Claude Code now talks to Tsukuyomi instead of directly to Anthropic. Tsukuyomi forwards the request to Anthropic if it passes the safety pipeline.

For other agents, see `docs/guides/integrating_*.md`.

## You'll need API keys

Tsukuyomi forwards requests to whatever model provider you tell it to use. It doesn't have its own model. So you need an API key for whichever provider you're using.

```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or
export OPENAI_API_KEY=sk-...
```

Set these in your shell before starting Tsukuyomi. **Do not put them in the config file.** They live in environment variables on purpose.

## What's probably going to confuse you

A few things worth knowing up front.

- **Two parts of v1.0 are stubs.** Protocol Gary's audit-LLM caller and the GitNexus blast-radius client. They're documented as stubs in `docs/research/PAPER.md` section 7.2 and in the ADRs. If you wonder why the audit always trivially passes or why blast radius is always "UNKNOWN treated as HIGH-risk," it's because these pieces aren't wired yet. Not hidden, just not done.

- **The Mouth defaults to "deny" on timeout.** This is on purpose. If you're testing in a script and the Mouth is waiting for human approval, it will time out and the request will fail. That's the safe default. You can adjust the timeout in `corelaw.json` if you need to.

- **The sandbox needs a git-tracked project.** It uses `git worktree` to clone the repo for simulation. If you point Tsukuyomi at a project that isn't a git repo, the sandbox steps don't work and Tsukuyomi falls back to other safety checks.

- **Logs go to a `data/` folder by default.** That folder is in `.gitignore` so don't commit it. If you want to see what Tsukuyomi is doing, look there.

## If something goes wrong

`docs/guides/troubleshooting.md` has the issues I've personally run into and how I solved them.

If you hit something not in that doc, please open an issue or email me:

- rob@droogdoc.info
- umakemedo@proton.me

Include the full error message, your Python version, and your OS. I can't promise I'll know how to fix it. At this point in the project my debugging toolkit is "put it in Cursor or Claude Code and see what they say." Beats silence.

## Uninstalling

```bash
pip uninstall tsukuyomi
rm -rf data/
```

That removes the package and the local data. If you want to also remove the config:

```bash
rm -rf ~/.local/share/tsukuyomi/
```

(Or the equivalent on your OS.)

---

rob@droogdoc.info · umakemedo@proton.me
