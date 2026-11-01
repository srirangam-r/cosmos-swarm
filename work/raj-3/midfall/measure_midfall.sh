#!/bin/bash
# raj-3 task 15: measure the mid-fall I2V clips with the seeded tracker (gripper scene -> no trk.blobs).
# Seeds = ball centre in the input frame (frame 0), located from the dd32->dd33 / dd34->dd35 frame difference + visual check.
cd /home/nail/swarm-work/raj-3/midfall
T=../cosmos-swarm/tools/trk_ballfall
mkdir -p res
for f in out/midfall_ball1_*.mp4; do [ -e "$f" ] || continue; n=$(basename $f .mp4)
  python3 -I $T/seeded.py $f --fps 24 --ppm 539.8 --point 287,155 --qc res/${n}_seeded_qc.png > res/${n}_seeded.json; done
for f in out/midfall_ball2_*.mp4; do [ -e "$f" ] || continue; n=$(basename $f .mp4)
  python3 -I $T/seeded.py $f --fps 24 --ppm 539.8 --point 290,172 --qc res/${n}_seeded_qc.png > res/${n}_seeded.json; done
grep -H '"g"\|g_fall"\|g_bounce"\|"flag"\|bounce_flag' res/*_seeded.json
