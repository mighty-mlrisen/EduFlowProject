#!/usr/bin/env python3
"""
Local model server — runs on macOS with MPS acceleration.
Start: python local_model_server.py
"""
import json
import os
import re
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer

import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "cointegrated/rut5-base-absum"
PORT = int(os.getenv("MODEL_PORT", "8001"))

CHUNK_SIZE = 400
OVERLAP_SENTENCES = 1
MAX_SUMMARY_TOKENS = 150
MIN_SUMMARY_TOKENS = 75


def _get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _load():
    device = _get_device()
    print(f"Loading model on {device}...", flush=True)
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME).to(device)
    model.eval()
    print(f"Model ready on {device}", flush=True)
    return tokenizer, model, device


def _split_sentences(text: str) -> list[str]:
    parts = re.split(r'(?<=[.!?])\s+(?=[А-ЯA-ZЁ])', text)
    return [s.strip() for s in parts if s.strip()]


def _split_into_chunks(text: str, tokenizer) -> list[str]:
    sentences = _split_sentences(text)

    def token_count(s: str) -> int:
        return len(tokenizer(s, truncation=False, add_special_tokens=False)["input_ids"])

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sent_tokens = token_count(sentence)

        if sent_tokens >= CHUNK_SIZE:
            if current:
                chunks.append(" ".join(current))
                current, current_tokens = [], 0
            chunks.append(sentence)
            continue

        if current_tokens + sent_tokens > CHUNK_SIZE and current:
            chunks.append(" ".join(current))
            overlap = current[-OVERLAP_SENTENCES:]
            current = overlap.copy()
            current_tokens = sum(token_count(s) for s in current)

        current.append(sentence)
        current_tokens += sent_tokens

    if current:
        chunks.append(" ".join(current))

    return chunks


def _postprocess(text: str) -> str:
    prev = None
    while prev != text:
        prev = text
        text = re.sub(r'\b(\w+)\s+\1\b', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\w+)\s+и\s+\1\b', r'\1', text, flags=re.IGNORECASE)
        text = re.sub(r'\b(\w+)(\s+\w+)\s+\1\b', r'\1\2', text, flags=re.IGNORECASE)
    return text


def _summarize_chunk(text: str, tokenizer, model, device) -> str:
    inputs = tokenizer(text, max_length=CHUNK_SIZE, truncation=True, return_tensors="pt").to(device)
    with torch.no_grad():
        out = model.generate(
            **inputs,
            max_new_tokens=MAX_SUMMARY_TOKENS,
            min_new_tokens=MIN_SUMMARY_TOKENS,
            num_beams=4,
            length_penalty=1.0,
            repetition_penalty=1.3,
            no_repeat_ngram_size=4,
            early_stopping=True,
        )
    return tokenizer.decode(out[0], skip_special_tokens=True)


def generate_summary(text: str, tokenizer, model, device) -> str:
    chunks = _split_into_chunks(text, tokenizer)
    print(f"Chunks: {len(chunks)}", flush=True)
    summaries = [_summarize_chunk(c, tokenizer, model, device) for c in chunks]
    return _postprocess(" ".join(summaries))


tokenizer, model, device = _load()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/generate":
            self._reply(404, {"error": "Not found"})
            return

        length = int(self.headers.get("Content-Length", 0))
        try:
            body = json.loads(self.rfile.read(length))
        except json.JSONDecodeError:
            self._reply(400, {"error": "Invalid JSON"})
            return

        text = body.get("text", "").strip()
        if not text:
            self._reply(400, {"error": "Field 'text' is required"})
            return

        print(f"Summarizing ({len(text)} chars)...", flush=True)
        summary = generate_summary(text, tokenizer, model, device)
        self._reply(200, {"summary": summary})

    def _reply(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        print(f"[model-server] {fmt % args}", flush=True)


if __name__ == "__main__":
    print(f"Model server listening on 0.0.0.0:{PORT}", flush=True)
    try:
        HTTPServer(("0.0.0.0", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("Stopped.", flush=True)
        sys.exit(0)
