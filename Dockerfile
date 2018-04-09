FROM ubuntu:17.10

RUN apt-get update && \
    apt-get install -y python3.6 python3.6-venv git curl \
    texlive-latex-base texlive-publishers texlive-fonts-recommended  \
    texlive-latex-extra texlive-bibtex-extra && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    useradd --create-home --shell /bin/bash procbuild

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ADD . /procbuild
WORKDIR /procbuild

RUN bash -c "python3.6 -m venv /procbuild_env && \
    chown -R procbuild.procbuild /procbuild_env && \
    chown -R procbuild.procbuild /procbuild"

RUN bash -c "source /procbuild_env/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r <(curl --silent https://raw.githubusercontent.com/scipy-conference/scipy_proceedings/2018/requirements.txt)"

USER procbuild

EXPOSE 7001

CMD bash -c "source /procbuild_env/bin/activate && \
             ./update_prs && python runserver.py"
