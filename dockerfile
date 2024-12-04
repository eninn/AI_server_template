FROM pytorch/pytorch:2.4.0-cuda12.4-cudnn9-devel

RUN apt update && apt install -y git build-essential autoconf automake libtool pkg-config libpcaudio-dev libespeak-ng-dev libglib2.0-dev libpulse-dev zlib1g-dev

COPY requirements.txt /home/

WORKDIR /home
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN git clone https://github.com/eninn/espeak-ng-custom.git
WORKDIR /home/espeak-ng-custom
RUN ./autogen.sh && ./configure
RUN make && make install

ENV PATH=/usr/local/bin:$PATH
ENV LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
RUN espeak-ng --version

WORKDIR /app

# docker build -t eninn/ai-server:v0.0 .
# docker run -it --rm --gpus 'all' -v /mnt:/mnt -v `pwd`:/app eninn/ai-server:v0.0 /bin/bash  