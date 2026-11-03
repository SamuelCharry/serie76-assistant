# Serie 76: tablas extraídas y datos que debemos guardar

Fuente: series_76_electric_data.pdf, cuatro páginas, copia localizada en data/raw.

## Alcance y método

Transcripción visual de las siete tablas completas a partir de las páginas renderizadas. Se conservaron los números publicados, sin sustituirlos por conversiones calculadas. Se expandieron únicamente celdas combinadas cuyo alcance se observa en la tabla (potencia del motor y bloque N/A). Esta entrega es una extracción revisada para analizar el modelo de datos; no constituye el script automático de ingestión que exige el assessment.

Archivos: serie76_tablas_extraidas.csv (filas y valores) y serie76_tablas_extraidas.json (mismos datos, encabezados, notas, método y huella SHA-256 del PDF).

Controles ejecutados: 68 filas y códigos únicos; conteos por tabla; cuatro filas N/A; cinco excepciones CSA; porcentajes en rango; potencia presente en las 64 filas con cifras. La revisión no incluye una segunda transcripción independiente ni aclaraciones del fabricante. Estos controles estructurales no demuestran por sí solos exactitud numérica.

## Inventario

| Página / tabla | Carcasa | Alimentación | Presentación del servicio | Filas |
|---|---|---|---|---:|
| 1 / 1 | Weatherproof | 110 V AC monofásica | On/Off y modulante, columnas separadas | 11 |
| 1 / 2 | Weatherproof | 220 V AC monofásica | On/Off y modulante, columnas separadas | 16 |
| 2 / 1 | Weatherproof | 220 V AC trifásica | Un solo juego de torque y duty cycle; nota 5 menciona ambos servicios | 11, incluidas 4 N/A |
| 3 / 1 | Explosionproof | 24 V AC/DC | On/Off | 5 |
| 3 / 2 | Explosionproof | 24 V DC | Modulante | 5 |
| 4 / 1 | Explosionproof | 110 V AC monofásica | On/Off y modulante, columnas separadas | 10 |
| 4 / 2 | Explosionproof | 220 V AC monofásica | On/Off y modulante, columnas separadas | 10 |

Son 68 referencias distintas listadas, 64 con cifras. Las cuatro N/A se conservan como referencias con datos explícitamente no disponibles en esta fuente, sin afirmar que no existan comercialmente.

## Qué guardar de un actuador

### 1. Identidad y alimentación

- Número de parte completo: texto, conservando ceros, guion y sufijo /A. El asterisco de nota se guarda aparte y también se conserva la cadena original.
- Familia: Serie 76 (metadato del catálogo).
- Carcasa: weatherproof o explosionproof, tomada del encabezado.
- Tensión nominal en voltios.
- Tipo de corriente: AC, DC o AC/DC, según el encabezado específico.
- Número de fases cuando esté indicado. No inventarlo en las tablas de 24 V.
- Potencia nominal del motor en W. No etiquetarla automáticamente como consumo eléctrico total del actuador.
- Estado del dato: reportado o N/A explícito.

### 2. Prestaciones por servicio

- Servicio: On/Off, modulante o valores compartidos según presentación de la fuente.
- Torque en Nm y en in-lb, conservando ambos valores publicados.
- Duty cycle S4 en porcentaje.
- Ciclos por hora y arranques por hora como campos distintos.
- Alcance del encabezado: en las tablas mixtas los ciclos acompañan las columnas On/Off y los arranques las de modulación. Conservar esa asociación; no intercambiar ni deducir uno a partir del otro.

La tabla trifásica no separa torque y duty cycle por servicio. Mantener sus valores compartidos y la nota 5 textual; no inventar una reducción de torque modulante ni presentarlos como dos mediciones independientes.

### 3. Prestaciones eléctricas y tiempo por frecuencia

- Frecuencia: 50 o 60 Hz cuando la tabla la distingue.
- Tiempo de operación en segundos (el resumen contextual lo describe como recorrido de 90 grados).
- Corriente FLA en amperios.
- Corriente LRA en amperios.

En las tablas de 24 V esos tres valores no se desglosan por frecuencia. Guardarlos sin frecuencia especificada, no duplicarlos como mediciones de 50 y 60 Hz. Para DC la frecuencia de red no aplica; para la opción AC de 24 V no está especificada en esa tabla.

