import streamlit as st
import pandas as pd
import numpy as np
from recommendation_engine import MovieRecommendationEngine
from auth import AuthManager
from PIL import Image
import requests
from io import BytesIO

st.set_page_config(
    page_title="NetflixAI - Movie Recommendations",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

@st.cache_data
def load_data():
    movies_df = pd.read_csv('movies_data.csv')
    return movies_df

@st.cache_resource
def init_recommendation_engine():
    movies_df = load_data()
    engine = MovieRecommendationEngine(movies_df)
    return engine
@st.cache_resource
def init_auth_manager():
    return AuthManager()

def apply_netflix_style():
    st.markdown("""
    <style>
        .stApp {
            background-color: #141414;
        }
        
        .main {
            background-color: #141414;
        }
        
        h1, h2, h3, h4, h5, h6, p, label, .stMarkdown {
            color: #ffffff !important;
        }
        
        .netflix-header {
            font-size: 48px;
            font-weight: bold;
            color: #E50914;
            text-align: center;
            margin-bottom: 20px;
            font-family: 'Arial Black', sans-serif;
        }
        
        .section-title {
            font-size: 24px;
            font-weight: bold;
            color: #ffffff;
            margin-top: 30px;
            margin-bottom: 15px;
        }
        
        .movie-card {
            background-color: #1a1a1a;
            border-radius: 8px;
            padding: 10px;
            margin: 5px;
            transition: transform 0.3s;
            cursor: pointer;
        }
        
        .movie-card:hover {
            transform: scale(1.05);
            box-shadow: 0 8px 16px rgba(229, 9, 20, 0.4);
        }
        
        .movie-title {
            font-size: 14px;
            font-weight: bold;
            color: #ffffff;
            margin-top: 8px;
        }
        
        .movie-info {
            font-size: 12px;
            color: #b3b3b3;
            margin-top: 4px;
        }
        
        .rating-badge {
            background-color: #E50914;
            color: white;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        }
        
        .stButton>button {
            background-color: #E50914;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 10px 24px;
            font-weight: bold;
        }
        
        .stButton>button:hover {
            background-color: #f40612;
        }
        
        .sidebar .sidebar-content {
            background-color: #1a1a1a;
        }
        
        div[data-testid="stSidebar"] {
            background-color: #1a1a1a;
        }
        
        .movie-detail-container {
            background: linear-gradient(to bottom, #1a1a1a, #141414);
            border-radius: 12px;
            padding: 30px;
            margin: 20px 0;
        }
        
        .genre-tag {
            background-color: #2a2a2a;
            color: #ffffff;
            padding: 5px 12px;
            border-radius: 15px;
            margin: 5px;
            display: inline-block;
            font-size: 12px;
        }
    </style>
    """, unsafe_allow_html=True)

def display_movie_grid(movies_df, cols=5):
    if movies_df.empty:
        st.warning("No movies found.")
        return
    
    movies_list = movies_df.to_dict('records')
    
    rows = (len(movies_list) + cols - 1) // cols
    
    for row in range(rows):
        columns = st.columns(cols)
        for col_idx in range(cols):
            movie_idx = row * cols + col_idx
            if movie_idx < len(movies_list):
                movie = movies_list[movie_idx]
                with columns[col_idx]:
                    try:
                        response = requests.get(movie['poster_url'], timeout=5)
                        img = Image.open(BytesIO(response.content))
                        st.image(img, use_container_width=True)
                    except:
                        st.image("https://via.placeholder.com/300x450/1a1a1a/ffffff?text=No+Poster", use_container_width=True)
                    
                    st.markdown(f"<div class='movie-title'>{movie['title']}</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='movie-info'>{movie['year']} • ⭐ {movie['rating']}</div>", unsafe_allow_html=True)
                    
                    if st.button(f"View Details", key=f"view_{movie['movie_id']}_{row}_{col_idx}"):
                        st.session_state['selected_movie_id'] = movie['movie_id']
                        st.session_state['page'] = 'movie_detail'
                        st.rerun()

def display_movie_detail(movie, engine):
    st.markdown(f"<h1 style='color: #E50914;'>{movie['title']}</h1>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        try:
            response = requests.get(movie['poster_url'], timeout=5)
            img = Image.open(BytesIO(response.content))
            st.image(img, use_container_width=True)
        except:
            st.image("https://via.placeholder.com/300x450/1a1a1a/ffffff?text=No+Poster", use_container_width=True)
        
        st.markdown("### Rate This Movie")
        user_rating = st.slider("Your Rating", 1.0, 10.0, 5.0, 0.5, key=f"rate_{movie['movie_id']}")
        
        if st.button("Submit Rating", key=f"submit_rating_{movie['movie_id']}"):
            if 'user_ratings' not in st.session_state:
                st.session_state['user_ratings'] = {}
            st.session_state['user_ratings'][movie['movie_id']] = user_rating
            st.success(f"Rated {movie['title']} with {user_rating} stars!")
    
    with col2:
        st.markdown(f"<div class='movie-detail-container'>", unsafe_allow_html=True)
        
        genres = movie['genre'].split(',')
        genre_html = "".join([f"<span class='genre-tag'>{g.strip()}</span>" for g in genres])
        st.markdown(genre_html, unsafe_allow_html=True)
        
        st.markdown(f"<h3>Overview</h3>", unsafe_allow_html=True)
        st.markdown(f"<p style='color: #b3b3b3; font-size: 16px;'>{movie['description']}</p>", unsafe_allow_html=True)
        
        st.markdown(f"<h3>Details</h3>", unsafe_allow_html=True)
        st.markdown(f"<p><strong>Director:</strong> {movie['director']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p><strong>Cast:</strong> {movie['cast']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p><strong>Year:</strong> {movie['year']}</p>", unsafe_allow_html=True)
        st.markdown(f"<p><strong>Rating:</strong> ⭐ {movie['rating']}/10</p>", unsafe_allow_html=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("<div class='section-title'>More Like This</div>", unsafe_allow_html=True)
    
    user_ratings = st.session_state.get('user_ratings', {})
    
    if user_ratings:
        similar_movies = engine.get_hybrid_recommendations(movie['movie_id'], user_ratings, n_recommendations=10)
    else:
        similar_movies = engine.get_content_based_recommendations(movie['movie_id'], n_recommendations=10)
    
    display_movie_grid(similar_movies, cols=5)
    
    if st.button("← Back to Browse", key="back_to_browse"):
        st.session_state['page'] = 'browse'
        st.rerun()

def main():
    apply_netflix_style()
    
    engine = init_recommendation_engine()
    movies_df = load_data()
    
    if 'page' not in st.session_state:
        st.session_state['page'] = 'browse'
    if 'user_ratings' not in st.session_state:
        st.session_state['user_ratings'] = {}
    if 'selected_movie_id' not in st.session_state:
        st.session_state['selected_movie_id'] = None
    
    st.markdown("<div class='netflix-header'>🎬 NetflixAI</div>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: #b3b3b3; margin-bottom: 30px;'>Powered by Machine Learning Recommendations</p>", unsafe_allow_html=True)
    
    with st.sidebar:
        st.markdown("### 🎯 Navigation")
        
        nav_option = st.radio(
            "Go to:",
            ["Browse All", "Search Movies", "Recommended for You", "Top Rated", "Trending Now"],
            key="navigation"
        )
        
        st.markdown("---")
        st.markdown("### 🔍 Filters")
        
        all_genres = ['All'] + engine.get_all_genres()
        selected_genre = st.selectbox("Genre", all_genres)
        
        year_range = st.slider(
            "Year Range",
            int(movies_df['year'].min()),
            int(movies_df['year'].max()),
            (int(movies_df['year'].min()), int(movies_df['year'].max()))
        )
        
        rating_range = st.slider(
            "Rating Range",
            float(movies_df['rating'].min()),
            float(movies_df['rating'].max()),
            (float(movies_df['rating'].min()), float(movies_df['rating'].max()))
        )
        
        st.markdown("---")
        st.markdown(f"### 📊 Your Stats")
        st.markdown(f"**Movies Rated:** {len(st.session_state['user_ratings'])}")
        st.markdown(f"**Total Movies:** {len(movies_df)}")
        
        if st.button("Clear All Ratings"):
            st.session_state['user_ratings'] = {}
            st.success("Ratings cleared!")
            st.rerun()
    
    if st.session_state['page'] == 'movie_detail' and st.session_state['selected_movie_id']:
        movie = engine.get_movie_by_id(st.session_state['selected_movie_id'])
        if movie is not None:
            display_movie_detail(movie, engine)
        else:
            st.error("Movie not found!")
            st.session_state['page'] = 'browse'
            st.rerun()
    else:
        filtered_movies = movies_df
        
        if selected_genre != 'All':
            filtered_movies = engine.filter_by_genre(selected_genre)
        
        filtered_movies = filtered_movies[
            (filtered_movies['year'] >= year_range[0]) & 
            (filtered_movies['year'] <= year_range[1])
        ]
        
        filtered_movies = filtered_movies[
            (filtered_movies['rating'] >= rating_range[0]) & 
            (filtered_movies['rating'] <= rating_range[1])
        ]
        
        if nav_option == "Browse All":
            st.markdown("<div class='section-title'>All Movies</div>", unsafe_allow_html=True)
            display_movie_grid(filtered_movies, cols=5)
        
        elif nav_option == "Search Movies":
            st.markdown("<div class='section-title'>Search Movies</div>", unsafe_allow_html=True)
            search_query = st.text_input("Enter movie title, genre, actor, or director...")
            
            if search_query:
                search_results = engine.search_movies(search_query)
                search_results = search_results[
                    (search_results['year'] >= year_range[0]) & 
                    (search_results['year'] <= year_range[1]) &
                    (search_results['rating'] >= rating_range[0]) & 
                    (search_results['rating'] <= rating_range[1])
                ]
                
                if selected_genre != 'All':
                    search_results = search_results[search_results['genre'].str.contains(selected_genre, na=False, case=False)]
                
                st.markdown(f"<p style='color: #b3b3b3;'>Found {len(search_results)} results</p>", unsafe_allow_html=True)
                display_movie_grid(search_results, cols=5)
            else:
                st.info("Enter a search term to find movies")
        
        elif nav_option == "Recommended for You":
            st.markdown("<div class='section-title'>Recommended for You</div>", unsafe_allow_html=True)
            
            user_ratings = st.session_state.get('user_ratings', {})
            
            if len(user_ratings) == 0:
                st.info("Rate some movies to get personalized recommendations!")
                st.markdown("<div class='section-title'>Popular Movies to Get Started</div>", unsafe_allow_html=True)
                recommendations = engine.get_top_rated_movies(20)
            else:
                recommendations = engine.get_collaborative_recommendations(user_ratings, n_recommendations=20)
            
            recommendations = recommendations[
                (recommendations['year'] >= year_range[0]) & 
                (recommendations['year'] <= year_range[1]) &
                (recommendations['rating'] >= rating_range[0]) & 
                (recommendations['rating'] <= rating_range[1])
            ]
            
            if selected_genre != 'All':
                recommendations = recommendations[recommendations['genre'].str.contains(selected_genre, na=False, case=False)]
            
            display_movie_grid(recommendations, cols=5)
        
        elif nav_option == "Top Rated":
            st.markdown("<div class='section-title'>Top Rated Movies</div>", unsafe_allow_html=True)
            top_rated = filtered_movies.nlargest(20, 'rating')
            display_movie_grid(top_rated, cols=5)
        
        elif nav_option == "Trending Now":
            st.markdown("<div class='section-title'>Trending Now</div>", unsafe_allow_html=True)
            trending = engine.get_trending_movies(20)
            trending = trending[
                (trending['year'] >= year_range[0]) & 
                (trending['year'] <= year_range[1]) &
                (trending['rating'] >= rating_range[0]) & 
                (trending['rating'] <= rating_range[1])
            ]
            
            if selected_genre != 'All':
                trending = trending[trending['genre'].str.contains(selected_genre, na=False, case=False)]
            
            display_movie_grid(trending, cols=5)

if __name__ == "__main__":
    main()
