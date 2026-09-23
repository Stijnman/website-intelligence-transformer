# Website Intelligence Transformer v6.2

**Autonomous AI Website Intelligence** — dark-mode Streamlit app for on-page SEO, structure, and content signals.

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-red)](https://streamlit.io)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

| Area | What it checks |
|------|----------------|
| Metadata | Title, meta description, canonical |
| Structure | H1/H2, viewport, Open Graph, JSON-LD |
| Content | Word count, keyword hints |
| Media | Image count & missing alt text |
| Links | Internal vs external mix |
| Score | 0–100 intelligence score + prioritized fixes |

## Quick start

```bash
git clone https://github.com/Stijnman/website-intelligence-transformer.git
cd website-intelligence-transformer
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

Open the local URL Streamlit prints (usually `http://localhost:8501`).

## Deploy

Works on any Streamlit host (Streamlit Community Cloud, Docker, VPS):

```bash
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

## Ethics

Only scan sites you own or are authorized to test. Respect `robots.txt` and rate limits.

## License

MIT © 2026 Stijnman

## Flagship integration

This project remains independently usable and is not deprecated. Its capabilities are also consumed by [CommerceForge](https://github.com/Stijnman/CommerceForge), where they are integrated with complementary repositories behind shared platform contracts. This repository remains the source of truth for its component-specific implementation.
