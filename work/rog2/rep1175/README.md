Independent replication of #1175 (rog-cc, task 31 negmeta 2x2). rog2, own code.
rep.py: cv2 decode, RGB 416x240 INTER_AREA, mean |frame diff| and pairwise MAE (rep.json). qc_inv.jpg / qc_same.jpg: 8 frames (0,8,16,24,36,50,70,92) per clip, all 16 clips.
Run: python3 -I rep.py CLIPDIR out.json
