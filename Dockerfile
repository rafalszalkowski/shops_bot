FROM python:3.8
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
ENV PYTHONUNBUFFERED=1
CMD ["python3", "./main.py"]