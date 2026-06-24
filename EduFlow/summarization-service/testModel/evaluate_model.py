#!/usr/bin/env python3


import os
import re
import torch
import numpy as np
from collections import Counter
from datasets import load_dataset
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from rouge_score import rouge_scorer
from bert_score import score as bert_score
import sacrebleu

os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# ── Пути ──────────────────────────────────────────────────────────────────────
BASE_MODEL_PATH     = "cointegrated/rut5-base-absum"
FINETUNED_MODEL_PATH = "/Users/artemmazurenko/EduFlow/summarization-service/models/finetuned-rut5"
TEST_DATASET_PATH   = "/Users/artemmazurenko/EduFlow/summarization-service/dataset/test.jsonl"

# ── Параметры генерации (те же что в local_model_server.py) ───────────────────
MAX_SOURCE_LENGTH   = 512
MAX_TARGET_LENGTH   = 200
GEN_PARAMS = dict(
    max_new_tokens=150,
    min_new_tokens=75,
    num_beams=4,
    length_penalty=1.0,
    repetition_penalty=1.3,
    no_repeat_ngram_size=4,
    early_stopping=True,
)


def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_model(path: str, device: torch.device):
    print(f"  Загрузка: {path}")
    tokenizer = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSeq2SeqLM.from_pretrained(path).to(device)
    model.eval()
    return tokenizer, model


def generate_summaries(texts: list[str], tokenizer, model, device: torch.device) -> list[str]:
    summaries = []
    for i, text in enumerate(texts):
        inputs = tokenizer(
            text,
            max_length=MAX_SOURCE_LENGTH,
            truncation=True,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            out = model.generate(**inputs, **GEN_PARAMS)
        summaries.append(tokenizer.decode(out[0], skip_special_tokens=True))
        if (i + 1) % 10 == 0:
            print(f"    {i + 1}/{len(texts)} готово")
    return summaries


# ── Метрики ───────────────────────────────────────────────────────────────────

def compute_rouge(predictions: list[str], references: list[str]) -> dict:
    scorer = rouge_scorer.RougeScorer(
        ["rouge1", "rouge2", "rougeL", "rougeLsum"], use_stemmer=False
    )
    agg = {"rouge1": [], "rouge2": [], "rougeL": [], "rougeLsum": []}
    for pred, ref in zip(predictions, references):
        scores = scorer.score(ref, pred)
        for k in agg:
            agg[k].append(scores[k].fmeasure)
    return {k: round(float(np.mean(v)), 4) for k, v in agg.items()}


def compute_bertscore(predictions: list[str], references: list[str]) -> dict:
    # lang="ru" использует multilingual BERT (bert-base-multilingual-cased)
    P, R, F1 = bert_score(predictions, references, lang="ru", verbose=False)
    return {
        "bertscore_precision": round(float(P.mean()), 4),
        "bertscore_recall":    round(float(R.mean()), 4),
        "bertscore_f1":        round(float(F1.mean()), 4),
    }


def compute_bleu(predictions: list[str], references: list[str]) -> dict:
    result = sacrebleu.corpus_bleu(predictions, [references])
    return {"sacrebleu": round(result.score, 4)}


def compute_length_stats(predictions: list[str], references: list[str]) -> dict:
    pred_lens = [len(p.split()) for p in predictions]
    ref_lens  = [len(r.split()) for r in references]
    ratios    = [p / r if r > 0 else 0 for p, r in zip(pred_lens, ref_lens)]
    return {
        "avg_pred_words": round(float(np.mean(pred_lens)), 1),
        "avg_ref_words":  round(float(np.mean(ref_lens)), 1),
        "length_ratio":   round(float(np.mean(ratios)), 3),  # 1.0 = идеально
    }


def compute_repetition_rate(predictions: list[str], n: int = 3) -> dict:
    """Доля повторяющихся n-грамм в предсказаниях (ниже — лучше)."""
    rates = []
    for pred in predictions:
        tokens = pred.lower().split()
        if len(tokens) < n:
            rates.append(0.0)
            continue
        ngrams = [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]
        total  = len(ngrams)
        unique = len(set(ngrams))
        rates.append(1 - unique / total)
    return {f"repetition_rate_{n}gram": round(float(np.mean(rates)), 4)}


def evaluate_model(name: str, predictions: list[str], references: list[str]) -> dict:
    print(f"\nВычисление метрик: {name}...")
    metrics = {}
    metrics.update(compute_rouge(predictions, references))
    metrics.update(compute_bleu(predictions, references))
    metrics.update(compute_bertscore(predictions, references))
    metrics.update(compute_length_stats(predictions, references))
    metrics.update(compute_repetition_rate(predictions, n=3))
    return metrics


def print_comparison(base_metrics: dict, ft_metrics: dict):
    print("\n" + "=" * 70)
    print(f"{'Метрика':<28} {'Базовая':>12} {'Дообученная':>12} {'Δ':>10}")
    print("-" * 70)

    metric_labels = {
        "rouge1":               "ROUGE-1 (F1)",
        "rouge2":               "ROUGE-2 (F1)",
        "rougeL":               "ROUGE-L (F1)",
        "rougeLsum":            "ROUGE-Lsum (F1)",
        "sacrebleu":            "SacreBLEU",
        "bertscore_f1":         "BERTScore F1",
        "bertscore_precision":  "BERTScore Precision",
        "bertscore_recall":     "BERTScore Recall",
        "avg_pred_words":       "Средняя длина (слов)",
        "avg_ref_words":        "Эталон длина (слов)",
        "length_ratio":         "Ratio длины (1.0=идеал)",
        "repetition_rate_3gram": "Repetition rate (3-gram)",
    }

    for key, label in metric_labels.items():
        b = base_metrics.get(key, "-")
        f = ft_metrics.get(key, "-")
        if isinstance(b, float) and isinstance(f, float):
            delta = f - b
            sign  = "+" if delta >= 0 else ""
            print(f"{label:<28} {b:>12.4f} {f:>12.4f} {sign}{delta:>9.4f}")
        else:
            print(f"{label:<28} {str(b):>12} {str(f):>12}")

    print("=" * 70)


def main():
    device = get_device()
    print(f"Устройство: {device}")

    print("\nЗагрузка тестового датасета...")
    dataset = load_dataset("json", data_files={"test": TEST_DATASET_PATH})["test"]
    texts     = dataset["text"]
    references = dataset["summary"]
    print(f"Примеров: {len(texts)}")

    print("\n[1/2] Базовая модель:")
    base_tok, base_model = load_model(BASE_MODEL_PATH, device)
    base_preds = generate_summaries(texts, base_tok, base_model, device)
    del base_model
    if device.type == "mps":
        import torch
        torch.mps.empty_cache()

    print("\n[2/2] Дообученная модель:")
    ft_tok, ft_model = load_model(FINETUNED_MODEL_PATH, device)
    ft_preds = generate_summaries(texts, ft_tok, ft_model, device)
    del ft_model

    base_metrics = evaluate_model("Базовая", base_preds, references)
    ft_metrics   = evaluate_model("Дообученная", ft_preds, references)

    print_comparison(base_metrics, ft_metrics)

    print("\nПример генерации (первый элемент теста):")
    print(f"  Текст (начало): {texts[0][:120]}...")
    print(f"  Эталон:         {references[0]}")
    print(f"  Базовая:        {base_preds[0]}")
    print(f"  Дообученная:    {ft_preds[0]}")


if __name__ == "__main__":
    main()
