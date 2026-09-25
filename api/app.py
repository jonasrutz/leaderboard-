import json
import os
import socket

import redis
from flask import Flask, jsonify, render_template_string, request

app = Flask(__name__)
r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
HOST = socket.gethostname()  # im Swarm = Container-ID -> zeigt, welche API-Replica antwortet

PAGE = """
<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta http-equiv="refresh" content="5">
  <title>Campus Gaming Leaderboard</title>
  <style>
    body { font-family: system-ui, sans-serif; max-width: 600px; margin: 40px auto; }
    table { width: 100%; border-collapse: collapse; }
    th, td { padding: 8px; border-bottom: 1px solid #ddd; text-align: left; }
    small { color: #777; }
  </style>
</head>
<body>
  <h1>🏆 Campus Gaming Leaderboard</h1>
  <table>
    <tr><th>Platz</th><th>Spieler</th><th>Punkte</th></tr>
    {% for e in rangliste %}
    <tr><td>{{ e.platz }}</td><td>{{ e.spieler }}</td><td>{{ e.punkte }}</td></tr>
    {% endfor %}
  </table>
  <p><small>Ausgeliefert von API-Container: {{ host }}</small></p>
</body>
</html>
"""


def top10():
    eintraege = r.zrevrange("leaderboard", 0, 9, withscores=True)
    return [
        {"platz": i + 1, "spieler": spieler, "punkte": int(punkte)}
        for i, (spieler, punkte) in enumerate(eintraege)
    ]


@app.post("/score")
def score():
    data = request.get_json(silent=True) or {}
    spieler = str(data.get("spieler", "")).strip()
    spiel = str(data.get("spiel", "")).strip()
    try:
        punkte = int(data.get("punkte"))
    except (TypeError, ValueError):
        return jsonify(error="punkte muss eine Zahl sein"), 400
    if not spieler or not spiel or punkte < 0:
        return jsonify(error="spieler, spiel und punkte (>= 0) sind Pflicht"), 400

    job = {"spieler": spieler, "spiel": spiel, "punkte": punkte}
    r.lpush("scores:queue", json.dumps(job))  # Worker holt den Job asynchron ab
    return jsonify(status="angenommen", verarbeitet_von_api=HOST, **job), 202


@app.get("/leaderboard")
def leaderboard():
    return jsonify(api=HOST, rangliste=top10())


@app.get("/")
def index():
    return render_template_string(PAGE, rangliste=top10(), host=HOST)


@app.get("/stats")
def stats():
    return jsonify(r.hgetall("worker:stats"))


@app.get("/health")
def health():
    try:
        r.ping()
        return jsonify(api=HOST, redis=True), 200
    except redis.exceptions.ConnectionError:
        return jsonify(api=HOST, redis=False), 503


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)