import json
import urllib.request

url = "http://localhost:8000/chat"


def ask(msg: str) -> dict:
    req = urllib.request.Request(
        url,
        data=json.dumps({"msg": msg}).encode(),
        headers={"content-type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


while True:
    msg = input("you: ").strip()
    if not msg:
        continue
    if msg in ("exit", "quit"):
        break

    res = ask(msg)
    if res["think"]:
        print(f"[thinking, {res['secs']:.1f}s] {res['think']}")
    print(f"zai: {res['txt']}")
