import re
from unidecode import unidecode

def normalize_keyword(keyword):
    # Supprimer les accents et mettre en minuscules
    keyword = unidecode(keyword.lower())
    
    # Supprimer la ponctuation et les chiffres
    keyword = re.sub(r'[^\w\s]', '', keyword)
    keyword = re.sub(r'\d+', '', keyword)
    
    # Supprimer les espaces supplémentaires
    keyword = re.sub(r'\s+', ' ', keyword).strip()
    
    # Traiter les pluriels spécifiques
    keyword = re.sub(r'tables? de chevet', 'table chevet', keyword)
    
    words = keyword.split()
    filtered_words = []
    for word in words:
        if word not in STOPWORDS or word == 'de':
            # Supprimer les terminaisons en 'e', 's', 'es' pour gérer le genre et le nombre
            word = re.sub(r'e?s?$', '', word) if len(word) > 3 else word
            filtered_words.append(word)
    
    # Trier les mots pour gérer l'ordre différent
    return ' '.join(sorted(filtered_words))
