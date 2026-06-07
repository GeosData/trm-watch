# trm-watch

Watch de la TRM (la tasa peso/dólar oficial de Colombia). Lee la serie publicada por la Superfinanciera en `datos.gov.co`, calcula tendencia, volatilidad y rachas, y entrega una lectura cambiaria lista para quien cobra o paga en dólares.

---

## La necesidad

Un freelancer que factura en dólares, un importador que paga proveedores afuera, una tesorería pequeña: todos viven pegados a la misma pregunta. **¿Hacia dónde se está moviendo el peso, y este cambio de hoy es ruido o es tendencia?**

La TRM se publica todos los días hábiles. Cualquiera puede ver el número de hoy en un titular. Pero un número suelto no es una decisión. El que va a convertir 3.000 dólares, o a fijar el precio de una factura, necesita saber otra cosa: si el peso viene devaluándose hace una semana, cuánto se movió en el mes, qué tan volátil está, si el salto de hoy es de los grandes o uno más. Para responder eso hoy toca:

- entrar al portal y mirar el valor del día,
- bajar la serie y armar a mano la diferencia contra la semana pasada,
- calcular en una hoja el máximo, el mínimo y la desviación del mes,
- y repetirlo cada vez, porque mañana el número ya es otro.

El dato existe y es oficial. Pero la lectura —tendencia, racha, volatilidad, movimiento atípico— no viene hecha. **El dolor no es no tener la TRM. Es que la TRM de hoy, sola, no te dice si conviene actuar hoy.**

## Por qué esta solución

La serie ya está, es pública y se actualiza a diario. Falta la capa que la convierte en lectura. Por eso `trm-watch` no guarda la TRM ni la grafica: la **lee**. Toma una ventana (un rango de fechas o las últimas N lecturas) y devuelve las cifras que importan más una lectura en lenguaje natural.

Decisiones que definen el alcance:

- **No replicamos la fuente, la consumimos.** Leemos la API oficial; el dato sigue siendo el de la Superfinanciera.
- **Tendencia primero, narrativa después.** El valor está en las cifras correctas (cambio, racha, volatilidad). La prosa solo las explica.
- **Describir, no aconsejar.** Decimos cómo se viene moviendo el peso y cuánto. No decimos "compre" ni "venda": eso es decisión y riesgo del usuario, no de un script.
- **CLI antes que UI.** El primer uso es un comando o un cron a las 8am. Una interfaz web es peso muerto hasta validar que la lectura sirve.

## Por qué esta arquitectura

El diseño responde a un riesgo concreto: **una lectura cambiaria con un número inventado induce una mala decisión de plata.** Si alguien fija una factura sobre una variación alucinada, pierde. Toda la arquitectura se ordena alrededor de evitar eso.

```
TRM API (SODA)   →  client  →  models  →  analytics  →  brief  →  CLI
 datos.gov.co       consulta   tipado     tendencia    narra     entrega
                              y limpia   (código)      (LLM)
```

**Separación dura entre el número y la palabra.** La tendencia (cambio en la ventana, máximo/mínimo, promedio, volatilidad, racha, movimientos fuertes) se calcula en `analytics.py`, código determinista y testeado. El LLM en `brief.py` recibe esas cifras ya hechas y solo las redacta. La regla está en el prompt y en el diseño: *usa solo los números que te paso, no inventes ni proyectes*. El LLM narra, no calcula. Una alucinación no puede mover la TRM.

**El LLM es opcional.** Sin `OPENAI_API_KEY` el comando funciona igual y entrega las cifras en plantilla. La inteligencia base es determinista; la IA es comodidad, no núcleo. Eso también deja el CI verde sin secretos.

**El prompt vive en un archivo de texto, no en el código.** `prompts/brief_es.txt` se edita sin tocar Python, y `TRM_BRIEF_PROMPT_PATH` permite apuntar a otro. El tono del narrador es un parámetro, no una constante compilada.

**Por capas pequeñas y aburridas.** `client` solo habla con la API. `models` solo tipa y limpia la fila cruda (el valor viene como string, la fecha como timestamp). `analytics` solo calcula sobre objetos limpios, sin red, por eso se testea en milisegundos. Cada pieza se entiende y se reemplaza sola.

### Trade-offs asumidos

- **Snapshot, no streaming.** Cada corrida es una foto de la ventana. Para alertas se programa `latest` o `brief` en cron; no montamos infraestructura de eventos para un primer usuario.
- **Racha y volatilidad simples.** La racha cuenta movimientos consecutivos en una dirección; la volatilidad es la desviación estándar de la ventana. No es un modelo cambiario, es una señal honesta para mirar.
- **Movimiento fuerte ≠ predicción.** Marcamos un cambio diario atípico frente a la ventana (z-score). Dice "esto se movió raro", no "esto va a seguir".
- **TRM por día hábil.** En fines de semana un valor rige hasta el siguiente hábil; trabajamos sobre `vigenciadesde` (fecha en que toma efecto) y no rellenamos días no hábiles.

## Instalación

```bash
pip install -e ".[dev]"
```

## Uso

```bash
# TRM vigente y su cambio frente a la lectura anterior
trm-watch latest

# Lectura de tendencia de los últimos 30 registros
trm-watch brief --limit 30

# Lectura de una ventana de fechas
trm-watch brief --since 2026-01-01 --until 2026-06-01
```

La lectura usa `OPENAI_API_KEY` si está presente; sin ella, entrega las cifras en plantilla. Para narrar con otro prompt: edita `prompts/brief_es.txt` o exporta `TRM_BRIEF_PROMPT_PATH`.

## Stack

Python 3.12 · httpx · Pydantic v2 · typer + rich · pytest · ruff · GitHub Actions. Los tests son deterministas y no tocan la red.

## Fuente

Tasa de Cambio Representativa del Mercado (TRM) — [datos.gov.co](https://www.datos.gov.co/resource/mcec-87by.json) (Socrata Open Data API, Superfinanciera). Serie histórica diaria.

## Autor

[Jotive](https://github.com/jotive) · [dev.jotive.com.co](https://dev.jotive.com.co)
