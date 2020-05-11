FROM python:3-slim as build

WORKDIR /app

COPY . .

RUN python3 -m venv venv

RUN pip3 install --no-cache-dir -r requirements.txt 

CMD [ "./entrypoint.sh" ]

EXPOSE 5000