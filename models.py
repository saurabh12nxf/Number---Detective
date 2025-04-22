from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# Setup database
db = SQLAlchemy()

class User(db.Model):
    """User model for storing user information"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    game_sessions = db.relationship('GameSession', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.username}>'
        
class GameSession(db.Model):
    """Game session model for tracking sessions"""
    __tablename__ = 'game_sessions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    start_time = db.Column(db.DateTime, default=datetime.now)
    end_time = db.Column(db.DateTime, nullable=True)
    predictions = db.relationship('Prediction', backref='session', lazy=True)
    
    def __repr__(self):
        return f'<GameSession {self.id}>'
        
class Prediction(db.Model):
    """Prediction model for tracking AI predictions"""
    __tablename__ = 'predictions'
    
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('game_sessions.id'), nullable=False)
    sequence = db.Column(db.JSON, nullable=False)  # Store the number sequence as JSON
    prediction = db.Column(db.Integer, nullable=False)
    correct_number = db.Column(db.Integer, nullable=True)  # Null until user provides correction
    method = db.Column(db.String(100), nullable=False)  # The method used for prediction
    confidence = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)
    was_correct = db.Column(db.Boolean, nullable=True)  # Was the prediction correct?
    
    def __repr__(self):
        return f'<Prediction {self.id} - {"Correct" if self.was_correct else "Incorrect" if self.was_correct is not None else "Unknown"}>'
        
class LearningPattern(db.Model):
    """Model to store learned patterns for the AI"""
    __tablename__ = 'learning_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    pattern_key = db.Column(db.String(255), unique=True, nullable=False)  # String representation of sequence
    next_number = db.Column(db.Integer, nullable=False)  # The correct next number 
    frequency = db.Column(db.Integer, default=1)  # How many times this pattern has been seen
    last_used = db.Column(db.DateTime, default=datetime.now)  # When this pattern was last used
    
    def __repr__(self):
        return f'<LearningPattern {self.pattern_key} -> {self.next_number}>'