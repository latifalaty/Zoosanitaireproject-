from flask import Flask, render_template, request, redirect, url_for, session, make_response
from pymongo import MongoClient
from bson import ObjectId
from back import webscraping, nettoyer_paragraphe, extraire_maladie, summarization
import pandas as pd
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connexion à la base de données MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['zoo']
collection = db['user']

# Nom d'utilisateur et mot de passe de l'administrateur
admin_username = 'admin'
admin_password = 'adminpassword'

@app.route('/')
def index():
    if 'username' in session:
        users = collection.find()
        return render_template('index.html', username=session['username'], users=users)
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Vérifier si l'utilisateur est administrateur
        if username == admin_username and password == admin_password:
            session['username'] = username
            return redirect(url_for('index'))
        
        # Vérifier les informations d'identification dans la base de données
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
    # Ajouter un utilisateur à la collection
    username = request.form['username']
    password = request.form['password']
    email = request.form['email']
    user_data = {'username': username, 'password': password, 'email': email}
    collection.insert_one(user_data)
    return redirect(url_for('index'))

@app.route('/delete_user/<user_id>', methods=['POST'])
def delete_user(user_id):
    # Supprimer un utilisateur de la collection en utilisant son ID
    collection.delete_one({'_id': ObjectId(user_id)})
    return redirect(url_for('index'))

@app.route('/userinterface')
def userinterface():
    return render_template('userinterface.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    # Obtenez les URL à partir du formulaire
    urls = request.form.getlist('url')
    
    # Effectuez le web scraping
    contenu = webscraping(urls)
    
    # Nettoyez le texte et extrayez les maladies pour chaque paragraphe
    maladies = []
    resumers = []  # Liste pour stocker les résumés de chaque paragraphe
    
    
    for paragraphe in contenu:
        paragraphe_propre = nettoyer_paragraphe(paragraphe)
        maladies_article = extraire_maladie(paragraphe_propre)
        maladies.append(maladies_article)
        resumer = summarization(paragraphe_propre)
        resumers.append(resumer)  # Ajoutez le résumé à la liste
    
    # Vous pouvez maintenant utiliser les données (contenu, maladies, résumé) comme vous le souhaitez
    return render_template('result.html', contenu=contenu, maladies=maladies, resumers=resumers)

@app.route('/export_to_excel', methods=['POST'])
def export_to_excel():
    contenu = request.form['contenu']
    maladies = request.form.getlist('maladie')
    resumes = request.form.getlist('resumer')

    # Créer un DataFrame avec les données
    data = {'Contenu': [contenu], 'Maladies': maladies, 'Résumés': resumes}
    df = pd.DataFrame(data)

    # Exporter vers un fichier Excel
    excel_file = 'exported_data.xlsx'
    df.to_excel(excel_file, index=False)

    # Créer une réponse pour télécharger le fichier Excel
    response = make_response(open(excel_file, 'rb').read())
    response.headers.set('Content-Type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response.headers.set('Content-Disposition', 'attachment', filename=excel_file)

    return response


if __name__ == '__main__':
    app.run(debug=True)
