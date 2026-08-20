FROM node:20-alpine

WORKDIR /usr/src/app

COPY package.json ./
RUN npm install --omit=dev

COPY instrumentation.js server.js ./

EXPOSE 3000

CMD ["node", "-r", "./instrumentation.js", "server.js"]
