# MedChem Flashcards

Researchers in chemoinformatics working on drug discovery need to
learn medicinal chemistry to work with and describe drug-like
molecules. This project aims to create a flashcard-style program to
interactively teach medicinal chemistry founctional groups. The
content should be organized by into decks, such as

  * Common Functional Groups
  * Aromatic Heterocycles
  * Bioisosteres
  * PAINS & Reactive Groups
  * Medicinal Chemistry Tools

and used randomized, spaced-repetition to facilitate
learning. Information about each functional group include their name,
depiction, basic physiochemical properties, known functional
relevance, and example drugs or other key biomolecules that contain
them. Chemicals should be depicted in high-quality SVG 2D formats and,
where relevant highlight the key functional group or motif.

Building on accurate data is a requirement, so decks should be sourced
from reliable online databases and processed with robust data curation
pipeline using RDKit. Decks should be represented using a well
described JSON schema, with data QC tools to describe where the
knowledge is sourced from, and identify and fix inconsistencies.

The backend should be a robust python package, using best practices
for testing, typechecking, linting, etc. Use uv and not pip for
package management. Data should be stored into a SQLite database, and
serve the data thorugh FastAPI or SQLAlchemy or related tools.

The user interface should be a clean web-based javascript single-page
applicaiton, that can be run locally, or hosted on a webserver. Users
can use platform without logging in, or login to save
progress/learning progress.
