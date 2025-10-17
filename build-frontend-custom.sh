#!/bin/bash

# Скрипт для сборки фронтенда с кастомным базовым путем

set -e

# Проверяем аргумент
if [ -z "$1" ]; then
    echo "❌ Укажите базовый путь!"
    echo "Пример: ./build-frontend-custom.sh /core"
    echo "Пример: ./build-frontend-custom.sh /admin"
    exit 1
fi

BASE_PATH=$1

echo "🚀 Начинаем сборку фронтенда с базовым путем: $BASE_PATH"

# Создаем директорию для собранных файлов на хосте
mkdir -p ./frontend-build

# Собираем фронтенд в контейнере с кастомным базовым путем
echo "📦 Собираем фронтенд в Docker контейнере..."
docker build \
  --build-arg FRONTEND_BASE_PATH=$BASE_PATH \
  -t ant-admin-frontend-builder ./frontend

# Запускаем контейнер с монтированием директории хоста
echo "📋 Копируем собранные файлы на хост..."
docker run --rm \
  -v "$(pwd)/frontend-build:/host-build" \
  ant-admin-frontend-builder

echo "✅ Сборка завершена!"
echo "📁 Собранные файлы находятся в: ./frontend-build/"
echo ""
echo "📋 Для размещения в nginx:"
echo "   sudo mkdir -p /var/www/html$BASE_PATH"
echo "   sudo cp -r ./frontend-build/* /var/www/html$BASE_PATH/"
echo "   sudo chown -R www-data:www-data /var/www/html$BASE_PATH"
echo "   sudo systemctl reload nginx"
