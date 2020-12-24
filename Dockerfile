FROM python:3.8.6-alpine

RUN apk add git tzdata

# IMAP connection variables
ENV IMAP_HOST=''
ENV IMAP_PORT='993'
ENV AUTH_USERNAME=''
ENV AUTH_PASSWORD=''

ENV TZ='America/Chicago'

ADD ./python spamguard/
ADD ./requirements.txt spamguard/
WORKDIR /spamguard
RUN pip install -r requirements.txt

CMD ["python", "-u", "spamguard.py"]