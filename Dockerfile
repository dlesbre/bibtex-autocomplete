# Docker file to check for compatibility with old python versions

FROM python:3.8-slim

WORKDIR /usr/src/app

COPY . .
RUN pip install .
CMD bash
