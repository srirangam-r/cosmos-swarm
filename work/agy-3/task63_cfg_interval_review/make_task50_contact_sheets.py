import cv2
import numpy as np
from pathlib import Path

def load_frames(path):
    cap = cv2.VideoCapture(str(path))
    frames = []
    while True:
        ret, f = cap.read()
        if not ret:
            break
        frames.append(f)
    cap.release()
    return frames

def create_seed1_sheet(base_frames, window_frames, out_path):
    # Selected key frames: [0, 15, 25, 28, 35, 48, 50, 61, 75, 92]
    key_frames = [0, 15, 25, 28, 35, 48, 50, 61, 75, 92]
    n_cols = len(key_frames)
    
    # We will crop the central vertical region x in [220, 420], y in [100, 420]
    # Crop size: 320 height x 200 width
    cw, ch = 200, 320
    
    # Header: 60px
    # Row 1 (Base): ch px
    # Row 2 (Window): ch px
    # Row 3 (Plank zoom): 120 px
    total_w = n_cols * cw
    total_h = 1000
    sheet = np.full((total_h, total_w, 3), 245, dtype=np.uint8)
    
    # Title
    cv2.putText(sheet, "TASK 50 AUDIT: SEED 1 - BASELINE CFG (ALL STEPS) vs RESTRICTED CFG WINDOW [220, 840]",
                (20, 38), cv2.FONT_HERSHEY_DUPLEX, 0.7, (20, 20, 20), 2)
    
    y_base = 60
    cv2.putText(sheet, "BASE S1 (CFG 6 all steps): Ball stuck in gripper + Phantom Duplicate bounces on plank (f28, f48, f61)",
                (20, y_base + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 180), 2)
    y_base += 32
    
    for col, fr in enumerate(key_frames):
        img = base_frames[fr]
        crop = img[100:420, 220:420].copy()
        
        # Annotations on crop
        # Highlight gripper box [130:185, 275:325] -> relative in crop: y in [30:85], x in [55:105]
        cv2.rectangle(crop, (55, 30), (105, 85), (0, 255, 255), 1)
        # Highlight plank box [340:380, 260:340] -> relative in crop: y in [240:280], x in [40:120]
        cv2.rectangle(crop, (40, 240), (120, 280), (255, 100, 0), 1)
        
        if fr in [28, 48, 61]:
            cv2.putText(crop, "PHANTOM IMPACT", (15, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
            
        cv2.putText(crop, f"f{fr}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        sheet[y_base:y_base+ch, col*cw:(col+1)*cw] = crop
        
    y_win = y_base + ch + 15
    cv2.putText(sheet, "WINDOW S1 (CFG window [220, 840]): Phantom duplicate extinguished; ball remains in gripper",
                (20, y_win + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 120, 0), 2)
    y_win += 32
    
    for col, fr in enumerate(key_frames):
        img = window_frames[fr]
        crop = img[100:420, 220:420].copy()
        
        cv2.rectangle(crop, (55, 30), (105, 85), (0, 255, 255), 1)
        cv2.rectangle(crop, (40, 240), (120, 280), (255, 100, 0), 1)
        
        if fr in [48, 50]:
            cv2.putText(crop, "Holder necking", (15, 75), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
            
        cv2.putText(crop, f"f{fr}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        sheet[y_win:y_win+ch, col*cw:(col+1)*cw] = crop
        
    # Bottom zoom comparison of plank at f28, f48, f61
    y_zoom = y_win + ch + 20
    cv2.putText(sheet, "PLANK REGION ZOOM (y: 330..390): Base (top) shows phantom ball impact; Window (bottom) shows clean wood",
                (20, y_zoom + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    y_zoom += 26
    
    # Zoom row
    for col, fr in enumerate(key_frames):
        # Zoom plank [330:390, 240:340] -> 60x100 resized to 120x200
        b_p = base_frames[fr][330:390, 240:340]
        w_p = window_frames[fr][330:390, 240:340]
        
        # Split half and half: top half Base, bottom half Window
        b_res = cv2.resize(b_p, (cw, 58))
        w_res = cv2.resize(w_p, (cw, 58))
        cv2.putText(b_res, f"Base f{fr}", (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
        cv2.putText(w_res, f"Win f{fr}", (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        
        sheet[y_zoom:y_zoom+58, col*cw:(col+1)*cw] = b_res
        sheet[y_zoom+60:y_zoom+118, col*cw:(col+1)*cw] = w_res
        
    cv2.imwrite(str(out_path), sheet)
    print(f"Saved Seed 1 sheet to {out_path}")


def create_seed2_sheet(base_frames, window_frames, out_path):
    key_frames = [0, 6, 12, 18, 24, 30, 45, 60, 75, 92]
    n_cols = len(key_frames)
    cw, ch = 200, 320
    
    total_w = n_cols * cw
    total_h = 1000
    sheet = np.full((total_h, total_w, 3), 245, dtype=np.uint8)
    
    cv2.putText(sheet, "TASK 50 AUDIT: SEED 2 - BASELINE CFG (ALL STEPS) vs RESTRICTED CFG WINDOW [220, 840]",
                (20, 38), cv2.FONT_HERSHEY_DUPLEX, 0.7, (20, 20, 20), 2)
                
    y_base = 60
    cv2.putText(sheet, "BASE S2 (CFG 6 all steps): Mechanical arm descends; dark mass deposited on plank from f12 to f92",
                (20, y_base + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 180), 2)
    y_base += 32
    
    for col, fr in enumerate(key_frames):
        img = base_frames[fr]
        crop = img[100:420, 220:420].copy()
        cv2.rectangle(crop, (55, 30), (105, 85), (0, 255, 255), 1)
        cv2.rectangle(crop, (40, 240), (120, 280), (255, 100, 0), 1)
        
        if fr >= 12:
            cv2.putText(crop, "PLANK MASS", (25, 275), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
            
        cv2.putText(crop, f"f{fr}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        sheet[y_base:y_base+ch, col*cw:(col+1)*cw] = crop
        
    y_win = y_base + ch + 15
    cv2.putText(sheet, "WINDOW S2 (CFG window [220, 840]): Arm motion restricted to upper corridor; ZERO mass on plank (0/93 frames)",
                (20, y_win + 22), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 120, 0), 2)
    y_win += 32
    
    for col, fr in enumerate(key_frames):
        img = window_frames[fr]
        crop = img[100:420, 220:420].copy()
        cv2.rectangle(crop, (55, 30), (105, 85), (0, 255, 255), 1)
        cv2.rectangle(crop, (40, 240), (120, 280), (255, 100, 0), 1)
        
        cv2.putText(crop, f"f{fr}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        sheet[y_win:y_win+ch, col*cw:(col+1)*cw] = crop
        
    y_zoom = y_win + ch + 20
    cv2.putText(sheet, "PLANK REGION ZOOM (y: 330..390): Base (top) shows heavy plank mass; Window (bottom) remains clean wood",
                (20, y_zoom + 18), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (50, 50, 50), 1)
    y_zoom += 26
    
    for col, fr in enumerate(key_frames):
        b_p = base_frames[fr][330:390, 240:340]
        w_p = window_frames[fr][330:390, 240:340]
        
        b_res = cv2.resize(b_p, (cw, 58))
        w_res = cv2.resize(w_p, (cw, 58))
        cv2.putText(b_res, f"Base f{fr}", (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 1)
        cv2.putText(w_res, f"Win f{fr}", (5, 18), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 255, 0), 1)
        
        sheet[y_zoom:y_zoom+58, col*cw:(col+1)*cw] = b_res
        sheet[y_zoom+60:y_zoom+118, col*cw:(col+1)*cw] = w_res
        
    cv2.imwrite(str(out_path), sheet)
    print(f"Saved Seed 2 sheet to {out_path}")

def main():
    p = Path("/home/nail/swarm-work/agy-3/task50_review")
    print("Loading videos...")
    base_s1 = load_frames(p / "base_s1.mp4")
    win_s1 = load_frames(p / "window_s1.mp4")
    base_s2 = load_frames(p / "base_s2.mp4")
    win_s2 = load_frames(p / "window_s2.mp4")
    
    print("Generating contact sheets...")
    create_seed1_sheet(base_s1, win_s1, p / "sheet_task50_seed1_audit.jpg")
    create_seed2_sheet(base_s2, win_s2, p / "sheet_task50_seed2_audit.jpg")

if __name__ == "__main__":
    main()
