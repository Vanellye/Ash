FROM node:22-bookworm-slim
ENV NODE_ENV=production PORT=8080 DATABASE_PATH=/data/eria.sqlite
WORKDIR /app
COPY dimensional-api/ ./
RUN mkdir -p /data && chown -R node:node /app /data
USER node
EXPOSE 8080
CMD ["node", "server.mjs"]
