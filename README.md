# SET50 Shareholder Relationship Graph

A Streamlit app that visualizes shareholder relationships across SET50 companies using NetworkX and Matplotlib.

## Deploy on Streamlit Community Cloud

1. **Push to GitHub**

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/<your-username>/<repo-name>.git
git push -u origin main
```

2. **Deploy** — go to https://share.streamlit.io, sign in with GitHub, click **New app**, select your repo, branch, and set `set50_SNA.py` as the main file.

## Deploy on Hugging Face Spaces

1. Create a Space at https://huggingface.co/new-space with **Streamlit** SDK
2. Push via Git:

```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin https://huggingface.co/spaces/<your-username>/<space-name>
git push -u origin main
```

3. The Space auto-detects `requirements.txt` and builds automatically.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run set50_SNA.py
```
