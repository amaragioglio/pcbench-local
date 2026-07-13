# Orígenes Coffee — Sitio web

Marca de café con memoria cultural, dirigida a latinos de segunda y tercera
generación en EE.UU. que conectan con el café de su tierra familiar
(Guatemala, México, Colombia). Editorial bilingüe, principalmente en inglés
con acentos en español. Es un **smoke test**: las historias son culturales
e históricas por región (no de trazabilidad de granos), y el CTA es unirse
a la lista de lanzamiento.

Estático, sin dependencias ni build: solo HTML, CSS y JavaScript. La
dirección de diseño está en [INVESTIGACION.md](INVESTIGACION.md). Las fotos
son reales (Unsplash, sin IA) y provisionales — ver `assets/img/CREDITOS.md`.

## Estructura

```text
website/
  index.html        → portada editorial: masthead, intro, el Atlas (índice de países), manifiesto, lista
  colombia.html     → artículo Nº 01 — La tierra del tinto
  mexico.html       → artículo Nº 02 — De contrabando y revolución
  venezuela.html    → artículo Nº 03 — El país del marrón y el guayoyo
  guatemala.html    → artículo Nº 04 — Tierra de volcanes
  brasil.html       → artículo Nº 05 — O gigante do cafezinho
  styles.css        → sistema editorial minimalista (ref. La Cabra): papel crema, serif ligera, hairlines
  script.js         → topbar, menú móvil, reveal, formulario de leads (mailto → cambiar a Formspree/Tally)
  INVESTIGACION.md  → investigación de referencias y dirección de diseño
  assets/img/       → fotografías reales + CREDITOS.md
```

Las páginas de país se generan a mano sobre una plantilla común; si cambias
la estructura de una, replica el cambio en las cinco.

## Ver en local

Abre `index.html` directamente en el navegador, o sirve la carpeta:

```bash
python3 -m http.server 8000 --directory website
```

Luego visita `http://localhost:8000`.

## Personalizar

- **Textos**: edita `index.html`. Los capítulos son Origen, Proceso,
  El café, Historias y Visítanos.
- **Nombre de la marca**: busca "Café Origen" en `index.html` y reemplázalo.
- **Fotos**: sustituye los archivos de `assets/img/` por fotografía propia
  manteniendo los nombres, o actualiza las rutas en `index.html`.
- **Colores**: variables CSS al inicio de `styles.css`
  (`--espresso`, `--crema`, `--tostado`, `--hoja`).
- **Video**: reservado para el hero o el proceso; usar Pexels Videos
  (real, sin IA) con póster de imagen y sin autoplay en móvil.

## Conectar Formspree (medición de leads)

El formulario ya envía por AJAX a Formspree y registra en cada lead el
**origen** (colombia, mexico, venezuela, guatemala, brasil o atlas) y la
página desde la que se envió. Solo falta el ID de tu cuenta:

1. Crea una cuenta gratis en <https://formspree.io> (con tu Gmail).
2. Crea un formulario nuevo; te dará una URL tipo
   `https://formspree.io/f/xayzabcd`.
3. En `script.js`, reemplaza `TU_ID_AQUI` por esa parte final
   (ej. `xayzabcd`) en la línea `const FORMSPREE_ID = ...`.

Mientras el ID siga siendo el placeholder, el formulario no pierde leads:
abre un correo pre-llenado como respaldo. Si Formspree falla en algún
envío, también cae a ese respaldo. El plan gratis de Formspree incluye
50 envíos/mes — suficiente para el smoke test.

## Publicar en GitHub Pages

1. En GitHub: *Settings → Pages*.
2. Source: *Deploy from a branch*, rama `main`, carpeta `/website`
   (si GitHub no ofrece esa carpeta, mueve el contenido a `/docs` o a la raíz).
3. Guarda y espera el enlace `https://<usuario>.github.io/<repo>/`.
