FROM node:lts-alpine as build-stage
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM nginx:stable-alpine as production-stage
# Копируем собранное приложение
COPY --from=build-stage /app/dist /usr/share/nginx/html
# Копируем нашу nginx конфигурацию
COPY ./nginx/default.conf /etc/nginx/conf.d/default.conf

# Открываем порт 80
EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]