import os
import streamlit as st
from PIL import Image
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langsmith import traceable
from dotenv import load_dotenv

# Load env vars from secrets (Streamlit Cloud injects them)
load_dotenv()
os.environ["LANGCHAIN_TRACING_V2"] = st.secrets.get("LANGCHAIN_TRACING_V2", "true")
os.environ["LANGCHAIN_API_KEY"] = st.secrets.get("LANGCHAIN_API_KEY")
os.environ["LANGCHAIN_PROJECT"] = st.secrets.get("LANGCHAIN_PROJECT", "movie-review-app")

# LLM setup
llm = ChatOpenAI(model="gpt-4", temperature=0.6)

# Prompt setup
prompt = ChatPromptTemplate.from_template(
    "You are a movie critic. Analyze this review and provide a detailed response:\n\n{review}"
)

@traceable  # LangSmith monitoring
def analyze_review(review):
    chain = prompt | llm
    return chain.invoke({"review": review}).content

# Streamlit UI
st.set_page_config(page_title="🎬 Movie Review Analyzer", layout="centered")
st.title("🎥 Movie Review Analyzer with LLM")
st.markdown("Enter a movie review below and get a deep analysis:")

review_input = st.text_area("✍️ Write your review here", height=200)

if st.button("🧠 Analyze Review"):
    if review_input.strip():
        with st.spinner("Analyzing..."):
            result = analyze_review(review_input)
        st.success("✅ Analysis Complete!")
        st.markdown("### 💡 LLM Feedback:")
        st.write(result)
    else:
        st.warning("⚠️ Please enter a review before analyzing.")
