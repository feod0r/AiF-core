import React from 'react';
import ReactDOM from 'react-dom/client';
import './index.css';
import './styles/theme.css';
import App from './App';
import reportWebVitals from './reportWebVitals';
import ErrorBoundary from './components/ErrorBoundary';

// Глобальный обработчик ошибок для предотвращения белых экранов
// eslint-disable-next-line @typescript-eslint/no-unused-vars
const handleError = (error: Error, errorInfo: React.ErrorInfo) => {
  console.error('Global error caught:', error);
  console.error('Error info:', errorInfo);
  
  // Не позволяем ошибкам валидации API делать страницу белой
  if (error.message.includes('Validation') || error.message.includes('422')) {
    console.warn('Validation error prevented from crashing the app');
    return;
  }
  
  // Для других ошибок можно добавить логирование в сервис аналитики
  // или показать пользователю сообщение об ошибке
};

// Глобальный обработчик необработанных ошибок
const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
  console.error('Unhandled promise rejection:', event.reason);
  
  // Не позволяем ошибкам API делать страницу белой
  if (event.reason?.response?.status === 422) {
    console.warn('API validation error prevented from crashing the app');
    event.preventDefault();
    return;
  }
};

// Регистрируем глобальные обработчики ошибок
window.addEventListener('unhandledrejection', handleUnhandledRejection);

const root = ReactDOM.createRoot(
  document.getElementById('root') as HTMLElement
);
root.render(
  <React.StrictMode>
    <ErrorBoundary>
      <App />
    </ErrorBoundary>
  </React.StrictMode>
);

// If you want to start measuring performance in your app, pass a function
// to log results (for example: reportWebVitals(console.log))
// or send to an analytics endpoint. Learn more: https://bit.ly/CRA-vitals
reportWebVitals();
