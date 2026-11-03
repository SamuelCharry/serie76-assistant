# Dominio y decisiones sobre datos

## Conceptos ya explicados a Samuel

- Serie 76: familia de actuadores eléctricos para mover válvulas y compuertas.
- Base Part Number: referencia completa de un modelo, no número de serie de una unidad física. No adivinar prestaciones decodificando caracteres.
- Weatherproof y Explosionproof: tipos de carcasa con usos distintos. Un marcado genérico no demuestra aptitud universal para cualquier atmósfera peligrosa.
- CSA es certificación según alcance; CE/UKCA son marcados de conformidad; IECEx/ATEX se relacionan con atmósferas explosivas. No transferir todas las siglas del resumen a cada modelo.
- Alimentación: voltaje, AC/DC y fases. Más voltaje no significa mayor torque.
- On/Off: movimiento hacia extremos. Modulante: posiciones intermedias. Apertura porcentual no equivale necesariamente al mismo porcentaje de caudal.
- Torque: capacidad de giro, Nm o in-lb. No es velocidad.
- Operating Speed: la tabla expresa tiempo en segundos para el recorrido; menos segundos significa más rápido. El resumen contextual describe 90 grados.
- FLA: corriente a carga nominal máxima. LRA: corriente con rotor detenido/bloqueado y motor alimentado, no potencia ni duración.
- Motor Power: potencia nominal en W; no asumir consumo eléctrico total sin especificación.
- Duty cycle S4: proporción de funcionamiento/reposo bajo condiciones del fabricante, con efecto de arranques. No convertir 40 % en cualquier tiempo arbitrario de marcha continua.
- MTPW fue una abreviatura inventada por el usuario para Motor Power, no un campo oficial del PDF.

## Resultado de extracción visual

Ver [análisis completo](../docs/DATOS.md). Cuatro páginas, siete tablas, 68 códigos únicos: 64 con cifras y cuatro N/A explícitos.

| Tabla | Contenido | Filas |
|---|---|---:|
| p1_t1 | Weatherproof, 110 V AC monofásico, On/Off y modulante | 11 |
| p1_t2 | Weatherproof, 220 V AC monofásico, On/Off y modulante | 16 |
| p2_t1 | Weatherproof, 220 V AC trifásico, columnas compartidas | 11, cuatro N/A |
| p3_t1 | Explosionproof, 24 V AC/DC, On/Off | 5 |
| p3_t2 | Explosionproof, 24 V DC, modulante | 5 |
| p4_t1 | Explosionproof, 110 V AC monofásico | 10 |
| p4_t2 | Explosionproof, 220 V AC monofásico | 10 |

Los PDF se renderizaron y transcribieron visualmente. Se comprobaron conteos, códigos únicos, porcentajes, N/A y excepciones; no hubo segunda transcripción independiente. No tratar esa referencia como infalible.

## Qué guardar

Identidad y carcasa; tensión/corriente/fases; potencia; prestaciones por servicio (torque en ambas unidades publicadas, duty S4, ciclos/h y arranques/h); tiempo/FLA/LRA por frecuencia cuando estén separados; estado del dato; fuente página/tabla/fila; notas, tolerancias y excepciones.

Identidad -> valores por servicio y frecuencia -> evidencia. Todavía no se diseñaron tablas SQL ni migraciones. El CSV ancho es una representación de revisión, no el esquema final.

## Trampas ya encontradas

1. 24 V On/Off es AC/DC; 24 V modulante es solo DC y usa otros códigos.
2. Existe 220 V trifásico aunque el resumen general no lo enumere.
3. Cuatro referencias -11330C00/A muestran N/A. No inferir inexistencia comercial ni rellenar con otra variante.
4. Potencia tiene celdas combinadas: heredar solo según alcance visual comprobado.
5. Cinco referencias de tamaños 6 y 7, sufijo -11320000/A, tienen excepción explícita «not CSA Certified». Guardar asterisco como nota, no como parte del identificador normalizado, conservando también el original.
6. La tabla trifásica no separa torque/duty por servicio; conservar columnas compartidas y nota 5, sin inventar dos mediciones.
7. Guardar ambos torques publicados, sin reemplazar por conversión exacta. La revisión del PDF durante el benchmark corrigió la referencia de 764X30-11320000/A: publica 5520 in-lb y **640 Nm**, no 620 Nm. Ver docs/OCR_REFERENCE_REVIEW.md.
8. Las páginas explosionproof dicen CSA y clasificación de área; no añadir ATEX/IECEx desde el resumen genérico.
9. null indica campo no publicado por separado; source_NA identifica N/A explícito. Nunca cero.

Ejemplo verificado visualmente: 761A00-11300000/A tiene 80 Nm On/Off y 65 Nm modulante; 17 s a 60 Hz y 20 s a 50 Hz; potencia 15 W. Pedir mínimo 70 Nm produce decisiones distintas según servicio.
