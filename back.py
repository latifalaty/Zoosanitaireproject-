
from newspaper import Article
import re
import spacy
from spacy.tokens import DocBin
from transformers import pipeline

import nltk
from rake_nltk import Rake
"""# web scrupping"""

def webscraping(urls):
    articles_content = []  # Liste pour stocker le contenu nettoyé des articles
    for url in urls:
        try:
            # Création de l'objet Article
            article = Article(url)

            # Téléchargement et extraction du contenu de l'article
            article.download()
            article.parse()
            content = article.title + ' ' + article.text
            articles_content.append(content)

        except Exception as e:
            print(f"Une erreur s'est produite lors de l'extraction de l'article à l'URL {url}: {e}")

    return articles_content

"""# nettoyer le text"""

def nettoyer_paragraphe(paragraphe):

    paragraphe_propre = re.sub(r'\s+', ' ', paragraphe)

    # Enlever la ponctuation
    punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
    for ele in punc:
        paragraphe_propre = paragraphe_propre.replace(ele, " ")

    return paragraphe_propre

"""#importer le modele en local"""

import zipfile
import io

"""#extraire les maladies"""

def extraire_maladie(text):
    nlp1 = spacy.load("model anglais\model-best")
    doc = nlp1(text)
    maladie = set()
    for ent in doc.ents:
        if ent.label_ == "DISEASE":
             maladie.add(ent.text.lower())
    print(maladie)
    return (maladie)

"""#resumer de l article"""

def summarization(text) :
  summarizer = pipeline('summarization')
  resumer=summarizer(text,max_length=300,min_length=50,do_sample=False)
  print(resumer)
  return (resumer)

"""#main

"""

urls=["https://equusmagazine.com/news/eq-edcc-health-watch/four-texas-horses-positive-for-eia/","https://www.mlive.com/news/saginaw-bay-city/2023/11/avian-influenza-detected-in-bay-county.html"]
contenu= webscraping(urls)
print(contenu)
for paragraphe in contenu:
    contenu_nettoye = nettoyer_paragraphe(paragraphe)
    print(contenu_nettoye)
    nlp1 = spacy.load("model anglais\model-best")
    resumer = summarization(paragraphe)
    maladies = extraire_maladie(contenu_nettoye)

"""#keywords

"""

nltk.download('stopwords')
nltk.download('punkt')
text="Four horses in Texas have been confirmed positive for equine infectious anemia . The cases are located in Waller, Montgomery, Denton and El Paso counties . The Texas Animal Health Commission is working closely with the owners and local veterinarians to monitor potentially exposed horses ."
r = Rake()  # Set max_length to 2 for one or two-word phrases
r.extract_keywords_from_text(text)
for rating, keyword in r.get_ranked_phrases_with_scores():
    if rating > 5:
        print(keyword,rating)