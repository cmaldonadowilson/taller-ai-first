"""El resumen del pedido, desglosado."""

from carrito.descuentos import PROMOCIONES, total_con_descuentos
from carrito.envio import costo_envio
from carrito.impuestos import iva
from carrito.precios import subtotal


ETIQUETAS = {
    "2x1": "Promoción 2x1",
    "volumen": "Descuento por volumen",
    "primera-compra": "Primera compra",
}


def resumen(pedido) -> dict[str, int]:
    """El desglose del pedido, en orden de presentación."""
    base = subtotal(pedido)
    descontado = total_con_descuentos(pedido)
    impuesto = iva(descontado)
    # El envío se decide sobre el bruto con IVA, no sobre lo que se paga: los
    # descuentos no bajan el umbral. Ver tests/features/envio.feature.
    threshold_base = base + iva(base)
    envio = costo_envio(pedido, threshold_base)

    lineas = {"Subtotal": base}
    if descontado != base:
        lineas["Descuentos"] = descontado - base
    lineas["IVA"] = impuesto
    lineas["Envío"] = envio
    lineas["Total"] = descontado + impuesto + envio
    return lineas
