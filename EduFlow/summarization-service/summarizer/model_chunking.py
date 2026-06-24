import os
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

MODEL_NAME = "cointegrated/rut5-base-absum"

CHUNK_SIZE = 450
CHUNK_OVERLAP = 50
MAX_SUMMARY_TOKENS = 300
MIN_SUMMARY_TOKENS = 120

_tokenizer = None
_model = None
_device = None


def _get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def _load_model():
    global _tokenizer, _model, _device
    if _model is not None:
        return
    _device = _get_device()
    # Use all available CPU cores when running on CPU
    if _device.type == "cpu":
        torch.set_num_threads(os.cpu_count() or 4)
    _tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    _model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    _model = _model.to(_device)
    _model.eval()


def _split_into_chunks(text: str) -> list[str]:
    token_ids = _tokenizer(text, truncation=False)["input_ids"]
    total = len(token_ids)

    chunks = []
    start = 0
    while start < total:
        end = min(start + CHUNK_SIZE, total)
        chunk_ids = token_ids[start:end]
        chunk_text = _tokenizer.decode(chunk_ids, skip_special_tokens=True)
        chunks.append(chunk_text)
        if end == total:
            break
        start += CHUNK_SIZE - CHUNK_OVERLAP

    return chunks


def _summarize_chunk(text: str) -> str:
    inputs = _tokenizer(
        text,
        max_length=CHUNK_SIZE,
        truncation=True,
        return_tensors="pt",
    ).to(_device)

    with torch.no_grad():
        output_ids = _model.generate(
            **inputs,
            max_new_tokens=MAX_SUMMARY_TOKENS,
            min_new_tokens=MIN_SUMMARY_TOKENS,
            num_beams=2,
            length_penalty=0.9,
            no_repeat_ngram_size=3,
            early_stopping=True,
        )

    return _tokenizer.decode(output_ids[0], skip_special_tokens=True)


def get_summary(text: str) -> str:
    _load_model()
    chunks = _split_into_chunks(text)
    chunk_summaries = [_summarize_chunk(chunk) for chunk in chunks]
    return " ".join(chunk_summaries)
