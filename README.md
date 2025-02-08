# twitch-tts

Requirements:

Python 3.12

Installation:

1.

```bash
python -m venv .venv
```

2.

In Linux do:

```bash
source .venv/bin/activate
```

In Windows do:

```bash
source .venv/Scripts/activate
```

3.

Install dependencies

```bash
pip install -r requirements.txt
```

Optional for Windows if you have an NVidia graphics card and you want better
performance:

```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu124
```
