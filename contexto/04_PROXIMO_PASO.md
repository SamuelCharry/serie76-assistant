# Próximo bloque: conseguir el primer OCR real

No implementar todo el producto en esta continuación. Completar un bloque explicable y revisar resultados con Samuel.

## Antes de actuar

1. Abrir clon principal y leer AGENTS.md. Ejecutar git status y revisar cambios del usuario. No sobrescribirlos.
2. Consultar issues #1 y #2 y estado actual del entorno. El bloqueo Docker descrito es histórico, puede haber cambiado.
3. Confirmar .venv y PDF. No gastar OpenRouter: la prueba prevista es local.

## Camino Docker, si el motor está listo

Desde la raíz del repositorio:

```powershell
docker info
```

Si falla, inspeccionar causa de forma acotada. No resetear Docker, borrar distribuciones WSL, volúmenes o reiniciar el PC sin autorización específica. Alternativa: instalar/configurar Tesseract local para avanzar con OCR, conservando pendiente Docker para el backend.

Preparar .env desde .env.example solo si no existe. Usar contraseña local de desarrollo; no copiar una clave real al repo. Compose necesita POSTGRES_PASSWORD incluso en el perfil OCR. Elegir carpetas de salida nuevas:

```powershell
docker compose --profile ocr build ocr
docker compose --profile ocr run --rm --no-deps ocr --page 1 --psm 3 --out data/ocr/page1-psm3-first
docker compose --profile ocr run --rm --no-deps ocr --page 1 --psm 6 --out data/ocr/page1-psm6-first
```

## Camino local, si Tesseract está disponible

```powershell
.\.venv\Scripts\python.exe scripts/ocr_probe.py --page 1 --psm 3 --out data/ocr/page1-local-first
```

Se admite --tesseract-cmd con la ruta real o TESSERACT_CMD como variable del proceso. El script no carga .env por sí solo.

## Qué verificar

- Debe existir texto OCR y TSV, no solo PNG. Manifest debe decir ocr_completed_unvalidated.
- Comparar las 11 filas de p1_t1 contra el PDF y referencia manual; la página incluye también p1_t2, no mezclar resultados.
- Revisar códigos, ceros/letras, decimales, separadores de miles, encabezados 50/60 Hz y On/Off/modulante, y potencia de celdas combinadas.
- Registrar errores concretos de cada configuración. La confianza de Tesseract no sustituye validación.
- No insertar OCR crudo en DB ni afirmar precisión global por algunas filas correctas.

## Cierre de este bloque

Entregar evidencia de OCR real y una comparación breve de fallos. Actualizar checklist de #2 solo en lo probado y guardar reporte reproducible. Después decidir con Samuel cómo reconstruir las tablas. La ingestión completa, SQL, agente y app siguen siendo bloques posteriores.
