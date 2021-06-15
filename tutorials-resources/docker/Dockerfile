FROM python:3.7-buster

WORKDIR /root/stream
RUN mkdir /root/position_tokens

RUN pip install pipenv
RUN pipenv --python $(which python)

ADD . /root/stream
RUN pipenv sync

#CMD pipenv run ls -alh
CMD pipenv run ./main.py
