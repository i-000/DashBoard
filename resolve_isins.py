"""
resolve_isins.py
-----------------
Ayuda a encontrar el simbolo correcto de Yahoo Finance para los ISIN
que en config.json todavia tienen "yahoo_symbol": null o "verified": false.

Uso:
    pip install requests
    python3 resolve_isins.py

Para cada ISIN pendiente, muestra los candidatos que Yahoo Finance conoce
(simbolo, nombre y bolsa) junto con un enlace a la ficha de cada uno en
Yahoo Finance, para que abras el que te interese y confirmes con un vistazo
que la divisa mostrada es EUR. Copia ese simbolo dentro de config.json en
el campo "yahoo_symbol" (y pon "verified": true).

Este script NO modifica config.json automaticamente: es una ayuda de
consulta, para evitar guardar un simbolo equivocado sin que lo hayas visto.
Solo necesita la libreria "requests" (no yfinance), para que funcione
incluso con versiones de Python mas antiguas.
"""

import json
import time
import requests

CONFIG_PATH = "config.json"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}

SEARCH_URL = "https://query2.finance.yahoo.com/v1/finance/search"


def buscar_isin(isin: str):
    params = {
        "q": isin,
        "quotesCount": 10,
        "newsCount": 0,
    }
    resp = requests.get(SEARCH_URL, params=params, headers=HEADERS, timeout=10)
    resp.raise_for_status()
    data = resp.json()
    return data.get("quotes", [])


def main():
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        config = json.load(f)

    pendientes = [
        h for h in config["holdings"]
        if h.get("isin") and not h.get("verified", False)
    ]

    if not pendientes:
        print("No hay ISIN pendientes de verificar. Todo listo.")
        return

    for holding in pendientes:
        isin = holding["isin"]
        print("\n" + "=" * 70)
        print(f"{holding['name']}  (ISIN: {isin})")
        print("=" * 70)
        try:
            candidatos = buscar_isin(isin)
        except Exception as e:
            print(f"  No se pudo consultar Yahoo Finance: {e}")
            continue

        if not candidatos:
            print("  Sin resultados. Prueba a buscar el ISIN manualmente en "
                  "https://finance.yahoo.com/lookup")
            continue

        for c in candidatos:
            symbol = c.get("symbol")
            nombre = c.get("shortname") or c.get("longname") or "?"
            bolsa = c.get("exchange") or "?"
            print(f"  simbolo: {symbol:<15} | {nombre:<45} | bolsa: {bolsa}")
            print(f"      -> revisa la divisa aqui: https://finance.yahoo.com/quote/{symbol}")

        print("\n  -> Abre los enlaces, mira cual dice 'Currency in EUR', y "
              "copia ESE 'simbolo' en config.json (campo yahoo_symbol), "
              "poniendo tambien verified: true")

        time.sleep(1)  # para no saturar el buscador de Yahoo


if __name__ == "__main__":
    main()
