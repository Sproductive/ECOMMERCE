from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy
# from sklearn.metrics.pairwise import cosine_similarity

# Load spaCy with appropriate word embeddings
nlp = spacy.load("en_core_web_md")

def find_closest_category(search_term, categories):
    search_embedding = nlp(search_term).vector
    
    similarities = []
    for category in categories:
        category_embedding = nlp(category).vector
        similarity = cosine_similarity([search_embedding], [category_embedding])[0][0]
        similarities.append((category, similarity))
    
    # Sort categories based on similarity
    sorted_categories = sorted(similarities, key=lambda x: x[1], reverse=True)
    return sorted_categories

# Example usage
categories = ["sports", "music", "technology", "art and culture", "health"]
search_term = "fitness"

closest_categories = find_closest_category(search_term, categories)
print(closest_categories)
