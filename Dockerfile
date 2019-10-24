FROM python:3.7.5-alpine3.10

COPY /marathon-lb-autoscaler.py /marathon-lb-autoscaler.py
COPY /requirements.txt /requirements.txt

RUN pip install -r /requirements.txt

CMD python /marathon-lb-autoscaler.py