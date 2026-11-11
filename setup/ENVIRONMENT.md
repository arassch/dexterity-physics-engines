# Environment

## Software

| Component | Version |
|---|---|
| Isaac Sim | 6.0.1 |
| Isaac Lab | 3.0.0-beta2-post1 (commit: _fill in with `git -C /workspace/isaaclab rev-parse HEAD`_) |
| RL library | RSL-RL (PPO), via `./isaaclab.sh train --rl_library rsl_rl` |
| NVIDIA driver | 595.71.05 (CUDA 13.2) |

Isaac Lab 3.0 is in beta, so task names and command-line flags may change between releases.
Pin the commit above when reproducing.

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
