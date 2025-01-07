from flask import Blueprint, render_template, redirect, url_for,request, flash
from flask_login import login_required, current_user
from .models import Cart, CartItem, Favorite, Sale, BookExchangeRequest
import os
views = Blueprint('views', __name__)
from .models import User,db
from .models import Book,Review, Cart, CartItem, Favorite, Sale, BookExchangeRequest

@views.route('/')
def index():
    if current_user.is_authenticated:
        # Redirect to appropriate dashboard based on role
        if current_user.role == 'buyer':
            return redirect(url_for('views.buyer_dashboard'))
        elif current_user.role == 'seller':
            return redirect(url_for('views.seller_dashboard'))
    return render_template('login_signup.html')  # Or whatever the index page should render

@views.route('/buyer_dashboard')
@login_required
def buyer_dashboard():
    if current_user.role != 'buyer':
        return redirect(url_for('views.index'))  # Ensure it redirects to an existing route

    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart_items = CartItem.query.filter_by(cart_id=cart.id).all() if cart else []

    total_cart_price = sum(item.book.price * item.quantity for item in cart_items)
    favorites = Favorite.query.filter_by(user_id=current_user.id).all()
    purchased_books = Sale.query.filter_by(seller_id=current_user.id).all()
    pending_requests = BookExchangeRequest.query.filter_by(user_id=current_user.id, status='Pending').all()

    return render_template('buyer_dashboard.html',
                           user=current_user,
                           cart_items=cart_items,
                           total_cart_price=total_cart_price,
                           favorites=favorites,
                           purchased_books=purchased_books,
                           pending_requests=pending_requests)

# Route for editing profile
@views.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # Get the form data
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        profile_picture = request.files.get('profile_picture')

        # Update the user record
        user = User.query.get(current_user.id)
        user.first_name = first_name
        user.email = email

        if profile_picture:
            # Create the profile_pics folder if it doesn't exist
            profile_pics_folder = os.path.join('MyChef','static', 'profile_pics')
            if not os.path.exists(profile_pics_folder):
                os.makedirs(profile_pics_folder)  # Create the directory if it doesn't exist
            
            # Save the uploaded profile picture
            profile_picture_path = os.path.join(profile_pics_folder, profile_picture.filename)
            profile_picture.save(profile_picture_path)

            # Update the user's profile picture field in the database
            user.profile_picture = profile_picture.filename

        # Commit changes to the database
        db.session.commit()

        flash('Profile updated successfully!', category='success')
        return redirect(url_for('views.buyer_dashboard'))  # Redirect back to the dashboard

    return render_template('edit_profile.html', user=current_user)


# Route for Seller Dashboard
@views.route('/seller_dashboard')
@login_required
def seller_dashboard():
    if current_user.role != 'seller':
        return redirect(url_for('views.index'))  # Redirect to the home page if the user is not a seller

    # Fetch books listed by the seller
    books = Book.query.filter_by(seller_id=current_user.id).all()

    # Fetch sales made by the seller
    sales = Sale.query.filter_by(seller_id=current_user.id).all()

    # Fetch pending book exchange requests for the seller
    pending_requests = BookExchangeRequest.query.filter_by(user_id=current_user.id, status='Pending').all()

    # Render the seller_dashboard template with the relevant data
    return render_template('seller_dashboard.html',
                           user=current_user,
                           books=books,
                           sales=sales,
                           pending_requests=pending_requests)
######## NEW BOOK PART #############
@views.route('/post_new_book', methods=['GET', 'POST'])
@login_required
def post_new_book():
    if current_user.role != 'seller':
        return redirect(url_for('views.index'))  # Redirect to home if the user is not a seller

    if request.method == 'POST':
        # Get form data
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        genre = request.form.get('genre')
        price = float(request.form.get('price'))
        is_used = False  # Force the book to be new (no used books allowed)
        image = request.files.get('image')  # Optional image for the book

        # Create a new book object
        new_book = Book(
            title=title,
            author=author,
            description=description,
            genre=genre,
            price=price,
            seller_id=current_user.id,
            is_used=is_used  # Set book as new
        )

        if image:
            # Save the image to the static folder
            book_images_folder = os.path.join('MyChef', 'static', 'book_images')
            if not os.path.exists(book_images_folder):
                os.makedirs(book_images_folder)

            image_path = os.path.join(book_images_folder, image.filename)
            image.save(image_path)

            # Set the image file name in the book object
            new_book.image = image.filename

        # Add the new book to the database
        db.session.add(new_book)
        db.session.commit()

        flash('New book posted successfully!', category='success')
        return redirect(url_for('views.seller_dashboard'))  # Redirect to the seller dashboard

    return render_template('post_new_book.html', user=current_user)  # Render the page with the form
