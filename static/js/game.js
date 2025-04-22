/**
 * Number Detective Game - Frontend Logic
 * This script handles the game interaction, making AJAX requests
 * to the backend for AI predictions and learning.
 */

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const sequenceForm = document.getElementById('sequenceForm');
    const numberSequenceInput = document.getElementById('numberSequence');
    const predictionResult = document.getElementById('predictionResult');
    const predictedNumber = document.getElementById('predictedNumber');
    const predictionMethod = document.getElementById('predictionMethod');
    const confidenceBar = document.getElementById('confidenceBar');
    const correctBtn = document.getElementById('correctBtn');
    const wrongBtn = document.getElementById('wrongBtn');
    const correctionForm = document.getElementById('correctionForm');
    const correctNumber = document.getElementById('correctNumber');
    const submitCorrection = document.getElementById('submitCorrection');
    const feedbackMessage = document.getElementById('feedbackMessage');
    const gameHistory = document.getElementById('gameHistory');
    const historyList = document.getElementById('historyList');
    const resetBtn = document.getElementById('resetBtn');
    
    // Current game state
    let currentSequence = [];
    
    // Event Listeners
    sequenceForm.addEventListener('submit', handleSequenceSubmit);
    correctBtn.addEventListener('click', handleCorrectPrediction);
    wrongBtn.addEventListener('click', showCorrectionForm);
    submitCorrection.addEventListener('click', handleCorrection);
    resetBtn.addEventListener('click', resetGame);
    
    // Form submission handler
    function handleSequenceSubmit(event) {
        event.preventDefault();
        
        // Parse and validate the input sequence
        const input = numberSequenceInput.value;
        const numbers = input.split(',').map(num => num.trim());
        
        if (numbers.length < 3) {
            showFeedback('Please enter at least 3 numbers!', 'warning');
            return;
        }
        
        // Check if all entries are valid numbers
        const invalidEntries = numbers.filter(n => isNaN(n) || n === '');
        if (invalidEntries.length > 0) {
            showFeedback('Please enter only valid numbers separated by commas!', 'warning');
            return;
        }
        
        // Store current sequence for later use
        currentSequence = numbers;
        
        // Make prediction request to backend
        fetch('/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ sequence: numbers }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Display prediction result
                displayPrediction(data.prediction, data.confidence, data.method);
            } else {
                // Show error message
                showFeedback(data.message, 'warning');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFeedback('Something went wrong with the prediction. Please try again!', 'danger');
        });
    }
    
    // Display the AI's prediction
    function displayPrediction(prediction, confidence, method) {
        // Show the prediction card
        predictionResult.classList.remove('d-none');
        
        // Update prediction display
        predictedNumber.textContent = prediction;
        predictionMethod.textContent = method;
        
        // Update confidence bar
        const confidencePercent = Math.round(confidence * 100);
        confidenceBar.style.width = confidencePercent + '%';
        confidenceBar.textContent = confidencePercent + '%';
        
        // Set confidence bar color based on confidence level
        if (confidencePercent < 40) {
            confidenceBar.className = 'progress-bar progress-bar-striped bg-danger';
        } else if (confidencePercent < 70) {
            confidenceBar.className = 'progress-bar progress-bar-striped bg-warning';
        } else {
            confidenceBar.className = 'progress-bar progress-bar-striped bg-success';
        }
        
        // Hide other sections
        correctionForm.classList.add('d-none');
        feedbackMessage.classList.add('d-none');
        
        // Scroll to prediction
        predictionResult.scrollIntoView({ behavior: 'smooth' });
        
        // Add bounce animation
        predictionResult.classList.add('bounce-animation');
        setTimeout(() => {
            predictionResult.classList.remove('bounce-animation');
        }, 1000);
    }
    
    // Handle when user confirms prediction is correct
    function handleCorrectPrediction() {
        const predictedValue = predictedNumber.textContent;
        
        // Send correction to backend (even though it's correct, it helps the AI learn)
        fetch('/correct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sequence: currentSequence,
                correct_number: predictedValue
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showFeedback('Great! I got it right! 🎉', 'success');
                updateHistory(currentSequence, predictedValue, predictedValue, true);
            } else {
                showFeedback(data.message, 'warning');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFeedback('Something went wrong. Please try again!', 'danger');
        });
    }
    
    // Show correction form when prediction is wrong
    function showCorrectionForm() {
        correctionForm.classList.remove('d-none');
        correctNumber.value = '';
        correctNumber.focus();
        
        // Scroll to correction form
        correctionForm.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Handle user correction submission
    function handleCorrection() {
        const userCorrection = correctNumber.value.trim();
        
        if (userCorrection === '' || isNaN(userCorrection)) {
            showFeedback('Please enter a valid number!', 'warning');
            return;
        }
        
        // Send correction to backend
        fetch('/correct', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                sequence: currentSequence,
                correct_number: userCorrection
            }),
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                showFeedback('Thank you for teaching me! I\'ll remember this pattern. 🧠', 'info');
                updateHistory(currentSequence, predictedNumber.textContent, userCorrection, false);
                correctionForm.classList.add('d-none');
            } else {
                showFeedback(data.message, 'warning');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showFeedback('Something went wrong with the correction. Please try again!', 'danger');
        });
    }
    
    // Show feedback message
    function showFeedback(message, type) {
        feedbackMessage.textContent = message;
        feedbackMessage.className = `alert alert-${type} d-block`;
        
        // Scroll to feedback message
        feedbackMessage.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Update game history display
    function updateHistory(sequence, prediction, correctValue, wasCorrect) {
        // Show history section if it was hidden
        gameHistory.classList.remove('d-none');
        
        // Create new history item
        const historyItem = document.createElement('li');
        historyItem.className = `list-group-item ${wasCorrect ? 'correct-prediction' : 'incorrect-prediction'}`;
        
        const sequenceText = sequence.join(', ');
        const historyHTML = `
            <div class="d-flex justify-content-between align-items-center">
                <div>
                    <strong>Sequence:</strong> ${sequenceText}
                </div>
                <span class="badge bg-${wasCorrect ? 'success' : 'danger'} ms-2">
                    ${wasCorrect ? 'Correct' : 'Incorrect'}
                </span>
            </div>
            <div class="mt-2">
                <span class="me-3"><strong>AI predicted:</strong> ${prediction}</span>
                ${!wasCorrect ? `<span><strong>Correct answer:</strong> ${correctValue}</span>` : ''}
            </div>
        `;
        
        historyItem.innerHTML = historyHTML;
        
        // Add to history list (at the beginning)
        historyList.insertBefore(historyItem, historyList.firstChild);
        
        // Scroll to history section
        gameHistory.scrollIntoView({ behavior: 'smooth' });
    }
    
    // Reset the game
    function resetGame() {
        if (confirm('Are you sure you want to reset the game? This will clear all history.')) {
            fetch('/reset', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Clear form inputs
                    numberSequenceInput.value = '';
                    
                    // Hide all game elements
                    predictionResult.classList.add('d-none');
                    correctionForm.classList.add('d-none');
                    feedbackMessage.classList.add('d-none');
                    gameHistory.classList.add('d-none');
                    
                    // Clear history list
                    historyList.innerHTML = '';
                    
                    // Show confirmation message
                    showFeedback('Game reset successfully! Start a new sequence.', 'success');
                    
                    // Focus on input
                    numberSequenceInput.focus();
                }
            })
            .catch(error => {
                console.error('Error:', error);
                showFeedback('Something went wrong with resetting the game.', 'danger');
            });
        }
    }
});