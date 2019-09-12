#! /bin/usr python

from flask import Flask, render_template, request, jsonify
from random import randrange
import datetime

app = Flask(__name__)


@app.route('/hw1.yml', methods=['GET', 'POST'])
def show_yml():
	return render_template('hw1.yml')

@app.route('/ttt/', methods=['GET', 'POST'])
def index():
	if request.method == 'POST':
		name = request.form.get('name')
		return '<p>Hello {}, {}</p><script></script>'.format(name, datetime.datetime.now())

	return render_template('name.html')
@app.route('/ttt/play', methods=['POST'])
def play():
	json = request.get_json()
	grid = json['grid']
	winner = check_win(grid)
	if winner != ' ':
		#return winner and grid
		response = {'winner': winner, 'grid': grid}
		return jsonify(response)
	winner = check_win(pick_ai_spot(grid))
	if winner != ' ':
		#return winner and grid
        	response = {'winner': winner, 'grid': grid}
        	return jsonify(response)
	#return no winner and grid
	response = {'winner': winner, 'grid': grid}
	return jsonify(response)

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
