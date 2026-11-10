# Investigación comercial — 10 de noviembre de 2026

Cada dato lleva su nivel de certeza: **Confirmado** (fuente oficial o comprobado en esta sesión),
**Fuentes secundarias** (blogs que coinciden o discrepan) o **Sin verificar**.

> **Límite de esta investigación.** El Mercado de Afiliados de TikTok Shop solo se ve con sesión
> iniciada en una cuenta de creador, y la red de esta sesión bloquea los dominios de TikTok,
> Kalodata y FastMoss. Por eso **no hay en este documento ni un precio, comisión o cifra de ventas
> de un producto concreto de TikTok Shop España**: no los he podido ver y no los invento.
> La sección 3 explica cómo conseguirlos tú en unos 10 minutos.

## 1. Condiciones de afiliación en TikTok Shop España

| Punto | Lo que se sabe | Certeza |
|---|---|---|
| Seguidores mínimos | TikTok no publica una cifra oficial para España. Los blogs citan 1.000, 1.500, 2.000 y 5.000. La más repetida para España es **1.500**. | Fuentes secundarias, contradictorias |
| Otros requisitos | Mayor de 18 años, cuenta de España, cumplir normas, haber publicado en los últimos 28 días. | Fuentes secundarias |
| Comisión de afiliado | La fija **cada vendedor** por producto (rango 1 %–80 %). No hay una comisión «de categoría». | Fuentes secundarias coincidentes |
| Comisión de plataforma al vendedor | Subió del 5 % al 9 % en la UE el 8-ene-2026 (coleccionables incluidos). Reduce el margen que el vendedor puede ceder al afiliado. | Fuentes secundarias coincidentes |
| Peso de los afiliados | ~70 % del GMV estimado de TikTok Shop España pasa por afiliados (estimación modelada, no oficial). | Fuente secundaria única |

**Qué hacer:** abre TikTok > Perfil > menú ☰ > *TikTok Studio* > *TikTok Shop para creadores*. La app te
dice si tu cuenta es elegible y qué te falta. Es la única fuente fiable. Si no llegas al mínimo de
seguidores, el contenido de «coleccionismo» de este sistema sirve igual para crecer hasta alcanzarlo.

## 2. Restricciones de la categoría (importan mucho en Pokémon)

- **Sobres «sorpresa», mystery boxes y lotes sorpresa de cartas** son productos **restringidos** en la
  política de la UE (el vendedor necesita cumplir requisitos específicos). — Confirmado en el índice
  del Seller Center UE; no he podido leer el texto completo.
- **Cartas graduadas**: categoría solo por invitación en Reino Unido; en la UE, sin verificar.
- **Mecánicas de azar** (ruletas, «breaks», rascas) están prohibidas o muy restringidas. — Fuentes secundarias.
- **IA**: el contenido con IA debe etiquetarse y **no puede alterar el producto** (tamaño, color,
  contenido, prestaciones). Algunas marcas prohíben IA en su programa de afiliados. — Fuentes secundarias coincidentes.

Consecuencia práctica: el producto sellado oficial lo venden pocos vendedores autorizados, con margen
estrecho; los accesorios tienen menos trabas y más margen para comisión.

## 3. Los 5 candidatos para empezar

Clasificación por **tipo de producto**, con el razonamiento. La puntuación real la calcula
`python main.py ranking` cuando importes fichas con datos reales.

| # | Tipo | Por qué | Riesgo principal | Estado |
|---|---|---|---|---|
| 1 | **Álbum/carpeta de 9 bolsillos con cremallera** (genérico o con licencia) | Compra por impulso, regalo de Navidad/Reyes sin acertar expansión ni idioma, muy fácil de enseñar sin rostro, no depende de stock de lanzamientos | Muchos álbumes baratos usan arte Pokémon **sin licencia**: esos se descartan | Hipótesis razonada |
| 2 | **Fundas + toploaders** (packs de protección) | Consumible, recompra, encaja con todo el contenido de «cómo proteger cartas» | Precio bajo = comisión baja por venta | Hipótesis razonada |
| 3 | **Caja de Entrenador Élite de Megaevolución-Dominio Delta** (en español) | Expansión actual (salió el 6-nov-2026, confirmado por Pokémon). Demanda alta | Margen estrecho, comisión probablemente baja; exige vendedor fiable y producto precintado | Producto existe; presencia en afiliados **sin verificar** |
| 4 | **Productos de Celebración 30.º Aniversario** (minilatas, paquetes de sobres) | Máximo interés de coleccionistas ahora mismo | Stock escaso y reventa: es probable que no haya comisión o que se agote | Producto existe; presencia en afiliados **sin verificar** |
| 5 | **Maletín / caja de almacenamiento / expositor** | Ticket más alto que el álbum, mismo ángulo de regalo | Menos demanda de búsqueda | Hipótesis razonada |

