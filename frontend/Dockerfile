# Используем официальный Node.js образ для сборки
FROM node:18-alpine AS builder

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем package.json и package-lock.json
COPY package*.json ./

# Устанавливаем зависимости
RUN npm ci --only=production

# Копируем исходный код
COPY . .

# Устанавливаем переменные окружения для сборки
ENV REACT_APP_API_URL=https://aif-tech.ru/api/
ENV NODE_ENV=production
# Базовый путь для фронтенда (можно переопределить при сборке)
ARG FRONTEND_BASE_PATH=/core
ENV FRONTEND_BASE_PATH=${FRONTEND_BASE_PATH}
ENV REACT_APP_BASE_PATH=${FRONTEND_BASE_PATH}

# Обновляем homepage в package.json
RUN node update-homepage.js

# Собираем приложение
RUN npm run build

# Второй этап - копируем собранные файлы
FROM alpine:latest AS final

# Устанавливаем необходимые инструменты
RUN apk add --no-cache bash

# Создаем директорию для собранных файлов
WORKDIR /build

# Копируем собранные файлы из builder
COPY --from=builder /app/build .

# Создаем скрипт для копирования файлов на хост
RUN echo '#!/bin/bash' > /copy-build.sh && \
    echo 'cp -r /build/* /host-build/' >> /copy-build.sh && \
    chmod +x /copy-build.sh

# Команда по умолчанию - копируем файлы на хост
CMD ["/copy-build.sh"]
