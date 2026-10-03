"""Asks a model for a test suite, one story at a time, and records everything.

A run directory holds the manifest (backend, model, prompt version and its
hash), the raw responses, and one suite per sample: sample-1/test_s1.py ...
Evaluating never calls a model; it only reads these files."""

from __future__ import annotations

import hashlib
import json
import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

from . import stories
from .backends import BACKENDS

FENCE = re.compile(r"```(?:python|py)?\s*\n(.*?)```", re.S)


def template(name: str) -> str:
    return resources.files("aievals").joinpath("prompts", name).read_text()


def build_prompt(version: str, story: stories.Story) -> str:
    others = "\n\n".join(s.text.strip() for s in stories.load() if s.id != story.id)
    return template(f"{version}.txt").format(
        api=stories.api().strip(),
        story=story.text.strip(),
        context=others,
        rules=template("rules.txt").strip(),
    )


def extract_code(text: str) -> str:
    blocks = FENCE.findall(text)
    if blocks:
        return max(blocks, key=len).strip() + "\n"
    return text.strip() + "\n"


def prompt_hash(version: str) -> str:
    h = hashlib.sha256()
    h.update(template("system.txt").encode())
    for s in stories.load():
        h.update(build_prompt(version, s).encode())
    return h.hexdigest()[:12]


def generate(out: Path, backend: str, model: str, prompt: str, samples: int = 1, only: list[str] | None = None, parallel: int = 4) -> None:
    client = BACKENDS[backend](model)
    system = template("system.txt").strip()
    out.mkdir(parents=True, exist_ok=True)
    (out / "raw").mkdir(exist_ok=True)
    manifest_path = out / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else {
        "backend": backend,
        "model": model,
        "prompt": prompt,
        "prompt_sha": prompt_hash(prompt),
        "created": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "samples": samples,
        "responses": {},
    }
    jobs = []
    for k in range(1, samples + 1):
        (out / f"sample-{k}").mkdir(exist_ok=True)
        for story in stories.load():
            key = f"sample-{k}/{story.test_file}"
            if (only and story.id not in only) or key in manifest["responses"]:
                continue  # recorded already: an interrupted run picks up where it stopped
            jobs.append((k, story, key))

    lock = threading.Lock()

    def one(job):
        k, story, key = job
        done = client.complete(system, build_prompt(prompt, story))
        (out / "raw" / f"sample-{k}-{story.id.lower()}.md").write_text(done.text)
        (out / f"sample-{k}" / story.test_file).write_text(extract_code(done.text))
        with lock:
            manifest["responses"][key] = {
                "served_model": done.model,
                "seconds": done.seconds,
                "input_tokens": done.input_tokens,
                "output_tokens": done.output_tokens,
            }
            manifest["responses"] = dict(sorted(manifest["responses"].items()))
            manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
            print(f"{key}: {done.seconds}s, {done.output_tokens} output tokens", flush=True)

    with ThreadPoolExecutor(parallel) as pool:
        for future in [pool.submit(one, job) for job in jobs]:
            future.result()
