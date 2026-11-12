# Environment

## Software

Isaac Lab in the launchable is installed from a container image, not a git clone, so there is no commit hash.
These are the exact versions used (from `cat /workspace/isaaclab/VERSION` and `./isaaclab.sh -p -m pip list`):

| Component | Version |
|---|---|
| Isaac Sim | 6.0.1 |
| Isaac Lab (`VERSION`) | 3.0.0 (launchable labels it 3.0.0-beta2-post1) |
| `isaaclab` | 6.1.16 |
| `isaaclab_tasks` (DexSuite lives here) | 1.10.9 |
| `isaaclab_rl` | 0.5.7 |
| `isaaclab_physx` | 1.1.3 |
| `isaaclab_newton` | 0.13.6 |
| `newton` | 1.2.1 |
| `mujoco` / `mujoco-warp` | 3.8.1 / 3.8.1 |
| `warp-lang` | 1.13.0 |
| `rsl-rl-lib` (PPO) | 5.0.1 |
| `torch` | 2.10.0+cu128 |
| NVIDIA driver | 595.71.05 (CUDA 13.2) |

Isaac Lab 3.0 is in beta, so task names and command-line flags may change between releases.

## Hardware and cloud

- **Provider:** NVIDIA Brev, using the official **Isaac Launchable** (Isaac Sim and Isaac Lab preinstalled in containers, VS Code in the browser)
- **Instance:** AWS `g6e.4xlarge`: 1× NVIDIA L40S (48 GB), 16 vCPU, 128 GiB RAM
- **Region:** us-east-1 (Ashburn, VA). European regions (eu-north-1, eu-central-1) failed to provision with "internal server error".
- **Cost:** $3.65/hr running, $0.04/hr stopped (storage only)

An RTX-class GPU (L40S, RTX 6000 Ada, RTX PRO 6000) is needed for Isaac Sim rendering and video capture.
Compute-only GPUs (A100, H100) can train but can't render.

## Working inside the launchable

- The VS Code terminal runs inside a container as a non-root user: no `sudo`, so no `tmux`.
  Long runs use `nohup` with `PYTHONUNBUFFERED=1` so the log updates live:

  ```bash
  PYTHONUNBUFFERED=1 nohup ./isaaclab.sh train ... > ~/runs/<name>.log 2>&1 &
  tail -f ~/runs/<name>.log
  ```

- Isaac Lab lives at `/workspace/isaaclab`; run outputs go to `/workspace/isaaclab/logs/rsl_rl/`.
- Harmless start-up warnings: repeated `OmniHub ... Hub failed to launch`, `failed to open the default display`,
  and `_isaac_sim/setup_conda_env.sh is missing`.

## Auto-stop when idle

`scripts/idle_stop.sh` stops the instance (`brev stop`) once no training or playback has run for 20 minutes.
It needs the Brev CLI inside the VS Code container (no `sudo`, so it goes in `~/bin`):

```bash
mkdir -p ~/bin /tmp/brev-cli && cd /tmp/brev-cli
URL=$(curl -s https://api.github.com/repos/brevdev/brev-cli/releases/latest \
  | grep browser_download_url | grep -i linux | grep -iE "amd64|x86_64" | grep "tar.gz" | head -1 | cut -d'"' -f4)
curl -sL "$URL" | tar xz && find . -name brev -type f -exec mv {} ~/bin/ \; && chmod +x ~/bin/brev
~/bin/brev login     # follow the link/code it prints
~/bin/brev ls        # confirm the instance name
```

## Server agent (Claude Code on the instance)

The instance runs a Claude Code agent that follows `PLAN.md`: it resumes crashed runs, starts the next tasks,
backs up results and reports in `STATUS.md`. See `CLAUDE.md` (its instructions) and `scripts/agent_prompt.md`.

One-time setup, in a VS Code terminal on the instance:

```bash
curl -fsSL https://claude.ai/install.sh | bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc && source ~/.bashrc
cd ~/dexterity-physics-engines && claude      # log in once, then type /exit
```

Unattended `git push` needs a stored credential, because the VS Code sign-in only works inside VS Code:
create a fine-grained GitHub token limited to this repository with **Contents: Read and write**, then

```bash
git config --global credential.helper store
git push        # username: arassch, password: the token (saved to ~/.git-credentials)
```

Start, stop and inspect the agent:

```bash
mkdir -p ~/runs/agent
scripts/agent_watch.sh --once                                   # one wake-up now, to test
nohup scripts/agent_watch.sh > ~/runs/agent/watch.log 2>&1 &    # keep watching
tail ~/runs/agent/ticks.log                                     # what each wake-up did
pkill -f agent_watch.sh                                         # stop watching
```

The watcher checks every 5 minutes without using Claude, and wakes Claude only when PLAN.md changes on GitHub,
a run starts/finishes/crashes, or 2 hours pass. Claude runs with `--permission-mode dontAsk` and an explicit
allow-list (in `scripts/agent_tick.sh`); `.claude/settings.json` denies `brev`, `sudo`, `rm`, `curl`, force-push.
