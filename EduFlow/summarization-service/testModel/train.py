#!/usr/bin/env python3
"""
Fine-tuning cointegrated/rut5-base-absum на своём датасете (русская суммаризация).
Оптимизировано под MacBook M1 Pro 13" 8 GB (MPS-ускорение).

Формат датасета — JSONL, одна запись на строку:
    {"text": "полный текст статьи...", "summary": "краткое содержание..."}

"""

import os
import numpy as np
from datasets import load_dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSeq2SeqLM,
    DataCollatorForSeq2Seq,
    Seq2SeqTrainer,
    Seq2SeqTrainingArguments,
    EarlyStoppingCallback,
)
from rouge_score import rouge_scorer

# MPS: fallback на CPU для операций, которые MPS не поддерживает
os.environ["PYTORCH_ENABLE_MPS_FALLBACK"] = "1"

# ── Пути ──────────────────────────────────────────────────────────────────────
BASE_MODEL  = "cointegrated/rut5-base-absum"
TRAIN_PATH  = "/Users/artemmazurenko/EduFlow/summarization-service/dataset/train.jsonl"
EVAL_PATH   = "/Users/artemmazurenko/EduFlow/summarization-service/dataset/eval.jsonl"
OUTPUT_DIR  = "/Users/artemmazurenko/EduFlow/summarization-service/models/finetuned-rut5"
LOGGING_DIR = "/Users/artemmazurenko/EduFlow/summarization-service/models/logs"

# ── Токенизация ────────────────────────────────────────────────────────────────
MAX_SOURCE_LENGTH = 512   # лимит токенов входного текста (T5 стандарт)
MAX_TARGET_LENGTH = 200   # лимит токенов саммари

# ── Гиперпараметры (M1 Pro 13" 8 GB) ──────────────────────────────────────────
# rut5-base ~250M параметров ≈ 1 GB float32
# AdamW optimizer states ≈ 2x модели ≈ 2 GB
# Активации batch=2, seq=512 ≈ 0.5-1 GB → итого ~4-5 GB из 8 GB
BATCH_SIZE  = 2    # физический batch (ограничение памяти)
GRAD_ACCUM  = 8    # effective batch = 2 × 8 = 16
LR          = 5e-5
NUM_EPOCHS  = 5    # с early stopping (patience=2) обычно останавливается раньше
WARMUP_RATIO     = 0.1   # 10% шагов на прогрев lr
WEIGHT_DECAY     = 0.01
MAX_GRAD_NORM    = 1.0
SAVE_TOTAL_LIMIT = 2     # хранить только 2 последних чекпоинта
SEED             = 42


def main():
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    def preprocess(examples):
        model_inputs = tokenizer(
            examples["text"],
            max_length=MAX_SOURCE_LENGTH,
            truncation=True,
            padding=False,
        )
        labels = tokenizer(
            text_target=examples["summary"],
            max_length=MAX_TARGET_LENGTH,
            truncation=True,
            padding=False,
        )
        model_inputs["labels"] = labels["input_ids"]
        return model_inputs

    print("Загрузка датасета...")
    dataset = load_dataset("json", data_files={"train": TRAIN_PATH, "eval": EVAL_PATH})
    tokenized = dataset.map(preprocess, batched=True, remove_columns=["text", "summary"])
    print(f"Train: {len(tokenized['train'])} примеров, Eval: {len(tokenized['eval'])} примеров")

    model = AutoModelForSeq2SeqLM.from_pretrained(BASE_MODEL)
    # gradient_checkpointing несовместим с кешем внимания — отключаем
    model.config.use_cache = False

    scorer = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=False)

    def compute_metrics(eval_preds):
        predictions, labels = eval_preds
        labels = np.where(labels != -100, labels, tokenizer.pad_token_id)
        decoded_preds  = tokenizer.batch_decode(predictions, skip_special_tokens=True)
        decoded_labels = tokenizer.batch_decode(labels,      skip_special_tokens=True)

        r1, r2, rl = [], [], []
        for pred, ref in zip(decoded_preds, decoded_labels):
            scores = scorer.score(ref, pred)
            r1.append(scores["rouge1"].fmeasure)
            r2.append(scores["rouge2"].fmeasure)
            rl.append(scores["rougeL"].fmeasure)

        return {
            "rouge1": round(float(np.mean(r1)), 4),
            "rouge2": round(float(np.mean(r2)), 4),
            "rougeL": round(float(np.mean(rl)), 4),
        }

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)

    training_args = Seq2SeqTrainingArguments(
        output_dir=OUTPUT_DIR,
        logging_dir=LOGGING_DIR,

        # Batch / градиент
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRAD_ACCUM,
        gradient_checkpointing=True,  # экономит ~30% памяти за счёт пересчёта активаций

        # Оптимизатор
        learning_rate=LR,
        num_train_epochs=NUM_EPOCHS,
        warmup_ratio=WARMUP_RATIO,
        weight_decay=WEIGHT_DECAY,
        max_grad_norm=MAX_GRAD_NORM,
        lr_scheduler_type="cosine",  # cosine даёт лучшую сходимость на малых датасетах

        # Оценка / чекпоинты
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="rouge2",
        greater_is_better=True,
        save_total_limit=SAVE_TOTAL_LIMIT,

        # Генерация для compute_metrics
        predict_with_generate=True,
        generation_max_length=MAX_TARGET_LENGTH,
        generation_num_beams=4,

        # Стабильность MPS
        dataloader_num_workers=0,  # >0 вызывает проблемы с форком процессов на MPS
        fp16=False,                # MPS не поддерживает float16 надёжно
        bf16=False,

        seed=SEED,
        logging_steps=10,
        report_to="none",          # отключить wandb / tensorboard
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["eval"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )

    print("Начало обучения...")
    trainer.train()

    trainer.save_model(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print(f"\nМодель сохранена в {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
