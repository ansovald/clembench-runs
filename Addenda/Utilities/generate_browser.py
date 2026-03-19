#!/usr/bin/env python3
"""
Generate transcript_browser.html — a self-contained transcript browser for clembench-runs.
Run from the repo root:  python generate_browser.py
"""

import json
import os
from pathlib import Path

VERSION = "v3.0"
BASE = Path(__file__).parent / VERSION
OUT = Path(__file__).parent / "transcript_browser.html"


def build_index():
    """Return {game: {model: {experiment: [instance, ...]}}}"""
    index = {}
    for model_dir in sorted(BASE.iterdir()):
        if not model_dir.is_dir():
            continue
        model = model_dir.name
        for game_dir in sorted(model_dir.iterdir()):
            if not game_dir.is_dir():
                continue
            game = game_dir.name
            for exp_dir in sorted(game_dir.iterdir()):
                if not exp_dir.is_dir():
                    continue
                experiment = exp_dir.name
                instances = sorted(
                    d.name for d in exp_dir.iterdir()
                    if d.is_dir() and (d / "transcript.html").exists()
                )
                if not instances:
                    continue
                index.setdefault(game, {}).setdefault(model, {})[experiment] = instances
    return index


def main():
    print("Scanning v3.0/ …")
    index = build_index()
    games = sorted(index.keys())
    print(f"  {len(games)} games, "
          f"{sum(len(v) for v in index.values())} model×game combinations")

    index_json = json.dumps(index, indent=None)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>CLembench Transcript Browser — v3.0</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

  body {{
    font-family: system-ui, sans-serif;
    background: #1e1e2e;
    color: #cdd6f4;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }}

  header {{
    background: #181825;
    border-bottom: 1px solid #313244;
    padding: .75rem 1.25rem;
    display: flex;
    align-items: center;
    gap: 1.5rem;
    flex-wrap: wrap;
  }}

  header h1 {{
    font-size: 1rem;
    font-weight: 600;
    color: #cba6f7;
    white-space: nowrap;
  }}

  .controls {{
    display: flex;
    gap: .75rem;
    flex-wrap: wrap;
    align-items: center;
  }}

  .ctrl-group {{
    display: flex;
    flex-direction: column;
    gap: .2rem;
  }}

  .ctrl-group label {{
    font-size: .7rem;
    color: #6c7086;
    text-transform: uppercase;
    letter-spacing: .05em;
  }}

  select {{
    background: #313244;
    color: #cdd6f4;
    border: 1px solid #45475a;
    border-radius: .4rem;
    padding: .35rem .6rem;
    font-size: .85rem;
    cursor: pointer;
    min-width: 200px;
  }}
  select:focus {{ outline: 2px solid #cba6f7; }}
  select:disabled {{ opacity: .4; cursor: default; }}

  #status {{
    font-size: .8rem;
    color: #6c7086;
    margin-left: auto;
    white-space: nowrap;
  }}

  #viewer {{
    flex: 1;
    border: none;
    background: #fff;
  }}

  #placeholder {{
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #45475a;
    font-size: 1.1rem;
  }}
</style>
</head>
<body>

<header>
  <h1>CLembench v3.0</h1>
  <div class="controls">
    <div class="ctrl-group">
      <label for="sel-game">Game</label>
      <select id="sel-game"><option value="">— select game —</option></select>
    </div>
    <div class="ctrl-group">
      <label for="sel-model">Model</label>
      <select id="sel-model" disabled><option value="">— select model —</option></select>
    </div>
    <div class="ctrl-group">
      <label for="sel-exp">Experiment</label>
      <select id="sel-exp" disabled><option value="">— select experiment —</option></select>
    </div>
    <div class="ctrl-group">
      <label for="sel-inst">Episode</label>
      <select id="sel-inst" disabled><option value="">— select episode —</option></select>
    </div>
  </div>
  <span id="status"></span>
</header>

<div id="placeholder">Select a game, model, experiment, and episode above.</div>
<iframe id="viewer" style="display:none"></iframe>

<script>
const INDEX = {index_json};

const selGame  = document.getElementById('sel-game');
const selModel = document.getElementById('sel-model');
const selExp   = document.getElementById('sel-exp');
const selInst  = document.getElementById('sel-inst');
const viewer   = document.getElementById('viewer');
const placeholder = document.getElementById('placeholder');
const status   = document.getElementById('status');