######## BOOK REVIEW PART #############
@views.route('/book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def book_details(book_id):
    # Fetch the book by ID
    book = Book.query.get_or_404(book_id)

    # Fetch reviews for the book
    reviews = Review.query.filter_by(book_id=book.id).all()

    # Calculate the average rating
    average_rating = None
    if reviews:
        average_rating = sum([review.rating for review in reviews]) / len(reviews)

    # Handle the review submission form
    if request.method == 'POST':
        rating = request.form.get('rating')
        comment = request.form.get('comment')

        if rating and comment:
            new_review = Review(
                rating=int(rating),
                comment=comment,
                book_id=book.id,
                user_id=current_user.id
            )
            db.session.add(new_review)
            db.session.commit()
            flash('Review added successfully!', category='success')
            return redirect(url_for('views.book_details', book_id=book.id))  # Redirect to the same page to show the new review

    return render_template('book_details.html', book=book, reviews=reviews, average_rating=average_rating)
########### EDIT BOOK ##############
@views.route('/book/<int:book_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)

    # Ensure the logged-in user is the seller of the book
    if book.seller_id != current_user.id:
        flash("You can only edit your own books.", "danger")
        return redirect(url_for('book.book_details', book_id=book.id))

    if request.method == 'POST':
        book.title = request.form['title']
        book.description = request.form['description']
        book.price = request.form['price']
        book.genre = request.form['genre']
        
        # Handle file upload for book image
        if 'image' in request.files:
            image = request.files['image']
            if image and allowed_file(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                book.image = filename
        
        db.session.commit()
        flash('Book details updated successfully!', 'success')
        return redirect(url_for('book.book_details', book_id=book.id))

    return render_template('edit_book.html', book=book)
######## ALL BOOKS ##########################
@views.route('/all_books')
def all_books():
    # Fetch all books from the database
    books = Book.query.all()
    
    return render_template('all_books.html', books=books)

###### FAV PART ###################

########### DELETE BOOK ##############
# from flask import Blueprint, render_template, session
# from flask_login import login_required, current_user
# from .models import FavoriteRecipe, MealPlan, Tag
# from datetime import datetime, timedelta
# import datetime
# from flask import Blueprint, render_template, request, flash, redirect, url_for
# from flask_login import login_required, current_user
# from . import db
# from .models import MealPlan, Recipe, Ingredient, Instruction
# from werkzeug.utils import secure_filename

# views = Blueprint('views', __name__)

# @views.route('/')
# def home():
#     if current_user.is_authenticated:
#         return redirect(url_for('views.dashboard'))
#     return render_template('index.html')


# @views.route('/login', methods=['GET'])
# def login():
#     return render_template('login_signup.html')


# from datetime import datetime, timedelta, date  # Ensure you import timedelta here


# @views.route('/dashboard')
# @login_required
# def user_dashboard():
#     today = datetime.today()
#     start_of_week = today - timedelta(days=today.weekday())
    
#     meal_plans = MealPlan.query.filter_by(user_id=current_user.id).all()

#     weekly_meals = [
#         {
#             'day': start_of_week + timedelta(days=day),
#             'meals': [meal for meal in meal_plans if meal.date == (start_of_week + timedelta(days=day)).date()]
#         }
#         for day in range(7)
#     ]

#     return render_template('dashboard.html', weekly_meals=weekly_meals, start_of_week=start_of_week)



# import os

# UPLOAD_FOLDER = os.path.join(os.getcwd(), 'MyChef', 'static', 'uploads')
# if not os.path.exists(UPLOAD_FOLDER):
#     os.makedirs(UPLOAD_FOLDER)

# @views.route('/add_recipe', methods=['GET', 'POST'])
# @login_required
# def add_recipe():
#     if request.method == 'GET':
#         return render_template('add_recipe.html', user=current_user)
#     if request.method == 'POST':
#         name = request.form.get('name')
#         description = request.form.get('description')
#         cuisine = request.form.get('cuisine')
#         image = request.files.get('image')  

#         if not name or not cuisine:
#             flash('Name and Cuisine are required!', category='error')
#             return render_template('add_recipe.html', user=current_user)

#         if image:
#             print("I AM HERE")
#             filename = secure_filename(image.filename)
#             image_path = os.path.join(UPLOAD_FOLDER, filename)  # Use the full path
#             image.save(image_path)  # Save image in the uploads folder
#             relative_image_path = f'uploads/{filename}'
#         else:
#             relative_image_path = None

#         new_recipe = Recipe(
#             name=name,
#             description=description,
#             cuisine=cuisine,
#             image=relative_image_path,  # Save relative path to the database
#             rating=0,  # Initialize with 0 rating
#             user_id=current_user.id # Assign the recipe to the logged-in user
#         )
#         db.session.add(new_recipe)
#         db.session.commit()

#         ingredients = request.form.get('ingredients')  # Make sure you collect all ingredients as a comma-separated string
#         for ingredient in ingredients.split(','):
#             new_ingredient = Ingredient(
#                 recipe_id=new_recipe.id,
#                 ingredient=ingredient.strip()
#             )
#             db.session.add(new_ingredient)

#         instructions = request.form.get('instructions')  # Make sure you collect all instructions
#         for step_number, instruction in enumerate(instructions.split('\n'), start=1):
#             new_instruction = Instruction(
#                 recipe_id=new_recipe.id,
#                 step_number=step_number,
#                 instruction=instruction.strip()
#             )
#             db.session.add(new_instruction)

#         db.session.commit()

#         flash('Recipe added successfully!', category='success')
#         return redirect(url_for('views.dashboard'))

#     return render_template('add_recipe.html', user=current_user)


# ######## ALL RECIPES ##############
# from sqlalchemy import func

# from flask import request, render_template
# from . import db
# from .models import Recipe
# import logging

# @views.route('/recipes', methods=['GET', 'POST'])
# def recipes():
#     filters = []
#     name_query = request.args.get('name')  
#     cuisine_query = request.args.get('cuisine')  

#     logging.debug(f"Searching for Name: {name_query}, Cuisine: {cuisine_query}")

#     if name_query:
#         filters.append(Recipe.name.ilike(f'%{name_query}%'))

#     if cuisine_query:
#         filters.append(Recipe.cuisine.ilike(f'%{cuisine_query}%'))

#     logging.debug(f"Final filters: {filters}")

#     filtered_recipes = Recipe.query.filter(*filters).all()

#     logging.debug(f"SQL Query: {str(Recipe.query.filter(*filters))}")

#     return render_template('recipes.html', recipes=filtered_recipes)


# @views.route('/recipe_details/<int:recipe_id>', methods=['GET'])
# def recipe_details(recipe_id):
#     recipe = Recipe.query.get_or_404(recipe_id)
#     average_rating = (
#         db.session.query(func.avg(Review.rating))
#         .filter(Review.recipe_id == recipe_id)
#         .scalar()
#     )
    
#     average_rating = round(average_rating, 1) if average_rating else "No ratings yet"
    
#     return render_template('recipe_details.html', recipe=recipe, average_rating=average_rating)


# @views.route('/my_recipes', methods=['GET'])
# @login_required
# def my_recipes():
#     # Fetch the recipes added by the current user, including reviews and average ratings
#     recipes = db.session.query(
#         Recipe,
#         func.coalesce(func.avg(Review.rating), 0).label('average_rating'),
#         func.count(Review.id).label('review_count')
#     ).outerjoin(Review).filter(Recipe.user_id == current_user.id).group_by(Recipe.id).all()

#     return render_template('my_recipes.html', recipes=recipes)



# @views.route('/delete_recipe/<int:recipe_id>', methods=['POST'])
# @login_required
# def delete_recipe(recipe_id):
#     recipe = Recipe.query.filter_by(id=recipe_id, user_id=current_user.id).first()
#     if recipe:
#         db.session.delete(recipe)
#         db.session.commit()
#         flash('Recipe deleted successfully!', category='success')
#     else:
#         flash('Recipe not found or you are not authorized to delete it.', category='error')
#     return redirect(url_for('views.my_recipes'))

# ####################################



# ######## Handle Chatbot ################
# def generate_response(user_message):
#     if "hello" in user_message.lower():
#         return "Hi there! How can I help you today?"
#     elif "recipe" in user_message.lower():
#         return "I can help you with recipes. What type of cuisine are you interested in?"
#     else:
#         return "I'm not sure I understand. Can you please rephrase?"

# @views.route('/chatbot', methods=['GET'])
# def chatbot():
#     return render_template('chatbot.html')

# @views.route('/temp', methods=['GET'])
# def temp():
#     return render_template('temp.html')

# from flask import jsonify

# @views.route('/chat', methods=['POST'])
# def chat():
#     user_message = request.json.get('message')
#     response = generate_response(user_message)
#     return jsonify({'response': response})


# @views.route('/dashboard')
# @login_required
# def dashboard():
#     meal_plans = MealPlan.query.filter_by(user_id=current_user.id).all()
    
#     today = datetime.today()
#     start_of_week = today - datetime.timedelta(days=today.weekday()) 
#     end_of_week = start_of_week + datetime.timedelta(days=6)  
    
#     weekly_meals = [meal for meal in meal_plans if start_of_week <= meal.date <= end_of_week]

#     return render_template('dashboard.html', meals=weekly_meals, start_of_week=start_of_week)


# from flask import  request

# # views.py
# from flask import render_template, request, redirect, url_for
# from .models import MealPlan, Recipe
# from flask_login import login_required, current_user

# @views.route('/add_meal', methods=['GET', 'POST'])
# @login_required
# def add_meal():
#     if request.method == 'POST':
#         name = request.form['name']
#         date_string = request.form['date'] 
#         recipe_id = request.form['recipe_id']
        
#         date_object = datetime.strptime(date_string, '%Y-%m-%d').date()

#         meal_plan = MealPlan(
#             name=name,
#             date=date_object,
#             user_id=current_user.id,  
#             recipe_id=recipe_id
#         )

#         db.session.add(meal_plan)
#         db.session.commit()

#         flash('Meal added successfully!', category='success')
#         return redirect(url_for('views.user_dashboard'))  # Redirect to user dashboard

#     recipes = Recipe.query.all()
#     return render_template('add_meal.html', recipes=recipes)



# # Route for removing a meal
# @views.route('/remove_meal/<int:meal_id>/<date>', methods=['POST'])
# def remove_meal(meal_id, date):
#     meal = MealPlan.query.get(meal_id)  
#     if meal:
#         db.session.delete(meal)
#         db.session.commit()
#         return jsonify({'success': True})
#     return jsonify({'success': False})

# # Route for replacing a meal
# @views.route('/replace_meal/<int:meal_id>/<date>', methods=['POST'])
# def replace_meal(meal_id, date):
#     data = request.get_json()
#     new_recipe_name = data.get('newRecipeName')

#     new_recipe = Recipe.query.filter_by(name=new_recipe_name).first()

#     if new_recipe:
#         meal = MealPlan.query.get(meal_id)  
#         if meal:
#             meal.recipe = new_recipe
#             db.session.commit()
#             return jsonify({'success': True})
#     return jsonify({'success': False})

# from .models import Review
# ########## Review Part ##########
# @views.route('/recipe_details/<int:recipe_id>/add_review', methods=['POST'])
# @login_required
# def add_review(recipe_id):
#     rating = request.form.get('rating')
#     comment = request.form.get('comment')
#     review = Review(
#         recipe_id=recipe_id,
#         user_id=current_user.id,
#         rating=rating,
#         comment=comment
#     )
#     db.session.add(review)
#     db.session.commit()
#     return redirect(url_for('views.recipe_details', recipe_id=recipe_id))
# ##################################


# ######views for fav recipe#######

# @views.route('/favorite/<int:recipe_id>', methods=['POST'])
# @login_required
# def favorite_recipe(recipe_id):
#     recipe = Recipe.query.get(recipe_id)
#     if not recipe:
#         flash("Recipe not found!", category='error')
#         return redirect(url_for('views.recipes'))  
    
#     existing_favorite = FavoriteRecipe.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    
#     if existing_favorite:
#         flash("Recipe is already in your favorites!", category='info')
#     else:
#         favorite = FavoriteRecipe(user_id=current_user.id, recipe_id=recipe_id)
#         db.session.add(favorite)
#         db.session.commit()
#         flash("Recipe added to favorites!", category='success')
    
#     return redirect(request.referrer)  




# @views.route('/favorites')
# @login_required
# def favorites():
#     user_id = current_user.id
    
#     favorited_recipes = FavoriteRecipe.query.filter_by(user_id=user_id).join(Recipe).all()
#     return render_template('favorites.html', recipes=[fav.recipe for fav in favorited_recipes])



# @views.route('/unfavorite/<int:recipe_id>', methods=['POST'])
# @login_required
# def unfavorite_recipe(recipe_id):
#     favorite = FavoriteRecipe.query.filter_by(user_id=current_user.id, recipe_id=recipe_id).first()
    
#     if favorite:
#         db.session.delete(favorite)
#         db.session.commit()
#         flash('Recipe removed from favorites.', 'success')
#     else:
#         flash('Recipe not found in your favorites.', 'error')
    
#     return redirect(url_for('views.favorites'))