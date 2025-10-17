#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

// Получаем базовый путь из переменной окружения или используем значение по умолчанию
const basePath = process.env.FRONTEND_BASE_PATH || '/';

// Путь к package.json
const packageJsonPath = path.join(__dirname, 'package.json');

try {
  // Читаем package.json
  const packageJson = JSON.parse(fs.readFileSync(packageJsonPath, 'utf8'));
  
  // Обновляем homepage
  packageJson.homepage = basePath;
  
  // Записываем обратно
  fs.writeFileSync(packageJsonPath, JSON.stringify(packageJson, null, 2));
  
  console.log(`✅ Updated homepage to: ${basePath}`);
  
  // Создаем .env файл с переменными окружения для React
  const envContent = `REACT_APP_API_URL=${process.env.REACT_APP_API_URL || 'http://localhost:8000/api'}
REACT_APP_BASE_PATH=${basePath}
`;
  
  const envPath = path.join(__dirname, '.env');
  fs.writeFileSync(envPath, envContent);
  
  console.log(`✅ Created .env file with REACT_APP_BASE_PATH: ${basePath}`);
} catch (error) {
  console.error('❌ Error updating files:', error.message);
  process.exit(1);
}
