from flask import Flask, render_template, flash,logging, request, redirect, url_for, session, logging
from flask_mysqldb import MySQL
from wtforms import Form, StringField, TextAreaField, PasswordField, validators
from passlib.hash import sha256_crypt
from flask_bootstrap import Bootstrap
from functools import wraps

app = Flask(__name__)
Bootstrap(app)
# configuring mysql
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'leondike23'
app.config['MYSQL_DB'] = 'myflaskapp'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'

#initialise MYSQL
mysql = MySQL(app)


# Articles = Articles()

@app.route('/')
def home():
	return render_template('home.html')

@app.route('/about')
def about():
	return render_template('about.html')

@app.route('/articles')
def articles():
	cur = mysql.connection.cursor()
	#Get Articles
	result = cur.execute(" SELECT * FROM articles")

	articles = cur.fetchall()

	if result >0:
		return render_template('articles.html', articles=articles)
	else:
		msg = 'No Articles Found'
		return render_template('articles.html', msg=msg)
	# Close connection
	cur.close()

	return render_template('articles.html', articles=Articles)

@app.route('/article/<string:id>/')
def article(id):
	cur = mysql.connection.cursor()

	#Get Article
	result = cur.execute("SELECT * FROM  articles WHERE id=%s", [id])

	article = cur.fetchone()

	return render_template('article.html', article=article)


class RegisterForm(Form):
	name = StringField('Name', [validators.Length(min=1, max=50)])
	username = StringField('Username', [validators.Length(min=4, max=25)])
	email = StringField('Email', [validators.Length(min=6, max=50)])
	password = PasswordField('Password', [
		validators.DataRequired(),
		validators.EqualTo('confirm', message = 'Passwords do not match')])
	confirm = PasswordField('Confirm Password')

@app.route('/register', methods=['GET', 'POST'])
def register():
	form = RegisterForm(request.form)
	if request.method=='POST' and form.validate():
		name = form.name.data
		email = form.email.data
		username = form.username.data
		password = sha256_crypt.encrypt(str(form.password.data))

		#Create a cursor
		cur = mysql.connection.cursor()
		#Adding a new user to the table users
		cur.execute("INSERT INTO users(name, email, username, password) \
			VALUES(%s, %s, %s, %s)",(name, email, username, password))
			#commit to DB
		mysql.connection.commit()
		cur.close()

		flash('You are now registered and can login', 'success')
		return redirect(url_for('login'))
		

	return render_template('register.html', form=form)

	#User login
@app.route('/login', methods=['GET', 'POST'])
def login():
	if request.method  == 'POST':
		#GET FORM FIELDS
		username = request.form['username']
		password_candidate = request.form['password']
		#Cursor creation
		cur = mysql.connection.cursor()
		#get user by username
		result = cur.execute("SELECT * FROM users WHERE username=%s", [username])

		if result > 0:
			#get the stored hash
			data = cur.fetchone()
			password = data['password']

			#Compare the passwords
			if sha256_crypt.verify(password_candidate, password):
				#success
				session['logged_in'] = True
				session['username'] = username\

				flash('You are now logged in', 'success')
				return redirect(url_for('dashboard'))
				

			else:
				error = 'Invalid username and password combination'
				return render_template('login.html', error=error)
			# Closing the database connection for the login system
			cur.close()

		else:
			error = 'Username not found'
			return render_template('login.html', error=error)

	return render_template('login.html')

#check if user is logged in
def is_logged_in(f):
	@wraps(f)
	def wrap(*args, **kwargs):
		if 'logged_in' in session:
			return f(*args, **kwargs)
		else:
			flash('Unauthorised, Please login', 'danger')
			return redirect(url_for('login'))
	return wrap


#Logout
@app.route('/logout')
def logout():
	session.clear()
	flash('You are now logged out', 'success')
	return redirect(url_for('login'))

#Dashboard
@app.route('/dashboard')
@is_logged_in
def dashboard():
	cur = mysql.connection.cursor()
	#Get Articles
	result = cur.execute(" SELECT * FROM articles")

	articles = cur.fetchall()

	if result >0:
		return render_template('dashboard.html', articles=articles)
	else:
		msg = 'No Articles Found'
		return render_template('dashboard.html', msg=msg)
	# Close connection
	cur.close()

class ArticleForm(Form):
	title = StringField('title', [validators.Length(min=1, max=200)])
	body = TextAreaField('Body', [validators.Length(min=30)])
	
#Add Article
@app.route('/add_article', methods=['GET', 'POST'])
@is_logged_in
def add_article():
	form = ArticleForm(request.form)
	if request.method == 'POST' and form.validate():
		title = form.title.data
		body = form.body.data

		#Create cursor
		cur = mysql.connection.cursor()

		#Execute an insert into articles table
		cur.execute("INSERT INTO articles(title, body, author) VALUES(%s, %s, %s)",(title,body,session['username']))
		mysql.connection.commit()
		cur.close()
		flash('Article Created', 'success')
		return redirect(url_for('dashboard'))

	return render_template('add_article.html', form=form)

@app.route('/edit_article/<string:id>', methods=['GET', 'POST'])
@is_logged_in
def edit_article(id):
	#Create cursor
	cur = mysql.connection.cursor()

	#Get article by id
	result = cur.execute("SELECT * FROM articles WHERE id=%s",[id])
	article = cur.fetchone()

	#Get form
	form = ArticleForm(request.form)

	#Populate article fieds
	form.title.data = article['title']
	form.body.data = article['body']

	if request.method == 'POST' and form.validate():
		title = request.form['title']
		body = request.form['body']

		#Create cursor
		cur = mysql.connection.cursor()

		#Execute an insert into articles table
		cur.execute("UPDATE articles SET title=%s,body=%s WHERE id=%s", (title,body,id))
		mysql.connection.commit()
		cur.close()
		flash('Article Updated', 'success')
		return redirect(url_for('dashboard'))

	return render_template('edit_article.html', form=form)

@app.route('/delete_article/<string:id>', methods=['POST'])
@is_logged_in
def delete_article(id):
	cur = mysql.connection.cursor()
	cur.execute("DELETE FROM articles WHERE id=%s", [id])
	mysql.connection.commit()
	cur.close()

	flash('Article Deleted', 'success')
	return redirect(url_for('dashboard'))

if __name__=='__main__':
	app.secret_key='secret123'
	app.run(debug=True)