#!/bin/bash

# Скрипт для сборки фронтенда и копирования на хост

set -e

echo "🚀 Начинаем сборку фронтенда..."

# Создаем директорию для собранных файлов на хосте
mkdir -p ./frontend-build

# Собираем фронтенд в контейнере
echo "📦 Собираем фронтенд в Docker контейнере..."
docker build -t ant-admin-frontend-builder ./frontend

# Запускаем контейнер с монтированием директории хоста
echo "📋 Копируем собранные файлы на хост..."
docker run --rm \
  -v "$(pwd)/frontend-build:/host-build" \
  ant-admin-frontend-builder

echo "✅ Сборка завершена!"
echo "📁 Собранные файлы находятся в: ./frontend-build/"
echo ""
echo "📋 Для размещения в nginx:"
echo "   sudo cp -r ./frontend-build/* /var/www/html/"
echo "   sudo chown -R www-data:www-data /var/www/html/"
echo "   sudo systemctl reload nginx"
