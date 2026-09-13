"""
fetch_prices.py
----------------
Descarga el ultimo cierre (o valor liquidativo) de cada posicion definida
en config.json usando Yahoo Finance (via yfinance), y actualiza docs/data.json
con un historial acumulado para poder pintar el dashboard.

Uso:
    pip install -r requirements.txt
    python fetch_prices.py

Pensado para ejecutarse una vez al dia desde GitHub Actions, pero funciona
igual de bien en local.
"""

import json
import datetime
from pathlib import Path

import yfinance as yf

CONFIG_PATH = Path("config.json")
DATA_PATH = Path("docs/data.json")
MAX_HISTORY_POINTS = 400


def cargar_json(path: Path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def guardar_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def obtener_historial(symbol: str):
    """Devuelve una lista de (fecha_iso, cierre) ordenada, o None si falla."""
    ticker = yf.Ticker(symbol)
    hist = ticker.history(period="1mo", auto_adjust=False)
    if hist.empty:
        return None, None

    puntos = [
        (idx.strftime("%Y-%m-%d"), round(float(row["Close"]), 4))
        for idx, row in hist.iterrows()
        if row["Close"] == row["Close"]  # descarta NaN
    ]

    moneda = None
    try:
        moneda = ticker.fast_info.get("currency")
    except Exception:
        pass

    return puntos, moneda


def fusionar_historial(historial_previo, puntos_nuevos):
    por_fecha = {fecha: cierre for fecha, cierre in historial_previo}
    for fecha, cierre in puntos_nuevos:
        por_fecha[fecha] = cierre
    fechas_ordenadas = sorted(por_fecha.keys())[-MAX_HISTORY_POINTS:]
    return [{"date": f, "close": por_fecha[f]} for f in fechas_ordenadas]


def main():
    config = cargar_json(CONFIG_PATH, {"holdings": []})
    data_previa = cargar_json(DATA_PATH, {"updated_at": None, "holdings": {}})
    holdings_previos = data_previa.get("holdings", {})

    resultado = {}

    for holding in config["holdings"]:
        symbol = holding.get("yahoo_symbol")
        key = holding.get("isin") or symbol
        nombre = holding["name"]

        base = holdings_previos.get(key, {
            "name": nombre,
            "type": holding.get("type"),
            "isin": holding.get("isin"),
            "symbol": symbol,
            "currency": None,
            "history": [],
            "last_close": None,
            "prev_close": None,
            "change_pct": None,
            "last_date": None,
            "status": "sin_datos",
        })
        base["name"] = nombre
        base["type"] = holding.get("type")
        base["symbol"] = symbol

        if not symbol:
            base["status"] = "sin_simbolo"
            resultado[key] = base
            print(f"[AVISO] {nombre}: no tiene yahoo_symbol asignado en "
                  f"config.json (usa resolve_isins.py)")
            continue

        try:
            puntos, moneda = obtener_historial(symbol)
            if not puntos:
                raise ValueError("sin datos devueltos")

            historial_previo = [(h["date"], h["close"]) for h in base["history"]]
            historial_fusionado = fusionar_historial(historial_previo, puntos)

            base["history"] = historial_fusionado
            base["currency"] = moneda or base.get("currency")
            base["last_date"] = historial_fusionado[-1]["date"]
            base["last_close"] = historial_fusionado[-1]["close"]
            if len(historial_fusionado) >= 2:
                base["prev_close"] = historial_fusionado[-2]["close"]
                if base["prev_close"]:
                    base["change_pct"] = round(
                        (base["last_close"] - base["prev_close"])
                        / base["prev_close"] * 100, 2,
                    )
            base["status"] = "ok"
            print(f"[OK] {nombre} ({symbol}): {base['last_close']} "
                  f"{base['currency']} ({base['last_date']})")

        except Exception as e:
            base["status"] = "error"
            print(f"[ERROR] {nombre} ({symbol}): {e}")

        resultado[key] = base

    data_final = {
        "updated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "holdings": resultado,
    }
    guardar_json(DATA_PATH, data_final)
    print(f"\nGuardado en {DATA_PATH}")


if __name__ == "__main__":
    main()
