import os
import logging
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from ai_engine import NumberDetectiveAI
from models import db, User, GameSession, Prediction, LearningPattern

# Setup logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "number_detective_secret")

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///number_detective.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the database
db.init_app(app)

# Create all tables
with app.app_context():
    db.create_all()
    
# Create AI engine instance
ai_engine = NumberDetectiveAI()

@app.route('/')
def index():
    """Render the main game page"""
    # Initialize game session if not already done
    if 'game_history' not in session:
        session['game_history'] = []
    
    # Create a new game session in database if not already in session
    if 'session_id' not in session:
        # Try to load patterns from database
        patterns = LearningPattern.query.order_by(
            LearningPattern.frequency.desc()
        ).limit(100).all()
        
        # Load patterns into AI engine for better predictions
        for pattern in patterns:
            try:
                # Convert pattern key string back to tuple format
                pattern_key = eval(pattern.pattern_key)
                ai_engine.trained_patterns[pattern_key] = pattern.next_number
            except Exception as e:
                app.logger.error(f"Error loading pattern: {e}")
                
    # Count some stats for display
    total_predictions = Prediction.query.count()
    correct_predictions = Prediction.query.filter_by(was_correct=True).count()
    patterns_learned = LearningPattern.query.count()
    
    return render_template('index.html', 
                          stats={'total': total_predictions, 
                                'correct': correct_predictions,
                                'patterns': patterns_learned})

@app.route('/predict', methods=['POST'])
def predict():
    """Endpoint to predict the next number in a sequence"""
    data = request.json
    sequence = data.get('sequence', [])
    
    # Convert strings to integers
    try:
        sequence = [int(num) for num in sequence if num.strip()]
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Please enter only numbers in your sequence!'
        })
    
    # Check if we have enough numbers
    if len(sequence) < 3:
        return jsonify({
            'success': False,
            'message': 'Please enter at least 3 numbers to make a prediction!'
        })
    
    # Make prediction
    prediction, confidence, method = ai_engine.predict(sequence)
    
    # Add to session history
    history_entry = {
        'sequence': sequence,
        'prediction': prediction,
        'method': method,
        'confidence': confidence
    }
    session['game_history'] = session.get('game_history', []) + [history_entry]
    session.modified = True
    
    # Store in database - create or get game session
    game_session = None
    if 'session_id' in session:
        game_session = GameSession.query.get(session['session_id'])
    
    # If no session exists, create a new one
    if not game_session:
        game_session = GameSession()
        db.session.add(game_session)
        db.session.commit()
        session['session_id'] = game_session.id
    
    # Store prediction in database
    db_prediction = Prediction(
        session_id=game_session.id,
        sequence=sequence,  # PostgreSQL supports JSON directly
        prediction=prediction,
        method=method,
        confidence=confidence
    )
    db.session.add(db_prediction)
    db.session.commit()
    
    # Store prediction ID in session for later reference
    session['last_prediction_id'] = db_prediction.id
    
    return jsonify({
        'success': True,
        'prediction': prediction,
        'confidence': confidence,
        'method': method
    })

@app.route('/correct', methods=['POST'])
def correct():
    """Endpoint to provide the correct next number and train the AI"""
    data = request.json
    sequence = data.get('sequence', [])
    correct_number = data.get('correct_number')
    
    # Convert strings to integers
    try:
        sequence = [int(num) for num in sequence if num.strip()]
        correct_number = int(correct_number)
    except ValueError:
        return jsonify({
            'success': False,
            'message': 'Please use only numbers!'
        })
    
    # Train the AI with correct data
    pattern_key = ai_engine.learn(sequence, correct_number)
    
    # Update the session history
    if 'game_history' in session and session['game_history']:
        last_entry = session['game_history'][-1]
        last_entry['correct_number'] = correct_number
        last_entry['was_correct'] = (last_entry['prediction'] == correct_number)
        session.modified = True
    
    # Update database
    was_correct = (ai_engine.last_prediction == correct_number)
    
    # Update the prediction record if it exists
    if 'last_prediction_id' in session:
        prediction = Prediction.query.get(session['last_prediction_id'])
        if prediction:
            prediction.correct_number = correct_number
            prediction.was_correct = was_correct
            db.session.commit()
    
    # Store the learned pattern in database for future reference
    existing_pattern = LearningPattern.query.filter_by(pattern_key=pattern_key).first()
    
    if existing_pattern:
        # Update existing pattern
        existing_pattern.next_number = correct_number
        existing_pattern.frequency += 1
        existing_pattern.last_used = datetime.now()
    else:
        # Create new pattern entry
        new_pattern = LearningPattern(
            pattern_key=pattern_key,
            next_number=correct_number
        )
        db.session.add(new_pattern)
    
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Thank you! I learned something new!',
        'was_correct': was_correct
    })

@app.route('/reset', methods=['POST'])
def reset():
    """Reset the game session"""
    # Clear the session
    game_session_id = session.get('session_id')
    session.clear()
    
    # Update the game session in database if it exists
    if game_session_id:
        game_session = GameSession.query.get(game_session_id)
        if game_session:
            game_session.end_time = datetime.now()
            db.session.commit()
    
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)