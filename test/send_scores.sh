#!/bin/bash
# Nutzung: ./send_scores.sh [URL] [ANZAHL]
URL=${1:-http://localhost:8080}
N=${2:-30}
SPIELER=(Jonas Aldin Qema Alex Mia Luca)
SPIELE=("Rocket League" "Mario Kart" "FIFA" "Tetris")

for i in $(seq 1 "$N"); do
  s=${SPIELER[$RANDOM % ${#SPIELER[@]}]}
  g=${SPIELE[$RANDOM % ${#SPIELE[@]}]}
  p=$(( (RANDOM % 900) + 100 ))
  curl -s -X POST "$URL/score" \
       -H "Content-Type: application/json" \
       -d "{\"spieler\":\"$s\",\"spiel\":\"$g\",\"punkte\":$p}"
  echo
done