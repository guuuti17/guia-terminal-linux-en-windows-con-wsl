# Pokémon TCG Shop — afiliación en TikTok Shop España

Sistema en Python para: importar productos del Mercado de Afiliados, clasificarlos, generar guiones
comerciales, voz, vídeos verticales con subtítulos, calendario de publicación y control de ingresos y costes.

Proyecto independiente: vive en esta carpeta y no comparte nada con el resto del repositorio.
La investigación comercial, legal y de herramientas está en [docs/INVESTIGACION.md](docs/INVESTIGACION.md).

## Instalación (una vez)

```bash
cd pokemon-tcg-shop
pip install -r requirements.txt     # instala requests, Pillow y python-dotenv
cp .env.ejemplo .env                # crea tu archivo de claves; edítalo y pon tu clave de ElevenLabs
python main.py voces-listar         # gratis: muestra tu cuota y las voces; copia un ID a ELEVENLABS_VOICE_ID en .env
```

Hace falta `ffmpeg` instalado (`sudo apt install ffmpeg`).

## Flujo por producto

```bash
# 1. Copia la plantilla y rellénala con datos REALES de la ficha en la app (ver docs, sección 3)
cp productos/plantilla_productos.csv productos/mis_productos.csv

# 2. Importa las fichas y mira la clasificación de oportunidades
python main.py importar productos/mis_productos.csv
python main.py ranking

# 3. Guarda fotos o clips reales y autorizados del producto en productos/medios/<ID>/
#    (fotos del vendedor o tu grabación de la muestra; jpg, png, mp4 o mov)

# 4. Genera los guiones (5 para accesorios, 2 para producto sellado)
python main.py guiones --producto 1

# 5. Voz: primero enseña el coste; solo gasta si añades --confirmar-gasto
python main.py voces --producto 1
python main.py voces --producto 1 --confirmar-gasto

# 6. Monta los vídeos 1080x1920 con subtítulos
python main.py videos --producto 1

# 7. Crea el calendario (2 al día) y una carpeta por publicación en publicaciones/lotes/
python main.py preparar --producto 1 --inicio 2026-11-16
```

Cada carpeta de `publicaciones/lotes/` contiene `video.mp4`, `descripcion.txt` y `pasos.txt` con los
toques exactos en la app de TikTok. Subir el vídeo y enlazar el producto es el único paso manual:
TikTok no ofrece una vía oficial abierta para hacerlo por API (detalle en docs, sección 4).

## Rutina diaria (~15 minutos)

```bash
python main.py estado                                              # qué toca publicar hoy
python main.py publicado --pub 3 --id-publicacion ENLACE_DEL_VIDEO  # tras publicar
python main.py resultado --pub 3 --ventas 2 --comision 6.30         # totales que muestra TikTok Shop
python main.py coste --concepto "ElevenLabs noviembre" --tipo suscripcion --importe 4.70
python main.py informe                                             # ingresos, costes y beneficio
```

## Barreras que el sistema aplica solo

- Rechaza al importar productos `no_oficial` (réplicas, proxies, arte Pokémon sin licencia).
- No genera guiones de fichas sin `verificado_el` ni con menos de 3 características verificadas.
- Los guiones no dicen precios y se bloquean si contienen promesas de inversión, cartas garantizadas,
  valor de cartas, urgencia falsa o superlativos de precio (`configuracion/reglas.py`).
- El producto sellado siempre lleva idioma y el aviso «El contenido de los sobres es aleatorio».
- Nunca genera imágenes de cartas ni de productos: si falta material real, el vídeo sale marcado como
  BORRADOR y no se puede preparar para publicar.
- No gasta créditos sin `--confirmar-gasto` y registra cada gasto en la tabla de costes.
- Un vídeo no puede publicarse dos veces ni dos publicaciones compartir hueco o identificador.

## Estructura

```
main.py                     órdenes de línea de comandos
bd.py                       esquema SQLite (negocio.sqlite3)
configuracion/              ajustes y reglas de cumplimiento
productos/                  importación, ranking, plantilla CSV y medios reales
guiones/                    plantillas de vídeo por categoría
voces/                      ElevenLabs
generador/                  montaje con ffmpeg
publicaciones/              calendario y paquetes de publicación
analisis/                   informe económico
tests/                      python -m unittest discover tests
```

## Pendiente (fase 2, cuando lo autorices)

- Fondos ambientales con Kling para las escenas sin producto.
- Publicación por la Content Posting API si decides crear y auditar una app propia de TikTok.
