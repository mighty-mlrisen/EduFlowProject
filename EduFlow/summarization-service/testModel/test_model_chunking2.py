import re
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pathlib import Path

MODEL_NAME = "cointegrated/rut5-base-absum"
ARTICLE_PATH = Path(__file__).parent / "article3.txt"
RESULT_PATH = Path(__file__).parent / "result_chunking2.txt"

"""
CHUNK_SIZE = 450        # максимум токенов на чанк
OVERLAP_SENTENCES = 1   # сколько предложений с предыдущего чанка переносим (контекст)
MAX_SUMMARY_TOKENS = 200
MIN_SUMMARY_TOKENS = 60
FINAL_MAX_SUMMARY_TOKENS = 300 #до 400
FINAL_MIN_SUMMARY_TOKENS = 100 # до 180-200
"""
CHUNK_SIZE = 450        # максимум токенов на чанк
OVERLAP_SENTENCES = 1
MAX_SUMMARY_TOKENS = 300 #150-200
MIN_SUMMARY_TOKENS = 80  #60-80

FINAL_MAX_SUMMARY_TOKENS = 320 #до 400 | 320
FINAL_MIN_SUMMARY_TOKENS = 120 # до 180-200 | 150-160

def get_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def load_model(device: torch.device):
    print(f"Загрузка модели {MODEL_NAME}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForSeq2SeqLM.from_pretrained(MODEL_NAME)
    model = model.to(device)
    model.eval()
    return tokenizer, model


def split_sentences(text: str) -> list[str]:
    # Делим по концу предложения (.!?) перед заглавной буквой (рус/лат)
    parts = re.split(r'(?<=[.!?])\s+(?=[А-ЯA-ZЁ])', text)
    return [s.strip() for s in parts if s.strip()]


def split_into_chunks(text: str, tokenizer) -> list[str]:
    sentences = split_sentences(text)

    def token_count(s: str) -> int:
        return len(tokenizer(s, truncation=False, add_special_tokens=False)["input_ids"])

    chunks: list[str] = []
    current: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sent_tokens = token_count(sentence)

        # Предложение само по себе длиннее лимита — отдаём отдельным чанком
        if sent_tokens >= CHUNK_SIZE:
            if current:
                chunks.append(" ".join(current))
                current, current_tokens = [], 0
            chunks.append(sentence)
            continue

        # Если добавление переполняет чанк — сохраняем текущий, переносим overlap
        if current_tokens + sent_tokens > CHUNK_SIZE and current:
            chunks.append(" ".join(current))
            overlap = current[-OVERLAP_SENTENCES:]
            current = overlap.copy()
            current_tokens = sum(token_count(s) for s in current)

        current.append(sentence)
        current_tokens += sent_tokens

    if current:
        chunks.append(" ".join(current))

    print(f"\nПредложений: {len(sentences)}, чанков: {len(chunks)}")
    for i, c in enumerate(chunks):
        ids = tokenizer(c, truncation=False)["input_ids"]
        print(f"  Чанк {i+1}: {len(ids)} токенов — «{c[:70].strip()}...»")

    return chunks


def summarize_chunk(text: str, tokenizer, model, device: torch.device) -> str:
    inputs = tokenizer(
        text,
        max_length=CHUNK_SIZE,
        truncation=True,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_SUMMARY_TOKENS,
            min_new_tokens=MIN_SUMMARY_TOKENS,
            num_beams=4,
            length_penalty=1.0,
            repetition_penalty=1.3,
            no_repeat_ngram_size=4,
            early_stopping=True,
        )

    return tokenizer.decode(output_ids[0], skip_special_tokens=True)


def main():
    article = ARTICLE_PATH.read_text(encoding="utf-8").strip()
    if not article:
        print(f"Ошибка: файл {ARTICLE_PATH} пустой.")
        return

    print(f"Статья прочитана ({len(article)} символов)")

    device = get_device()
    print(f"Устройство: {device}")

    tokenizer, model = load_model(device)

    chunks = split_into_chunks(article, tokenizer)

    print("\n--- Суммаризация чанков ---")
    chunk_summaries = []
    for i, chunk in enumerate(chunks):
        summary = summarize_chunk(chunk, tokenizer, model, device)
        print(f"\nЧанк {i+1} → {summary}")
        chunk_summaries.append(summary)

    combined = " ".join(chunk_summaries)

    if len(chunk_summaries) > 1:
        print("\n--- Финальная суммаризация ---")
        inputs = tokenizer(
            combined,
            max_length=CHUNK_SIZE,
            truncation=True,
            return_tensors="pt",
        ).to(device)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                max_new_tokens=FINAL_MAX_SUMMARY_TOKENS,
                min_new_tokens=FINAL_MIN_SUMMARY_TOKENS,
                num_beams=4,
                length_penalty=1.2,
                repetition_penalty=1.4,
                no_repeat_ngram_size=4,
                early_stopping=True,
            )
        final_summary = tokenizer.decode(out[0], skip_special_tokens=True)
    else:
        final_summary = combined

    RESULT_PATH.write_text(final_summary, encoding="utf-8")
    print(f"\n=== Итоговое краткое содержание ===\n{final_summary}")
    print(f"\nРезультат сохранён в {RESULT_PATH}")


if __name__ == "__main__":
    main()
