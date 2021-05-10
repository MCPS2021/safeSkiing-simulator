FROM python:3.8
ADD ./ /code
WORKDIR code
RUN pip install -r requirements-docker.txt
CMD ["python", "main.py", "true"]