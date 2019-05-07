import os
import json
import requests
from flask import Flask, session, request, render_template, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
	raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"), pool_pre_ping=True)
db = scoped_session(sessionmaker(bind=engine))


@app.route("/", methods=['POST', 'GET'])
def index():
	if request.method == "POST":

		book = request.form.get("book")
		books  = db.execute("SELECT * FROM books WHERE title = :book or isbn = :book or author = :book", {"book" : book}).fetchall()
		if books:
			#return render_template("book.html", name= name)
			return render_template("index.html", books = books) 
		else:
			return render_template("index.html", name = "nothing founed")
	return render_template("index.html")

	   

@app.route("/register", methods=["POST", "GET"])
def register():
	if request.method == 'POST':
		email = request.form.get("email")
		username = request.form.get("username")
		checker = db.execute("SELECT email, username FROM users WHERE email = :email or username = :username",{"email":email, "username":username}).fetchone()
		psw = request.form.get("psw")
		pswrepeat = request.form.get("psw-repeat")
		if checker :
			return render_template("registererror.html", error2 = "this email or username are registered before.")
		elif psw != pswrepeat:
			return render_template("registererror.html", error1 = "the password is not matching.")
		else:
			db.execute("INSERT INTO users (email, username, password) VALUES (:email, :username,:psw)", {"email":email, "username":username, "psw":psw})
			db.commit()     
			return redirect(url_for("login"))
	return render_template("register.html")

#user log in
@app.route("/login", methods=['GET', 'POST'])
def login():
	if request.method == 'POST':
		#get form fields
		email = request.form.get("email")
		username = request.form.get('username')
		psw = request.form.get("psw")
		checker = db.execute("SELECT email, password, username FROM users WHERE email = :email and password = :psw and username = :username", {"email":email, "psw":psw, "username":username}).fetchone()
		db.commit()
		if checker:
			session['login'] = True
			session['username'] = username 

			#session['username'] = checker['username']
			return redirect(url_for('index'))
		else:
			error = "somthing went wrong your email or password is not registred"
			return render_template("login.html", error=error)

	return render_template("login.html", error="")

# clear the session and return to the home page 
@app.route("/logout")
def logout():
	session.clear()
	return redirect(url_for("index"))

@app.route("/books/<book>", methods=['GET', 'POST'])
def books(book):
	#book = request.form.get("book")
	#get info for the book
	name  = db.execute("SELECT * FROM books WHERE title = :book", {"book" : book}).fetchone()
	isbn = name[0]
	bookname = name[1]
	bookauther = name[2]
	year = name[3]
	book_id = name[4]
	res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "wUQJfOtm86FHJ1DyXJj1Wg", "isbns": isbn})
	goodreads_info = res.json()
	allinfo = goodreads_info['books'][0]
	rate = allinfo['average_rating']

	#get info for the user 
	username = session['username']
	user_db = db.execute("SELECT * FROM users WHERE  username = :username", {"username":username}).fetchone()
	user_id = user_db.id

	#get reviews
	reviews = db.execute("SELECT title, body, username FROM reviews JOIN users ON users.id = reviews.user_id").fetchall()


	#add reviews
	if request.method == "POST":

		#get rev data
		review = request.form.get("bio")
		title = request.form.get("title")

		#isert review if the user has no review
		checker = db.execute("SELECT * FROM reviews WHERE user_id = :user_id and book_id = :book_id", {"user_id":user_id, "book_id":book_id}).fetchone()

		if checker :
			return render_template("book.html", bookname = bookname, bookauther = bookauther, bookdate = year, rate = rate, book_id= book_id, book=name, reviews = reviews, msg="you can't add another review but you can edit it.")
			
		else:	
			db.execute("INSERT INTO reviews (title, body, user_id, book_id) VALUES (:title, :body, :user_id, :book_id)", {"title":title, "body":review, "user_id":user_id, "book_id":book_id})
			db.commit() 
		return render_template("book.html", bookname = bookname, bookauther = bookauther, bookdate = year, rate = rate, book_id= book_id, book=name, reviews = reviews, msg="you add your review succecfully")	
	
	return render_template("book.html", bookname = bookname, bookauther = bookauther, bookdate = year, rate = rate, book_id= book_id, book=name, reviews = reviews)
			
@app.route("/add_review/<bookname>", methods=['POST','GET'])
def add_review(bookname): 
	return render_template("add_review.html", bookname = bookname)

		
 