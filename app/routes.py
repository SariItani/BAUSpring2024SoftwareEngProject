# app/routes.py
import hashlib
import time
from flask import jsonify, redirect, render_template, request, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
import requests
from app import app, login_manager, User, db, Message
from datetime import datetime
from openai import OpenAI
import os
from dotenv import load_dotenv
from werkzeug.utils import secure_filename


bcrypt = Bcrypt(app) #library used for encryption


load_dotenv() #load all api keys 

API_KEY = os.getenv('API_KEY')
SPOON_KEY = os.getenv('SPOON_KEY')

def run_conversation(prompt):
    client = OpenAI(api_key=API_KEY)

    messages = [{"role": "user", "content": prompt}]

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=messages
    )

    response_text = response.choices[0].message.content

    return response_text


@login_manager.user_loader #load the user
def load_user(user_id):
    return User.query.get(int(user_id))


@app.route('/') #home directory, load the index
@login_required
def index():
    return redirect(url_for('home'))


def get_similar_recipes(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/similar?apiKey={SPOON_KEY}" #endpoints
    response = requests.get(url)
    print(response)
    if response.status_code == 200:
        similar_recipes = response.json()
        return similar_recipes
    else:
        pass

@app.route('/home', methods=['GET', 'POST']) #index, for better practice
@login_required
def home(): #login required
    random_recipe = None
    
    if request.method == 'POST': #requires more details for recipe
        id = request.form['detail']
        print("Recipe id:", id)

    random_recipe_response = requests.get( #posting a request for spoonkey api to get random recipe
        f"https://api.spoonacular.com/recipes/random?&apiKey={SPOON_KEY}"
    )
    
    if random_recipe_response.status_code == 200: #if ok respond, error management
        random_recipe_data = random_recipe_response.json() #takes response for http request as json and parse it
        #only getting data
        id = random_recipe_data['recipes'][0]['id']
        readyInMinutes = random_recipe_data['recipes'][0]['readyInMinutes']
        instructions = random_recipe_data['recipes'][0]['instructions']
        dishTypes = random_recipe_data['recipes'][0]['dishTypes']
        extendedIngredients = random_recipe_data['recipes'][0]['extendedIngredients']
        servings = random_recipe_data['recipes'][0]['servings']
        ingredient_amounts=[]
        ingredient_names=[]
        ingredient_units=[]
        for each in extendedIngredients:
            ingredient_amounts.append(each["amount"])
            ingredient_names.append(each["name"])
            ingredient_units.append(each["unit"])
        ingredients = []
        for amount, name, unit in zip(ingredient_amounts, ingredient_names, ingredient_units):
            ingredients.append(f"{amount} {name} {unit}")
        recipe_image = random_recipe_data['recipes'][0]['image']
        recipe_title = random_recipe_data['recipes'][0]['title']
        source_name = random_recipe_data['recipes'][0]['sourceName']
        source_url = random_recipe_data['recipes'][0]['sourceUrl']
        price_per_serving = random_recipe_data['recipes'][0]['pricePerServing']
        summary = random_recipe_data['recipes'][0]['summary']
        
        similar_recipes = get_similar_recipes(id)
        
        print("similar_recipes:",similar_recipes)
        recipe_titles = []
        recipe_images = []
        recipe_price_per_serving = []
        for recipe in similar_recipes:
            # recipe = recipe[0]
            recipe_id = recipe['id']
            print(recipe_id)
            # GET https://api.spoonacular.com/recipes/{id}/information
            print(requests.get(f"https://api.spoonacular.com/recipes/{recipe_id}/information?&apiKey={SPOON_KEY}"))
            r = requests.get(f"https://api.spoonacular.com/recipes/{recipe_id}/information?&apiKey={SPOON_KEY}")
            print(r)
            print(r.status_code)
            if r.status_code == 200:
                r = r.json()
                print(r)
                recipe_title = r['title']
                recipe_image_ = r['image']
                recipe_price = r['pricePerServing']
                
                recipe_titles.append(recipe_title)
                recipe_images.append(recipe_image_)
                recipe_price_per_serving.append(recipe_price)

                # Do something with the retrieved similar recipes data
                print(f"Recipe ID: {recipe_id}")
                print(f"Title: {recipe_title}")
                print(f"recipe_price: {recipe_price}")

        print(recipe_price_per_serving, recipe_titles, recipe_images)
        
    imgpath = current_user.imgpath #needs to load the user, takes data from  database and rest 
    username = current_user.username #pass them to frontend
    bio = current_user.bio
    return render_template('home.html', imgpath=imgpath, username=username, bio=bio, recipe_image=recipe_image, recipe_title=recipe_title, source_name=source_name, source_url=source_url, price_per_serving=price_per_serving, summary=summary, ingredients=ingredients, readyInMinutes=readyInMinutes, id=id, servings=servings, recipe_price_per_serving=recipe_price_per_serving, recipe_titles=recipe_titles, recipe_images=recipe_images)


@app.route('/login', methods=['GET', 'POST']) #get info from login form and verify data
def login():
    if request.method == 'POST':     #to log the user in
        print(request.form)
        if 'loginButton' in request.form:
            username = request.form['username']
            password = request.form['password']
            email = request.form['emailAddress']
            
            user = User.query.filter_by(username=username).first()  #select first from query

            if user and bcrypt.check_password_hash(user.password, password):
                login_user(user)
                return redirect(url_for('home'))
            else:
                flash('Login unsuccessful. Please check your username and password.', 'danger')
                
        elif 'signupButton' in request.form:
            print("\nSo yeah we got here:")
            username = request.form['username2']
            password = request.form['password2']
            email = request.form['emailAddressBelow']
            check = request.form['check']
            print(username, password, email, check)
            
            if check != password:
                flash('Passwords dont match', 'danger')
                redirect(url_for('login'))
            
            hashed_password = bcrypt.generate_password_hash(password).decode('utf-8') #encrypt pass

            existing_user_username = User.query.filter_by(username=username).first()
            existing_user_email = User.query.filter_by(email=email).first()
            
            if existing_user_username:
                flash('Username is already taken. Please choose a different one.', 'danger')
            elif existing_user_email:
                flash('Email is already taken. Please choose a different one.', 'danger')
            else:
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                user = User(username=username, email=email, password=hashed_password, imgpath="assets/img/avataaars.svg", bio="Enter bio in the Profile Section...")
                db.session.add(user)
                db.session.commit()
                print(f"\nCreated User: {username}, {email}, {password}, assets/img/avataaars.svg, Enter bio in the Profile Section...")
                flash('Your account has been created! You can now log in.', 'success')
                return redirect(url_for('home'))

    joke_url = f'https://api.spoonacular.com/food/jokes/random?apiKey={SPOON_KEY}' #random jokes
    print(joke_url)
    response = requests.get(joke_url)
    print(response)
    if response.status_code == 200:
        joke = response.json().get('text')
    else:
        joke = 'Unable to fetch a joke at the moment'

    return render_template('login.html', joke=joke)


@app.route('/logout') #logout and redirect to home page
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


UPLOAD_FOLDER = 'app/static/assets/img/profilepics' #getting profile pics
ALLOWED_EXTENSIONS = ['jpeg', 'jpg', 'png', 'gif', 'bmp', 'tiff', 'tif', 'svg', 'webp']

def allowed_file(filename): #finding if file is right image
    file_ext = filename.rsplit('.', 1)[1].lower()
    return '.' in filename and file_ext in ALLOWED_EXTENSIONS

def generate_filename(username, extension): #get username and ext of file, so every username has a hash
    unique_string = f"{username}{time.time()}" #which is private image
    hashed_string = hashlib.sha256(unique_string.encode()).hexdigest()
    return f"{hashed_string}.{extension}"

@app.route('/profile', methods=['GET', 'POST']) #change and validation profil stuff, update
@login_required
def profile():
    imgpath = current_user.imgpath
    if request.method == 'POST':
        username = request.form.get('username').strip()
        bio = request.form.get('bio').strip()
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file and allowed_file(file.filename):
                extension = file.filename.rsplit('.', 1)[1].lower()
                filename = generate_filename(username, extension)
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                imgpath = f'assets/img/profilepics/{filename}'
                if current_user.imgpath and current_user.imgpath != imgpath:
                    old_img_path = os.path.join(UPLOAD_FOLDER, current_user.imgpath.split('/')[-1])
                    if os.path.exists(old_img_path):
                        os.remove(old_img_path)
        if username!="" and username != current_user.username:
            current_user.username = username
        if bio and bio != current_user.bio:
            current_user.bio = bio
        if imgpath and imgpath != current_user.imgpath:
            current_user.imgpath = imgpath
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('profile.html', imgpath=imgpath)

