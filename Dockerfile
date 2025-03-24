FROM python:3.12.9-bookworm

COPY ./requirements.txt ./requirements.txt

RUN pip install --no-cache-dir --upgrade -r /requirements.txt

WORKDIR /app

COPY ./app /app
RUN ["aerich", "init-db"]
RUN ["aerich", "upgrade"]
CMD ["python", "polling.py"]