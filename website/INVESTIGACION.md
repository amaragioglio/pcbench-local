# Investigación de diseño — Página web de café

Fecha: julio 2026. Este documento resume la investigación de referencias y
define la dirección de diseño del sitio.

## 1. Qué hacen los mejores sitios de café

Referencias estudiadas: colecciones de Awwwards, Sitebuilder Report, Colorlib,
Elias Studio (Top 30 coffee shops), HubSpot y 99designs.

Sitios destacados y por qué funcionan:

- **Blue Bottle Coffee** — minimalismo controlado: mucho espacio en blanco,
  tipografía elegante, visuales contenidos.
- **Stumptown Coffee Roasters** — navegación fluida, fotografía de producto
  excelente y narrativa sobre los productores (origen del grano).
- **49th Parallel** — imágenes hero impactantes de la producción de café,
  mezcla de storytelling y e-commerce.
- **Lula Café / Roots Brooklyn** — paletas naturales (salvia, beige, blanco),
  texturas y tipografía suave.
- **Culture Espresso** — fotografía de estilo de vida: la gente que hace el
  café y la gente que lo disfruta, no solo el producto.
- **District Café & Bakery** — menú en HTML (no PDF), fotos profesionales,
  cero fricción para encontrar información.

Patrones comunes:

1. **La web como experiencia sensorial**, no como menú online: diseño,
   fotografía, narración y ambiente pesan tanto como el producto.
2. **Paletas tierra**: marrones cálidos, crema, terracota, verdes apagados.
   Transmiten confort y calidad.
3. **Tipografía con intención**: serif = tradición y herencia;
   sans-serif = moderno y limpio. Los mejores combinan ambas.
4. **Fotografía inmersiva** a pantalla completa en el hero, con primeros
   planos del producto y de las manos que lo trabajan.
5. **Transparencia del productor**: origen del grano, proceso de tostado,
   quién está detrás.
6. **Mobile-first**: más del 60 % de las búsquedas de cafeterías ocurren en
   el teléfono.
7. **Navegación directa**: horarios, ubicación, menú y compra a un clic.

## 2. Qué aportan los sitios agrícolas / de finca

Referencias: Local Line, Sitebuilder Report (agriculture), Vandelay Design.

- La **autenticidad manda**: el visitante quiere ver la tierra, conocer a los
  agricultores y entender las prácticas de cultivo. Las fotos genéricas de
  stock que no corresponden al lugar matan la credibilidad — por eso las
  fotos de banco son un **placeholder temporal** hasta tener fotos propias.
- Hero con la finca en acción: tomas aéreas de los campos, primeros planos
  del fruto, gente trabajando.
- Misión y visión claras fortalecen la conexión emocional.
- Verde natural, tonos tierra, marrones cálidos y dorados de cosecha.
- Funcionalidad útil: reservas de visitas/tours, suscripciones de producto.

## 3. Qué aportan las revistas narrativas (scrollytelling)

Referencias: Shorthand, Maglr, Vev, ejemplos de BBC Sport, SCMP y Pitchfork.

- **Scrollytelling**: el contenido (texto, imágenes, video, datos) se revela
  y anima al ritmo del scroll del lector.
- Funciona cuando **sirve a la narrativa** — el efecto nunca es el
  protagonista; la historia sí.
- Recursos típicos: imágenes fijas con texto que se desliza encima
  (sticky + overlay), capítulos con transiciones de color, tipografía
  editorial grande, ritmo alternado texto ↔ imagen a sangre completa.

## 4. Tendencias 2026 aplicables

Referencias: Figma, Wix, Envato, TheeDigital.

- Hero de impacto: fotografía o video a sangre completa con tipografía
  gigante y limpia encima.
- Tipografía protagonista: titulares enormes, fuentes display con carácter.
- Profundidad e inmersión con animaciones disparadas por scroll (sin abusar).
- **Rendimiento primero**: una foto optimizada casi siempre gana a un video
  de fondo en autoplay; el video se reserva para momentos clave.

## 5. Fotos y videos: bancos elegidos (reales, sin IA)

Requisito del proyecto: solo fotografía y video **reales** — nada generado
por IA.

| Banco | Licencia | Notas |
| --- | --- | --- |
| **Unsplash** | Unsplash License: uso comercial gratuito, sin atribución obligatoria | **No acepta imágenes generadas o editadas con IA** — ideal para este proyecto |
| **Pexels** | Pexels License: fotos **y videos** gratis para uso comercial | Buena fuente de video real (cafetales, barismo, tostado) |
| **Pixabay** | Pixabay License | Tiene filtro para **excluir contenido IA** en la búsqueda |

Reglas de uso:

- Verificar cada foto/video antes de usar: que sea real, coherente con la
  marca y de buena resolución.
- No usar fotos que muestren marcas o personas identificables en contexto
  comercial sin revisar la licencia del caso.
- Todas las fotos de banco son provisionales: se reemplazarán por fotografía
  propia de la finca/cafetería cuando exista.

## 6. Dirección de diseño definida

**Concepto**: una marca de café con historia de origen — mezcla de
*marca de café + finca + revista*. El sitio cuenta el viaje del grano
(la tierra → el proceso → la taza) con fotografía real a pantalla completa
y ritmo editorial.

- **Estructura (una página, por capítulos):**
  1. *Hero* — foto a sangre completa (cafetal o taza en manos), titular serif
     gigante, una sola llamada a la acción.
  2. *Origen* — la finca y la gente; bloque editorial texto + foto.
  3. *Proceso* — del grano a la taza en pasos (cosecha, secado, tostado,
     barismo), revelados con el scroll.
  4. *El café* — productos/variedades en tarjetas limpias.
  5. *Historias* — sección tipo revista con artículos/notas.
  6. *Visita / contacto* — ubicación, horarios, correo.
- **Paleta**: espresso `#2b1d16`, crema `#f5efe6`, tostado `#a9744a`,
  verde hoja `#5c6b4c`. Fondo claro crema con capítulos oscuros de contraste.
- **Tipografía**: display serif (Fraunces / Playfair Display, con fallback a
  Georgia) para titulares; sans humanista (Inter / system-ui) para texto.
- **Fotografía**: real, cálida, con personas y manos trabajando; primeros
  planos de fruto, grano y bebida; heros a sangre completa.
- **Video**: reservado para un momento clave (hero o proceso), desde Pexels,
  con póster de imagen y sin autoplay en móvil (rendimiento).
- **Interacción**: aparición suave al hacer scroll, sin efectos gratuitos;
  mobile-first; navegación pegada con acceso directo a contacto.

## Fuentes

- https://www.awwwards.com/30-coffee-websites.html
- https://www.sitebuilderreport.com/inspiration/cafe-coffee-shop-websites
- https://colorlib.com/wp/coffee-shop-websites/
- https://www.elias.studio/en/blog/post/top-30-des-meilleurs-site-internet-de-coffee-shop
- https://blog.hubspot.com/website/coffee-shops-websites
- https://99designs.com/inspiration/websites/coffee
- https://www.localline.co/blog/farm-website-design
- https://www.sitebuilderreport.com/inspiration/agriculture-farm-websites
- https://www.vandelaydesign.com/farm-websites/
- https://shorthand.com/the-craft/scrollytelling-examples/index.html
- https://www.maglr.com/blog/best-scrollytelling-examples
- https://www.vev.design/blog/editorial-websites/
- https://www.figma.com/resource-library/web-design-trends/
- https://www.wix.com/blog/web-design-trends
- https://elements.envato.com/learn/web-design-trends
- https://unsplash.com/license
- https://www.pexels.com/license/
- https://pixabay.com/