**Producto elegido para el primer lote: el nº 1 (álbum de 9 bolsillos con cremallera).** Es el único que
cumple a la vez: se puede promocionar sin comprar inventario ni abrir sobres, no tiene restricciones
de categoría, admite vídeo sin rostro con fotos del vendedor o una muestra, y llega en plena campaña
de Black Friday (27-nov) y Navidad. No es el de mayor demanda (ese sería el sellado), es el de mayor
potencial **verificable y ejecutable hoy**.

### Cómo conseguir los datos reales (10 minutos, una vez)

1. TikTok > *TikTok Shop para creadores* > **Mercado de afiliados** (o *Añadir productos*).
2. Busca: `álbum cartas pokemon`, `carpeta cartas 9 bolsillos`, `fundas cartas`, `toploader`,
   `caja entrenador élite`, `pokemon tcg`.
3. De cada producto interesante apunta en `productos/mis_productos.csv` (copia de la plantilla):
   precio, **% de comisión**, vendedor, valoración, nº de reseñas, vendidos, idioma y 3 características
   literales de la ficha. Pon la fecha de hoy en `verificado_el`.
4. Descarta lo que use dibujos de Pokémon sin ser de marca oficial/licenciada (`no_oficial`).
5. Pulsa **Solicitar muestra gratis** en los que lo ofrezcan: es la forma legítima de tener producto
   real para grabar sin comprar nada.
6. Pulsa **Añadir al escaparate** en el elegido.

## 4. Automatización de la publicación

| Paso | ¿Vía oficial automática? | Detalle |
|---|---|---|
| Subir el vídeo | Sí, pero no para ti todavía | *Content Posting API*: exige crear tu propia app y pasar una auditoría de TikTok. Sin auditar, todo se publica **solo en privado**. No tiene programación ni campo de producto. |
| Vincular el producto afiliado (carrito naranja) | **No** | La *Affiliate Creator API* (añadir al escaparate, enlaces) existe en el Partner Center, pero es para apps de socios aprobados; su disponibilidad en España está sin verificar. La Content Posting API no admite productos. |
| Programar | Manual | Desde la app o TikTok Studio. Comprueba si tu cuenta permite programar con producto enlazado; si no, publica en el momento. |
| Ventas y comisiones | Manual | Se leen en *TikTok Shop para creadores > Análisis* y se anotan con `python main.py resultado`. |

**Decisión:** nada de bots ni automatización del navegador. El sistema deja cada publicación en una
carpeta con `video.mp4`, `descripcion.txt` y `pasos.txt`; tú haces la subida y el enlace del producto
(unos 2 minutos por vídeo). Es el único paso manual obligatorio y no hay alternativa autorizada hoy.

## 5. Herramientas de IA elegidas

| Función | Elección | Motivo |
|---|---|---|
| Guiones, descripciones, hashtags | Plantillas propias en Python | Gratis, repetible y sin riesgo de que una IA invente datos del producto |
| Voz | **ElevenLabs** (API oficial) | Ya tienes plan Starter activo: 11.004 de 40.000 caracteres usados (comprobado hoy). Un lote de 5 vídeos son ~2.300 caracteres |
| Montaje, subtítulos, formato vertical | **ffmpeg + Pillow** | Gratis, por lotes, sin marca de agua |
| Escenas ambientales | **Kling** (fase 2, no implementado) | Tienes 26 unidades de prueba. Solo para fondos sin cartas ni producto. Lo añadiré cuando lo autorices |

Descartadas por ahora: **Veo 3.1** (la más cara por segundo), **Runway** (coste medio, no aporta sobre Kling),
**Creatify / Pippit** (anuncios con avatar a partir de una URL: suenan a anuncio y generan el producto con IA),
**Symphony Creative Studio** (gratis dentro de TikTok, pero manual; útil como plan B para probar un vídeo suelto).
Los precios por segundo de vídeo que circulan son de blogs y se contradicen; se verificarán antes de contratar nada.

## 6. Legal y fiscal en España

