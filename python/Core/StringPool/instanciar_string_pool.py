# generar_pool.py
import spacy
nlp = spacy.load("es_core_news_sm")

# Lista de palabras base — puedes usar aspell o cualquier fuente
from spellchecker import SpellChecker
spell = SpellChecker(language='es')
palabras = list(spell.word_frequency.keys())

# Categorizar
pool = {
    "sustantivos": [],
    "verbos": [],
    "adjetivos": [],
    "adverbios": [],
    "preposiciones": []
}

mapping = {
    "NOUN": "sustantivos",
    "VERB": "verbos",
    "ADJ": "adjetivos",
    "ADV": "adverbios",
    "ADP": "preposiciones"
}

for palabra in palabras:
    doc = nlp(palabra)
    pos = doc[0].pos_
    if pos in mapping:
        pool[mapping[pos]].append(palabra)

# Generar string_pool.py
with open("string_pool.py", "w", encoding="utf-8") as f:
    for categoria, palabras in pool.items():
        f.write(f"{categoria} = {palabras}\n")