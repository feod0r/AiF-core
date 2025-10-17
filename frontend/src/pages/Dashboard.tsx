import React, { useState, useEffect } from 'react';
import { Typography, Row, Col, Card, Statistic, Spin, Alert, Divider } from 'antd';
import { 
  BankOutlined,
  DesktopOutlined,
  DollarOutlined,
  GiftOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { accountsApi, terminalOperationsApi, reportsApi } from '../services/api';
import { Account, TerminalOperation } from '../types';

const { Title } = Typography;

const Dashboard: React.FC = () => {
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [reportsData, setReportsData] = useState<any[]>([]);
  const [terminalOperations, setTerminalOperations] = useState<TerminalOperation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isMobile, setIsMobile] = useState(false);

  // Определяем мобильное устройство
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Загружаем данные
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const today = dayjs().format('YYYY-MM-DD');
        
        // Загружаем данные параллельно
        const [accountsData, reportsResponse, terminalData] = await Promise.all([
          accountsApi.getList(),
          reportsApi.list(today),
          terminalOperationsApi.list({ operation_date: today })
        ]);

        setAccounts(accountsData || []);
        setReportsData(reportsResponse || []);
        setTerminalOperations(terminalData || []);
      } catch (err) {
        setError('Ошибка загрузки данных');
        console.error('Dashboard error:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  const getColSpan = () => {
    if (isMobile) {
      return 12; // 2 колонки на мобильных
    }
    return 6; // 4 колонки на десктопе
  };



  if (loading) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>Загрузка данных...</div>
      </div>
    );
  }

  if (error) {
    return (
      <Alert
        message="Ошибка загрузки данных"
        description={error}
        type="error"
        showIcon
        style={{ margin: 24 }}
      />
    );
  }

  return (
    <div style={{ padding: isMobile ? 12 : 24 }}>
      <Title level={2} style={{ marginBottom: isMobile ? 16 : 24 }}>
        Главная панель
      </Title>

      {/* Баланс аккаунтов */}
      <Title level={3} style={{ marginBottom: 16 }}>
        💰 Баланс счетов
      </Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        {accounts.map((account) => (
          <Col key={account.id} span={getColSpan()}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={account.name}
                value={account.balance || 0}
                prefix={<BankOutlined />}
                formatter={(value) => `${Number(value).toLocaleString('ru-RU')} ₽`}
                valueStyle={{ 
                  color: (account.balance || 0) >= 0 ? '#52c41a' : '#ff4d4f',
                  fontSize: isMobile ? 16 : 20,
                }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Divider />

      {/* Отчеты автоматов - выручка за сегодня */}
      <Title level={3} style={{ marginBottom: 16 }}>
        🪙 Выручка автоматов за сегодня
      </Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        {reportsData.map((report) => (
          <Col key={`revenue-${report.id}`} span={getColSpan()}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={report.machine?.name || `Автомат ${report.machine_id}`}
                value={report.revenue || 0}
                prefix={<DollarOutlined />}
                formatter={(value) => `${Number(value).toLocaleString('ru-RU')}`}
                suffix="₽"
                valueStyle={{ 
                  color: '#1890ff',
                  fontSize: isMobile ? 16 : 20,
                }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Divider />

      {/* Отчеты автоматов - игрушки за сегодня */}
      <Title level={3} style={{ marginBottom: 16 }}>
        🧸 Игрушки автоматов за сегодня
      </Title>
      <Row gutter={[16, 16]} style={{ marginBottom: 32 }}>
        {reportsData.map((report) => (
          <Col key={`toys-${report.id}`} span={getColSpan()}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={report.machine?.name || `Автомат ${report.machine_id}`}
                value={report.toy_consumption || 0}
                prefix={<GiftOutlined />}
                suffix="шт"
                valueStyle={{ 
                  color: '#52c41a',
                  fontSize: isMobile ? 16 : 20,
                }}
              />
            </Card>
          </Col>
        ))}
      </Row>

      <Divider />

      {/* Операции терминалов за день */}
      <Title level={3} style={{ marginBottom: 16 }}>
        🖥️ Операции терминалов за сегодня
      </Title>
      <Row gutter={[16, 16]}>
        {terminalOperations.map((operation) => (
          <Col key={operation.id} span={getColSpan()}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={operation.terminal?.name || `Терминал ${operation.terminal?.id || 'N/A'}`}
                value={operation.amount || 0}
                prefix={<DesktopOutlined />}
                formatter={(value) => `${Number(value).toLocaleString('ru-RU')} ₽`}
                valueStyle={{ 
                  color: '#722ed1',
                  fontSize: isMobile ? 16 : 20,
                }}
              />
              {operation.transaction_count && (
                <div style={{ marginTop: 8, fontSize: 12, color: '#666' }}>
                  Операций: {operation.transaction_count}
                </div>
              )}
            </Card>
          </Col>
        ))}
      </Row>
    </div>
  );
};

export default Dashboard;