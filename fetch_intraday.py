"""
fetch_intraday.py
------------------
Actualiza un precio "casi en vivo" (con el retraso habitual de Yahoo Finance,
15-20 minutos) para las posiciones de tipo Accion, ETF y ETC. Los fondos
(Fondo indexado, Fondo, Renta fija) se ignoran aqui porque solo publican un
valor liquidativo al dia: de eso ya se encarga fetch_prices.py.

Este script NO modifica el historico de cierres diarios (docs/data.json ->
history): solo anade/actualiza los campos intraday_price, intraday_time e
intraday_change_pct de cada posicion, para que el dashboard pueda mostrar
un precio mas fresco durante el dia sin ensuciar la grafica de evolucion.

Uso:
    pip install -r requirements.txt
    python fetch_intraday.py
"""

import json
import datetime
from pathlib import Path

import yfinance as yf

CONFIG_PATH = Path("config.json")
DATA_PATH = Path("docs/data.json")

TIPOS_INTRADIA = {"Accion", "ETF", "ETC"}


def cargar_json(path: Path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def guardar_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def precio_actual(symbol: str):
    ticker = yf.Ticker(symbol)
    try:
        precio = ticker.fast_info.get("last_price")
        if precio:
            return float(precio)
    except Exception:
        pass

    # Alternativa si fast_info no trae nada: ultima vela intradia disponible
    hist = ticker.history(period="1d", interval="5m")
    if not hist.empty:
        return float(hist["Close"].dropna().iloc[-1])

    return None


def main():
    config = cargar_json(CONFIG_PATH, {"holdings": []})
    data = cargar_json(DATA_PATH, {"updated_at": None, "holdings": {}})
    holdings_data = data.get("holdings", {})

    ahora = datetime.datetime.utcnow()
    hora_str = ahora.strftime("%H:%M")

    for holding in config["holdings"]:
        if holding.get("type") not in TIPOS_INTRADIA:
            continue

        symbol = holding.get("yahoo_symbol")
        key = holding.get("isin") or symbol
        nombre = holding["name"]

        if not symbol or key not in holdings_data:
            # si todavia no existe entrada (nunca se ha corrido fetch_prices.py),
            # no forzamos nada aqui: que la cree primero el job diario.
            continue

        entrada = holdings_data[key]
        baseline = entrada.get("last_close")

        try:
            precio = precio_actual(symbol)
            if precio is None:
                raise ValueError("sin precio disponible")

            entrada["intraday_price"] = round(precio, 4)
            entrada["intraday_time"] = hora_str
            if baseline:
                entrada["intraday_change_pct"] = round(
                    (precio - baseline) / baseline * 100, 2
                )
            entrada["intraday_status"] = "ok"
            print(f"[OK] {nombre} ({symbol}): {precio} a las {hora_str} UTC")

        except Exception as e:
            entrada["intraday_status"] = "error"
            print(f"[ERROR] {nombre} ({symbol}): {e}")

        holdings_data[key] = entrada

    data["holdings"] = holdings_data
    data["intraday_updated_at"] = ahora.isoformat() + "Z"
    guardar_json(DATA_PATH, data)
    print(f"\nGuardado en {DATA_PATH}")


if __name__ == "__main__":
    main()
