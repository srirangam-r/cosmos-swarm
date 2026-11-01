#!/bin/bash
# (F and QT share an identical f0, MAE 0.0, so static uses F s1 per input + the real clip f0.)
# Builds midq controls from <clipdir> into <ctldir>. trunc36 = first 36 frames; static = f0 x93 @24 fps.
set -e; C=$1; O=$2; mkdir -p $O
for f in $C/*_F_*.mp4 $C/*_QT_*.mp4 $C/real_*.mp4; do b=$(basename $f)
  ffmpeg -nostdin -loglevel error -y -i $f -frames:v 36 -c:v libx264 -crf 12 -pix_fmt yuv420p $O/trunc36_$b; done
for f in $C/ball_F_ball1_fps24_93f_s1.mp4 $C/ball_F_ball2_fps24_93f_s1.mp4 $C/real_ball1_dd32_93f.mp4; do b=$(basename $f)
  ffmpeg -nostdin -loglevel error -y -i $f -frames:v 1 /tmp/midq_f0.png
  ffmpeg -nostdin -loglevel error -y -loop 1 -framerate 24 -i /tmp/midq_f0.png -frames:v 93 -c:v libx264 -crf 12 -pix_fmt yuv420p $O/static_$b; done
