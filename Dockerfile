FROM ghcr.io/hannah-earley/texlive:full
RUN apt-get update \
 && apt-get install -y \
    python3-dev \
    python3-pip \
    python3.12-venv \
    poppler-utils \
    pdf2svg \
 && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /python
ENV PATH="/python/bin:${PATH}"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /tikz-server
RUN pip install gunicorn
COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY *.py tikz.js ./
CMD [ "gunicorn", "--bind", "0.0.0.0:5000", "serve:app" ]
