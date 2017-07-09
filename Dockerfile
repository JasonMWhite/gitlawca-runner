FROM python:3.6.1

COPY scripts /app/scripts
RUN /app/scripts/install_java && \
    /app/scripts/install_gcloud

COPY requirements /app/requirements
RUN pip install -r /app/requirements/ci.txt

COPY . /app
RUN pip install -e /app

WORKDIR /app
