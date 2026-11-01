from pathlib import Path
import json,numpy as np
import matplotlib;matplotlib.use('Agg')
import matplotlib.pyplot as plt
p=Path(__file__).parent;d=json.loads((p/'output/results.json').read_text()); ids=list(range(1,21));fig,axes=plt.subplots(2,1,figsize=(10,8),sharex=True)
for ax in axes:
 for i in ids:
  r=d[str(i)];t=r['tool'];v=r['ratio'];ref=r['reference_crossing']['period_s'];lo,hi=np.array(t['period_ci95'])/ref
  ax.errorbar(i,v,yerr=[[v-lo],[hi-v]],fmt='o',ms=4,color='#1565c0' if t['flag']=='ok' else '#b71c1c',capsize=2)
  ax.plot(i,r['ratio_turning'],'x',ms=5,color='#555555')
 ax.axhline(1,color='black',lw=1);ax.axhspan(.95,1.05,color='green',alpha=.06);ax.set_xticks(ids);ax.set_ylabel('Tool period / mocap period')
axes[0].set_title('93-frame real continuation calibration: all20 recordings')
axes[1].set_title('Same results, magnified around correct period (outliers above panel)');axes[1].set_ylim(.96,1.07);axes[1].set_xlabel('Real GAUGE recording')
axes[0].plot([],[],'o',color='#1565c0',label='flag=ok, fit / crossing reference; fit bootstrap CI95');axes[0].plot([],[],'o',color='#b71c1c',label='flag=check');axes[0].plot([],[],'x',color='#555555',label='Fit / turning-point reference');axes[0].legend(fontsize=8,loc='upper right');fig.tight_layout();fig.savefig(p/'calibration.png',dpi=160);plt.close(fig)
