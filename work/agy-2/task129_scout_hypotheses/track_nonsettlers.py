import cv2
import numpy as np
import os
import json
import matplotlib.pyplot as plt

out_dir = "/home/nail/swarm-work/agy-2/cosmos-swarm/work/agy-2/task129_scout_hypotheses"
clips_dir = "/home/nail/swarm-work/agy-2/cosmos-swarm/work/rog1/rep2460/clips"

clips = {
    "s22": os.path.join(clips_dir, "r60_8bf9f5.mp4"),
    "s23": os.path.join(clips_dir, "r60_0c3579.mp4"),
}

# The wooden plank is located roughly at:
# x in [220, 360], top surface y in [315, 345]
# Let's track the ball center (x, y) per frame using template NCC + local blob centroid

def track_ball(video_path):
    cap = cv2.VideoCapture(video_path)
    frames = []
    while True:
        ret, frame = cap.read()
        if not ret: break
        frames.append(frame)
    cap.release()
    
    n_frames = len(frames)
    trajectory = []
    
    # In frame 0, ball2 is at gripper / upper corridor:
    # Let's find initial ball center around (281, 119)
    # Ball is black disc of radius ~15-20 px
    for f in range(n_frames):
        frame = frames[f]
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Search corridor: x in [180, 400], y in [80, 420]
        # In frame f, find connected dark blobs
        roi = gray[80:420, 180:400]
        mask = (roi < 55).astype(np.uint8)
        num, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
        
        best_blob = None
        best_score = -1e9
        
        # If we have previous position, prioritize proximity
        prev_pos = trajectory[-1] if len(trajectory) > 0 else (280.0, 120.0)
        
        for i in range(1, num):
            area = stats[i, cv2.CC_STAT_AREA]
            w = stats[i, cv2.CC_STAT_WIDTH]
            h = stats[i, cv2.CC_STAT_HEIGHT]
            aspect = float(w) / max(1, h)
            # Ball area is typically 200 - 1500 px, aspect 0.5 - 2.0
            if 50 < area < 3000 and 0.4 < aspect < 2.5:
                bx = centroids[i][0] + 180
                by = centroids[i][1] + 80
                dist = np.hypot(bx - prev_pos[0], by - prev_pos[1])
                score = area - dist * 15.0
                if score > best_score:
                    best_score = score
                    best_blob = (bx, by, area, w, h)
                    
        if best_blob is not None:
            trajectory.append((best_blob[0], best_blob[1], best_blob[2], False))
        else:
            # Fallback to prev pos
            trajectory.append((prev_pos[0], prev_pos[1], 0, True))
            
    return trajectory

traj_s22 = track_ball(clips["s22"])
traj_s23 = track_ball(clips["s23"])

print("Tracked s22 and s23.")

# Let's extract turning points (apexes and impacts)
def analyze_kinematics(traj, name):
    y = np.array([p[1] for p in traj])
    x = np.array([p[0] for p in traj])
    frames = np.arange(len(y))
    
    # Plank surface is typically around y=325-345.
    # Impacts are local maxima of y (lowest points on screen)
    # Apexes are local minima of y (highest points on screen)
    
    # Smooth slightly with 3-tap window for robust turning points
    y_smooth = np.convolve(y, [0.25, 0.5, 0.25], mode='same')
    
    apexes = []
    impacts = []
    for i in range(1, len(y) - 1):
        if y_smooth[i] < y_smooth[i-1] and y_smooth[i] <= y_smooth[i+1]:
            # Peak height (apex)
            apexes.append((i, float(y[i]), float(x[i])))
        elif y_smooth[i] > y_smooth[i-1] and y_smooth[i] >= y_smooth[i+1]:
            # Lowest point (impact)
            impacts.append((i, float(y[i]), float(x[i])))
            
    print(f"\n=== {name} ===")
    print(f"Total apexes detected: {len(apexes)}")
    for a in apexes:
        # Bounce height above plank (plank y ~ 335)
        h_px = 335.0 - a[1]
        print(f"  Apex at f{a[0]:02d}: y={a[1]:.1f} px, x={a[2]:.1f} px, h={h_px:.1f} px")
        
    print(f"Total impacts detected: {len(impacts)}")
    for imp in impacts[:8]:
        print(f"  Impact at f{imp[0]:02d}: y={imp[1]:.1f} px, x={imp[2]:.1f} px")
        
    return {"y": y.tolist(), "x": x.tolist(), "apexes": apexes, "impacts": impacts}

res_s22 = analyze_kinematics(traj_s22, "s22 (r60_8bf9f5)")
res_s23 = analyze_kinematics(traj_s23, "s23 (r60_0c3579)")

with open(f"{out_dir}/nonsettlers_kinematics.json", "w") as f:
    json.dump({"s22": res_s22, "s23": res_s23}, f, indent=2)
print("\nSaved nonsettlers_kinematics.json")
