import numpy as np
from sklearn.linear_model import LinearRegression
import logging

class NumberDetectiveAI:
    """Class that implements the AI for the Number Detective game."""
    
    def __init__(self):
        self.last_prediction = None
        self.last_sequence = None
        self.trained_patterns = {}  # Store known patterns for learning
        self.logger = logging.getLogger(__name__)
    
    def predict(self, sequence):
        """
        Predict the next number in the sequence using different techniques.
        
        Args:
            sequence: List of integers representing the number sequence
            
        Returns:
            tuple: (prediction, confidence, method)
        """
        self.last_sequence = sequence.copy()
        
        # Check for common patterns
        result = self._check_common_patterns(sequence)
        if result:
            prediction, confidence, method = result
            self.last_prediction = prediction
            return prediction, confidence, method
        
        # Check for arithmetic sequence (constant difference)
        result = self._check_arithmetic(sequence)
        if result:
            prediction, confidence, method = result
            self.last_prediction = prediction
            return prediction, confidence, method
        
        # Check for geometric sequence (constant ratio)
        result = self._check_geometric(sequence)
        if result:
            prediction, confidence, method = result
            self.last_prediction = prediction
            return prediction, confidence, method
        
        # Linear regression as a fallback
        result = self._use_linear_regression(sequence)
        prediction, confidence, method = result
        self.last_prediction = prediction
        return prediction, confidence, method
    
    def _check_common_patterns(self, sequence):
        """Check if the sequence matches any known patterns."""
        # Convert sequence to tuple to use as dictionary key
        seq_key = tuple(sequence)
        
        # Check if we've seen and learned this exact pattern before
        if seq_key in self.trained_patterns:
            return (
                self.trained_patterns[seq_key],
                0.95,  # High confidence since this was explicitly taught
                "I remember this pattern!"
            )
            
        # Fibonacci-like sequence check (each number is the sum of the two preceding numbers)
        if len(sequence) >= 3:
            is_fibonacci = True
            for i in range(2, len(sequence)):
                if sequence[i] != sequence[i-1] + sequence[i-2]:
                    is_fibonacci = False
                    break
            
            if is_fibonacci:
                prediction = sequence[-1] + sequence[-2]
                return prediction, 0.9, "Fibonacci pattern"
        
        # Powers of a number
        if len(sequence) >= 2:
            # Check if powers of 2
            if all(sequence[i] == 2**i for i in range(len(sequence))):
                prediction = 2**len(sequence)
                return prediction, 0.9, "Powers of 2"
            
            # Check if powers of 3
            if all(sequence[i] == 3**i for i in range(len(sequence))):
                prediction = 3**len(sequence)
                return prediction, 0.9, "Powers of 3"
        
        # Square numbers
        if len(sequence) >= 3:
            if all(sequence[i] == (i+1)**2 for i in range(len(sequence))):
                prediction = (len(sequence)+1)**2
                return prediction, 0.9, "Square numbers"
            
        # Alternating patterns
        if len(sequence) >= 4:
            # Check for alternating addition pattern like 2,4,6,8
            if all(sequence[i] - sequence[i-2] == sequence[i-1] - sequence[i-3] for i in range(3, len(sequence))):
                diff = sequence[2] - sequence[0]
                prediction = sequence[-2] + diff
                return prediction, 0.8, "Alternating pattern"
        
        return None
    
    def _check_arithmetic(self, sequence):
        """Check if the sequence is arithmetic (constant difference)."""
        if len(sequence) < 3:
            return None
            
        diffs = [sequence[i] - sequence[i-1] for i in range(1, len(sequence))]
        
        # If all differences are the same, it's an arithmetic sequence
        if all(diff == diffs[0] for diff in diffs):
            prediction = sequence[-1] + diffs[0]
            return prediction, 0.9, "Arithmetic pattern"
        
        return None
    
    def _check_geometric(self, sequence):
        """Check if the sequence is geometric (constant ratio)."""
        if len(sequence) < 3 or 0 in sequence[:-1]:  # Avoid division by zero
            return None
            
        ratios = [sequence[i] / sequence[i-1] for i in range(1, len(sequence))]
        
        # If all ratios are the same (within a small tolerance), it's a geometric sequence
        if all(abs(ratio - ratios[0]) < 0.0001 for ratio in ratios):
            prediction = int(sequence[-1] * ratios[0])
            return prediction, 0.8, "Geometric pattern"
        
        return None
    
    def _use_linear_regression(self, sequence):
        """Use linear regression to predict the next number."""
        try:
            X = np.array(range(len(sequence))).reshape(-1, 1)
            y = np.array(sequence)
            
            model = LinearRegression()
            model.fit(X, y)
            
            next_x = np.array([[len(sequence)]])
            prediction = int(round(model.predict(next_x)[0]))
            
            # Calculate R-squared as a confidence measure
            from sklearn.metrics import r2_score
            y_pred = model.predict(X)
            r2 = r2_score(y, y_pred)
            
            confidence = max(0.3, min(0.7, r2))  # Limit confidence between 0.3 and 0.7
            
            return prediction, confidence, "Number trend"
        except Exception as e:
            self.logger.error(f"Linear regression error: {e}")
            # Fallback to simple method if regression fails
            return sequence[-1], 0.1, "Best guess"
    
    def learn(self, sequence, correct_next):
        """
        Learn from user corrections to improve future predictions.
        
        Args:
            sequence: The original sequence
            correct_next: The correct next number provided by the user
        """
        self.logger.debug(f"Learning: Sequence {sequence}, Correct next: {correct_next}")
        
        # Store this specific pattern for future reference
        seq_key = tuple(sequence)
        self.trained_patterns[seq_key] = correct_next
        
        # We could implement more sophisticated learning here, like
        # adjusting weights of different prediction methods based on
        # their historical accuracy, but we'll keep it simple for now
        
        # Return the pattern key as a string to store in database
        return str(seq_key)