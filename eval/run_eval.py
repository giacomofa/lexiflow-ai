"""
Harness de avaliação fim a fim do LexiFlow AI.

Substitui a avaliação manual feita em planilha: carrega os documentos de
sample_docs/, roda a pipeline real (analyze_document -> LLM da OpenAI) e
compara o resultado com o gabarito estruturado em eval/gabarito.json.

Requer OPENAI_API_KEY configurada (faz chamadas reais à API da OpenAI).

Uso:
    python -m eval.run_eval
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

# Em alguns terminais Windows (cmd/PowerShell com codepage legado), imprimir
# acentos no console pode lançar UnicodeEncodeError e derrubar o script antes
# de terminar. Força a saída padrão para UTF-8 para evitar isso.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.llm_analysis_service import analyze_document  # noqa: E402
from services.document_loader import load_document  # noqa: E402
from services.text_preprocessor import preprocess_text  # noqa: E402

GABARITO_PATH = Path(__file__).resolve().parent / "gabarito.json"
RESULTS_DIR = Path(__file__).resolve().parent / "results"

# Nem todo caso do gabarito precisa checar os 4 campos: alguns (ex.: o lote de
# documentos públicos reais) só têm gabarito de document_type, porque validar
# os demais campos exigiria ler cláusula por cláusula de cada documento. O
# harness calcula actual/field_matches apenas para os campos presentes em
# `case["expected"]`, sem quebrar os casos que já têm gabarito completo.
_ALL_FIELDS = ("document_type", "personal_data_mentions", "has_penalty_clause", "has_confidentiality_clause")


def load_gabarito() -> list[dict]:
    with open(GABARITO_PATH, encoding="utf-8") as f:
        data = json.load(f)
    return data["cases"]


def load_case_text(file_path: str) -> str:
    absolute_path = PROJECT_ROOT / file_path
    with open(absolute_path, "rb") as f:
        raw_text = load_document(f)
    return preprocess_text(raw_text)


def evaluate_case(case: dict) -> dict:
    file_path = case["file_path"]
    expected = case["expected"]

    text = load_case_text(file_path)
    result = analyze_document(text, Path(file_path).name)
    full_analysis = result.get("full_analysis", {})

    actual_all = {
        "document_type": result.get("document_type"),
        "personal_data_mentions": full_analysis.get("personal_data_mentions"),
        "has_penalty_clause": bool(full_analysis.get("penalty_clause")),
        "has_confidentiality_clause": bool(full_analysis.get("confidentiality_clause")),
    }

    actual = {field: actual_all[field] for field in expected}
    field_matches = {field: actual[field] == expected[field] for field in expected}
    passed = all(field_matches.values())

    return {
        "id": case["id"],
        "file_path": file_path,
        "passed": passed,
        "expected": expected,
        "actual": actual,
        "field_matches": field_matches,
        "alerts": result.get("alerts", []),
        "needs_review": result.get("needs_review"),
        "summary": result.get("summary"),
    }


def run() -> dict:
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "ERRO: OPENAI_API_KEY não configurada. Configure a variável de ambiente "
            "antes de rodar `python -m eval.run_eval` (o harness faz chamadas reais à API da OpenAI)."
        )
        sys.exit(1)

    cases = load_gabarito()
    case_results = []

    for case in cases:
        print(f"Avaliando: {case['id']} ({case['file_path']})...")
        try:
            case_results.append(evaluate_case(case))
        except Exception as e:
            case_results.append({
                "id": case["id"],
                "file_path": case["file_path"],
                "passed": False,
                "error": str(e),
            })

    total = len(case_results)
    passed = sum(1 for r in case_results if r.get("passed"))

    field_accuracy = {}
    for field in _ALL_FIELDS:
        matches = [
            r["field_matches"][field]
            for r in case_results
            if "field_matches" in r and field in r["field_matches"]
        ]
        field_accuracy[field] = round(sum(matches) / len(matches), 3) if matches else None

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_cases": total,
        "passed_cases": passed,
        "pass_rate": round(passed / total, 3) if total else None,
        "field_accuracy": field_accuracy,
        "cases": case_results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    report_path = RESULTS_DIR / f"report_{timestamp}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print()
    print(f"Resultado: {passed}/{total} casos aprovados ({report['pass_rate']:.1%})")
    for field, accuracy in field_accuracy.items():
        print(f"  - acurácia de '{field}': {accuracy:.1%}" if accuracy is not None else f"  - '{field}': sem dados")
    print()
    for r in case_results:
        status = "OK " if r.get("passed") else "FAIL"
        print(f"[{status}] {r['id']}")
        if not r.get("passed") and "field_matches" in r:
            for field, matched in r["field_matches"].items():
                if not matched:
                    print(f"       {field}: esperado={r['expected'][field]!r} obtido={r['actual'][field]!r}")
        elif "error" in r:
            print(f"       erro: {r['error']}")

    print()
    print(f"Relatório completo salvo em: {report_path.relative_to(PROJECT_ROOT)}")

    return report


if __name__ == "__main__":
    run()
