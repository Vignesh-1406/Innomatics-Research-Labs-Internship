FROM python:3.11-slim

WORKDIR /app

COPY bedrock_requirements.txt .
RUN pip install --no-cache-dir -r bedrock_requirements.txt

COPY . .

RUN mkdir -p /app/data

ENV AWS_REGION=us-east-1
ENV PYTHONUNBUFFERED=1

EXPOSE 8501

CMD ["streamlit", "run", "bedrock_streamlit_app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
