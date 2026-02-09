import streamlit as st
import joblib
import pandas as pd
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from scripts.preprocess import clean_text

st.set_page_config(page_title="Sentiment Analysis", layout="wide")
st.title("Badminton Reviews - Sentiment Analysis")

model_dir = os.path.join(os.path.dirname(__file__), '..', 'models')

try:
    model = joblib.load(os.path.join(model_dir, 'best_classical_model.pkl'))
    tfidf = joblib.load(os.path.join(model_dir, 'tfidf_vectorizer.pkl'))
    le = joblib.load(os.path.join(model_dir, 'label_encoder.pkl'))
    st.success("Model loaded successfully!")
except FileNotFoundError:
    st.error("Model files not found. Please train the model first using train_with_mlflow.py")
    st.stop()

st.markdown("---")

col1, col2 = st.columns([2, 1])

with col1:
    review_text = st.text_area("Enter a review:", height=150, placeholder="Enter your review here...")

with col2:
    st.markdown("### Instructions")
    st.info("Enter a review and click 'Predict' to see the sentiment classification.")

if st.button("Predict", type="primary"):
    if review_text.strip():
        cleaned = clean_text(review_text)
        vectorized = tfidf.transform([cleaned])
        prediction = model.predict(vectorized)[0]
        probability = model.predict_proba(vectorized)[0]
        
        sentiment = le.inverse_transform([prediction])[0]
        confidence = max(probability) * 100
        
        st.markdown("---")
        st.subheader("Prediction Result")
        
        col_sentiment, col_confidence = st.columns(2)
        
        with col_sentiment:
            if sentiment == "positive":
                st.success(f"Sentiment: **{sentiment.upper()}** 😊")
            else:
                st.error(f"Sentiment: **{sentiment.upper()}** 😞")
        
        with col_confidence:
            st.info(f"Confidence: **{confidence:.2f}%**")
        
        st.markdown("---")
        st.subheader("Detailed Probabilities")
        prob_df = pd.DataFrame({
            'Sentiment': le.classes_,
            'Probability': probability
        }).sort_values('Probability', ascending=False)
        
        st.bar_chart(prob_df.set_index('Sentiment'))
    else:
        st.warning("Please enter a review text.")
