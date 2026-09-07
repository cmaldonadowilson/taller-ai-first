# CLAUDE.md

Este archivo le da contexto a Claude Code (claude.ai/code) para trabajar con el código de este repositorio.

## Arbitraje entre documentación y código

Cuando la documentación y el código se contradigan, **la documentación es la fuente de verdad**: el código es lo que está mal y hay que alinear.

**Avisa al usuario antes de actuar.** Expón la contradicción —qué dice cada lado, qué implicaría alinear el código, qué totales o comportamiento cambian— y espera respuesta. No apliques la corrección por tu cuenta.

Distingue contradicción de omisión. Si la doc simplemente no menciona algo que el código hace, es documentación incompleta, no un conflicto: la regla no pide borrar funcionalidad. Avisa igual, pero ahí lo que se corrige es la doc.

## Convenciones de nombres

**El código nuevo se escribe en inglés**: funciones, variables, parámetros, clases y constantes. `volume_discount()` en `descuentos.py` y `free_shipping_for_new_customer()` en `envio.py` ya cumplen la convención.

El código existente está mayoritariamente en español (`subtotal`, `costo_envio`, `total_con_descuentos`, `pedido`, `monto`). No lo renombres en masa: migra un nombre cuando ya estás tocando esa función por otra razón. Mientras dure la mezcla, ojo al navegar — `PROMOCIONES["volumen"]` apunta a `volume_discount`, así que buscar "volumen" no encuentra la implementación.

Hay identificadores que **no** se pueden traducir solos porque están atados a `datos/ejemplo.json`:

- Los campos de `Producto` (`sku`, `nombre`, `precio`) y de `Cupon` (`codigo`, `tipo`, `valor`) se construyen con `Producto(**p)` y `Cupon(**c)` en `datos.py`. Renombrarlos rompe la carga salvo que cambies el JSON en el mismo commit.
- Las claves de `PROMOCIONES` (`2x1`, `volumen`, `primera-compra`), las de `TRAMOS` (`metropolitana`, `regiones`, `extremo`) y los valores de `Cupon.tipo` (`porcentaje`, `monto`) son datos, no identificadores. Vienen del JSON como strings.

La prosa sigue en español: docstrings, comentarios, mensajes de commit y nombres de rama.

## Comandos

```sh
uv sync                                        # instalar (editable) + dependencias de dev
uv run pytest                                  # toda la suite
uv run pytest tests/test_descuentos.py -v      # un archivo
uv run pytest -k cupon_porcentual              # un test por subcadena del nombre
uv run python -m carrito total --pedido 42     # correr el CLI
```

Flags del CLI: `--pedido N` (obligatorio), `--detalle` (imprime cada línea del pedido), `--sin PROMO` (repetible; desactiva una promoción, las opciones salen de las claves de `PROMOCIONES`).

No hay linter ni formateador configurados. La única dependencia de dev es pytest, y no hay tabla `[tool.pytest.ini_options]` — pytest usa `pyproject.toml` solo como ancla de `rootdir`.

## Arquitectura

El cálculo es un pipeline de módulos sin estado. `resumen.resumen()` es el único orquestador; todo lo demás son funciones puras que reciben un `Pedido`.

```
precios.subtotal
  → descuentos.total_con_descuentos   (3 etapas, ver abajo)
    → impuestos.iva                   (sobre el monto ya descontado)
    → envio.costo_envio               (recibe el subtotal BRUTO más su IVA)
      → resumen.resumen               arma el dict del desglose
```

`resumen()` devuelve un `dict[str, int]` ordenado para presentación. La línea `"Descuentos"` solo aparece si hubo alguno, y su valor es **negativo**. `cli.py` lo formatea en columnas alineadas.

### El orden de los descuentos importa

`descuentos.total_con_descuentos()` tiene **tres** etapas, en este orden:

1. **Promociones** — se calculan todas contra el *subtotal* y se **suman**; no se encadenan. Dos promociones del 15% descuentan 30% del subtotal, no 27,75%.
2. **Cupones porcentuales**
3. **Cupones de monto fijo** — sobre lo que quedó de la etapa anterior.

