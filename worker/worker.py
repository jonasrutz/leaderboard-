import json
import os
import socket
import time

import redis

r = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)
HOST = socket.gethostname()

print(f"[{HOST}] Worker gestartet, warte auf Jobs in scores:queue", flush=True)

while True:
    try:
        # BRPOP ist atomar: auch bei 6 Worker-Replicas bekommt jeder Job genau EIN Worker
        item = r.brpop("scores:queue", timeout=5)
        if item is None:
            continue
        job = json.loads(item[1])

        total = r.zincrby("leaderboard", job["punkte"], job["spieler"])
        r.hincrby("worker:stats", HOST, 1)
        r.lpush("scores:history", json.dumps({**job, "worker": HOST}))

        print(
            f"[{HOST}] {job['spieler']} +{job['punkte']} ({job['spiel']}) -> Total {int(total)}",
            flush=True,
        )
    except redis.exceptions.ConnectionError:
        print(f"[{HOST}] Redis nicht erreichbar, neuer Versuch in 3 s", flush=True)
        time.sleep(3)