# A ML service for recommendations

import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer
from django.core.cache import cache

class RecommendationService:
    @staticmethod
    def get_destination_recommendations(destination_id, limit=5):
        """Get content-based recommendations for a destination"""
        cache_key = f"rec_{destination_id}_{limit}"
        cached = cache.get(cache_key)
        if cached:
            return cached
            
        # Get all destinations
        from api.models import Destination
        destinations = Destination.objects.all()
        
        # Create a DataFrame
        df = pd.DataFrame(list(destinations.values('id', 'name', 'type', 'region', 'description')))
        
        # Simple content-based filtering
        df['content'] = df['name'] + ' ' + df['type'] + ' ' + df['region'] + ' ' + df['description']
        
        # Create TF-IDF matrix
        tfidf = TfidfVectorizer(stop_words='english')
        tfidf_matrix = tfidf.fit_transform(df['content'])
        
        # Get index of the source destination
        idx = df[df['id'] == destination_id].index[0]
        
        # Compute similarity scores
        cosine_sim = cosine_similarity(tfidf_matrix[idx].reshape(1, -1), tfidf_matrix).flatten()
        
        # Get top similar destinations (excluding self)
        sim_scores = list(enumerate(cosine_sim))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = [x for x in sim_scores if x[0] != idx][:limit]
        
        # Get indices and scores
        indices = [i[0] for i in sim_scores]
        ids = df.iloc[indices]['id'].tolist()
        
        # Get actual destination objects
        recommended = list(Destination.objects.filter(id__in=ids))
        
        # Sort in order of similarity
        recommended_sorted = sorted(
            recommended, 
            key=lambda x: ids.index(x.id)
        )
        
        # Cache for 24 hours
        cache.set(cache_key, recommended_sorted, 60*60*24)
        
        return recommended_sorted