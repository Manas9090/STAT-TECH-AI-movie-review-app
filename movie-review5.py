import streamlit as st
import requests
import openai 
from langsmith import traceable
from langchain_openai import ChatOpenAI
import os

# --- API KEYS ---
TMDB_API_KEY = st.secrets["TMDB_API_KEY"]
openai.api_key = st.secrets["OPENAI_API_KEY"]
os.environ["LANGCHAIN_API_KEY"] = st.secrets["LANGCHAIN_API_KEY"]
os.environ["LANGCHAIN_PROJECT"] = st.secrets["LANGCHAIN_PROJECT"]
os.environ["LANGCHAIN_ENDPOINT"] = st.secrets.get("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")

# --- Streamlit Page Config ---
st.set_page_config(page_title="Bollywood Movie & Review App", page_icon="🎬", layout="centered")

# --- Custom CSS ---
st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
    }
    h1, h2, h3 {
        color: #b30059;
    }
    .stButton>button {
        background-color: #ff4b4b;
        color: white;
        border-radius: 8px;
        padding: 10px 20px;
        margin: 5px 0px;
    }
    .stTextInput>div>div>input {
        background-color: #fff5f8;
        border-radius: 8px;
        border: 1px solid #ffcccc;
        padding: 8px;
    }
    </style>
""", unsafe_allow_html=True)

# --- LangChain LLM ---
llm = ChatOpenAI(model="gpt-4", temperature=0.7)

# --- Functions ---
def get_movie_info(title):
    try:
        url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}&language=hi-IN"
        response = requests.get(url).json()
        if response['results']:
            movie = response['results'][0]
            movie_id = movie['id']

            video_url = f"https://api.themoviedb.org/3/movie/{movie_id}/videos?api_key={TMDB_API_KEY}"
            video_response = requests.get(video_url).json()
            trailer_key = None
            for video in video_response.get("results", []):
                if video['type'] == "Trailer" and video['site'] == "YouTube":
                    trailer_key = video['key']
                    break

            return {
                'title': movie['title'],
                'overview': movie['overview'],
                'poster': f"https://image.tmdb.org/t/p/w500{movie['poster_path']}" if movie.get('poster_path') else None,
                'release_date': movie['release_date'],
                'trailer_key': trailer_key
            }
    except Exception as e:
        st.error(f"Error fetching movie info: {e}")
    return None

@traceable(name="Generate Movie Review")
def generate_review(title, overview):
    try:
        prompt = f"""Write a short, emotional, and engaging movie review in English for this Hindi movie.

Movie Title: {title}
Overview: {overview}

Review:"""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        st.error(f"Error generating review: {e}")
        return "⚠️ Review generation failed."

@traceable(name="Movie Recommendation")
def ask_llm_for_movie_suggestions(user_query):
    try:
        prompt = f"""You are a Bollywood movie expert. Based on this user's request, suggest 3 relevant Hindi movies to watch.

User Request: "{user_query}"

Reply format:
1. Movie Name - 1-line reason

Only suggest family-friendly Hindi movies unless user specifies otherwise. Answer in plain English."""
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}]
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        st.error(f"Error generating recommendations: {e}")
        return "⚠️ Could not fetch suggestions."


# --- Header ---
st.markdown("<h1 style='text-align: center;'>🎬 STAT-TECH-AI: Your Movie Search Buddy</h1>", unsafe_allow_html=True)
st.markdown("<h5 style='text-align: center; color: grey;'>Powered by STAT-TECH-AI 💖</h5>", unsafe_allow_html=True)
st.markdown("<hr style='border: 1px solid #ffd1dc;'>", unsafe_allow_html=True)

# --- Search Movie ---
st.subheader("🔍 Search a Hindi Movie")
movie_title = st.text_input("Enter the name of a Bollywood movie:")

if movie_title:
    with st.spinner("📡 Fetching movie details..."):
        movie = get_movie_info(movie_title)

    if movie:
        poster_url = movie.get('poster')
        if poster_url and isinstance(poster_url, str) and poster_url.startswith("http") and poster_url.lower().endswith((".jpg", ".jpeg", ".png", ".gif")):
            st.image(poster_url, width=300)
        else:
            st.warning("🎬 Poster not available or not a valid image URL.")

        st.markdown(f"<h3 style='color:#ff0066'>{movie['title']} ({movie['release_date']})</h3>", unsafe_allow_html=True)
        st.write(movie['overview'])

        if movie.get('trailer_key'):
            st.markdown("### 🎞️ Official Trailer")
            st.video(f"https://www.youtube.com/embed/{movie['trailer_key']}")

        if st.button("✍️ Generate AI Review"):
            with st.spinner("✨ Generating review..."):
                review = generate_review(movie['title'], movie['overview'])
                st.markdown("### 🧠 AI-Powered Review")
                st.success(review)

        st.markdown("<hr style='border: 1px dashed #ff99aa;'>", unsafe_allow_html=True)
        st.subheader("🎟️ Check Showtimes & Book Tickets Near You")

        cities = ['Mumbai', 'Delhi', 'Bengaluru', 'Hyderabad', 'Chennai', 'Kolkata', 'Pune', 'Ahmedabad']
        selected_city = st.selectbox("Select your city to view local showtimes:", cities)

        if selected_city:
            search_url = f"https://in.bookmyshow.com/explore/movies-{selected_city.lower()}/search?q={movie_title.replace(' ', '%20')}"
            st.markdown(f"""
            🔍 **Looking for '{movie_title}' in {selected_city}?**  
            🎬 Check local cinema listings and showtimes on BookMyShow.  
            👉 [🎟️ Book Now on BookMyShow]({search_url})
            """, unsafe_allow_html=True)
    else:
        st.warning("😢 Movie not found in TMDB. Please try a different title.")

st.markdown("<hr style='border: 1px dashed #ff99aa;'>", unsafe_allow_html=True)

# --- Recommendations ---
st.subheader("🤖 Ask for Movie Recommendations")
user_query = st.text_input("Ask me anything! (e.g., '3 emotional Bollywood movies for weekend')")

if user_query:
    with st.spinner("🤔 Thinking..."):
        suggestions = ask_llm_for_movie_suggestions(user_query)
        st.markdown("### 🎥 AI Recommendations:")
        st.info(suggestions)

st.markdown("<hr style='border: 1px dashed #ff99aa;'>", unsafe_allow_html=True)

# --- Trending Movies ---
st.subheader("🔥 Latest Trending Hindi Movies")

if st.button("🎬 Show Latest Hindi Movies"):
    try:
        url = f"https://api.themoviedb.org/3/discover/movie?api_key={TMDB_API_KEY}&with_original_language=hi&sort_by=popularity.desc"
        response = requests.get(url).json()
        st.markdown("### 🌟 Top Trending Now")
        for movie in response.get("results", [])[:3]:
            if movie.get('poster_path'):
                st.image(f"https://image.tmdb.org/t/p/w500{movie['poster_path']}", width=250)
            st.markdown(f"**🎞️ {movie['title']}** ({movie['release_date']})")
            st.write(movie['overview'])
            st.markdown("---")
    except Exception as e:
        st.error(f"❌ Error fetching trending movies: {e}")

# --- Footer ---
st.markdown("<br><center><span style='color:grey'>Made with ❤️ by STAT-TECH-AI</span></center>", unsafe_allow_html=True)
