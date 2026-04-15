FROM python:3.12-alpine

RUN pip install psycopg2-binary boto3

WORKDIR /app
COPY seed.py .

CMD ["python", "seed.py"]
