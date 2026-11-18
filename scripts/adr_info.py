"""T26b helpers: read the ADR difficulty and the gravity actually applied, and freeze ADR (no demotion).

The Play configs start ADR at max_difficulty but leave `promotion_only` False, so `DifficultyScheduler` lowers each
env's difficulty by 1 on every reset without success (always, with the cube parked). The difficulty fraction scales
`variable_gravity` (0 -> -9.81) and the observation noises. `freeze_adr(env_cfg)` sets promotion_only=True, so with
init = max the difficulty stays at max.
"""

import contextlib


def freeze_adr(env_cfg):
    env_cfg.curriculum.adr.params["promotion_only"] = True
    return env_cfg.curriculum.adr.params


def adr_state(u):
    """dict: difficulty mean/min/max over envs, difficulty_frac, configured gravity z range, applied gravity z."""
    d = {}
    with contextlib.suppress(Exception):
        sched = u.curriculum_manager.cfg.adr.func
        x = sched.current_adr_difficulties.float().cpu().numpy()
        d.update(adr_mean=float(x.mean()), adr_min=float(x.min()), adr_max=float(x.max()),
                 adr_frac=float(sched.difficulty_frac))
    with contextlib.suppress(Exception):
        g = u.event_manager.get_term_cfg("variable_gravity").params["gravity_distribution_params"]
        d.update(g_cfg_lo=float(g[0][2]), g_cfg_hi=float(g[1][2]))
    try:  # Newton: per-world gravity array
        import warp as wp
        from isaaclab_newton.physics.newton_manager import NewtonManager

        m = NewtonManager.get_model()
        gz = wp.to_torch(m.gravity).reshape(-1, 3)[:, 2].float().cpu().numpy()
        d.update(g_z_mean=float(gz.mean()), g_z_min=float(gz.min()), g_z_max=float(gz.max()))
    except Exception:
        with contextlib.suppress(Exception):  # PhysX: scene-wide
            import isaaclab.sim as sim_utils

            g = sim_utils.SimulationContext.instance().physics_sim_view.get_gravity()
            gz = float(g[2])
            d.update(g_z_mean=gz, g_z_min=gz, g_z_max=gz)
    return d


def fmt(d):
    def f(k, p=2):
        return f"{d[k]:.{p}f}" if k in d else "?"
    return (f"ADR difficulty mean {f('adr_mean')} (min {f('adr_min', 0)}, max {f('adr_max', 0)}), frac {f('adr_frac', 3)}; "
            f"gravity z cfg [{f('g_cfg_lo')}, {f('g_cfg_hi')}], applied mean {f('g_z_mean')} "
            f"(min {f('g_z_min')}, max {f('g_z_max')})")
