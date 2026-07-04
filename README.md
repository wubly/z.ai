# zai

selenium-driven api wrapper for chat.z.ai

## install

```
pip install -r requirements.txt
```

## run

```
python main.py
```

## endpoints

`POST /chat`

```
{"msg": "hello", "think": null}
```

```
{"txt": "...", "think": "...", "secs": 4.2, "id": "message-1"}
```

`POST /new` — starts a fresh chat

## library

```python
from zai import ZaiClient

with ZaiClient() as zai:
    res = zai.send("hello")
    print(res.text, res.thinking_seconds)
```
