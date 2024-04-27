from newspaper import Article
import re
import spacy
from bs4 import BeautifulSoup
import requests
import time
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
from langdetect import detect
from transformers import pipeline

# Initialisation des pipelines de traduction
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-fr-en")
translator_ar_to_en = pipeline("translation", model="Helsinki-NLP/opus-mt-ar-en")

def webscraping(url):
    try:
        session = requests.Session()
        retry = Retry(connect=3, backoff_factor=0.5)
        adapter = HTTPAdapter(max_retries=retry)
        session.mount('http://', adapter)
        session.mount('https://', adapter)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'
        }

        article = Article(url)
        response = session.get(url, headers=headers)
        time.sleep(5)

        article.download(input_html=response.text)
        article.parse()
        contenu = article.title + ' ' + article.text
    except requests.exceptions.RequestException as e:
        print(f"Une erreur de requête s'est produite lors de l'extraction de l'article à l'URL {url}: {e}")
        return None, None
    except Exception as e:
        print(f"Une erreur inattendue s'est produite lors de l'extraction de l'article à l'URL {url}: {e}")
        return None, None

    date = article.publish_date

    if date is None:
        soup = BeautifulSoup(response.content, "html.parser")
        datetime_spans = soup.find_all("span", class_=lambda c: c and "date" in c)
        for span in datetime_spans:
            date = span.text.strip()
            break

    return date, contenu

def nettoyer_paragraphe(paragraphe):
    paragraphe_propre = re.sub(r'\s+', ' ', paragraphe)
    punc = '''!()-[]{};:'’"\,<>./?@#$%^&*_~'''
    for ele in punc:
        paragraphe_propre = paragraphe_propre.replace(ele, " ")
    return paragraphe_propre

def detect_language(text):
    return detect(text)

def translate_fr(text):
    text_morceaux = [text[i:i+512] for i in range(0, len(text), 512)]
    resultats = []
    for morceau in text_morceaux:
        resultat = translator(morceau)
        resultats.append(resultat)
    resultat_final = " ".join([resultat[0]['translation_text'] for resultat in resultats])
    return resultat_final

def translate_arabe(text):
    text_morceaux = [text[i:i+512] for i in range(0, len(text), 512)]
    resultats = []
    for morceau in text_morceaux:
        resultat = translator_ar_to_en(morceau)
        resultats.append(resultat)
    resultat_final = " ".join([resultat[0]['translation_text'] for resultat in resultats])
    return resultat_final

def extraire_maladie_ang(text):
    nlp1 = spacy.load("D:/zoosaintaireplatform/model anglais/model-best")
    doc = nlp1(text)
    maladies = set()
    for ent in doc.ents:
        if ent.label_ == "DISEASE":
             maladie = ent.text.lower()  # Convertir en minuscules pour normaliser
            # Vérifier si la maladie n'a pas déjà été ajoutée ou une version similaire
             if maladie not in maladies:
                 maladies.add(maladie)
    return(maladies)

def extraire_maladie_fr(text):
    nlp1 = spacy.load("D:/zoosaintaireplatform/modelfrancais2/model-best")
    doc = nlp1(text)
    maladies = set()
    for ent in doc.ents:
        if ent.label_ == "DISEASE":
             maladie = ent.text.lower()  # Convertir en minuscules pour normaliser
            # Vérifier si la maladie n'a pas déjà été ajoutée ou une version similaire
             if maladie not in maladies :
                maladies.add(maladie)
    return(maladies)

def extraire_maladie_ar(text):
    nlp1 = spacy.load("D:/zoosaintaireplatform/modelar/model-best")
    doc = nlp1(text)
    maladies = set()
    mots_specifiques = ("السل", "الجدري", "البروسيلا")
    for ent in doc.ents:
        if ent.label_ == "DISEASE":
            maladie = ent.text
            # Vérifier si la maladie n'a pas déjà été ajoutée ou une version similaire
            if maladie not in maladies and (len(maladie.split()) > 1 or maladie in mots_specifiques):
                maladies.add(maladie)
    return maladies

def extract_country_ang(text):
    text = text.title()
    nlp = spacy.load("en_core_web_lg")
    doc = nlp(text)
    countries = []
    for ent in doc.ents:
        if (ent.label_ == "LOC_B" or ent.label_ == "GPE") and ent.text not in countries:
            countries.append(ent.text)
    return countries

def summarize_article(article_text, sentences_count=3):
    parser = PlaintextParser.from_string(article_text, Tokenizer("english"))
    summarizer = LsaSummarizer()
    summary = summarizer(parser.document, sentences_count)
    return " ".join(str(sentence) for sentence in summary)

"""#main

"""

urls = ["https://akhbarelyom.com/news/newdetails/4309637/1/%D8%AA%D8%AD%D8%B5%D9%8A%D9%86-51-%D9%85%D9%86-%D8%A7%D9%84%D9%85%D8%A7%D8%B4%D9%8A%D8%A9-%D8%B6%D8%AF-%D9%85%D8%B1%D8%B6-%D8%A7%D9%84%D8%AC%D9%84%D8%AF-%D8%A7%D9%84%D8%B9%D9%82%D8%AF%D9%8A-"]
for url in urls:
    (date, contenu) = webscraping(url)
    print(contenu)
    if contenu is not None:
        if detect_language(contenu) == "fr":
          contenu_ang = translate_fr(contenu)
          maladies = extraire_maladie_fr(nettoyer_paragraphe(contenu))
        elif detect_language(contenu) == "ar":
          contenu_ang = translate_arabe(contenu)
          maladies = extraire_maladie_ar(nettoyer_paragraphe(contenu))
        elif detect_language(contenu) == "en":
          contenu_ang=contenu
          maladies = extraire_maladie_ang(nettoyer_paragraphe(contenu_ang))
        else:
          print("Langue non supportée")
          break

        contenu_nettoye = nettoyer_paragraphe(contenu_ang)

        summary=summarize_article(contenu, sentences_count=4)
        pays = extract_country_ang(contenu_nettoye)
        print("Date de publication:", date)
        print("Résumé:", summary)
        print("Maladies:", maladies)
        print("Pays:", pays)