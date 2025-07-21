import os
import streamlit as st
import requests
from PIL import Image
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import traceable
from dotenv import load_dotenv

# Load secrets from Streamlit Cloud
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = st.secrets.get("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_API_KEY"] = st.secrets.get("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = st.secrets.get("LANGCHAIN_PROJECT", "movie-review-app")

TMDB_API_KEY = st.secrets.get("TMDB_API_KEY")

# LangChain LLM
llm = ChatOpenAI(model="gpt-4", temperature=0.6)

# LangChain prompt template
prompt_template = ChatPromptTemplate.from_template(
    """
You are an expert movie critic and assistant.

Movie Title: {title}
Genres: {genres}
Director: {director}
Cast: {cast}
TMDB Overview: {overview}
User Rating: {rating}/10
User Review: {review}

Now do the following:
1. Analyze the review and sentiment.
2. Suggest improvements in the review.
3. Provide a 2-line summary of the movie.
4. Provide an overall LLM critique.

Respond in a structured markdown format.
"""
)

# Fetch movie details from TMDB
def fetch_movie_details(title):
    search_url = f"https://api.themoviedb.org/3/search/movie?api_key={TMDB_API_KEY}&query={title}"
    res = requests.get(search_url).json()
    if not res["results"]:
        return None
    movie = res["results"][0]
    movie_id = movie["id"]

    detail_url = f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={TMDB_API_KEY}&append_to_response=credits"
    details = requests.get(detail_url).json()

    genres = ", ".join([g["name"] for g in details.get("genres", [])])
    director = ""
    cast_list = []

    for crew in details["credits"]["crew"]:
        if crew["job"] == "Director":
            director = crew["name"]
            break

    for cast in details["credits"]["cast"][:5]:
        cast_list.append(cast["name"])

    overview = details.get("overview", "")
    poster_path = f"https://image.tmdb.org/t/p/w500{details['poster_path']}" if details.get("poster_path") else ""

    return {
        "title": movie["title"],
        "genres": genres,
        "director": director,
        "cast": ", ".join(cast_list),
        "overview": overview,
        "poster": poster_path
    }

@traceable
def analyze_movie_review(data):
    chain = prompt_template | llm
    return chain.invoke(data).content

# Streamlit UI
st.set_page_config(page_title="🎬 Movie Review Analyzer", layout="wide")
st.title("🎥 Movie Review Analyzer with LangSmith")

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("📌 Enter Movie Title")
    movie_title = st.text_input("Movie Title")
    st.subheader("🌟 Your Rating (1 to 10)")
    user_rating = st.slider("Rating", 1, 10, 7)
    st.subheader("📝 Your Review")
    user_review = st.text_area("Write your review here", height=200)
    analyze_btn = st.button("Analyze Review")

with col2:
    if analyze_btn and movie_title and user_review:
        with st.spinner("Fetching movie info and analyzing..."):
            details = fetch_movie_details(movie_title)
            if details:
                st.image(details["poster"], width=250)
                st.markdown(f"**🎬 Title:** {details['title']}")
                st.markdown(f"**🎭 Genres:** {details['genres']}")
                st.markdown(f"**🎬 Director:** {details['director']}")
                st.markdown(f"**👥 Cast:** {details['cast']}")
                st.markdown(f"**📝 Overview:** {details['overview']}")

                response = analyze_movie_review({
                    "title": details["title"],
                    "genres": details["genres"],
                    "director": details["director"],
                    "cast": details["cast"],
                    "overview": details["overview"],
                    "rating": user_rating,
                    "review": user_review
                })

                st.markdown("### 🧠 GPT Analysis")
                st.markdown(response)
            else:
                st.error("❌ Movie not found. Try another title.")
