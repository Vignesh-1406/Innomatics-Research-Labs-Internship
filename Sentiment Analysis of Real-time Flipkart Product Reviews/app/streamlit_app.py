import os
import sys
import streamlit as st
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.preprocess import clean_text

st.set_page_config(
    page_title="Sentiment Analyzer - Flipkart Reviews",
    page_icon="🎯",
    layout="wide"
)

st.title("🎯 Product Review Sentiment Analyzer")
st.markdown("Analyze Flipkart product reviews and classify sentiment as **positive** or **negative**")


MODELS_DIR = Path(__file__).parent.parent / "models"


@st.cache_resource
def load_model():
    try:
        model = joblib.load(MODELS_DIR / "best_classical_model.pkl")
        tfidf = joblib.load(MODELS_DIR / "tfidf_vectorizer.pkl")
        le = joblib.load(MODELS_DIR / "label_encoder.pkl")
        return model, tfidf, le
    except FileNotFoundError:
        return None, None, None


def predict(text, model, tfidf, le):
    cleaned = clean_text(text)
    vec = tfidf.transform([cleaned])
    pred = model.predict(vec)[0]
    
    
    try:
        proba = model.predict_proba(vec)[0]
        confidence = np.max(proba)
    except AttributeError:
        decision = model.decision_function(vec)[0]
        confidence = 1.0 / (1.0 + np.exp(-decision))
    
    sentiment = le.inverse_transform([pred])[0]
    return sentiment, float(confidence)


model, tfidf, le = load_model()

if model is None:
    st.error("❌ **Model not found!** Please train the model first:")
    st.code("python -m scripts.train_classical --data_path reviews_badminton/data.csv --output_dir models")
else:
    st.subheader("Analyze a Single Review")
    
    review_text = st.text_area(
        "Enter a product review:",
        placeholder="Example: The quality is poor and it broke after 2 days. Disappointed with the purchase.",
        height=100
    )
    
    if st.button("🚀 Predict Sentiment", use_container_width=True):
        if review_text.strip():
            with st.spinner("Analyzing..."):
                sentiment, confidence = predict(review_text, model, tfidf, le)
                
                # Display results
                col_sent, col_conf = st.columns([1, 1])
                
                with col_sent:
                    if sentiment == 'positive':
                        st.metric("Sentiment", "✅ POSITIVE")
                    else:
                        st.metric("Sentiment", "❌ NEGATIVE")
                
                with col_conf:
                    st.metric("Confidence", f"{confidence:.1%}")
        else:
            st.warning("⚠️ Please enter a review text.")


st.markdown("---")
st.caption("💡 Tip: Use the batch upload feature to analyze multiple reviews at once")
