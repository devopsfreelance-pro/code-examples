FROM node:20-alpine

WORKDIR /app

COPY app/package.json ./
COPY app/index.js ./

EXPOSE 8080

CMD ["node", "index.js"]
