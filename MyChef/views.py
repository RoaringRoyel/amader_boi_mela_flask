from flask import Blueprint, render_template, redirect, url_for,request, flash
from flask_login import login_required, current_user
from .models import Cart, CartItem, Favorite, Sale, BookExchangeRequest
import os
views = Blueprint('views', __name__)
from .models import User,db
from .models import Book,Review, Cart, CartItem, Favorite, Sale, BookExchangeRequest,Blog

@views.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'buyer':
            return redirect(url_for('views.buyer_dashboard'))
        elif current_user.role == 'seller':
            return redirect(url_for('views.seller_dashboard'))
    return render_template('login_signup.html')  

@views.route('/buyer_dashboard')
@login_required
def buyer_dashboard():
    if current_user.role != 'buyer':
        return redirect(url_for('views.index'))  

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

@views.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        email = request.form.get('email')
        profile_picture = request.files.get('profile_picture')

        user = User.query.get(current_user.id)
        user.first_name = first_name
        user.email = email

        if profile_picture:
            profile_pics_folder = os.path.join('MyChef','static', 'profile_pics')
            if not os.path.exists(profile_pics_folder):
                os.makedirs(profile_pics_folder)

            profile_picture_path = os.path.join(profile_pics_folder, profile_picture.filename)
            profile_picture.save(profile_picture_path)

            user.profile_picture = profile_picture.filename

        db.session.commit()

        flash('Profile updated successfully!', category='success')
        return redirect(url_for('views.buyer_dashboard'))  

    return render_template('edit_profile.html', user=current_user)


@views.route('/seller_dashboard')
@login_required
def seller_dashboard():
    if current_user.role != 'seller':
        return redirect(url_for('views.index'))  

    books = Book.query.filter_by(seller_id=current_user.id).all()

    sales = Sale.query.filter_by(seller_id=current_user.id).all()

    pending_requests = BookExchangeRequest.query.filter_by(user_id=current_user.id, status='Pending').all()

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
        return redirect(url_for('views.index'))  

    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        genre = request.form.get('genre')
        price = float(request.form.get('price'))
        is_used = False  
        image = request.files.get('image')  

        new_book = Book(
            title=title,
            author=author,
            description=description,
            genre=genre,
            price=price,
            seller_id=current_user.id,
        )

        if image:
            book_images_folder = os.path.join('MyChef', 'static', 'book_images')
            if not os.path.exists(book_images_folder):
                os.makedirs(book_images_folder)

            image_path = os.path.join(book_images_folder, image.filename)
            image.save(image_path)

            new_book.image = image.filename

        db.session.add(new_book)
        db.session.commit()

        flash('New book posted successfully!', category='success')
        return redirect(url_for('views.seller_dashboard'))  

    return render_template('post_new_book.html', user=current_user)  
######## BOOK REVIEW PART #############
@views.route('/book/<int:book_id>', methods=['GET', 'POST'])
@login_required
def book_details(book_id):
    book = Book.query.get_or_404(book_id)

    reviews = Review.query.filter_by(book_id=book.id).all()

    average_rating = None
    if reviews:
        average_rating = sum([review.rating for review in reviews]) / len(reviews)

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

    if book.seller_id != current_user.id:
        flash("You can only edit your own books.", "danger")
        return redirect(url_for('book.book_details', book_id=book.id))

    if request.method == 'POST':
        book.title = request.form['title']
        book.description = request.form['description']
        book.price = request.form['price']
        book.genre = request.form['genre']
        
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
@views.route('/all_books', methods=['GET'])
def all_books():
    search_query = request.args.get('search_query', '') 

    if search_query:
        books = Book.query.filter(
            (Book.title.ilike(f'%{search_query}%')) |  
            (Book.description.ilike(f'%{search_query}%'))  
        ).all()
    else:
        books = Book.query.all()  

    return render_template('all_books.html', books=books)

# ######## Handle Chatbot ################
def generate_response(user_message):
    if "hello" in user_message.lower():
        return "Hi there! How can I help you today?"
    elif "recipe" in user_message.lower():
        return "I can help you with recipes. What type of cuisine are you interested in?"
    else:
        return "I'm not sure I understand. Can you please rephrase?"

@views.route('/chatbot', methods=['GET'])
def chatbot():
    return render_template('chatbot.html')

@views.route('/temp', methods=['GET'])
def temp():
    return render_template('temp.html')

from flask import jsonify

@views.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message')
    response = generate_response(user_message)
    return jsonify({'response': response})

########## BLOG PART ################

@views.route('/create_blog', methods=['GET', 'POST'])
@login_required
def create_blog():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        new_blog = Blog(
            title=title, 
            content=content, 
            author_id=current_user.id
        )
        db.session.add(new_blog)
        db.session.commit()
        print("New blog post added successfully!")
        blogs = Blog.query.all()
        return render_template('blogs.html', blogs=blogs)

    return render_template('create_blog.html')

@views.route('/blogs')
def all_blogs():
    blogs = Blog.query.all()
    return render_template('blogs.html', blogs=blogs)


@views.route('/blog/<int:blog_id>')
def blog_details(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    return render_template('blog_details.html', blog=blog)

########### CART
@views.route('/add_to_cart/<int:book_id>', methods=['POST'])
@login_required
def add_to_cart(book_id):
    if current_user.role != 'buyer':  
        return redirect(url_for('views.all_books'))  

    book = Book.query.get_or_404(book_id)

    cart = Cart.query.filter_by(user_id=current_user.id, is_active=True).first()  # Ensure `is_active` is checked
    if not cart:
        cart = Cart(user_id=current_user.id)
        db.session.add(cart)
        db.session.commit()

    existing_cart_item = CartItem.query.filter_by(cart_id=cart.id, book_id=book.id).first()
    if existing_cart_item:
        existing_cart_item.quantity += 1
        db.session.commit()
        flash('This book quantity was updated in your cart!', 'info')
    else:
        new_cart_item = CartItem(cart_id=cart.id, book_id=book.id, quantity=1)
        db.session.add(new_cart_item)
        db.session.commit()
        flash('Book added to cart!', 'success')

    return redirect(url_for('views.all_books'))



@views.route('/add_to_favorites/<int:book_id>', methods=['POST'])
@login_required
def add_to_favorites(book_id):
    book = Book.query.get_or_404(book_id)

    existing_favorite = Favorite.query.filter_by(user_id=current_user.id, book_id=book.id).first()
    if existing_favorite:
        flash('This book is already in your favorites!', 'info')
    else:
        new_favorite = Favorite(user_id=current_user.id, book_id=book.id)
        db.session.add(new_favorite)
        db.session.commit()
        flash('Book added to favorites!', 'success')

    return redirect(url_for('views.all_books'))
