# La terraza del Miramar · versión corporal · partitura sonora

Versión CORPORAL V1 · 18/09/2026.

Este paquete sustituye el criterio de efectos/onomatopeyas genéricas por una dramaturgia física: **respiración, cuerpo, pinza, sábana, móvil, suelo, aire y mar**. No incorpora una música externa a la acción.

## Duración canónica

La duración se toma de la matriz existente del proyecto y se conserva sin cambios:

**42:40 = 2.560 s · 30 escenas.**

`MATRIZ_TIEMPOS_EXACTOS_30_ESCENAS.csv` fija IN, OUT y duración de cada escena. La generación sonora no puede alterar esos límites.

## Arcos acústicos

- **Respiración:** individuo → invasión → masa → recuperación → mar.
- **Pinza:** CLAC doméstico → límite → vigilancia → máquina → ritmo → desaparición.
- **Sábana:** roce → tensión → territorio → arquitectura → membrana → resto → juego → sábana.
- **Cuerpo:** presencia → número → mecanismo → Reina → caída → baile → respiración.

Puntos críticos: 04 · CLAC originario; 23 · máquina exacta; 24 · fallo; 26 · RAM; 29 · baile construido sólo con materiales anteriores; 30 · desmontaje → respiración → mar → segundo OK.

## Generación

El workflow `build-miramar-corporal.yml` genera de forma reproducible:

- un MASTER continuo de 42:40;
- 30 FLAC y 30 MP3 de escena como artefacto de Actions;
- dos MP3 web a 64 kb/s en `audio/`:
  - escenas 01–15;
  - escenas 16–30;
- `MANIFIESTO_AUDIO.json`.

Los archivos lossless y de montaje se conservan como artefacto de Actions para no inflar innecesariamente el historial Git.

## Regla de diseño

Si un sonido puede ser sustituido por un efecto de librería sin perder identidad, todavía no está resuelto. La técnica debe amplificar la materia física de la escena, no reemplazarla.
