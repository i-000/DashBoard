# Mi cartera — dashboard automático

Dashboard que muestra el cierre diario (o último NAV conocido) de tu cartera:
acciones, ETFs, ETCs y fondos indexados. Se actualiza solo, una vez al día,
sin que tengas que hacer nada ni tener el ordenador encendido.

## Cómo funciona

1. `config.json` — la lista de tus posiciones (nombre, ISIN/ticker, tipo, y el
   símbolo de Yahoo Finance que hay que consultar).
2. `fetch_prices.py` — descarga el último cierre oficial de cada posición
   (fondos incluidos) y lo guarda, con historial, en `docs/data.json`.
   Se ejecuta **una vez al día**.
3. `fetch_intraday.py` — actualiza el precio "casi en vivo" (retraso típico
   de 15-20 min) solo de Acciones, ETFs y ETC, sin tocar el histórico de
   cierres. Se ejecuta **cada 15 minutos** en horario de mercado.
4. `.github/workflows/update.yml` y `update_intraday.yml` — hacen que GitHub
   ejecute esos dos scripts automáticamente y guarde el resultado en el
   propio repositorio:
   - `update.yml`: una vez al día, de lunes a sábado, 05:00 UTC.
   - `update_intraday.yml`: cada 15 minutos, de 07:00 a 21:00 UTC, de lunes
     a viernes (cubre el horario de las bolsas europeas y estadounidenses).
5. `docs/index.html` — el dashboard visual, que lee `docs/data.json` y pinta
   una tarjeta por posición con precio, variación y una mini gráfica. Para
   Acciones/ETF/ETC muestra el precio intradía cuando está disponible
   (con la etiqueta "Intradía · HH:MM"); para fondos, el último cierre/NAV.

## Puesta en marcha (una sola vez)

1. **Crea un repositorio en GitHub** (público, para poder usar GitHub Pages
   gratis) y sube todos estos archivos.

2. **Resuelve los 3 símbolos pendientes.** En `config.json`, tres posiciones
   tienen `"yahoo_symbol": null` (Storm Bond Fund, iShares Physical Gold ETC
   e iShares Copper Miners UCITS ETF) porque cotizan en varias bolsas y hay
   que elegir la tuya en euros. En tu ordenador:

   ```bash
   pip install requests
   python resolve_isins.py
   ```

   Te mostrará los símbolos candidatos con su bolsa y divisa. Copia el que
   corresponda dentro de `config.json` (campo `yahoo_symbol`) y cambia
   `"verified": false` a `"verified": true`. Los otros 5 símbolos que llevan
   `.IR` o `.DE` también conviene que los compruebes una vez contra lo que ves
   en tu bróker, por si tu bolsa exacta es otra — es un ajuste de una sola vez.

3. **Activa GitHub Pages:** en el repositorio, ve a *Settings → Pages* y
   selecciona como fuente la rama `main` y la carpeta `/docs`.

4. **Da permiso de escritura a las Actions:** en *Settings → Actions →
   General → Workflow permissions*, marca "Read and write permissions".
   (Sin esto, el workflow no podrá guardar los datos actualizados cada día.)

5. **Lanza la primera actualización a mano:** pestaña *Actions* →
   "Actualizar cartera" → *Run workflow*. Tras un minuto, `docs/data.json`
   se habrá rellenado y el dashboard mostrará datos reales.

6. A partir de ahí, consulta cada día:
   `https://<tu-usuario>.github.io/<nombre-del-repo>/`

## Sobre el precio intradía

- Viene de Yahoo Finance gratis, así que trae el retraso habitual de
  15-20 minutos — no es un precio en tiempo real de bolsa.
- Solo se calcula para Acciones, ETF y ETC. Los fondos siguen mostrando
  solo su NAV diario, que es todo lo que publican.
- Si quieres cambiar la frecuencia (por ejemplo cada 30 min en vez de 15),
  edita la línea `cron` en `.github/workflows/update_intraday.yml`.
- Si algún día ves que deja de actualizarse, revisa la pestaña *Actions* del
  repo: Yahoo puede bloquear temporalmente si se le pide con demasiada
  frecuencia; en ese caso basta con espaciar más el cron.

## Notas importantes

- **La Cartera Indexada Indie de MyInvestor no está incluida**: al ser una
  combinación de varios fondos que MyInvestor rebalancea internamente y sin
  ISIN propio, no hay una fuente automática fiable para su valor. Se consulta
  aparte en la app de MyInvestor.
- Los precios pueden diferir ligeramente de los que ves en Trade Republic o
  MyInvestor por pequeños desfases horarios, redondeos o tipo de cambio — es
  una herramienta de seguimiento, no un extracto oficial.
- Si algún día un símbolo deja de funcionar (cambios en Yahoo, ETF
  liquidado, etc.), la tarjeta correspondiente mostrará "Sin datos
  disponibles todavía" en vez de romper el resto del dashboard.
