FROM ubuntu:focal

ENV DEBIAN_FRONTEND=noninteractive

ENV UID_PROCBUILD=1002
ENV GID_PROCBUILD=1006

RUN apt-get update && \
    apt-get install -y build-essential python3 python3-dev python3-wheel python3-venv git curl \
    texlive-latex-base texlive-publishers texlive-fonts-recommended  \
    texlive-latex-extra texlive-bibtex-extra && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/* && \
    groupadd -g ${GID_PROCBUILD} procbuild && \
    useradd -u ${UID_PROCBUILD} -g ${GID_PROCBUILD} --create-home --shell /bin/bash procbuild

ENV LC_ALL=C.UTF-8
ENV LANG=C.UTF-8

ADD . /procbuild
WORKDIR /procbuild

RUN bash -c "python3 -m venv /procbuild_env && \
    chown -R procbuild.procbuild /procbuild_env && \
    chown -R procbuild.procbuild /procbuild"

RUN bash -c "source /procbuild_env/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install -r <(curl --silent https://raw.githubusercontent.com/scipy-conference/scipy_proceedings/2023/requirements.txt)"

USER procbuild

EXPOSE 7001

CMD bash -c "source /procbuild_env/bin/activate && \
             ./update_prs && python runserver.py"
