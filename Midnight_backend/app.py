import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from flask_marshmallow import Marshmallow
from flask_cors import CORS
from sqlalchemy.orm import joinedload
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema


load_dotenv()

db = SQLAlchemy()

app = Flask(__name__)

url = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_DATABASE_URI"] = url
# app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

ma = Marshmallow(app)

CORS(app)


class Player(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100))
    score = db.Column(db.Integer, nullable=True)
    round_id = db.Column(db.Integer, db.ForeignKey("round.id"), nullable=True)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=True)
    # is_active = db.Column(db.Boolean, default=False)
    is_winner = db.Column(db.Boolean, default=False)

    def __init__(self, name, score, is_winner, round_id, game_id):
        self.name = name
        self.score = score
        # self.is_active = is_active
        self.is_winner = is_winner
        self.round_id = round_id
        self.game_id = game_id


class PlayerSchema(SQLAlchemyAutoSchema):
    class Meta:
      model = Player


player_schema = PlayerSchema()


class Card(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    suit = db.Column(db.String(50), nullable=True)
    rank = db.Column(db.String(50), nullable=True)
    value = db.Column(db.Integer)
    deck_id = db.Column(db.Integer, db.ForeignKey("deck.id"), nullable=True)
    is_drawn = db.Column(db.Boolean, default=False)

    def __init__(self, suit, rank, value, deck_id, is_drawn):
        self.suit = suit
        self.rank = rank
        self.value = value
        self.deck_id = deck_id
        self.is_drawn = is_drawn


class CardSchema(SQLAlchemyAutoSchema):
    class Meta:
       model = Card


card_schema = CardSchema()
class Deck(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cards = relationship("Card", backref="deck")
    shuffled = db.Column(db.Boolean, default=False)
    game_id = db.Column(db.Integer, db.ForeignKey("game.id"), nullable=True)

    def __init__(self, cards, shuffled, game_id):
        self.cards = cards
        self.shuffled = shuffled
        self.game_id = game_id


class DeckSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Deck

deck_schema = DeckSchema()

class Round(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    number = db.Column(db.Integer)
    players = db.Column(db.Integer, nullable=True)

    def __init__(self, number, players):
        self.number = number
        self.players = players


class RoundSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Round


round_schema = RoundSchema()

class Game(db.Model):
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50))
    players = relationship("Player", backref="game")
    deck = relationship("Deck", backref="game")

    def __init__(self, name, players, deck):
        self.name = name
        self.players = players
        self.deck = deck

class GameSchema(SQLAlchemyAutoSchema):
    class Meta:
        model = Game 

game_schema = GameSchema()

@app.get("/")
def home():
    return "Hello world!"


# creates a new card
@app.post("/card")
def create_card():
    suit = request.json["suit"]
    rank = request.json["rank"]
    value = request.json["value"]
    deck_id = request.json["deck_id"]
    is_drawn = request.json["is_drawn"]

    new_card = Card(suit, rank, value, deck_id, is_drawn)

    db.session.add(new_card)
    db.session.commit()

    return jsonify(card_schema.dump(new_card))


# gets all cards
@app.get("/card")
def get_cards():
    cards = card_schema.dump(Card.query.all(),many=True)
    return jsonify(cards)


# get a single card
@app.get("/card/<id>")
def get_card(id):
    card = Card.query.get(id)
    return jsonify(card_schema.dump(card))


@app.delete("/card/<id>")
def delete_card(id):
    Card.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify(id)


@app.patch("/card/<id>")
def update_card(id):
    Card.query.filter_by(id=id).update(request.json)
    db.session.commit()
    card = Card.query.get(id)
    return jsonify(card_schema.dump(card))


with app.app_context():
    db.create_all()


# create a new_player
@app.post("/player")
def create_player():
    # id = request.json["id"]
    name = request.json["name"]
    score = request.json["score"]
    round_id = request.json["round_id"]
    game_id = request.json["game_id"]
    # is_active = request.json["is_active"]
    is_winner = request.json["is_winner"]

    new_player = Player(name, score, is_winner, round_id, game_id, )

    db.session.add(new_player)
    db.session.commit()

    return jsonify(player_schema.dump(new_player))


@app.get("/player")
def get_players():
    players = player_schema.dump(Player.query.all(), many=True)
    return jsonify(players)


@app.get("/player/<id>")
def get_player(id):
    player = Player.query.get(id)
    return jsonify(player_schema.dump(player))


@app.delete("/player/<id>")
def delete_player(id):
    Player.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify(id)


@app.patch("/player/<id>")
def update_player(id):
    Player.query.filter_by(id=id).update(request.json)
    db.session.commit()
    player = Player.query.get(id)
    return jsonify(player_schema.dump(player))


@app.post("/game")
def create_game():
    # id = request.json["id"]
    name = request.json["name"]
    # score = request.json["score"]
    players = request.json["players"]
    deck = request.json["deck"]

    new_game = Game(name, players, deck)

    db.session.add(new_game)
    db.session.commit()

    return jsonify(game_schema.dump(new_game))


@app.get("/game")
def get_games():
    games = Game.query.all()

    # Filter out 'Deck' and 'Players' from each game in the list
    modified_games = [
        {
            'id': game.id,
            'name': game.name,
            "players": player_schema.dump(game.players, many=True),
            "deck": deck_schema.dump(game.deck,many=True)
        }
        for game in games
    ]

    return jsonify(modified_games)


@app.get("/game/<id>")
def get_game(id):
    game = Game.query.get(id)
    return jsonify(game_schema.dump(game))


@app.delete("/game/<id>")
def delete_game(id):
    Game.query.filter_by(id=id).delete()
    db.session.commit()
    return game_schema.jsonify(id)


@app.patch("/game/<id>")
def update_game(id):
    Game.query.filter_by(id=id).update(request.json)
    db.session.commit()
    game = Game.query.get(id)
    return jsonify(game_schema.dump(game))

@app.post('/deck')
def create_deck():
    form = request.get_json()
    cards = form.get('cards')
    shuffled = form.get('shuffled')
    game_id = form.get('game_id')

    # Ensure cards is a list
    if not isinstance(cards, list):
        return jsonify({'error': 'cards must be a list'}), 400

    # Create a new deck
    new_deck = Deck(cards, shuffled, game_id)

    # Save the deck to the database
    db.session.add(new_deck)
    db.session.commit()

    return jsonify(deck_schema.dump(new_deck))

@app.get("/deck")
def get_decks():
    
 decks = Deck.query.all()
 modified_decks = [
        {
            'id': deck.id,  # Include other fields as needed
            'cards': card_schema.dump(deck.cards, many=True),
            'shuffled': deck.shuffled
        }
        for deck in decks
    ]
 return jsonify(modified_decks)



@app.get("/deck/<id>")
def get_deck(id):
    deck = Deck.query.get(id)
    return jsonify(deck_schema.dump(deck))


@app.delete("/deck/<id>")
def delete_deck(id):
    Deck.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify(id)


@app.patch("/deck/<id>")
def update_deck(id):
    Deck.query.filter_by(id=id).update(request.json)
    db.session.commit()
    deck = Deck.query.get(id)
    return jsonify(deck_schema.dump(deck))


@app.post("/round")
def create_round():
    # id = request.json["id"]
    number = request.json["number"]
    players = request.json["players"]

    new_round = Round(number, players)

    db.session.add(new_round)
    db.session.commit()

    return jsonify(round_schema.dump(new_round))


@app.get("/round")
def get_rounds():
    rounds = round_schema.dump(Round.query.all(), many=True)
    return jsonify(rounds)


@app.get("/round/<id>")
def get_round(id):
    round = Round.query.get(id)
    return jsonify(round_schema.dump(round))


@app.delete("/round/<id>")
def round_deck(id):
    Round.query.filter_by(id=id).delete()
    db.session.commit()
    return jsonify(id)


@app.patch("/round/<id>")
def update_round(id):
    Round.query.filter_by(id=id).update(request.json)
    db.session.commit()
    round = round_schema.dump(Round.query.get(id))
    return jsonify(round)
