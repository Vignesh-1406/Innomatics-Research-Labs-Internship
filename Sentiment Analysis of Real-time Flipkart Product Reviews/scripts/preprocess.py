
import re
import unicodedata
import pandas as pd
from nltk.corpus import stopwords
import nltk
import joblib

try:
    import spacy
except Exception:
    spacy = None

nltk.download('stopwords')
STOPWORDS = set(stopwords.words('english'))

CONTRACTION_MAP = {
    "n't": ' not',
    "'re": ' are',
    "'s": ' is',
    "'d": ' would',
    "'ll": ' will',
    "'t": ' not',
    "'ve": ' have',
    "'m": ' am',
}


def load_data(path: str) -> pd.DataFrame:
    return pd.read_csv(path)


def rating_to_sentiment(rating):
    try:
        r = float(rating)
    except Exception:
        return None
    if r >= 4:
        return 'positive'
    if r <= 2:
        return 'negative'
    return 'neutral'


def expand_contractions(text: str) -> str:
    for k, v in CONTRACTION_MAP.items():
        text = text.replace(k, v)
    return text


def clean_text(text: str) -> str:
    if not isinstance(text, str):
        return ''
    # remove common artifacts
    text = re.sub(r'READ\s*MORE', ' ', text, flags=re.IGNORECASE)
    text = re.sub(r'<[^>]+>', ' ', text)
    # normalize unicode
    text = unicodedata.normalize('NFKC', text)
    # remove non-word characters (keeps spaces)
    text = re.sub(r"[^\w\s]", ' ', text)
    text = text.lower()
    text = expand_contractions(text)
    # collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    tokens = [t for t in text.split() if t and t not in STOPWORDS]
    return ' '.join(tokens)


def lemmatize_texts(texts, model_name='en_core_web_sm'):
    if spacy is None:
        raise RuntimeError('spaCy not available; install spacy and download model')
    try:
        nlp = spacy.load(model_name, disable=['parser', 'ner'])
    except OSError:
        # user must run: python -m spacy download en_core_web_sm
        raise
    out = []
    for doc in nlp.pipe(texts, batch_size=64):
        lem = ' '.join([tok.lemma_ for tok in doc if tok.lemma_ != '-PRON-'])
        out.append(lem)
    return out


def preprocess_dataframe(df: pd.DataFrame, text_col='Review text', drop_neutral=True) -> pd.DataFrame:

    df = df.copy()
    df['sentiment'] = df['Ratings'].apply(rating_to_sentiment)
    if drop_neutral:
        df = df[df['sentiment'] != 'neutral'].copy()
    df['clean_text'] = df[text_col].fillna('').apply(clean_text)
    if spacy is not None:
        try:
            df['lemma'] = lemmatize_texts(df['clean_text'].astype(str).tolist())
        except Exception:
            df['lemma'] = df['clean_text']
    else:
        df['lemma'] = df['clean_text']
    return df


def save_cleaned_csv(df: pd.DataFrame, path: str):
    df.to_csv(path, index=False)


if __name__ == '__main__':
    import os
    root = os.path.join(os.path.dirname(__file__), '..')
    data_path = os.path.join(root, 'reviews_badminton', 'data.csv')
    if os.path.exists(data_path):
        df = load_data(data_path)
        df2 = preprocess_dataframe(df)
        out_path = os.path.join(root, 'reviews_badminton', 'data_cleaned.csv')
        save_cleaned_csv(df2, out_path)
        print('Saved cleaned CSV to', out_path)
    else:
        print('Data file not found at', data_path)
