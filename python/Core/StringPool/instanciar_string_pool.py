import spacy
from spellchecker import SpellChecker
import os

# Ruta absoluta al lado del propio script
directorio = os.path.dirname(os.path.abspath(__file__))
ruta = os.path.join(directorio, "string_pool.py")

nlp = spacy.load("es_core_news_sm")
spell = SpellChecker(language='es')
palabras = list(spell.word_frequency.keys())

pool = {
    "sustantivos": [],
    "verbos": [],
    "adjetivos": [],
    "adverbios": [],
    "preposiciones": [],
    "auxiliares": []
}

mapping = {
    "NOUN": "sustantivos",
    "VERB": "verbos",
    "ADJ": "adjetivos",
    "ADV": "adverbios",
    "ADP": "preposiciones",
    "AUX": "auxiliares"
}

for palabra in palabras:
    doc = nlp(palabra)
    pos = doc[0].pos_
    if pos in mapping:
        pool[mapping[pos]].append(palabra)

with open(ruta, "w", encoding="utf-8") as f:
    for categoria, lista in pool.items():
        f.write(f"{categoria} = {lista}\n")

print("Generado string_pool.py")
for categoria, lista in pool.items():
    print(f"{categoria}: {len(lista)} palabras")
