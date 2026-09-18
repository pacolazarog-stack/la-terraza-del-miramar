# La terraza del Miramar · partitura sonora de onomatopeyas

Versión V1 · 18/09/2026.

Partitura sonora para la versión corporal/gestual y de objetos. No es una canción ni una banda sonora narrativa: trabaja con cuerpo, objetos, respiración, onomatopeya, silencio y lenguaje mínimo.

## Célula madre

**TUM – TA – AH – TUM**

Léxico acústico:
- **CLAC** = pinza / linde / voto
- **TUM** = cuerpo / madera / peso
- **TAC** = sello / autoridad
- **BRR** = teléfono / máquina
- **SHH / RAS** = papel / sábana / viento
- **PLIP** = agua / mar
- **AH** = respiración / esfuerzo

Palabras esenciales: **MAR · MIRAMAR · OK · COMUNIDAD · RAM · DIEZ MINUTOS**.

Cadena figurada única: **«Mira mar. Mar mira.»**

## Arquitectura temporal

La matriz completa dura exactamente **42:40 = 2.560 s** y contiene 30 escenas.

- 01–08 · DOMÉSTICA
- 09–13 · COMUNIDAD
- 14–21 · REINA / AUTORIDAD
- 22–28 · MÁQUINA / ARCHIVO
- 29 · DESARMAR A LA REINA
- 30 · DIEZ MINUTOS

`MATRIZ_TIEMPOS_EXACTOS_30_ESCENAS.csv` fija los límites exactos de cada escena.

## Salidas

El workflow `build-miramar-onomatopeyas.yml` genera:
- 30 MP3 individuales a 192 kb/s;
- un MASTER MP3 continuo de 42:40;
- 30 FLAC sample-exactos y un MASTER FLAC como artefacto de GitHub Actions;
- `MANIFIESTO_AUDIO.json`.

Los MP3 se incorporan al repositorio. Los FLAC se conservan como artefacto de Actions para evitar inflar el historial Git.

## Estatuto

Los límites temporales de escena son la matriz de montaje. Los cues internos de palabra, respiración y percusión son composición sonora V1 y pueden ajustarse tras ensayo escénico sin alterar la duración de cada escena.