function populate(sel, values, placeholder) {{
  sel.innerHTML = `<option value="">${{placeholder}}</option>`;
  values.forEach(v => {{
    const o = document.createElement('option');
    o.value = o.textContent = v;
    sel.appendChild(o);
  }});
}}

function reset(...sels) {{
  sels.forEach(s => {{
    s.innerHTML = `<option value="">—</option>`;
    s.disabled = true;
  }});
}}

const REPO_RAW = 'https://raw.githubusercontent.com/clembench/clembench-runs/main';

function showTranscript() {{
  const game  = selGame.value;
  const model = selModel.value;
  const exp   = selExp.value;
  const inst  = selInst.value;
  if (!game || !model || !exp || !inst) return;
  const path = `v3.0/${{model}}/${{game}}/${{exp}}/${{inst}}/transcript.html`;
  const url  = `${{REPO_RAW}}/${{path}}`;
  status.textContent = path;
  placeholder.style.display = 'none';
  viewer.style.display = 'block';
  viewer.srcdoc = '<p style="font-family:sans-serif;padding:2rem;color:#888">Loading…</p>';
  fetch(url)
    .then(r => {{ if (!r.ok) throw new Error(r.status); return r.text(); }})
    .then(html => {{ viewer.srcdoc = html; }})
    .catch(err => {{
      viewer.srcdoc = `<p style="font-family:sans-serif;padding:2rem;color:red">Failed to load transcript: ${{err}}</p>`;
    }});
}}

// Populate games on load
populate(selGame, Object.keys(INDEX).sort(), '— select game —');

selGame.addEventListener('change', () => {{
  const game = selGame.value;
  reset(selModel, selExp, selInst);
  viewer.style.display = 'none';
  placeholder.style.display = 'flex';
  status.textContent = '';
  if (!game) return;
  const models = Object.keys(INDEX[game] || {{}}).sort();
  populate(selModel, models, '— select model —');
  selModel.disabled = false;
}});

selModel.addEventListener('change', () => {{
  const game     = selGame.value;
  const model    = selModel.value;
  const prevExp  = selExp.value;
  const prevInst = selInst.value;
  reset(selExp, selInst);
  status.textContent = '';
  if (!model) {{
    viewer.style.display = 'none';
    placeholder.style.display = 'flex';
    return;
  }}
  const exps = Object.keys((INDEX[game] || {{}})[model] || {{}}).sort();
  populate(selExp, exps, '— select experiment —');
  selExp.disabled = false;
  // Restore previous experiment if available under the new model
  if (prevExp && exps.includes(prevExp)) {{
    selExp.value = prevExp;
    const insts = ((INDEX[game] || {{}})[model] || {{}})[prevExp] || [];
    populate(selInst, insts, '— select episode —');
    selInst.disabled = false;
    // Restore previous instance if available
    if (prevInst && insts.includes(prevInst)) {{
      selInst.value = prevInst;
      showTranscript();
    }} else {{
      viewer.style.display = 'none';
      placeholder.style.display = 'flex';
    }}
  }} else {{
    viewer.style.display = 'none';
    placeholder.style.display = 'flex';
  }}
}});

selExp.addEventListener('change', () => {{
  const game     = selGame.value;
  const model    = selModel.value;
  const exp      = selExp.value;
  const prevInst = selInst.value;
  reset(selInst);
  status.textContent = '';
  if (!exp) {{
    viewer.style.display = 'none';
    placeholder.style.display = 'flex';
    return;
  }}
  const insts = ((INDEX[game] || {{}})[model] || {{}})[exp] || [];
  populate(selInst, insts, '— select episode —');
  selInst.disabled = false;
  // Restore previous instance if available under the new experiment
  if (prevInst && insts.includes(prevInst)) {{
    selInst.value = prevInst;
    showTranscript();
  }} else {{
    viewer.style.display = 'none';
    placeholder.style.display = 'flex';
  }}
}});

selInst.addEventListener('change', showTranscript);
</script>
</body>
</html>
"""

    OUT.write_text(html, encoding="utf-8")
    print(f"Written: {OUT}")


if __name__ == "__main__":
    main()