### 4. Evidencia, notas y restricciones

- Documento, huella del archivo, página, tabla, fila y encabezado de origen.
- Método de extracción y estado de revisión.
- Certificaciones/marcados tal como aparecen y sus excepciones por modelo.
- Clasificación de área peligrosa textual para las páginas explosionproof.
- Notas compartidas: tolerancia de tensión +/-10 %, tolerancia de frecuencia +/-5 %, referencia de duty cycle IEC 60034-1, FLA a máxima carga nominal, LRA con rotor bloqueado y tasas por hora basadas en torque nominal.

Las notas se guardan con su alcance documental. Su presencia no justifica aplicar una frecuencia a DC ni ampliar la clasificación a ambientes no listados. No hace falta duplicarlas físicamente en cada registro: se pueden vincular por tabla o página.

## Ejemplo concreto

Modelo 761A00-11300000/A, página 1, tabla de 110 V:

| Campo | Valor |
|---|---|
| Carcasa | Weatherproof |
| Alimentación | 110 V AC, monofásica |
| Potencia del motor | 15 W |
| Torque On/Off | 700 in-lb / 80 Nm |
| Duty cycle On/Off | 40 % S4 |
| Ciclos por hora | 36 |
| Torque modulante | 580 in-lb / 65 Nm |
| Duty cycle modulante | 40 % S4 |
| Arranques por hora | 960 |
| Tiempo a 60 / 50 Hz | 17 / 20 s |
| FLA a 60 / 50 Hz | 1.2 / 1.1 A |
| LRA a 60 / 50 Hz | 1.4 / 1.3 A |

Una búsqueda de al menos 70 Nm puede aceptar este modelo por torque para On/Off, pero no para modulación. Falta evaluar las demás restricciones del usuario antes de recomendarlo.

## Hallazgos que no debemos perder

1. **24 V no implica AC/DC en todos los modelos.** On/Off es AC/DC; modulante es DC y usa otra referencia.
2. **220 V también puede ser trifásico.** El resumen general no enumera todas las variantes de estas tablas.
3. **N/A no es cero ni un valor inventable.** Las referencias 761A00, 761B00, 762A00 y 762B00 con sufijo -11330C00/A muestran un bloque N/A. No se puede afirmar que cumplen requisitos con datos de otra variante.
4. **La potencia utiliza celdas combinadas.** Una celda visualmente vacía puede heredar el valor de su grupo, pero solo si el diseño de la tabla lo demuestra.
5. **Hay cinco excepciones CSA.** 766A00, 766B00, 767A00, 767B00 y 767C00 con sufijo -11320000/A tienen asterisco: tamaños 6 y 7 no certificados CSA. El encabezado general no anula la excepción.
6. **Explosionproof no demuestra automáticamente ATEX o IECEx.** Las páginas eléctricas dicen CSA y publican una clasificación de área; no añadir certificaciones desde el resumen genérico.
7. **Conservar las dos unidades de torque publicadas.** Hay redondeos y valores que no se corresponden con una conversión exacta. Ejemplo: 764X30-11320000/A publica 5520 in-lb y 620 Nm en modulación. No corregir silenciosamente a partir de otra fila o de una conversión.
8. **El código completo distingue variantes.** No buscar únicamente por el prefijo 761A00; distintas alimentaciones tienen códigos diferentes.

## Lectura de los archivos extraídos

El CSV es una representación de revisión, amplia y cercana a las tablas; no es un diseño final de base de datos. Los prefijos on_off_, modulating_ y shared_ distinguen el alcance del valor. Los sufijos _60hz y _50hz conservan la frecuencia; unqualified identifica valores sin desglose de frecuencia en la fuente. Las unidades aparecen en los nombres de campos.

Un vacío en CSV o null en JSON significa que ese campo no se publica por separado en esa estructura. No demuestra que la característica no exista. data_status=source_NA distingue las cuatro filas con N/A explícito. En JSON se conservan las notas comunes y de clasificación de áreas que no caben cómodamente en el CSV.

## Decisión propuesta

Guardar una identidad por número de parte, vinculada a sus valores por servicio y por frecuencia, junto con la fuente y sus notas. No guardar un único torque, una única corriente o una única velocidad por actuador: se perderían condiciones necesarias para recomendar correctamente.
