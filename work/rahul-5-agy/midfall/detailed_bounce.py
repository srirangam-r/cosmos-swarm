#!/usr/bin/env python3
import json
import numpy as np

for clip_name, res_file in [("Ball 1 (0007_raj-3)", "/home/sha/swarm-work/rahul-5-agy/res_b1.json"),
                            ("Ball 2 (0012_raj-3)", "/home/sha/swarm-work/rahul-5-agy/res_b2.json")]:
    with open(res_file) as f:
        data = json.load(f)
    
    track_y = np.array([np.nan if y is None else y for y in data["track_y"]])
    fps = 24.0
    mpp = 0.001852538
    
    # Let's find local minima (apexes, since y is down) and local maxima (impacts)
    # Floor level is around y ~ 310 - 340
    # Let's find segments where ball descends and ascends
    peaks = data["peaks"]
    
    print(f"\n=======================================================")
    print(f"Detailed Bounce Analysis: {clip_name}")
    print(f"Total frames: {len(track_y)}, tracked: {data['n_tracked']}")
    print(f"Impact candidate frames (max y): {peaks[:12]}")
    
    # Compute impacts and apexes
    # We can iterate through peaks and find apex between peak[i] and peak[i+1]
    bounces = []
    for i in range(len(peaks) - 1):
        p1 = peaks[i]
        p2 = peaks[i+1]
        if p2 - p1 < 4 or p2 - p1 > 20:
            continue
        sub = track_y[p1:p2+1]
        if np.isnan(sub).any():
            continue
        apex_offset = np.argmin(sub)
        apex_fr = p1 + apex_offset
        y_imp1 = track_y[p1]
        y_apex = track_y[apex_fr]
        y_imp2 = track_y[p2]
        rise = y_imp1 - y_apex
        flight_frames = p2 - p1
        flight_time = flight_frames / fps
        bounces.append({
            "bounce_num": len(bounces) + 1,
            "imp1_fr": int(p1),
            "apex_fr": int(apex_fr),
            "imp2_fr": int(p2),
            "rise_px": float(rise),
            "rise_cm": float(rise * mpp * 100),
            "flight_frames": int(flight_frames),
            "flight_time_s": float(flight_time),
            "g_eff": float(8 * (rise * mpp) / (flight_time**2)) if flight_time > 0 else None
        })
    
    print(f"Found {len(bounces)} clear bounce cycles:")
    print(f"{'#':<3} {'Imp1':<6} {'Apex':<6} {'Imp2':<6} {'Rise(cm)':<10} {'T(s)':<8} {'g_eff(m/s^2)':<12}")
    for b in bounces[:10]:
        print(f"{b['bounce_num']:<3} {b['imp1_fr']:<6} {b['apex_fr']:<6} {b['imp2_fr']:<6} {b['rise_cm']:<10.1f} {b['flight_time_s']:<8.3f} {b['g_eff']:<12.2f}")
    
    # Compute successive height ratios: sqrt(h_{k+1}/h_k) and flight time ratios: T_{k+1}/T_k
    e_h_list = []
    e_T_list = []
    for i in range(len(bounces) - 1):
        h1 = bounces[i]["rise_cm"]
        h2 = bounces[i+1]["rise_cm"]
        T1 = bounces[i]["flight_time_s"]
        T2 = bounces[i+1]["flight_time_s"]
        if h1 > 0 and h2 > 0:
            e_h_list.append(np.sqrt(h2 / h1))
        if T1 > 0 and T2 > 0:
            e_T_list.append(T2 / T1)
    
    if e_h_list:
        print(f"Mean e_h = sqrt(h_{{k+1}}/h_k): {np.mean(e_h_list):.3f} +/- {np.std(e_h_list)/np.sqrt(len(e_h_list)):.3f} (n={len(e_h_list)})")
    if e_T_list:
        print(f"Mean e_T = T_{{k+1}}/T_k:       {np.mean(e_T_list):.3f} +/- {np.std(e_T_list)/np.sqrt(len(e_T_list)):.3f} (n={len(e_T_list)})")
    
    # Total duration of bouncing
    if bounces:
        t_start = bounces[0]["imp1_fr"] / fps
        t_end = bounces[-1]["imp2_fr"] / fps
        print(f"Bouncing duration: {t_end - t_start:.2f} seconds (from frame {bounces[0]['imp1_fr']} to {bounces[-1]['imp2_fr']})")
        print(f"Still bouncing at clip end (frame 189)? {data['still_bouncing_at_end']}")
