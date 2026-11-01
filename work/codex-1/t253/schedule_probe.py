"""Prototype: trace a scheduler's step arguments during the main pipeline call.

Install only after auxiliary calls, while the caller holds the pipeline lock. This
is a diagnostic proposal, not deployed server code. It intentionally records
actual step calls, rather than inferring them from the requested step count.
"""
from contextlib import contextmanager


def _values(x):
    if hasattr(x, 'detach'):
        x = x.detach().cpu()
    if hasattr(x, 'tolist'):
        x = x.tolist()
    if isinstance(x, (list, tuple)):
        return [float(v) for v in x]
    return float(x)


@contextmanager
def trace_schedule(scheduler):
    trace = {'scheduler_class': type(scheduler).__name__, 'timesteps': None,
             'sigmas': None, 'step_timesteps': []}
    original = scheduler.step
    had_instance_step = 'step' in vars(scheduler)
    previous_instance_step = vars(scheduler).get('step')

    def step(*args, **kwargs):
        # Diffusers scheduler.step(model_output, timestep, sample, ...).
        t = args[1] if len(args) > 1 else kwargs['timestep']
        if trace['timesteps'] is None:
            trace['timesteps'] = _values(scheduler.timesteps)
            trace['sigmas'] = _values(scheduler.sigmas)
        trace['step_timesteps'].append(_values(t))
        return original(*args, **kwargs)

    scheduler.step = step
    try:
        yield trace
    finally:
        if had_instance_step:
            scheduler.step = previous_instance_step
        else:
            del scheduler.step
