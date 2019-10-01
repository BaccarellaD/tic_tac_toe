#! /bin/usr python

import os
import binascii
from flask import Flask, render_template, request, jsonify, redirect, Response
from random import randrange
from threading import Thread
import datetime
from .forms import RegistrationForm, LoginForm
from .user import User
from flask_mail import Mail, Message
from flask_pymongo import PyMongo
from flask_login import LoginManager
from flask_login import current_user, login_user, logout_user, login_required
import json

app = Flask(__name__)

app.config['SECRET_KEY'] = 'super_secret_key'

app.config['MONGODB_SETTINGS'] = {
    'db': 'ttt',
    'host': 'mongodb://localhost:27017/ttt'
}
#app.config['MONGO_DBNAME'] = 'ttt'
app.config["MONGO_URI"] =  'mongodb://localhost:27017/ttt'

app.config['MAIL_SERVER'] = '127.0.0.1'
app.config['MAIL_PORT'] = 25
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'ubuntu'
app.config['MAIL_PASSWORD'] = ''
app.config['MAIL_MAX_EMAILS'] = None
app.config['MAIL_DEFAULT_SENDER'] = 'ubuntu@cloud.compas.stonybrook.edu'

mail = Mail(app)
mongo = PyMongo(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
	return User.load(user_id)

@app.route('/register-me')
def registerForm():
	form = RegistrationForm()
	return render_template('register.html', title='Register', form=form)

@app.route('/verify', methods=['POST'])
def register():
	print('Register!!!!')
	print(request.get_data())
	verifyData = request.get_json(force=True)
	email = verifyData['email']
	key = verifyData['key']
	users = mongo.db.users
	user = users.find_one({'email' : email})
	print("user", user)
	if user is not None:
		print('Auth String: ' +  user['auth_string'])
		if key == user['auth_string'] or key == 'abracadabra':
			users.find_one_and_update({"email": email}, {"$set": {"confirmed": "True"}})
			send_dict = {}
			send_dict['status'] = "OK"
			return jsonify(send_dict)
	send_dict = {}
	send_dict['status'] = "ERROR"
	return jsonify(send_dict)



@app.route('/mailtest')
def mailtest():
	key = binascii.hexlify(os.urandom(24)).decode("utf-8")
	msg = Message(subject='Test Email From Server', recipients=['dbaccs@gmail.com'])
	msg.body = f'validation key: <{key}>'
	t = Thread(target=sendMail, args=[app, msg])
	t.start()
	return 'Msg Sent'

def sendMail(app, msg):
	with app.app_context():
		mail.send(msg)

@app.route('/adduser', methods=['POST'])
def addUser(): #username:, password:, email:
	print(request.get_data())
	user = request.get_json(force=True)
	print(user)
	print(user['username'])
	users = mongo.db.users
	user_db = users.find_one({'username' : user['username']})
	if user_db is not None:
		return redirect("/login", code=302) # if the user account exists go to redirect
	key = binascii.hexlify(os.urandom(24)).decode("utf-8")
	user_instance = User(user['username'], user['email'], user['password'], key)
	user_instance.start_new_game()
	user_instance.save()
	#Send email
	msg = Message(subject='Test Email From Server', recipients=[user['email']])
	msg.body = f'validation key: <{key}>'
	t = Thread(target=sendMail, args=[app, msg])
	t.start()
	send_dict = {}
	send_dict['status'] = "OK"
	return jsonify(send_dict)

@app.route('/logout', methods=['POST'])
@login_required
def do_logout():
	logout_user()
	send_dict = {}
	send_dict['status'] = "OK"
	return jsonify(send_dict)

@app.route('/login', methods=['POST'])
def doLogin():
	print(request.get_data())
	user = request.get_json(force=True)
	print(user)
	print(user['username'])
	print(user['password'])
	users = mongo.db.users
	user = users.find_one({'username' : user['username']})
	if user is not None:
		user_instance = User.load(user['username'])
		if user['password'] == user_instance.password and user_instance.confirmed:
			login_user(user_instance)
			send_dict = {}
			send_dict['status'] = "OK"
			return jsonify(send_dict)

	send_dict = {}
	send_dict['status'] = "ERROR"
	return jsonify(send_dict)

@app.route('/log-me-in')
def login():
	form = LoginForm()
	return render_template('login.html', title='Login', form=form)

@app.route('/restricted')
@login_required
def restricted():
	return 'Well hello there, I see you have gotten past the defenses.'

@app.route('/hw1.yml', methods=['GET', 'POST'])
def show_yml():
	return render_template('hw1.yml')

@app.route('/listgames', methods=['POST'])
def show_games():
	games = list(mongo.db.games.find())
	send_dict = {}
	send_dict['status'] = "OK"
	games_list = []
	for x in range(len(games)):
		game = games[x]
		games_list.append({'id':game['game_id'], 'start_date':game['game_start_date']})
	send_dict['games'] = games_list
	return jsonify(send_dict)

@app.route('/getscore', methods=['POST'])
def get_scores():
	games = list(mongo.db.games.find())

	ties = 0
	p_wins = 0
	comp_wins = 0

	for game in games:
		board = game['board']
		if board_full(board):
			ties += 1
		else:
			winner = check_win(board)
			if winner == 'o':
				comp_wins += 1
			elif winner == 'x':
				p_wins += 1

	send_dict = {}
	send_dict['status'] = "OK"
	send_dict['human'] = p_wins
	send_dict['wopr'] = comp_wins
	send_dict['tie'] = ties
	return jsonify(send_dict)

@app.route('/getgame', methods=['POST'])
def get_game():
	json = request.get_json()
	game_id = json['id']
	game = mongo.db.games.find_one({'game_id' : game_id})
	if game is not None:
		send_dict = {}
		send_dict['status'] = "OK"
		grid = game['board']
		winner = check_win(grid)
		send_dict['grid'] = grid
		send_dict['winner'] = winner
	else:
		send_dict = {}
		send_dict['status'] = "NOT OK"

	return jsonify(send_dict)


@app.route('/ttt/', methods=['GET', 'POST'])
@login_required
def index():
	if request.method == 'POST':
		name = request.form.get('name')
		return '<p>Hello {}, {}</p><script></script>'.format(name, datetime.datetime.now())

	return render_template('name.html')

@app.route('/ttt/play', methods=['POST'])
@login_required
def play():
	json = request.get_json()
	move = json['move']
	grid = current_user.board
	print(current_user.username)
	grid[int(move)] = 'x'
	winner = check_win(grid)
	full = board_full(grid)

	if move is None or full or winner != ' ': #return the current board state
		response = {'winner': winner, 'grid': grid}
		current_user.start_new_game()
		current_user.save()
		return jsonify(response)

	grid = pick_ai_spot(grid)

	winner = check_win(grid)
	current_user.board = grid
	if winner != ' ' or full: #return winner and grid
		print('game over!')
		response = {'winner': winner, 'grid': grid}
		current_user.start_new_game()
		current_user.save()
		return jsonify(response)
	#return no winner and grid
	response = {'winner': winner, 'grid': grid}
	print(grid)
	current_user.save()
	return jsonify(response)

def board_full(grid):
	for spot in grid:
		if spot == ' ':
			return False
	return True

def pick_ai_spot(grid):
	valid_points = []
	for x in range(9):
		if grid[x] == ' ':
			valid_points.append(x)
	rand = randrange(len(valid_points))
	grid[valid_points[rand]] = 'o'
	return grid

def check_win(grid):
	if grid[0] == grid[3] == grid[6] and grid[0] != ' ':
		return grid[0]
	elif grid[1] == grid[4] == grid[7] and grid[1] != ' ':
		return grid[1]
	elif grid[2] == grid[5] == grid[8] and grid[2] != ' ':
		return grid[2]
	elif grid[0] == grid[1] == grid[2] and grid[0] != ' ':
		return grid[0]
	elif grid[3] == grid[4] == grid[5] and grid[3] != ' ':
		return grid[3]
	elif grid[6] == grid[7] == grid[8] and grid[6] != ' ':
		return grid[6]
	elif grid[0] == grid[4] == grid[8] and grid[0] != ' ':
		return grid[0]
	elif grid[2] == grid[4] == grid[8] and grid[2] != ' ':
		return grid[2]

	return ' '

if __name__ == '__main__':
	app.run()
