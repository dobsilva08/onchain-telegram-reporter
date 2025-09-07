
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Scenario B — Gera relatório "Dados On-Chain — {data} — Diário — Nº {contador}" com OpenAI API,
# salva em PDF e envia via Telegram Bot API, sem libs externas.

import os, json, argparse, textwrap, requests
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any, List

BRT = timezone(timedelta(hours=-3), name="BRT")

def load_env_if_present():
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k, v = k.strip(), v.strip()
            if k and v and k not in os.environ:
                os.environ[k] = v

def today_brt_str():
    meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
    now = datetime.now(BRT)
    return f"{now.day} de {meses[now.month-1]} de {now.year}"

def iso_to_brt_human(iso_date: str) -> str:
    try:
        dt = datetime.strptime(iso_date, "%Y-%m-%d")
        dt = dt.replace(tzinfo=BRT)
        meses = ["janeiro","fevereiro","março","abril","maio","junho","julho","agosto","setembro","outubro","novembro","dezembro"]
        return f"{dt.day} de {meses[dt.month-1]} de {dt.year}"
    except Exception:
        return iso_date

def read_counter(counter_file: str, start_counter: int = 1) -> int:
    try:
        if os.path.exists(counter_file):
            with open(counter_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = {}
        val = int(data.get("diario", start_counter))
        data["diario"] = val + 1
        with open(counter_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return val
    except Exception:
        return start_counter

def build_prompt(data_str: str, numero: int, metrics: Optional[Dict[str, Any]]) -> str:
    header = "Dados On-Chain — " + data_str + " — Diário — Nº " + str(numero)
    rules = (
        "Você é um analista on-chain sênior. Produza um relatório em português do Brasil no formato abaixo:\n"
        "com estilo objetivo, profissional e consistência terminológica. Estruture com subtítulos claros.\n\n"
        "TÍTULO (linha única):\n"
        + header + "\n\n"
        "REGRAS:\n"
        "- Se métricas forem fornecidas (JSON), use os valores; se NÃO houver, NÃO invente números: descreva apenas sinais qualitativos (alta/baixa/estável) com linguagem prudente.\n"
        "- Não coloque links. Não cite fontes.\n"
        "- Termine com 'Interpretação Executiva' em bullets e 'Conclusão'.\n"
        "- Mencione a data completa no primeiro parágrafo.\n"
        "- Ordem e blocos fixos:\n"
        "  1) Exchange Inflow (MA7) — 1 parágrafo\n"
        "  2) Exchange Netflow (Total) — 1 parágrafo\n"
        "  3) Reservas em Exchanges — 1 parágrafo\n"
        "  4) Fluxos de Baleias (Whale-to-Exchange Flows) — 2 parágrafos: (a) depósitos de whales/mineradores; (b) Whale Ratio\n"
        "  5) Resumo de Contexto Institucional — 1 parágrafo\n"
        "  6) Interpretação Executiva — 5–8 bullets curtos, diretos e acionáveis\n"
        "  7) Conclusão — 1 parágrafo com tom executivo\n\n"
        "DADOS (JSON opcional):\n"
    )
    dados = json.dumps(metrics, ensure_ascii=False, indent=2) if metrics else "null"
    return rules + dados

def openai_generate(api_key: str, model: Optional[str], prompt: str) -> str:
    # Default alinhado com o chat: gpt-5
    if not model:
        model = os.environ.get("OPENAI_MODEL", "gpt-5")
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Authorization": "Bearer " + api_key,
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "Você é um analista on-chain sênior e escreve em português do Brasil."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.4,
        "max_tokens": 1800
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    if resp.status_code != 200:
        raise RuntimeError("OpenAI API error: HTTP {} — {}".format(resp.status_code, resp.text))
    data = resp.json()
    return data["choices"][0]["message"]["content"]

def wrap_text(text: str, width: int = 95) -> List[str]:
    lines: List[str] = []
    for para in text.splitlines():
        if not para.strip():
            lines.append("")
            continue
        for seg in textwrap.wrap(para, width=width, break_long_words=True, replace_whitespace=False):
            lines.append(seg)
    return lines

def escape_pdf_text(s: str) -> str:
    return s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)").replace("\r", "").replace("\t", "    ")

def write_simple_pdf(path: str, title: str, body: str, font_size: int = 11):
    page_width, page_height = 595.28, 841.89
    margin = 56.7
    leading = font_size * 1.35

    wrapped_title = textwrap.fill(title, width=80)
    body_lines = wrap_text(body, width=95)

    objects = []
    xref = []

    def add_object(obj_str: str) -> int:
        pos = sum(len(o) for o in objects)
        xref.append(pos)
        objects.append(obj_str)
        return len(xref)

    pdf = ["%PDF-1.4\n%\xFF\xFF\xFF\xFF\n"]

    font_obj_num = add_object("1 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n")

    contents_obj_nums = []
    pages_kids = []

    def flush_page(page_text):
        stream_text = "\n".join(page_text)
        stream_len = len(stream_text.encode("latin-1", "ignore"))
        content_obj_num = add_object("{} 0 obj\n<< /Length {} >>\nstream\n{}\nendstream\nendobj\n".format(len(xref)+1, stream_len, stream_text))
        page_obj_num = add_object(
            "{} 0 obj\n<< /Type /Page /Parent 0 0 R /MediaBox [0 0 {} {}] /Resources << /Font << /F1 {} 0 R >> >> /Contents {} 0 R >>\nendobj\n".format(
                len(xref)+1, page_width, page_height, font_obj_num, content_obj_num
            )
        )
        contents_obj_nums.append(content_obj_num)
        pages_kids.append(page_obj_num)

    cur_y = page_height - margin
    line_count = 0
    lines_per_page = int((page_height - margin - margin) / leading) - 3

    page_text = ["BT", "/F1 {} Tf".format(font_size), "{} {} Td".format(margin, cur_y)]
    for i, line in enumerate(wrapped_title.splitlines()):
        if i == 0:
            page_text.append("0 0 Td ({}) Tj".format(escape_pdf_text(line)))
        else:
            page_text.append("0 -{:.2f} Td ({}) Tj".format(leading, escape_pdf_text(line)))
    page_text.append("0 -{:.2f} Td".format(leading*2))
    line_count = 0

    for line in body_lines:
        if line_count >= lines_per_page:
            page_text.append("ET")
            flush_page(page_text)
            cur_y = page_height - margin
            page_text = ["BT", "/F1 {} Tf".format(font_size), "{} {} Td".format(margin, cur_y)]
            line_count = 0
        safe = escape_pdf_text(line if line else " ")
        page_text.append("0 -{:.2f} Td ({}) Tj".format(leading, safe))
        line_count += 1

    page_text.append("ET")
    flush_page(page_text)

    kids_str = " ".join("{} 0 R".format(kid) for kid in pages_kids)
    pages_obj_num = add_object("{} 0 obj\n<< /Type /Pages /Kids [ {} ] /Count {} >>\nendobj\n".format(len(xref)+1, kids_str, len(pages_kids)))
    catalog_obj_num = add_object("{} 0 obj\n<< /Type /Catalog /Pages {} 0 R >>\nendobj\n".format(len(xref)+1, pages_obj_num))

    xref_start = sum(len(p) for p in pdf) + sum(len(o) for o in objects)
    xref_table = ["xref\n0 {}\n0000000000 65535 f \n".format(len(xref)+1)]
    for pos in xref:
        xref_table.append("{:010d} 00000 n \n".format(pos))

    out_bytes = "".join(pdf + objects + xref_table + ["trailer\n<< /Size {} /Root {} 0 R >>\nstartxref\n{}\n%%EOF".format(len(xref)+1, catalog_obj_num, xref_start)]).encode("latin-1", "ignore")
    with open(path, "wb") as f:
        f.write(out_bytes)

def telegram_send_document(token: str, chat_id: str, file_path: str, caption: Optional[str] = None, parse_mode: str = "HTML"):
    url = "https://api.telegram.org/bot{}/sendDocument".format(token)
    with open(file_path, "rb") as f:
        files = {"document": (os.path.basename(file_path), f, "application/pdf")}
        data = {"chat_id": chat_id}
        if caption:
            data["caption"] = caption
            data["parse_mode"] = parse_mode
        r = requests.post(url, data=data, files=files, timeout=120)
    if r.status_code != 200:
        raise RuntimeError("Telegram error: HTTP {} — {}".format(r.status_code, r.text))
    out = r.json()
    if not out.get("ok"):
        raise RuntimeError("Telegram error payload: {}".format(out))
    return out

def main():
    load_env_if_present()

    parser = argparse.ArgumentParser(description="Gera PDF 'Dados On-Chain — Diário' via OpenAI e envia no Telegram.")
    parser.add_argument("--date", help="Data (YYYY-MM-DD). Padrão=hoje (BRT).")
    parser.add_argument("--start-counter", type=int, default=1, help="Valor inicial do contador se counters.json não existir.")
    parser.add_argument("--counter-file", default=os.path.join(os.path.dirname(__file__), "counters.json"), help="Arquivo do contador.")
    parser.add_argument("--metrics", help="Caminho de um JSON com métricas reais (opcional).")
    parser.add_argument("--no-send", action="store_true", help="Só gerar o PDF, sem enviar.")
    parser.add_argument("--model", help="Modelo OpenAI (padrão: $OPENAI_MODEL ou gpt-5).")

    args = parser.parse_args()

    api_key = os.environ.get("OPENAI_API_KEY")
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat = os.environ.get("TELEGRAM_CHAT_ID")

    if not api_key:
        raise SystemExit("Defina OPENAI_API_KEY no .env")
    if not args.no_send and (not tg_token or not tg_chat):
        raise SystemExit("Defina TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID no .env para envio. Ou use --no-send.")

    data_str = iso_to_brt_human(args.date) if args.date else today_brt_str()
    numero = read_counter(args.counter_file, start_counter=args.start_counter)

    metrics = None
    if args.metrics:
        with open(args.metrics, "r", encoding="utf-8") as f:
            metrics = json.load(f)

    prompt = build_prompt(data_str, numero, metrics)
    content = openai_generate(api_key, args.model, prompt)

    titulo = "Dados On-Chain — " + data_str + " — Diário — Nº " + str(numero)
    caption = titulo

    out_dir = os.path.join(os.path.dirname(__file__), "out")
    os.makedirs(out_dir, exist_ok=True)
    filename = "Dados On-Chain — " + data_str + " — Diário — Nº " + str(numero) + ".pdf"
    out_path = os.path.join(out_dir, filename)

    write_simple_pdf(out_path, titulo, content, font_size=11)

    if not args.no_send:
        telegram_send_document(tg_token, tg_chat, out_path, caption=caption)
        print("[ok] Enviado no Telegram: {}".format(out_path))
    else:
        print("[ok] PDF gerado (sem enviar): {}".format(out_path))

if __name__ == "__main__":
    main()
