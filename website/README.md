# Sitio web

Sitio web estático nuevo, independiente del CLI de PCBench. No requiere
dependencias ni proceso de build: solo HTML, CSS y JavaScript.

## Estructura

```text
website/
  index.html   → contenido de la página (textos, secciones, enlaces)
  styles.css   → estilos, temas claro/oscuro y responsive
  script.js    → tema, menú móvil, animaciones y contadores
  assets/      → imágenes y otros recursos
```

## Ver en local

Abre `index.html` directamente en el navegador, o sirve la carpeta:

```bash
python3 -m http.server 8000 --directory website
```

Luego visita `http://localhost:8000`.

## Personalizar

- **Textos y secciones**: edita `index.html`. Las secciones actuales son
  Inicio, Sobre mí, Proyectos, Habilidades y Contacto.
- **Proyectos**: duplica cualquier `<article class="card">` dentro de la
  sección `#proyectos`.
- **Colores**: cambia las variables CSS al inicio de `styles.css`
  (`--accent`, `--bg`, etc.). El tema oscuro se define en `[data-theme="dark"]`.
- **Contadores**: los números de "Sobre mí" usan `data-count="N"`.

## Publicar en GitHub Pages

1. En GitHub: *Settings → Pages*.
2. Source: *Deploy from a branch*, rama `main`, carpeta `/website`
   (si GitHub no ofrece esa carpeta, mueve el contenido a `/docs` o a la raíz).
3. Guarda y espera el enlace `https://<usuario>.github.io/<repo>/`.
