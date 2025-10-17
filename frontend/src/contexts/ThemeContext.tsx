import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { ConfigProvider, theme } from 'antd';

interface ThemeContextType {
  isDarkMode: boolean;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (context === undefined) {
    throw new Error('useTheme must be used within a ThemeProvider');
  }
  return context;
};

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    // Проверяем сохраненную тему в localStorage
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
      return savedTheme === 'dark';
    }
    // Если тема не сохранена, используем системные настройки
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    // Сохраняем тему в localStorage
    localStorage.setItem('theme', isDarkMode ? 'dark' : 'light');
    
    // Добавляем класс к body для дополнительной кастомизации
    if (isDarkMode) {
      document.body.classList.add('dark-theme');
      document.body.classList.remove('light-theme');
    } else {
      document.body.classList.add('light-theme');
      document.body.classList.remove('dark-theme');
    }
  }, [isDarkMode]);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
  };

  const { defaultAlgorithm, darkAlgorithm } = theme;

  return (
    <ThemeContext.Provider value={{ isDarkMode, toggleTheme }}>
      <ConfigProvider
        theme={{
          algorithm: isDarkMode ? darkAlgorithm : defaultAlgorithm,
          token: {
            // Кастомные токены для темы
            colorPrimary: '#1890ff',
            borderRadius: 6,
            ...(isDarkMode ? {
              // Темная тема
              colorBgContainer: '#141414',
              colorBgElevated: '#1f1f1f',
              colorBgLayout: '#000000',
              colorBorder: '#434343',
              colorBorderSecondary: '#303030',
              colorText: '#ffffff',
              colorTextSecondary: '#a6a6a6',
              colorTextTertiary: '#737373',
            } : {
              // Светлая тема (по умолчанию)
              colorBgContainer: '#ffffff',
              colorBgElevated: '#ffffff',
              colorBgLayout: '#f5f5f5',
              colorBorder: '#d9d9d9',
              colorBorderSecondary: '#f0f0f0',
              colorText: '#000000',
              colorTextSecondary: '#666666',
              colorTextTertiary: '#999999',
            }),
          },
          components: {
            Layout: {
              colorBgHeader: isDarkMode ? '#001529' : '#001529', // Темный header в обеих темах
              colorBgBody: isDarkMode ? '#141414' : '#f5f5f5',
              colorBgTrigger: isDarkMode ? '#1f1f1f' : '#ffffff',
            },
            Menu: {
              colorBgContainer: isDarkMode ? '#001529' : '#001529', // Темное меню в обеих темах
              colorText: '#ffffff',
              colorItemTextSelected: '#ffffff',
              colorItemBgSelected: isDarkMode ? '#1890ff' : '#1890ff',
              colorItemBgHover: isDarkMode ? 'rgba(255, 255, 255, 0.1)' : 'rgba(255, 255, 255, 0.1)',
            },
            Card: {
              colorBgContainer: isDarkMode ? '#1f1f1f' : '#ffffff',
              colorBorderSecondary: isDarkMode ? '#434343' : '#f0f0f0',
            },
            Table: {
              colorBgContainer: isDarkMode ? '#1f1f1f' : '#ffffff',
              colorFillAlter: isDarkMode ? '#262626' : '#fafafa',
              colorBorderSecondary: isDarkMode ? '#434343' : '#f0f0f0',
            },
            Input: {
              colorBgContainer: isDarkMode ? '#262626' : '#ffffff',
              colorBorder: isDarkMode ? '#434343' : '#d9d9d9',
              colorText: isDarkMode ? '#ffffff' : '#000000',
            },
            Select: {
              colorBgContainer: isDarkMode ? '#262626' : '#ffffff',
              colorBorder: isDarkMode ? '#434343' : '#d9d9d9',
              colorText: isDarkMode ? '#ffffff' : '#000000',
            },
            Button: {
              colorBgContainer: isDarkMode ? '#262626' : '#ffffff',
              colorBorder: isDarkMode ? '#434343' : '#d9d9d9',
            },
            Modal: {
              colorBgElevated: isDarkMode ? '#1f1f1f' : '#ffffff',
              colorBgMask: isDarkMode ? 'rgba(0, 0, 0, 0.65)' : 'rgba(0, 0, 0, 0.45)',
            },
            Drawer: {
              colorBgElevated: isDarkMode ? '#1f1f1f' : '#ffffff',
              colorBgMask: isDarkMode ? 'rgba(0, 0, 0, 0.65)' : 'rgba(0, 0, 0, 0.45)',
            },
          },
        }}
      >
        {children}
      </ConfigProvider>
    </ThemeContext.Provider>
  );
};
