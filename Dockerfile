FROM debian AS builder
WORKDIR /build
RUN apt update && apt install -y python3 python3-pip patchelf
RUN pip3 install nuitka
COPY requirements.txt ./
RUN pip3 install -r requirements.txt

FROM builder AS build
ARG MODULE
COPY server.py $MODULE.py ./
RUN nuitka3 --standalone --onefile --include-module=$MODULE -o vlc-bridge-$MODULE server.py

FROM debian
ARG MODULE
WORKDIR /app
RUN apt update && apt install -y ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=build /build/vlc-bridge-$MODULE /app/
RUN ln -nsf /app/vlc-bridge-$MODULE /app/vlc-bridge
ENV PYTHONUNBUFFERED=1
ENV PROVIDER=$MODULE
EXPOSE 7777/tcp
ENTRYPOINT ["/app/vlc-bridge"]
