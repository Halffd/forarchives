import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics import accuracy_score

class NaiveBayesClassifier:
    def __init__(self):
        self.vectorizer = CountVectorizer()
        self.is_fitted = False

    def fit(self, X, y):
        """Fit the model to the training data."""
        X_vectorized = self.vectorizer.fit_transform(X).toarray()
        self.model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=(X_vectorized.shape[1],)),
            tf.keras.layers.Dense(1, activation='sigmoid')
        ])
        
        self.model.compile(optimizer='adam', loss='binary_crossentropy', metrics=['accuracy'])
        self.model.fit(X_vectorized, y, epochs=10, verbose=0)
        self.is_fitted = True

    def predict(self, X):
        """Predict the class labels for the provided data."""
        if not self.is_fitted:
            raise RuntimeError("You must fit the model before making predictions.")
        
        X_vectorized = self.vectorizer.transform(X).toarray()
        return (self.model.predict(X_vectorized) > 0.5).astype("int32").flatten()

    def evaluate(self, X, y):
        """Evaluate the model's accuracy."""
        predictions = self.predict(X)
        return accuracy_score(y, predictions)

    def plot_binomial_distribution(self, n, p):
        """Plot the binomial distribution for a given number of trials and probability."""
        x = np.arange(0, n + 1)
        binomial_dist = (np.math.factorial(n) / 
                         (np.math.factorial(x) * np.math.factorial(n - x))) * (p ** x) * ((1 - p) ** (n - x))

        plt.figure(figsize=(10, 6))
        plt.bar(x, binomial_dist, color='skyblue')
        plt.title('Binomial Distribution of Topic Classification')
        plt.xlabel('Number of Successful Classifications')
        plt.ylabel('Probability')
        plt.xticks(x)
        plt.grid(axis='y')
        plt.show()

# Example usage
if __name__ == '__main__':
    data = pd.DataFrame({
        'search_query': ["anime recommendations", "best horror movies", "learn python programming", 
                         "cute animals", "anime conventions", "python libraries", "horror game reviews"],
        'topic': ["anime", "movies", "programming", "animals", "anime", "programming", "games"]
    })

    # Encode the topics into binary labels
    data['topic_encoded'] = (data['topic'] == "anime").astype(int)  # Example binary classification

    # Split the dataset
    X_train, X_test, y_train, y_test = train_test_split(
        data['search_query'], data['topic_encoded'], test_size=0.2, random_state=42
    )

    # Initialize and fit the classifier
    classifier = NaiveBayesClassifier()
    classifier.fit(X_train, y_train)

    # Evaluate the model
    accuracy = classifier.evaluate(X_test, y_test)
    print(f"Accuracy: {accuracy:.2f}")

    # Plot binomial distribution
    n = len(y_test)  # Number of trials
    p = classifier.model.predict(classifier.vectorizer.transform(X_test).toarray()).mean()  # Estimated probability
    classifier.plot_binomial_distribution(n, p)