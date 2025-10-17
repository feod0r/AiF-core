import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, Row, Col, Statistic, Spin, Alert, DatePicker } from 'antd';
import {
  ArrowUpOutlined,
  ArrowDownOutlined,
  CalculatorOutlined,
  TransactionOutlined,
} from '@ant-design/icons';
import { TransactionSummary } from '../types';
import { Dayjs } from 'dayjs';

const { RangePicker } = DatePicker;

interface DashboardSummaryProps {
  // API функция для получения данных
  fetchSummary: (params?: any) => Promise<TransactionSummary>;
  // Заголовок дашборда
  title?: string;
  // Показывать ли фильтр по датам
  showDateFilter?: boolean;
  // Дополнительные параметры для API
  extraParams?: Record<string, any>;
  // Размер карточек
  size?: 'small' | 'default';
  // Количество колонок на desktop
  columns?: number;
}

const DashboardSummary: React.FC<DashboardSummaryProps> = ({
  fetchSummary,
  title = 'Финансовая сводка',
  showDateFilter = true,
  extraParams = {},
  size = 'default',
  columns = 4,
}) => {
  const [summary, setSummary] = useState<TransactionSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dateRange, setDateRange] = useState<[Dayjs | null, Dayjs | null] | null>(null);
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

  // Стабилизируем extraParams с помощью useMemo
  const extraParamsString = JSON.stringify(extraParams);
  const stableExtraParams = useMemo(() => extraParams, [extraParamsString]);

  // Загружаем данные
  const loadSummary = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const params = {
        ...stableExtraParams,
      };

      // Добавляем даты если выбраны
      if (dateRange && dateRange[0] && dateRange[1]) {
        params.date_from = dateRange[0].format('YYYY-MM-DD');
        params.date_to = dateRange[1].format('YYYY-MM-DD');
      }

      const data = await fetchSummary(params);
      setSummary(data);
    } catch (err) {
      setError('Ошибка при загрузке данных');
      console.error('Dashboard summary error:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchSummary, stableExtraParams, dateRange]);

  // Загружаем данные при монтировании и изменении параметров
  useEffect(() => {
    loadSummary();
  }, [loadSummary]);

  // Обработчик изменения дат
  const handleDateChange = (dates: [Dayjs | null, Dayjs | null] | null) => {
    setDateRange(dates);
  };

  // Функция для форматирования валюты
  const formatCurrency = (value: number): string => {
    return new Intl.NumberFormat('ru-RU', {
      style: 'currency',
      currency: 'RUB',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Определяем количество колонок в зависимости от размера экрана
  const getColSpan = () => {
    if (isMobile) {
      return 12; // 2 колонки на мобильных
    }
    return 24 / columns; // columns колонок на десктопе
  };

  if (error) {
    return (
      <Alert
        message="Ошибка загрузки данных"
        description={error}
        type="error"
        showIcon
        style={{ marginBottom: 16 }}
        action={
          <button onClick={loadSummary} style={{ border: 'none', background: 'none', color: '#1890ff', cursor: 'pointer' }}>
            Повторить
          </button>
        }
      />
    );
  }

  return (
    <div style={{ marginBottom: 16 }}>
      {/* Заголовок и фильтр дат */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
        flexDirection: isMobile ? 'column' : 'row',
        gap: isMobile ? 12 : 0,
      }}>
        <h3 style={{ margin: 0, fontSize: isMobile ? 16 : 18 }}>
          {title}
        </h3>
        
        {showDateFilter && (
          <RangePicker
            value={dateRange}
            onChange={handleDateChange}
            placeholder={['Дата от', 'Дата до']}
            style={{ width: isMobile ? '100%' : 300 }}
            size={isMobile ? 'small' : 'middle'}
          />
        )}
      </div>

      {/* Карточки со статистикой */}
      <Spin spinning={loading}>
        <Row gutter={[16, 16]}>
          {/* Общий доход */}
          <Col span={getColSpan()}>
            <Card size={size}>
              <Statistic
                title="Общий доход"
                value={summary?.income || 0}
                formatter={(value) => formatCurrency(Number(value))}
                valueStyle={{ 
                  color: '#3f8600',
                  fontSize: isMobile ? 18 : 24,
                }}
                prefix={<ArrowUpOutlined />}
              />
            </Card>
          </Col>

          {/* Общий расход */}
          <Col span={getColSpan()}>
            <Card size={size}>
              <Statistic
                title="Общий расход"
                value={Math.abs(summary?.expense || 0)}
                formatter={(value) => formatCurrency(Number(value))}
                valueStyle={{ 
                  color: '#cf1322',
                  fontSize: isMobile ? 18 : 24,
                }}
                prefix={<ArrowDownOutlined />}
              />
            </Card>
          </Col>

          {/* Чистая прибыль/убыток */}
          <Col span={getColSpan()}>
            <Card size={size}>
              <Statistic
                title="Чистая прибыль"
                value={summary?.net || 0}
                formatter={(value) => formatCurrency(Number(value))}
                valueStyle={{ 
                  color: (summary?.net || 0) >= 0 ? '#3f8600' : '#cf1322',
                  fontSize: isMobile ? 18 : 24,
                }}
                prefix={<CalculatorOutlined />}
              />
            </Card>
          </Col>

          {/* Количество транзакций */}
          <Col span={getColSpan()}>
            <Card size={size}>
              <Statistic
                title="Количество операций"
                value={summary?.total_transactions || 0}
                valueStyle={{ 
                  color: '#1890ff',
                  fontSize: isMobile ? 18 : 24,
                }}
                prefix={<TransactionOutlined />}
              />
            </Card>
          </Col>
        </Row>
      </Spin>
    </div>
  );
};

export default DashboardSummary;