- **Alta de autónomo:** las gestorías consultadas coinciden en que cobrar comisiones de forma habitual
  exige alta en Hacienda (modelo 036) y en el RETA, y que **no existe exención general por ingresar poco**.
- **IVA:** depende de dónde esté cada vendedor (21 % si es español; inversión del sujeto pasivo y
  modelo 349 si es de otro país de la UE, con alta en el ROI). Las fuentes discrepan en los detalles.
- **DAC7:** TikTok informa a Hacienda de tus ingresos (umbrales citados: 30 operaciones o 2.000 €/año).
- Todo esto procede de blogs de gestorías, no de la AEAT. **Consulta con un gestor antes de cobrar la primera comisión.**
- **Marcas e imágenes:** «Pokémon» y sus ilustraciones son de Nintendo/Creatures/GAME FREAK. Ser afiliado
  no da derecho a usar imágenes de internet. Usa solo: fotos/vídeos del vendedor del producto que promocionas,
  grabación propia de una muestra, o fondos ambientales sin personajes ni cartas.
- **Publicidad:** activa la divulgación de contenido comercial cuando TikTok la ofrezca y la etiqueta de IA.

## 7. Novedades útiles para contenido (confirmadas)

- **Megaevolución-Dominio Delta**: a la venta desde el 6-nov-2026 (Mega-Rayquaza ex). Fuente: Pokémon.
- **Celebración 30.º Aniversario**: set lanzado el 16-sep-2026; Colección Ultraprémium, Colección Prémium
  Ditto y Colección con Figura previstas en noviembre, **sin día ni precio oficial en España**.
- **Japón:** set del 27-nov-2026 con Mega Lucario Z. No es un lanzamiento europeo.

## Fuentes

- [Pokémon: Mega Evolution—Delta Reign llega el 6-nov-2026](https://www.pokemon.com/us/news/the-pokemon-tcg-mega-evolution-delta-reign-expansion-arrives-november-6-2026)
- [Pokémon España: productos de Celebración 30.º Aniversario](https://www.pokemon.com/es/noticias/productos-de-celebracion-30-o-aniversario-de-jcc-pokemon)
- [Centro Pokémon: Megaevolución-Dominio Delta en español](https://www.centropkmn.com/2026/11/06/megaevolucion-dominio-delta-de-pokemon-tcg-lista-y-galeria-con-todas-las-cartas-en-espanol/)
- [TikTok Seller Center UE: productos restringidos](https://seller-ie.tiktok.com/university/essay?default_language=en-GB&knowledge_id=748206502201108)
- [TikTok for Developers: Direct Post](https://developers.tiktok.com/docs/en/content-posting-api-reference-direct-post) · [Guía de inicio](https://developers.tiktok.com/docs/en/content-posting-api-get-started)
- [TikTok Shop Partner Center: Add Showcase Products](https://partner.tiktokshop.com/docv2/page/add-showcase-products-202405) · [APIs de afiliados (beta)](https://partner.tiktokshop.com/docv2/page/new-apis-and-webhook-for-affiliates-beta)
- [inicia.academy: empezar en TikTok Shop desde España](https://inicia.academy/blog/como-empezar-tiktok-shop-espana) · [forliveshopping: afiliado en España](https://forliveshopping.es/afiliado-tiktok-shop-espana)
- [marketing4ecommerce: subida de comisión al 9 %](https://marketing4ecommerce.net/en/tiktok-shop-increases-commission/) · [noovid: TikTok Shop en Europa 2026](https://noovid.com/en/blog/tiktok-shop-europe-2026)
- [Gestoría 24/7: ¿autónomo para cobrar de TikTok Shop?](https://gestoria247.com/blog/autonomo-para-cobrar-tiktok-shop-2026) · [IVA e IRPF de las comisiones](https://gestoria247.com/blog/comisiones-tiktok-shop-impuestos-2026) · [copilotgestoria: guía fiscal 2026](https://copilotgestoria.com/blog/tiktok-shop-espana-guia-fiscal-2026-iva-irpf-verifactu)
- [storika: reglas de IA en TikTok Shop](https://www.storika.ai/guides/tiktok-shop-ai-content-disclosure-rules-2026) · [affiversemedia: IA y afiliados](https://www.affiversemedia.com/tiktok-shop-ai-generated-videos-affiliate-trust/)
- [apiframe: precios de APIs de vídeo IA](https://apiframe.ai/blog/ai-video-api-pricing-2026) · [cloudzero: precios de Kling](https://www.cloudzero.com/blog/kling-ai-pricing/)
