import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity, linear_kernel
from sklearn.preprocessing import MinMaxScaler
import re

class MovieRecommendationEngine:
    def __init__(self, movies_df):
        self.movies_df = movies_df.copy()
        self.prepare_data()
        self.build_content_based_model()
        
    def prepare_data(self):
        self.movies_df['combined_features'] = (
            self.movies_df['genre'].fillna('') + ' ' +
            self.movies_df['keywords'].fillna('') + ' ' +
            self.movies_df['director'].fillna('') + ' ' +
            self.movies_df['cast'].fillna('')
        )
        
        self.movies_df['combined_features'] = self.movies_df['combined_features'].str.lower()
        self.movies_df['title_lower'] = self.movies_df['title'].str.lower()
        
    def build_content_based_model(self):
        self.tfidf = TfidfVectorizer(stop_words='english', max_features=5000)
        self.tfidf_matrix = self.tfidf.fit_transform(self.movies_df['combined_features'])
        self.cosine_sim = linear_kernel(self.tfidf_matrix, self.tfidf_matrix)
        
    def get_content_based_recommendations(self, movie_id, n_recommendations=10):
        idx = self.movies_df[self.movies_df['movie_id'] == movie_id].index
        
        if len(idx) == 0:
            return pd.DataFrame()
        
        idx = idx[0]
        sim_scores = list(enumerate(self.cosine_sim[idx]))
        sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
        sim_scores = sim_scores[1:n_recommendations+1]
        
        movie_indices = [i[0] for i in sim_scores]
        recommendations = self.movies_df.iloc[movie_indices].copy()
        recommendations['similarity_score'] = [i[1] for i in sim_scores]
        
        return recommendations
    
    def get_collaborative_recommendations(self, user_ratings, n_recommendations=10):
        if not user_ratings:
            return self.get_top_rated_movies(n_recommendations)
        
        user_profile = np.zeros(self.tfidf_matrix.shape[1])
        total_weight = 0
        
        for movie_id, rating in user_ratings.items():
            idx = self.movies_df[self.movies_df['movie_id'] == movie_id].index
            if len(idx) > 0:
                idx = idx[0]
                weight = (rating - 2.5) / 2.5
                user_profile += self.tfidf_matrix[idx].toarray()[0] * weight
                total_weight += abs(weight)
        
        if total_weight > 0:
            user_profile = user_profile / total_weight
        
        user_profile_matrix = user_profile.reshape(1, -1)
        sim_scores = cosine_similarity(user_profile_matrix, self.tfidf_matrix)[0]
        
        rated_movie_ids = set(user_ratings.keys())
        recommendations_with_scores = []
        
        for idx, score in enumerate(sim_scores):
            movie_id = self.movies_df.iloc[idx]['movie_id']
            if movie_id not in rated_movie_ids:
                recommendations_with_scores.append((idx, score))
        
        recommendations_with_scores = sorted(recommendations_with_scores, key=lambda x: x[1], reverse=True)
        recommendations_with_scores = recommendations_with_scores[:n_recommendations]
        
        movie_indices = [i[0] for i in recommendations_with_scores]
        recommendations = self.movies_df.iloc[movie_indices].copy()
        recommendations['recommendation_score'] = [i[1] for i in recommendations_with_scores]
        
        return recommendations
    
    def get_hybrid_recommendations(self, movie_id, user_ratings, n_recommendations=10):
        content_recs = self.get_content_based_recommendations(movie_id, n_recommendations * 2)
        collab_recs = self.get_collaborative_recommendations(user_ratings, n_recommendations * 2)
        
        if content_recs.empty:
            return collab_recs.head(n_recommendations)
        if collab_recs.empty:
            return content_recs.head(n_recommendations)
        
        content_scores = dict(zip(content_recs['movie_id'], content_recs.get('similarity_score', [1] * len(content_recs))))
        collab_scores = dict(zip(collab_recs['movie_id'], collab_recs.get('recommendation_score', [1] * len(collab_recs))))
        
        all_movie_ids = set(content_scores.keys()) | set(collab_scores.keys())
        
        hybrid_scores = {}
        for movie_id in all_movie_ids:
            content_score = content_scores.get(movie_id, 0) * 0.5
            collab_score = collab_scores.get(movie_id, 0) * 0.5
            hybrid_scores[movie_id] = content_score + collab_score
        
        sorted_movies = sorted(hybrid_scores.items(), key=lambda x: x[1], reverse=True)
        top_movie_ids = [movie_id for movie_id, score in sorted_movies[:n_recommendations]]
        
        recommendations = self.movies_df[self.movies_df['movie_id'].isin(top_movie_ids)].copy()
        recommendations['hybrid_score'] = recommendations['movie_id'].map(dict(sorted_movies))
        recommendations = recommendations.sort_values('hybrid_score', ascending=False)
        
        return recommendations
    
    def get_top_rated_movies(self, n=10):
        return self.movies_df.nlargest(n, 'rating')
    
    def get_trending_movies(self, n=10):
        recent_movies = self.movies_df[self.movies_df['year'] >= 2010].copy()
        recent_movies['trend_score'] = recent_movies['rating'] * (recent_movies['year'] - 2000) / 25
        return recent_movies.nlargest(n, 'trend_score')
    
    def search_movies(self, query):
        query = query.lower()
        mask = (
            self.movies_df['title_lower'].str.contains(query, na=False, regex=False) |
            self.movies_df['genre'].str.lower().str.contains(query, na=False, regex=False) |
            self.movies_df['director'].str.lower().str.contains(query, na=False, regex=False) |
            self.movies_df['cast'].str.lower().str.contains(query, na=False, regex=False) |
            self.movies_df['keywords'].str.lower().str.contains(query, na=False, regex=False)
        )
        return self.movies_df[mask]
    
    def filter_by_genre(self, genre):
        if genre == 'All':
            return self.movies_df
        return self.movies_df[self.movies_df['genre'].str.contains(genre, na=False, case=False)]
    
    def filter_by_year_range(self, min_year, max_year):
        return self.movies_df[
            (self.movies_df['year'] >= min_year) & 
            (self.movies_df['year'] <= max_year)
        ]
    
    def filter_by_rating_range(self, min_rating, max_rating):
        return self.movies_df[
            (self.movies_df['rating'] >= min_rating) & 
            (self.movies_df['rating'] <= max_rating)
        ]
    
    def get_movie_by_id(self, movie_id):
        movies = self.movies_df[self.movies_df['movie_id'] == movie_id]
        if len(movies) > 0:
            return movies.iloc[0]
        return None
    
    def get_all_genres(self):
        all_genres = set()
        for genres in self.movies_df['genre'].dropna():
            all_genres.update([g.strip() for g in genres.split(',')])
        return sorted(list(all_genres))