Cambiar este orden cambia los totales. `tests/test_descuentos.py` fija las etapas 2 y 3 con un caso donde el orden inverso daría un resultado distinto.

Las promociones son un registro: el dict `PROMOCIONES` mapea la clave que aparece en el JSON a la función que la implementa. Agregar una promoción = escribir `funcion(pedido, monto) -> int` (devuelve el monto a descontar, no el total) y registrarla en el dict. El flag `--sin` del CLI toma sus opciones de ahí automáticamente.

### Dinero

Todo son pesos enteros (`int`), nunca float ni Decimal. `dinero.py` fija la política: cuando un cálculo produce decimales se redondea al peso más cercano, con el medio peso hacia arriba. Usa `dinero.porcentaje()` para cualquier cálculo porcentual nuevo.

### Datos

`datos.py` lee `datos/ejemplo.json` y arma los dataclasses de `modelo.py`. `cargar()` re-parsea el archivo completo en cada llamada — no hay caché.

**Depende del install editable.** `datos.ARCHIVO` resuelve `parents[2]` desde el archivo fuente, lo que sale del árbol del paquete, y `datos/ejemplo.json` no se incluye en el wheel (verificado con `uv build`). Funciona solo porque `uv sync` instala editable. Lo mismo vale para los tests: importan `carrito` sin `conftest.py` ni `pythonpath` gracias a ese install.

## Discrepancias conocidas entre docs y código

Verificadas en una auditoría. Aplica la regla de arbitraje de arriba: avisa antes de tocar cualquiera de estas.

**Contradicción** — la doc gana, se corrige el código:

- **`impuestos.iva()` trunca** (`int(monto * IVA / 100)`) en vez de redondear. `dinero.py` declara como política del sistema que todo cálculo con decimales se redondea al peso más cercano, e `impuestos.py` ni siquiera importa `dinero`. Alinearlo (usar `dinero.porcentaje(monto, IVA)`) **cambia totales ya emitidos**: difiere en 1 peso en varios montos, ej. 12.345 → 2.345 hoy vs 2.346 según la política.

**Omisiones de la doc** — el código hace algo que la doc no menciona; se corrige la doc, no el código:

- **El README describe solo dos etapas de descuento** (cupones % y monto fijo), omitiendo la de promociones. El docstring de `descuentos.py` y el de `tests/test_descuentos.py` repiten la misma omisión.
- **El README no menciona que `cliente_nuevo` da envío gratis siempre**, sin importar región ni monto (`envio.py`). El pedido 46 del JSON es región `extremo` y paga $0.
- **`envio.costo_envio()` cae silenciosamente al tramo `"regiones"`** para regiones desconocidas.

Código sin llamadores: `impuestos.con_iva()`, el dict `ETIQUETAS` y el import de `PROMOCIONES` en `resumen.py`, y el módulo `exportar.py` completo (los reportes se descartaron en favor de un sistema externo).

## Entorno y CI

`.tool-versions` declara Python 3.13.5 y uv 0.9.5. El workflow usa `setup-uv` con `version-file: .tool-versions`, que toma de ahí **ambas** versiones, así que CI corre en 3.13.5.

El venv local puede estar en otra versión (`requires-python = ">=3.12"` es laxo y no se queja). Si necesitas que coincidan: `uv venv --python 3.13.5 && uv sync`.

`astral-sh/setup-uv` publica tags mayores flotantes solo hasta `v7`; de `v8` en adelante hay que fijar la versión exacta, por eso el workflow dice `@v10.0.1`.

## Flujo de trabajo

El repo trabaja con ramas y PRs — `main` recibe merges, no commits directos. Los nombres de rama son kebab-case descriptivo (`fix-orden-cupones`, `test-orden-descuentos`, `ci-workflow-tests`). Los mensajes de commit van en español, con el asunto en infinitivo ("Aplicar los cupones porcentuales antes de los de monto fijo") y un cuerpo que explica el porqué.
