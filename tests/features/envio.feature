# language: es

# Criterios de aceptación de la regla de envío gratis.
#
# Las cuatro decisiones de negocio que fijan esta regla — no se derivan del
# código, lo mandan:
#
#   1. El umbral se evalúa ANTES del descuento.
#   2. El IVA SÍ cuenta para el umbral.
#   3. Las promociones descuentan igual que los cupones. Como por (1) el umbral
#      se mira antes del descuento, "igual" significa que ninguna de las dos
#      baja la base: promoción y cupón se tratan idéntico.
#   4. Con $50.000 justos el envío ES GRATIS. El umbral es inclusivo (>=).
#
# De (1) + (2) sale la única fórmula posible para la base del umbral: si los
# descuentos no cuentan, el IVA que cuenta es el del subtotal bruto.
#
#     base del umbral = subtotal + 19% del subtotal
#
# El envío se decide con esa base. El monto que el cliente paga —con sus
# promociones y sus cupones— no entra en la decisión.

Característica: Envío gratis por monto del pedido

  Sobre cierto monto el envío no se cobra. El monto que se mira es lo que el
  pedido vale bruto y con IVA, antes de cualquier rebaja: un pedido grande al
  que un cupón le baja mucho el precio sigue siendo un pedido grande.

  Aparte del monto, el cliente nuevo nunca paga envío.

  Antecedentes:
    Dado que el umbral de envío gratis es de $50.000
    Y que el IVA es de 19%
    Y que el envío cuesta $3.990 en "metropolitana", $5.990 en "regiones" y $12.990 en "extremo"

  # Los tres subtotales del medio están elegidos para caer en $49.999, $50.000
  # y $50.001 exactos de base. Sus IVA (7.983,04 / 7.983,23 / 7.983,42) quedan
  # todos en $7.983 tanto si se trunca como si se redondea, así que estos
  # bordes no dependen de cómo se resuelva ese detalle.
  Esquema del escenario: El envío se decide por el monto bruto con IVA
    Dado un pedido en la región "metropolitana" con estas líneas:
      | producto           | precio     | cantidad |
      | Producto de prueba | <subtotal> | 1        |
    Cuando calculo el resumen del pedido
    Entonces el IVA es <iva>
    Y la base del umbral es <base>
    Y el envío es <envio>

    Ejemplos: Los cuatro bordes del umbral
      | caso           | subtotal | iva  | base  | envio |
      | lejos debajo   | 20000    | 3800 | 23800 | 3990  |
      | justo debajo   | 42016    | 7983 | 49999 | 3990  |
      | justo el borde | 42017    | 7983 | 50000 | 0     |
      | justo encima   | 42018    | 7983 | 50001 | 0     |

  # Subtotal 50.000 → base 50.000 + 9.500 = 59.500, sobre el umbral: gratis.
  # El cupón baja lo que se paga a 25.000, pero eso no toca la base.
  # Si el umbral se evaluara DESPUÉS del descuento, la base sería
  # 25.000 + 4.750 = 29.750 y este pedido pagaría $3.990.
  Escenario: Un cupón baja el precio pero no la base del umbral
    Dado un pedido en la región "metropolitana" con estas líneas:
      | producto           | precio | cantidad |
      | Producto de prueba | 50000  | 1        |
    Y un cupón "OTONO50" de tipo "porcentaje" con valor 50
    Cuando calculo el resumen del pedido
    Entonces el monto con descuentos es 25000
    Y la base del umbral es 59500
    Y el envío es 0

  # Mismo subtotal, mismo monto pagado y mismo envío que el escenario del
  # cupón: así se ve la decisión 3. La promoción 2x1 sobre 4 unidades regala
  # 2 × $12.500 = $25.000, y la base sigue siendo 50.000 + 9.500 = 59.500.
  Escenario: Una promoción baja el precio pero tampoco la base del umbral
    Dado un pedido en la región "metropolitana" con estas líneas:
      | producto           | precio | cantidad |
      | Cuaderno de prueba | 12500  | 4        |
    Y la promoción "2x1" activa
    Cuando calculo el resumen del pedido
    Entonces el monto con descuentos es 25000
    Y la base del umbral es 59500
    Y el envío es 0

  # Base 12.500 + 2.375 = 14.875, muy debajo del umbral, y la región más cara.
  # Sin la regla del cliente nuevo este pedido pagaría $12.990.
  Escenario: El cliente nuevo no paga envío aunque el pedido sea chico
    Dado un pedido en la región "extremo" con estas líneas:
      | producto           | precio | cantidad |
      | Producto de prueba | 12500  | 1        |
    Y que el cliente es nuevo
    Cuando calculo el resumen del pedido
    Entonces la base del umbral es 14875
    Y el envío es 0
