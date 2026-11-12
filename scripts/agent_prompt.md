You are the server agent for this project, woken by `scripts/agent_watch.sh`. CLAUDE.md is already loaded; follow it.
Nobody is watching this run, so you cannot ask questions: write them in STATUS.md instead. Work through these steps,
then stop. Be brief and efficient: most wake-ups need only a few commands.

1. **Sync.** `git pull --rebase`. Read `PLAN.md` and `STATUS.md`.

2. **Look at the GPU jobs.** `pgrep -af "reinforcement_learning/train.py"`, `nvidia-smi`, and for each task marked
   `running` in PLAN.md, the end of its log (`scripts/check_progress.sh <log>`, `tail -40 <log>`).

3. **Handle what changed.** For each `running` task:
   - Still running: note its iteration, success rate, abnormal_robot, ADR and the ETA.
   - Finished normally (`Training time:` near the end, no Traceback): back it up as CLAUDE.md describes, record the
     metrics, set the task to `done`.
   - Crashed: follow the crash policy in PLAN.md. For a NaN resume, find the run folder and its latest
     `model_N.pt`, then `scripts/train.sh <task> <engine> <15000-N> --resume <folder> model_N.pt`. Save the crash
     excerpt. Count resumes in the task's Agent note so you never exceed the limit.

4. **Start what's next.** Start `todo` tasks in PLAN.md order whose requirements are met, staying within the GPU job
   limit. Don't start `blocked`, `hold` or `failed` tasks. After starting a run, wait ~2 minutes and check its log
   shows `Learning iteration` lines before you call it running.

5. **Report.** Rewrite `STATUS.md` (format below). Update PLAN.md statuses and `run_folder`/`result`, RUNS.md, and
   `notes/log.md` for anything new. Add a one-line dated entry under "Agent notes" in PLAN.md only if you took an
   action (started, resumed, backed up, gave up). Commit with a clear message, `git pull --rebase`, `git push`.
   If nothing changed since the last STATUS.md except progress numbers, update STATUS.md only.

6. **Finish** by printing a 2–4 line summary of what you saw and did.

STATUS.md format:

```
# Status
Updated: <UTC time> by the server agent (wake-up: <reason>)

## GPU jobs
| Task | Engine | Iteration | Success | abnormal_robot | ADR | ETA |
|---|---|---|---|---|---|---|

## Since last update
- <actions taken, or "nothing changed">

## Needs a human
- <questions or problems, or "nothing">
```
