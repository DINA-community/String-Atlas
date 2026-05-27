FROM python:3.13-slim

RUN pip install --upgrade pip setuptools wheel

# scikit-learn benötigt compilers und build tools, um korrekt zu funktionieren
RUN apt-get update && apt-get install -y --no-install-recommends \
    openssh-server \
    dos2unix \
    sudo \
    gcc \
    g++ \
    make \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# develop maintance port, not at production
RUN useradd -rm -d /home/docker -s /bin/bash -g root -G sudo -u 999 docker \
    && echo 'docker:docker' | chpasswd
RUN groupadd docker
RUN usermod -aG docker docker

RUN echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config
RUN mkdir -p /app/resources

WORKDIR /app

# für AI test algorithmens
# RUN pip install --upgrade pip setuptools

COPY requirements.txt .
COPY __init__.py __init__.py
COPY api_server.py ./app.py
COPY normalizer ./normalizer
COPY string_helperfunctions.py .
COPY config ./config
COPY docker-run-api/config/api.ini ./config/api.ini

# resources for courpus
COPY header_field_mapper ./header_field_mapper
# TODO noch in Database mappen
COPY oui.csv .

ENV PYTHONPATH="/app:${PYTHONPATH}"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# --no-cache-dir ist workarround for ModuleNotFoundError: No module named 'distutils'
# RUN pip install --prefer-binary -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Optional for annotate strategy
# RUN python -m spacy download en_core_web_sm
# develop only
RUN chgrp docker -R /app
RUN chmod 775 -R /app

EXPOSE 22
EXPOSE 5000

COPY docker-run-api/entrypoint.sh ./entrypoint.sh
RUN find /app -type f -exec dos2unix {} \;
RUN chmod +x /app/entrypoint.sh

CMD ["/bin/sh", "/app/entrypoint.sh"]



