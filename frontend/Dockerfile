FROM node:22-alpine AS node

WORKDIR /app

COPY --chown=node:node package*.json .

RUN npm ci

COPY --chown=node:node . .

EXPOSE 5173

#######################################################################
FROM node AS dev

RUN chown -R node:node /app

USER node

CMD ["npm", "run", "dev", "--", "--host"]

#######################################################################
FROM node AS builder

RUN chown -R node:node /app

USER node

RUN npm run build

#######################################################################
FROM nginx:alpine AS prod

RUN rm -rf /usr/share/nginx/html/*

COPY --from=builder /app/dist /usr/share/nginx/html

RUN touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid /var/cache/nginx /var/log/nginx /usr/share/nginx/html /etc/nginx/conf.d

USER nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]