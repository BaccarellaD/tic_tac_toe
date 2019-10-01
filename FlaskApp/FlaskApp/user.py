import datetime
import uuid
from flask_login import UserMixin
from flask_pymongo import PyMongo
from flask_login import current_user, login_user, logout_user, login_required

class User(UserMixin, ):

    def __init__(self, username, email, password, auth_string, confirmed=None,_id=None, game_active=False, active_game_id="-1", game_start_date=None):

        self.username = username
        self.email = email
        self.password = password
        self._id = uuid.uuid4().hex if _id is None else _id
        self.auth_string = auth_string
        self.confirmed = confirmed if confirmed is not None else False
        self.game_active = game_active
        self.active_game_id = active_game_id
        self.game_start_date = None
        self.board = []
        if game_active:
            self.load_active_game(active_game_id)

    def save(self):
        from .__init__ import mongo
        users = mongo.db.users
        user = users.find_one({'username' : self.username})
        confirmed = str(self.confirmed)
        game_active = str(self.game_active)

        if user is None:
            users.insert_one({'username' : self.username, 'email' : self.email, 'password' : self.password, 'auth_string' : self.auth_string,  'confirmed' : confirmed, '_id' : self._id, 'game_active' : game_active, 'game_id' : self.active_game_id})
        else:
            users.replace_one({'username' : self.username},
                              {'username' : self.username, 'email' : self.email, 'password' : self.password, 'auth_string' : self.auth_string, 'confirmed' : confirmed, '_id' : self._id, 'game_active' : game_active, 'game_id' : self.active_game_id})

        if self.game_active:
            self.save_game()

    def load_active_game(self, active_game_id):
        from .__init__ import mongo
        games = mongo.db.games
        game = games.find_one({'game_id' : self.active_game_id})

        if game is not None:
            self.game_active = True
            self.board = game['board']
            self.active_game_id = game['game_id']
            self.game_start_date = game['game_start_date']
        else:
            print('TRIED TO LOAD A GAME THAT DOES NOT EXIST')

    def save_game(self):
        from .__init__ import mongo
        games = mongo.db.games
        game = games.find_one({'game_id' : self.active_game_id})

        if game is None:
            games.insert_one({'username': self.username, 'game_id' : self.active_game_id, 'game_start_date' : self.game_start_date, 'board' : self.board})
        else:
            games.replace_one({'game_id' : self.active_game_id}, {'username': self.username, 'game_id' : self.active_game_id, 'game_start_date' : self.game_start_date,  'board' : self.board})

    def start_new_game(self):
        if self.game_active:
            self.save_game()
        #clear the board
        self.board = []
        for x in range(9):
            self.board.append(' ')

        self.game_start_date = datetime.datetime.now()
        self.active_game_id =  uuid.uuid4().hex
        self.game_active = True

    @staticmethod
    def load(username):
        from .__init__ import mongo
        users = mongo.db.users
        user = users.find_one({'username': username})
        if user is None:
            return None

        if(user['confirmed'] == 'True'):
            confirmed = True
        else:
            confirmed = False

        if(user['game_active'] == 'True'):
            game_active = True
        else:
            game_active = False

        user_instance = User(user['username'], user['email'], user['password'], user['auth_string'], confirmed, user['_id'], game_active=game_active, active_game_id=user['game_id'])
        if game_active:
            user_instance.load_active_game(user_instance.active_game_id)

        return user_instance

    @staticmethod
    def is_authenticated():
        return True

    @staticmethod
    def is_active():
        return True

    @staticmethod
    def is_anonymous():
        return False

    def get_id(self):
        return self.username
