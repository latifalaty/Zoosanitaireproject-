from flask import Flask, render_template, request, redirect, url_for, session
from pymongo import MongoClient
from bson import ObjectId
app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connexion à la base de données MongoDB
client = MongoClient('mongodb://localhost:27017/')
db = client['zoo']
collection = db['user']

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
        
        # Vérifier les informations d'identification dans la base de données
        user = collection.find_one({'username': username, 'password': password})
        
        if user:
            session['username'] = username
            return redirect(url_for('index'))
        else:
            return 'Identifiants invalides. Veuillez réessayer.'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('index'))

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

if __name__ == '__main__':
    app.run(debug=True)
