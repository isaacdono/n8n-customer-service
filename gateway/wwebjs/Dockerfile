FROM ghcr.io/puppeteer/puppeteer:latest

USER root
WORKDIR /usr/src/app

ENV PUPPETEER_SKIP_DOWNLOAD=true

COPY package*.json ./
RUN npm install --omit=dev --no-audit --no-fund \
    && ln -sf /home/pptruser/.cache/puppeteer/chrome/*/chrome-linux*/chrome /usr/bin/google-chrome-stable

COPY . .

CMD [ "node", "index.js" ]
