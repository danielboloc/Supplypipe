FROM continuumio/miniconda3

VOLUME /supplypipe
COPY ./ /supplypipe

RUN . ~/.bashrc && conda init bash && \
    conda env update --name base --file /supplypipe/environment.yml
WORKDIR /supplypipe

ENTRYPOINT ["python", "Supplypipe.py"]