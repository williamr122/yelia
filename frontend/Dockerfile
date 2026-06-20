FROM node:20-bookworm-slim
WORKDIR /app
ENV NODE_ENV=development
ENV NEXT_TELEMETRY_DISABLED=1
ENV npm_config_registry=https://registry.npmjs.org/
COPY package.json ./
RUN npm config set registry https://registry.npmjs.org/ \
    && npm config set fetch-retries 5 \
    && npm config set fetch-retry-mintimeout 20000 \
    && npm config set fetch-retry-maxtimeout 120000 \
    && npm install --no-package-lock --legacy-peer-deps --no-audit --no-fund
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev"]
