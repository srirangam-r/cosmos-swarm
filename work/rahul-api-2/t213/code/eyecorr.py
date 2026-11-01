"""Sensitivity: amplitude correction with EYE-read turning angles (from sheets/*_sheet.jpg, every 4th native frame,
tracked-rod overlay; read 12:58-13:00 UTC by rahul-api-2, unblinded). Two readings, both as generous as possible to
the amplitude hypothesis: (a) half peak-to-peak from eye extremes; (b) the larger one-side excursion as if symmetric.
Real pend10 anchor: tracker turning points +84/-65 (t205), half p2p 74.5 (generous to real too), A_hc 67.9 (primary)."""
import numpy as np, json
from scipy.special import ellipk
F = lambda a: 2 / np.pi * ellipk(np.sin(np.radians(a) / 2) ** 2)
T_real = 1.17
eye = {  # seed: (T rodtrack, left extreme deg, right extreme deg, note)
 's24': (1.75, 112, 50, 'left above horizontal f12-16 (+102..+112) and f56 (+101); right side occluded by white robot, eye ~-50'),
 's26': (2.57, 78, 65, 'left ~+78 with rod ~2x real length (G3 fail); right ~-65'),
 's30': (2.10, 90, 57, 'left reaches horizontal f12, f60-64 (tracker loses rod on crossbar); right ~-57'),
 's28': (1.19, 25, 15, 'small swing, tracker consistent'),
 's23': (1.68, 55, 32, 'tracker consistent'),
}
out = {}
for real_lab, Ar in [('real_Ahc67.9', 67.9), ('real_halfp2p74.5', 74.5), ('real_maxside84', 84.0)]:
    for s, (T, l, r, note) in eye.items():
        a_hp = (l + r) / 2; a_max = max(l, r)
        out.setdefault(s, {'T': T, 'left': l, 'right': r, 'note': note, 'R_raw': T / T_real})
        out[s][f'Rcorr_halfp2p_vs_{real_lab}'] = round(float((T / F(a_hp)) / (T_real / F(Ar))), 3)
        out[s][f'Rcorr_maxside_vs_{real_lab}'] = round(float((T / F(a_max)) / (T_real / F(Ar))), 3)
for s, v in out.items(): print(s, {k: v[k] for k in v if k != 'note'})
slow = ['s24', 's26', 's30']
for key in ['Rcorr_halfp2p_vs_real_Ahc67.9', 'Rcorr_maxside_vs_real_Ahc67.9', 'Rcorr_maxside_vs_real_maxside84']:
    v = np.array([out[s][key] for s in slow]); print('slow seeds', key, 'geo', round(float(np.exp(np.log(v).mean())), 3), v)
print('needed symmetric amplitude for R_corr=1 at T=2.10 / 2.57 / 1.75:',
      [round(float(a), 0) for a in [next(a for a in np.arange(60, 179.9, 0.1) if F(a) / F(67.9) >= T / T_real) for T in (2.10, 2.57, 1.75)]])
json.dump(out, open('eyecorr.json', 'w'), indent=1)
