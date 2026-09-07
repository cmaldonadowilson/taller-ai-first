"""Traducción a pytest-bdd de tests/features/envio.feature.

Cada escenario arma su propio Pedido con `carrito.modelo`; nada sale de
datos/ejemplo.json.

Sobre el step "la base del umbral es N": la spec llama "base del umbral" al
monto contra el que se decide el envío, así que el test observa el monto que
`resumen()` le entrega a `costo_envio()`. Calcular la fórmula aparte dentro
del test no probaría nada del sistema. El espía va sobre
`carrito.resumen.costo_envio` porque ahí es donde resumen.py dejó ligado el
nombre con su `from carrito.envio import costo_envio`. Si el arreglo termina
moviendo el cálculo de la base adentro de `costo_envio()`, hay que reapuntar
este step al nuevo punto de observación.
"""

import pytest
from pytest_bdd import given, parsers, scenarios, then, when

import carrito.resumen
from carrito.descuentos import total_con_descuentos
from carrito.envio import TRAMOS, UMBRAL_ENVIO_GRATIS
from carrito.impuestos import IVA
from carrito.modelo import Cupon, Linea, Pedido, Producto
from carrito.resumen import resumen

scenarios("features/envio.feature")


def pesos(text: str) -> int:
    """Convierte "$50.000" en 50000. El punto es separador de miles."""
    return int(text.replace("$", "").replace(".", ""))


@pytest.fixture
def threshold_base(monkeypatch):
    """Registra el monto contra el que se decide el envío."""
    seen = {}
    original = carrito.resumen.costo_envio

    def spy(order, amount):
        seen["amount"] = amount
        return original(order, amount)

    monkeypatch.setattr(carrito.resumen, "costo_envio", spy)
    return seen


# --- Antecedentes: las constantes que la spec da por sentadas ---------------


@given(parsers.parse("que el umbral de envío gratis es de ${threshold}"))
def free_shipping_threshold(threshold):
    assert UMBRAL_ENVIO_GRATIS == pesos(threshold)


@given(parsers.parse("que el IVA es de {rate:d}%"))
def vat_rate(rate):
    assert IVA == rate


@given(
    parsers.parse(
        'que el envío cuesta ${metro} en "metropolitana", '
        '${regions} en "regiones" y ${far} en "extremo"'
    )
)
def shipping_tiers(metro, regions, far):
    assert TRAMOS == {
        "metropolitana": pesos(metro),
        "regiones": pesos(regions),
        "extremo": pesos(far),
    }


# --- El pedido del escenario ------------------------------------------------


@given(
    parsers.parse('un pedido en la región "{region}" con estas líneas:'),
    target_fixture="order",
)
def order_with_lines(region, datatable):
    """La primera fila del datatable es el encabezado."""
    header, *rows = datatable
    column = {name: index for index, name in enumerate(header)}
    lines = [
        Linea(
            producto=Producto(
                sku=f"TEST-{number}",
                nombre=row[column["producto"]],
                precio=int(row[column["precio"]]),
            ),
            cantidad=int(row[column["cantidad"]]),
        )
        for number, row in enumerate(rows, start=1)
    ]
    return Pedido(numero=1, lineas=lines, region=region)


@given(parsers.parse('un cupón "{code}" de tipo "{kind}" con valor {value:d}'))
def add_coupon(order, code, kind, value):
    order.cupones.append(Cupon(codigo=code, tipo=kind, valor=value))


@given(parsers.parse('la promoción "{promo}" activa'))
def enable_promo(order, promo):
    order.promociones.append(promo)


@given("que el cliente es nuevo")
def new_customer(order):
    order.cliente_nuevo = True


# --- Cálculo ----------------------------------------------------------------


@when("calculo el resumen del pedido", target_fixture="breakdown")
def compute_breakdown(order, threshold_base):
    """`threshold_base` va como parámetro para que el espía quede puesto antes."""
    return resumen(order)


# --- Verificaciones ---------------------------------------------------------


@then(parsers.parse("el IVA es {expected:d}"))
def check_vat(breakdown, expected):
    assert breakdown["IVA"] == expected


@then(parsers.parse("el monto con descuentos es {expected:d}"))
def check_discounted_amount(order, expected):
    assert total_con_descuentos(order) == expected


@then(parsers.parse("la base del umbral es {expected:d}"))
def check_threshold_base(threshold_base, expected):
    assert threshold_base["amount"] == expected


@then(parsers.parse("el envío es {expected:d}"))
def check_shipping_cost(breakdown, expected):
    assert breakdown["Envío"] == expected
