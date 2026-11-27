FROM python:3.14-slim

WORKDIR /goinfre

COPY worker.py .
COPY sandbox_utils.py .

CMD ["python", "worker.py"]