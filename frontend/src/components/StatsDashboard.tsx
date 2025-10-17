import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { Card, Row, Col, Statistic, Spin, Alert, DatePicker } from 'antd';
import { Dayjs } from 'dayjs';

const { RangePicker } = DatePicker;

interface StatItem {
  title: string;
  value: number | string;
  prefix?: React.ReactNode;
  suffix?: string;
  color?: string;
  formatter?: (value: number | string) => string;
}

interface StatsDashboardProps {
  // API функция для получения данных
  fetchData: (params?: any) => Promise<any>;
  // Функция для рендеринга статистики
  renderStats: (data: any) => StatItem[];
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

const StatsDashboard: React.FC<StatsDashboardProps> = ({
  fetchData,
  renderStats,
  title = 'Статистика',
  showDateFilter = true,
  extraParams = {},
  size = 'default',
  columns = 4,
}) => {
  const [data, setData] = useState<any>(null);
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
  const loadData = useCallback(async () => {
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

      const response = await fetchData(params);
      setData(response);
    } catch (err) {
      setError('Ошибка при загрузке данных');
      console.error('Stats dashboard error:', err);
    } finally {
      setLoading(false);
    }
  }, [fetchData, stableExtraParams, dateRange]);

  // Загружаем данные при монтировании и изменении параметров
  useEffect(() => {
    loadData();
  }, [loadData]);

  // Обработчик изменения дат
  const handleDateChange = (dates: [Dayjs | null, Dayjs | null] | null) => {
    setDateRange(dates);
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
          <button onClick={loadData} style={{ border: 'none', background: 'none', color: '#1890ff', cursor: 'pointer' }}>
            Повторить
          </button>
        }
      />
    );
  }

  const stats = data ? renderStats(data) : [];

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
          {stats.map((stat, index) => (
            <Col key={index} span={getColSpan()}>
              <Card size={size}>
                <Statistic
                  title={stat.title}
                  value={stat.value}
                  prefix={stat.prefix}
                  suffix={stat.suffix}
                  formatter={stat.formatter}
                  valueStyle={{ 
                    color: stat.color || '#1890ff',
                    fontSize: isMobile ? 18 : 24,
                  }}
                />
              </Card>
            </Col>
          ))}
        </Row>
      </Spin>
    </div>
  );
};

export default StatsDashboard;










