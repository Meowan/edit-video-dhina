#!/bin/bash
# make_triptych.sh OUT DUR clipA msA clipB msB clipC msC  -> 1080x1920 three stacked stage crops
OUT=$1; DUR=$2; shift 2
C=video/assets/clips
ffmpeg -v error -y -ss $2 -t $DUR -i $C/$1.mp4 -ss $4 -t $DUR -i $C/$3.mp4 -ss $6 -t $DUR -i $C/$5.mp4 -filter_complex \
"[0:v]crop=1080:620:0:730,setsar=1[a];[1:v]crop=1080:620:0:730,setsar=1[b];[2:v]crop=1080:620:0:730,setsar=1[c];\
color=c=0xffcc1f:s=1080x15:d=$DUR[s1];color=c=0xffcc1f:s=1080x15:d=$DUR[s2];\
[a][s1][b][s2][c]vstack=inputs=5,pad=1080:1920:0:15:color=0xffcc1f,fps=30,format=yuv420p[v]" -map "[v]" -t $DUR -c:v libx264 -preset veryfast -crf 20 -g 15 $OUT
