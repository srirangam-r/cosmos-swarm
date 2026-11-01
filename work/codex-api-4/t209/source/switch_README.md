# Prompt-switch probe (task 22 v8; scout #2337 method a)
When in denoising does the timed-settle clause (QT, #2460) act? server_prompt_switch.py = ro-1's :8021 server plus an
optional extra_params `prompt_switch {"prompt": P2, "from": a, "to": b}`: for steps a <= i < b of 35, the CONDITIONAL
CFG pass gets P2's packed text (captured by a 1-step dry run that aborts at the first transformer call); the uncond
pass is unchanged (empty negative in both F and QT). Arms (ball1 dd33, seeds 3 and 5, base prompt F, P2 = QT):
SWfull [0,35) = hook check, must reproduce cause5_QT pixel-for-pixel; SWe3 [0,3); SWe7 [0,7); SWl7 [7,35); SWl17 [17,35).
Prediction (TunerDiT 2605.31590): if the settle is a layout-level decision, SWe7 ~ QT and SWl7 ~ F.
Readout: eye settle code plus the late20 corridor proxy (cause_v5/analyze.py), as in #2460.
