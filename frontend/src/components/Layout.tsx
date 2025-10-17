import React, { useState, useEffect } from 'react';
import { Layout, Menu, theme, Avatar, Dropdown, Space, Badge, Button, Drawer, Switch, Tooltip } from 'antd';
import {
  UserOutlined,
  DesktopOutlined,
  SettingOutlined,
  BarChartOutlined,
  PhoneOutlined,
  DollarOutlined,
  HomeOutlined,
  LogoutOutlined,
  BankOutlined,
  TeamOutlined,
  FileTextOutlined,
  AccountBookOutlined,
  InboxOutlined,
  ShopOutlined,
  DatabaseOutlined,
  SwapOutlined,
  PieChartOutlined,
  SafetyCertificateOutlined,
  AuditOutlined,
  InfoCircleOutlined,
  MacCommandOutlined,
  FileOutlined,
  KeyOutlined,
  MenuOutlined,
  EnvironmentOutlined,
  MessageOutlined,
  RobotOutlined,
  ClockCircleOutlined,
  MoonOutlined,
  SunOutlined,
} from '@ant-design/icons';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';

const { Header, Sider, Content } = Layout;

const AppLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  const navigate = useNavigate();
  const location = useLocation();
  const { user, logout } = useAuth();
  const { isDarkMode, toggleTheme } = useTheme();
  const {
    token: { colorBgContainer, borderRadiusLG },
  } = theme.useToken();

  // Определяем мобильное устройство
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
      if (window.innerWidth > 768) {
        setMobileDrawerVisible(false);
      }
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Закрываем drawer при переходе на новую страницу на мобильных
  useEffect(() => {
    if (isMobile) {
      setMobileDrawerVisible(false);
    }
  }, [location.pathname, isMobile]);

  const menuItems = [
    {
      key: '/',
      icon: <HomeOutlined />,
      label: 'Главная',
    },
    {
      key: '/info-cards',
      icon: <InfoCircleOutlined />,
      label: 'Информационные карточки',
    },
    {
      key: '/documents',
      icon: <FileOutlined />,
      label: 'Документы',
    },

    {
      key: 'company',
      icon: <MacCommandOutlined />,
      label: 'Управление предприятием',
      children: [
        {
          key: '/owners',
          icon: <UserOutlined />,
          label: 'Владельцы',
        },
        {
          key: '/terminals',
          icon: <DesktopOutlined />,
          label: 'Терминалы',
        },
        {
          key: '/machines',
          icon: <SettingOutlined />,
          label: 'Машины',
        },
        {
          key: '/phones',
          icon: <PhoneOutlined />,
          label: 'Телефоны',
        },
        {
          key: '/rent',
          icon: <DollarOutlined />,
          label: 'Аренда',
        },
        {
          key: '/rent-map',
          icon: <EnvironmentOutlined />,
          label: 'Карта аренды',
        },
        
      ],
    },
    
    {
      key: '/monitoring',
      icon: <BarChartOutlined />,
      label: 'Мониторинг',
    },
    {
      key: '/reports',
      icon: <PieChartOutlined />,
      label: 'Отчеты',
    },
    {
      key: '/charts',
      icon: <BarChartOutlined />,
      label: 'Графики',
    },
    {
      key: '/terminal-operations',
      icon: <DollarOutlined />,
      label: 'Операции терминалов',
    },
    
    {
      key: 'inventory',
      icon: <InboxOutlined />,
      label: 'Инвентарь',
      children: [
        {
          key: '/item-categories',
          icon: <DatabaseOutlined />,
          label: 'Категории товаров',
        },
        {
          key: '/items',
          icon: <ShopOutlined />,
          label: 'Товары',
        },
        {
          key: '/warehouses',
          icon: <InboxOutlined />,
          label: 'Склады',
        },
        {
          key: '/warehouse-stocks',
          icon: <DatabaseOutlined />,
          label: 'Остатки на складах',
        },
        {
          key: '/machine-stocks',
          icon: <SettingOutlined />,
          label: 'Остатки в автоматах',
        },
        {
          key: '/inventory-movements',
          icon: <SwapOutlined />,
          label: 'Движения товаров',
        },
      ],
    },
    {
      key: 'accounting',
      icon: <AccountBookOutlined />,
      label: 'Аккаунтинг',
      children: [
        {
          key: '/account-types',
          icon: <BankOutlined />,
          label: 'Типы счетов',
        },
        {
          key: '/accounts',
          icon: <BankOutlined />,
          label: 'Счета',
        },
        {
          key: '/counterparty-categories',
          icon: <TeamOutlined />,
          label: 'Категории контрагентов',
        },
        {
          key: '/counterparties',
          icon: <TeamOutlined />,
          label: 'Контрагенты',
        },
        {
          key: '/transaction-categories',
          icon: <FileTextOutlined />,
          label: 'Категории операций',
        },
        {
          key: '/transactions',
          icon: <FileTextOutlined />,
          label: 'Операции',
        },
        {
          key: '/accounting-pivot',
          icon: <PieChartOutlined />,
          label: 'Сводные таблицы',
        },
      ],
    },
    // Административные функции (только для админов)
    ...(user?.role?.name === 'admin' ? [
      {
        key: 'admin',
        icon: <SafetyCertificateOutlined />,
        label: 'Администрирование',
        children: [
          {
            key: '/users',
            icon: <UserOutlined />,
            label: 'Пользователи',
          },
          {
            key: '/api-tokens',
            icon: <KeyOutlined />,
            label: 'API Токены',
          },
                  {
          key: '/audit',
          icon: <AuditOutlined />,
          label: 'Аудит',
        },
      ],
    },
  ] : []),
    // Telegram уведомления
    {
      key: 'telegram',
      icon: <MessageOutlined />,
      label: 'Telegram Уведомления',
      children: [
        {
          key: '/telegram-bots',
          icon: <RobotOutlined />,
          label: 'Telegram Боты',
        },
        {
          key: '/telegram-notifications',
          icon: <MessageOutlined />,
          label: 'Отправка уведомлений',
        },
      ],
    },
    // Автоматизация
    ...(user?.role?.name === 'admin' ? [{
      key: 'automation',
      icon: <ClockCircleOutlined />,
      label: 'Автоматизация',
      children: [
        {
          key: '/scheduled-jobs',
          icon: <ClockCircleOutlined />,
          label: 'Запланированные задачи',
        },
      ],
    }] : []),
    
];

  const userMenuItems = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: 'Профиль',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: 'Выйти',
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    navigate(key);
    // Закрываем drawer на мобильных устройствах
    if (isMobile) {
      setMobileDrawerVisible(false);
    }
  };

  const handleUserMenuClick = ({ key }: { key: string }) => {
    if (key === 'logout') {
      logout();
      navigate('/login');
    } else if (key === 'profile') {
      navigate('/profile');
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      {/* Desktop Sider */}
      {!isMobile && (
        <Sider trigger={null} collapsible collapsed={collapsed}>
          <div style={{ 
            height: 32, 
            margin: 16, 
            background: 'rgba(255, 255, 255, 0.2)',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontSize: collapsed ? 12 : 16,
            fontWeight: 'bold'
          }}>
            {collapsed ? 'AiF' : 'AiF-Tech'}
          </div>
          <Menu
            theme="dark"
            mode="inline"
            selectedKeys={[location.pathname]}
            items={menuItems}
            onClick={handleMenuClick}
          />
        </Sider>
      )}

      <Layout>
        <Header style={{ 
          padding: isMobile ? '0 16px' : '0 24px', 
          background: isDarkMode ? '#001529' : '#001529', // Темный header в обеих темах для лучшей читаемости
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 16,
            fontSize: isMobile ? 16 : 18, 
            fontWeight: 'bold',
            color: '#ffffff' // Белый текст на темном header
          }}>
            {isMobile && (
              <Button
                type="text"
                icon={<MenuOutlined />}
                onClick={() => setMobileDrawerVisible(true)}
                style={{ 
                  fontSize: 18,
                  color: '#ffffff' // Белая иконка для видимости
                }}
              />
            )}
            <span style={{ 
              display: isMobile ? 'none' : 'block',
              fontSize: isMobile ? 14 : 18,
              color: '#ffffff' // Белый текст для читаемости
            }}>
              Система мониторинга
            </span>
            {isMobile && (
              <span style={{ 
                fontSize: 14,
                color: '#ffffff' // Белый текст для читаемости
              }}>
                AiF-Tech
              </span>
            )}
          </div>
          
          <Space size="middle">
            <Tooltip title={isDarkMode ? 'Переключить на светлую тему' : 'Переключить на темную тему'}>
              <Switch
                checked={isDarkMode}
                onChange={toggleTheme}
                checkedChildren={<MoonOutlined />}
                unCheckedChildren={<SunOutlined />}
                style={{
                  backgroundColor: isDarkMode ? '#1890ff' : '#bfbfbf',
                }}
              />
            </Tooltip>
            
            <Dropdown
            menu={{
              items: userMenuItems,
              onClick: handleUserMenuClick,
            }}
            placement="bottomRight"
          >
            <Space style={{ cursor: 'pointer' }}>
              <Badge dot={user?.role?.name === 'admin'}>
                <Avatar icon={<UserOutlined />} />
              </Badge>
              {!isMobile && (
                <span>{user?.full_name || user?.username || 'Пользователь'}</span>
              )}
              {user?.role?.name === 'admin' && !isMobile && (
                <span style={{ 
                  fontSize: '12px', 
                  color: '#1890ff',
                  fontWeight: 'bold'
                }}>
                  Админ
                </span>
              )}
            </Space>
          </Dropdown>
          </Space>
        </Header>
        
        <Content
          style={{
            margin: isMobile ? '16px 8px' : '24px 16px',
            padding: isMobile ? 16 : 24,
            minHeight: 280,
            background: colorBgContainer,
            borderRadius: borderRadiusLG,
          }}
        >
          <Outlet />
        </Content>
      </Layout>

      {/* Mobile Drawer */}
      <Drawer
        title={
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 8,
            color: 'white'
          }}>
            <div style={{ 
              height: 32, 
              padding: '0 12px',
              background: 'rgba(255, 255, 255, 0.2)',
              borderRadius: 6,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: 14,
              fontWeight: 'bold'
            }}>
              AiF-Tech
            </div>
          </div>
        }
        placement="left"
        onClose={() => setMobileDrawerVisible(false)}
        open={mobileDrawerVisible}
        width={280}
        styles={{
          header: { background: '#001529', color: 'white' },
          body: { padding: 0, background: '#001529' }
        }}
      >
        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={[location.pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          style={{ border: 'none', background: '#001529' }}
        />
      </Drawer>
    </Layout>
  );
};

export default AppLayout; 