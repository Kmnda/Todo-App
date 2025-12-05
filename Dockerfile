FROM python:3.9-alpine as builder

WORKDIR /app

RUN apk add --no-cache gcc musl-dev postgresql-dev

COPY requirements.txt .
RUN pip install --prefix=/install -r requirements.txt

FROM python:3.9-alpine

WORKDIR /app

RUN apk add --no-cache libpq

COPY --from=builder /install /usr/local
COPY app.py .

RUN adduser -D appuser
USER appuser

CMD ["python", "app.py"]

