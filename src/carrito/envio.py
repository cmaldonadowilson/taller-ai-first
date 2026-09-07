"""Costo de envío según la región de destino.

Sobre cierto monto el envío no se cobra. El umbral se compara contra lo que el
pedido vale bruto y con IVA, antes de cualquier rebaja: ni los cupones ni las
promociones bajan esa base. Quien la calcula y la entrega es
`resumen.resumen()`. Los criterios están en tests/features/envio.feature.
"""

TRAMOS = {
    "metropolitana": 3990,
    "regiones": 5990,
    "extremo": 12990,
}

UMBRAL_ENVIO_GRATIS = 50000


def free_shipping_for_new_customer(order) -> bool:
    """Los clientes nuevos no pagan envío en su primera compra."""
    return order.cliente_nuevo


def costo_envio(pedido, threshold_base: int) -> int:
    if free_shipping_for_new_customer(pedido):
        return 0
    if threshold_base >= UMBRAL_ENVIO_GRATIS:
        return 0
    return TRAMOS.get(pedido.region, TRAMOS["regiones"])
