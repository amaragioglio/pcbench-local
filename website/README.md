# Café Origen — Sitio web

Sitio web de una marca de café con historia de origen (finca + cafetería +
revista). Estático, sin dependencias ni build: solo HTML, CSS y JavaScript.
La dirección de diseño está documentada en [INVESTIGACION.md](INVESTIGACION.md).

El nombre "Café Origen" es provisional. Las fotos son reales (Unsplash,
sin IA) y también provisionales — ver `assets/img/CREDITOS.md`.

## Estructura

```text
website/
  index.html        → contenido por capítulos (hero, origen, proceso, café, historias, visita)
  styles.css        → paleta espresso/crema, tipografía editorial, responsive
  script.js         → header al scroll, menú móvil, animaciones de aparición
  INVESTIGACION.md  → investigación de referencias y dirección de diseño
  assets/img/       → fotografías reales + CREDITOS.md
```

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

## Publicar en GitHub Pages

1. En GitHub: *Settings → Pages*.
2. Source: *Deploy from a branch*, rama `main`, carpeta `/website`
   (si GitHub no ofrece esa carpeta, mueve el contenido a `/docs` o a la raíz).
3. Guarda y espera el enlace `https://<usuario>.github.io/<repo>/`.
