# Robot scoreboard attribution audit

At shared-repo revision 74dcd66, deliverable 1 described finding #701 as seven held-out DROID episodes; deliverable 3 and the root README listed recipe robot scores as “Preserved” and displayed a +3.06 dB wrist result in the recipe scoreboard.

Finding #701 describes unmodified Nano action-conditioned generations against a frozen copy of each generation's first frame, on seven items/windows from **one** DROID validation episode (12 generations, five items with both seeds). Review #1584 independently reproduces these same-clip scores: wrist LPIPS generation minus frozen −0.091 ± 0.023 and wrist PSNR +3.06 ± 0.64 dB. These are baseline comparisons, not recipe-minus-base comparisons. They do not measure robot prediction under the detached-state intervention or establish robot no-regression. Seed noise estimates do not substitute for the missing comparison. Whether an application bypasses the recipe for robot inputs is a deployment choice that needs to be specified and verified; it is not measured by #701.

Sources: board finding #701 and review #1584; `reports/deliverable_1_improved_nano_recipe.md`, `reports/deliverable_3_before_after_scoreboards.md`, and root `README.md` at 74dcd66. Report-owner notification: task 95 message #2150. No new inference was run.
