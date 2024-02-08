from pandas import pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import spacy

nlp = spacy.load("en_core_web_md")

def find_closest_relation(query):
    product_data = pd.read_csv('database/amazon_products.csv')
    query_embedding = nlp(query).vector
    product_data['Product Name'] = product_data['Product Name'].str.lower()
    product_data['category'] = product_data['category'].str.lower()
    product_data['Brand Name'] = product_data['Brand Name'].str.lower()
    categories = []
    for category in product_data['category']:  
        categories.append(*category.split('|').strip())
    categories = list(set(categories))
    best_categories = []
    for category in categories:
        category_embedding = nlp(category).vector
        similiarity = cosine_similarity([query_embedding], [category_embedding])[0][0]
        if similiarity >= 0.8:
            best_categories.append((category, similiarity))
    best_categories.sort(key=lambda x: x[1], reverse=True)
    if len(best_categories) > 0:
        return {"type": categories, "data":best_categories[0][0]}
    
    brands = []
    for brand in product_data['Brand Name']:
        brands.append(brand)
    brands = list(set(categories))
    best_brands = []
    for brand in brands:
        brand_embedding = nlp(brand).vector
        similiarity = cosine_similarity([query_embedding], [brand_embedding])[0][0]
        if similiarity >= 0.8:
            best_brands.append((brands, similiarity))
    best_brands.sort(key=lambda x: x[1], reverse=True)
    if len(best_brands) > 0:
        return {"type": brands, "data": best_brands[0][0]}

    name_similiarity = []
    for name in product_data['Product Name']:
        name_embedding = nlp(name).vector
        similiarity = cosine_similarity([query_embedding], [name_embedding])[0][0]
        name_similiarity.append((name, similiarity))
    name_similiarity.sort(key=lambda x: x[1], reverse=True)
    return {'type': "names", "data": name_similiarity[:50]}

find_closest_terms