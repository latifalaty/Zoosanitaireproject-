from flask import Flask, render_template, request, redirect, url_for, session, make_response,jsonify
from pymongo import MongoClient
from bson import ObjectId
import pandas as pd
from datetime import datetime
from back import webscraping, nettoyer_paragraphe, detect_language, translate_fr, translate_arabe, summarize_article, extract_country_ang, extraire_maladie_fr, extraire_maladie_ar, extraire_maladie_ang

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connexion à la base de données MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['zoo']
collection = db['user']
extracteddata = db['extracteddata']

# Nom d'utilisateur et mot de passe de l'administrateur
admin_username = 'admin'
admin_password = 'adminpassword'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if username == admin_username and password == admin_password:
            session['username'] = username
            return redirect(url_for('index'))
        
        user = collection.find_one({'username': username, 'password': password})
        
        if user:
            session['username'] = username
            return redirect(url_for('userinterface'))
        else:
            return 'Identifiants invalides. Veuillez réessayer.'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/add_user', methods=['POST'])
def add_user():
    # Extraire les données du formulaire
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    
    # Vérifier si l'utilisateur existe déjà dans la base de données
    existing_user = collection.find_one({'$or': [{'username': username}, {'email': email}]})
    
    if existing_user:
        # Si l'utilisateur existe déjà, renvoyer une alerte
        return 'Cet utilisateur existe déjà.'
    else:
        # Ajouter l'utilisateur à la collection
        user_data = {'username': username, 'password': password, 'email': email}
        collection.insert_one(user_data)
        return redirect(url_for('listusers'))

@app.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    collection.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('listusers'))

@app.route('/filter_by_disease', methods=['POST'])
def filter_by_disease():
    disease_name = request.form.get('disease')

    filtered_data = extracteddata.find({'maladies': disease_name})

    filtered_data_list = list(filtered_data)

    return render_template('filtered_data.html', filtered_data=filtered_data_list)



@app.route('/userinterface')
def userinterface():
    return render_template('userinterface.html')
@app.route('/scrape', methods=['POST'])
def scrape():
    urls = request.form.getlist('url')
    
    extracted_data = []

    for url in urls:
        existing_data = extracteddata.find_one({'url': url})
        
        if existing_data:
            extracted_data.append(existing_data)
        else:
            (date, contenu) = webscraping(url)

            if contenu is not None:
                if detect_language(contenu) == "fr":
                    contenu_ang = translate_fr(contenu)
                    maladies = extraire_maladie_fr(nettoyer_paragraphe(contenu))
                elif detect_language(contenu) == "ar":
                    contenu_ang = translate_arabe(contenu)
                    maladies = extraire_maladie_ar(nettoyer_paragraphe(contenu))
                elif detect_language(contenu) == "en":
                    contenu_ang = contenu
                    maladies = extraire_maladie_ang(nettoyer_paragraphe(contenu_ang))
                else:
                    print("Langue non supportée")
                    
                # Nettoyage du contenu
                contenu_nettoye = nettoyer_paragraphe(contenu_ang)

                # Résumé de l'article
                summary = summarize_article(contenu, sentences_count=4)

                # Extraction des pays
                pays = extract_country_ang(contenu_nettoye)

                if isinstance(date, str):
                    date = datetime.strptime(date, '%Y-%m-%d')

                date_formatted = date.strftime('%Y-%m-%d')

                # Stockage des données extraites dans un dictionnaire
                data = {
                    'url': url,
                    'date': date_formatted,
                    'summary': summary,
                    'maladies': list(maladies),
                    'pays': pays
                }
                
                extracteddata.insert_one(data)
                
                extracted_data.append(data)

    return render_template('result.html', extracted_data=extracted_data)
@app.route('/filter', methods=['POST'])
def filter_by_date():
    # Récupérer les dates de début et de fin filtrées à partir du formulaire
    start_date_str = request.form['start_date']
    end_date_str = request.form['end_date']

    # Filtrer les données extraites par date
    filtered_data = extracteddata.find({
        'date': {
            '$gte': start_date_str,
            '$lte': end_date_str
        }
    })

    return render_template('filtered_result.html', filtered_data=filtered_data)

@app.route('/export_to_excel', methods=['POST'])
def export_to_excel():
    # Récupérer les données depuis la base de données extracteddata
    extracted_data = extracteddata.find()

    # Créer une liste de dictionnaires avec les données extraites
    data_list = []
    for data in extracted_data:
        data_dict = {
            'Maladies': ', '.join(data['maladies']) if 'maladies' in data else '',
            'Résumés': data['summary'] if 'summary' in data else '',
            'URL': data['url'] if 'url' in data else '',
            'Date': data['date'] if 'date' in data else '',
            'Pays': ', '.join(data['pays']) if 'pays' in data else ''
        }
        data_list.append(data_dict)

    # Créer un DataFrame avec les données
    df = pd.DataFrame(data_list)

    # Exporter vers un fichier Excel
    excel_file = 'exported_data.xlsx'
    df.to_excel(excel_file, index=False)

    # Créer une réponse pour télécharger le fichier Excel
    response = make_response(open(excel_file, 'rb').read())
    response.headers.set('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response.headers.set('Content-Disposition', 'attachment', filename=excel_file)

    return response

@app.route('/add_user_form')
def add_user_form():
    return render_template('add_user_form.html')

@app.route('/listusers')
def listusers():
    if 'username' in session:
        users = collection.find()
        return render_template('listeusers.html', username=session['username'], users=users)
    else:
        return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
