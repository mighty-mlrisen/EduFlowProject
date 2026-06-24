import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
from pathlib import Path

MODEL_NAME = "cointegrated/rut5-base-absum"
ARTICLE_PATH = Path(__file__).parent / "article.txt"
RESULT_PATH = Path(__file__).parent / "result.txt"
"""
MAX_INPUT_TOKENS = 600
MAX_SUMMARY_TOKENS = 150
MIN_SUMMARY_TOKENS = 40
"""
MAX_INPUT_TOKENS = 1500
MAX_SUMMARY_TOKENS = 300
MIN_SUMMARY_TOKENS = 120

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


def summarize(text: str, tokenizer, model, device: torch.device) -> str:
    # Сначала токенизируем без обрезки, чтобы узнать реальную длину
    full_ids = tokenizer(text, truncation=False)["input_ids"]
    total_tokens = len(full_ids)

    if total_tokens > MAX_INPUT_TOKENS:
        kept_ids = full_ids[:MAX_INPUT_TOKENS]
        cut_ids = full_ids[MAX_INPUT_TOKENS:]
        cut_text = tokenizer.decode(cut_ids, skip_special_tokens=True)
        print(f"Токенов в тексте: {total_tokens} — ОБРЕЗАНО до {MAX_INPUT_TOKENS}")
        print(f"Обрезанный хвост ({len(cut_ids)} токенов): «...{cut_text[:120]}»")
    else:
        print(f"Токенов в тексте: {total_tokens} — всё вместилось (лимит {MAX_INPUT_TOKENS})")

    inputs = tokenizer(
        text,
        max_length=MAX_INPUT_TOKENS,
        truncation=True,
        return_tensors="pt",
    ).to(device)

    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=MAX_SUMMARY_TOKENS,
            min_new_tokens=MIN_SUMMARY_TOKENS,
            num_beams=4,
            length_penalty=0.9,
            #length_penalty=1.5,
            no_repeat_ngram_size=3,
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
    print("Модель загружена. Генерация краткого содержания...")

    summary = summarize(article, tokenizer, model, device)

    RESULT_PATH.write_text(summary, encoding="utf-8")
    print(f"\nКраткое содержание:\n{summary}")
    print(f"\nРезультат сохранён в {RESULT_PATH}")


if __name__ == "__main__":
    main()
