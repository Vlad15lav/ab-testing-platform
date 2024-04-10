FROM python:3.11

WORKDIR /app

COPY ./requirements.txt ./requirements.txt
RUN pip install --no-cache-dir --upgrade -r ./requirements.txt

COPY ./src ./src

EXPOSE 8501

CMD ["streamlit", "run", "src/Home.py" "--server.port" "8501"]