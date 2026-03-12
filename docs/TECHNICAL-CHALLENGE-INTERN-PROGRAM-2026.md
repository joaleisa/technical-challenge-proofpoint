```
TITLE: TECHNICAL CHALLENGE INTERN PROGRAM – 2026 – Communication to Applicants -
```
**Email message to send to each applicant-**

“¡Hola!

Queremos agradecerte por tu interés en ser parte del programa de pasantías en Proofpoint – 2026. Esperamos que el proceso
de selección sea una gran experiencia y un desafío enriquecedor.

Antes de avanzar a la etapa de entrevistas, te enviamos algunas preguntas y unos ejercicios prácticos que deberás completar
y enviar antes del JUEVES 12/03 _al final del día_ por este medio al siguiente mail: University Recruiting
UniversityRecruiting@proofpoint.com

**A-Por favor, responder a las siguientes preguntas lo más preciso posible, preferentemente en Inglés.**

1. Describe the most relevant learnings from programming-related subjects during your career.
2. Describe a situation you had to resolve with a teammate from a study or work group.
3. Describe your personal learning plans or development expectations in technical areas in the short and long term.

**B- Ejercicio Práctico a resolver:**

**The Streaming Service’s Lost Episodes**

**Context**

A streaming platform is digitizing its catalog of series, seasons, and episodes.

However, during the ingestion of data, no validation or uniqueness checks were applied, which resulted in a corrupted catalog
containing missing information, inconsistent values, and duplicated episodes.

You will be given a CSV file where each row represents an episode.
Each entry should contain the following fields in this order:

- Series Name – name of the series (required)
- Season Number – season number (may be missing or invalid)
- Episode Number – episode number (may be missing or invalid)
- Episode Title – episode title (may be missing)
- Air Date – date when the episode aired (may be missing or invalid)

Because of the lack of checks during data entry, the file may contain inconsistencies, incorrect formats, and repeated entries.

# Goal

Your task is to process this CSV file and produce a clean, corrected, and de-duplicated catalog.
You must:

- Parse and normalize all entries
- Correct missing or invalid information following the rules below
- Detect and remove duplicated episodes
- Keep only one valid record for each unique episode
- Produce a final, well‑organized list of episodes
- Generate a quality report summarizing your corrections


Additional organization (e.g., grouping or sorting) is a plus but not mandatory.

**Problems You May Encounter in the File**

**1. Missing or Empty Fields**
    
The following fields may be empty or missing entirely:
- Series Name
    If missing or empty → discard the record (required to identify an episode)
- Season Number
    If missing, empty, negative, or not a number → set to 0
- Episode Number
    If missing, empty, negative, or not a number → set to 0
- Episode Title
    If missing or empty → replace with "Untitled Episode"
- Air Date
    If missing, empty, or invalid → replace with "Unknown"
- When Episode Number, Episode Title **and** Air Date are missing (the three fields), discard the record (required to
    identify and merge)
    Consider values 0 and "Unknown" as missing information

**2. Invalid Data Formats**

    You may find:
- Non‑numeric values in Season or Episode numbers 
    e.g., "one", "3.5", "--2"
- Impossible dates
    e.g., "not a date", "2022- 40 - 99", "0000- 00 - 00"
- Extra whitespace, inconsistent capitalization, strange characters, etc.
    All such cases should be cleaned and normalized.

**3. Duplicate Entries**
    
Because no uniqueness constraints were enforced during ingestion, the same episode may appear:
- several times,
- with different titles,
- different air dates,
- different spacing or formatting,
- or inconsistent season/episode numbering.

```
Episodes must be considered duplicates when they refer to the same:
(SeriesName_normalized, SeasonNumber, EpisodeNumber)
```
```
Or
(SeriesName_normalized, 0, EpisodeNumber, EpisodeTitle_normalized)
Or
(SeriesName_normalized, SeasonNumber, 0, EpisodeTitle_normalized)
Normalized means: trimmed, collapsed spaces, and lowercased for comparison.
```

```
When duplicates exist, you must keep only the “best” record, following this priority:
o Episodes with a valid Air Date over "Unknown"
o Episodes with a known Episode Title over "Untitled Episode"
o Episodes with a valid Season Number and Episode Number
o If still tied → keep the first entry encountered in the file
```
**Output**

You must provide the source code (any language of your preference) of a program that can read the csv input file. Feel free to
share a Github link if that's easier. The code should generate the following output:

**1. Cleaned Episode Catalog**

Output file name: **episodes_clean.csv**

With columns:
    
    SeriesName,SeasonNumber,EpisodeNumber,EpisodeTitle,AirDate

Requirements:

- All corrections applied
- No duplicates
- Safe defaults used where appropriate
- Each row represents a valid episode

**2. Data Quality Report**

Output file name: **report.md**

Must include:
- Total number of input records
- Total number of output records
- Number of discarded entries
- Number of corrected entries
- Number of duplicates detected
- Explanation of the deduplication strategy
This report helps assess data quality and your decision‑making

**C- Adicionalmente, si alguien cuenta con tiempo, les enviamos este otro ejercicio:**

**Análisis de Frecuencia de Palabras**

Escribe un programa que lea un archivo de texto y realice un análisis de frecuencia de palabras:

- El programa debe ser capaz de leer un archivo de texto proporcionado como entrada y contar cuántas veces aparece
    cada palabra en el texto.
- La comparación de palabras debe ser sin distinción entre mayúsculas y minúsculas y no considerar signos de puntuación
    y caracteres especiales.
- Mostrar las 10 palabras más frecuentes, junto con su frecuencia de aparición.


**Fecha límite de entrega: JUEVES 12 de MARZO (final del día) respondiendo a este mail.**

Si necesitas consultar alguno de los puntos, no dudes en enviar un mensaje por mail y te ayudaremos a resolver la consulta.

Muchas gracias y quedamos a disposición por cualquier consulta.

University Relations Team”


