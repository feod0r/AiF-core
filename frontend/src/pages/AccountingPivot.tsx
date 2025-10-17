import React, { useState, useEffect } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Card, Tabs, Table, Select, DatePicker, Row, Col, Statistic, Spin, message, List, Tag, Space } from 'antd';
import { 
  getAccountingChartData,
  getTransposedSumByCategories,
  getTransposedSumByCounterparties,
  getTransposedSumByMachines
} from '../services/api';
import { 
  AccountingChartResponse,
  TransposedSumResponse,
  TransposedSumRow
} from '../types';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

const { RangePicker } = DatePicker;

const AccountingPivot: React.FC = () => {
  const [activeTab, setActiveTab] = useState('categories');
  const [period, setPeriod] = useState<'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly'>('monthly');
  const [dateRange, setDateRange] = useState<[string, string] | null>(null);
  const [loading, setLoading] = useState(false);
  const [chartData, setChartData] = useState<AccountingChartResponse | null>(null);
  const [tableData, setTableData] = useState<TransposedSumResponse | null>(null);
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

  useEffect(() => {
    fetchChart();
  }, [period, dateRange]);

  useEffect(() => {
    fetchTable();
  }, [activeTab, period, dateRange]);

  const fetchChart = async () => {
    setLoading(true);
    try {
      const params: any = { period };
      if (dateRange) {
        params.start_date = dateRange[0];
        params.end_date = dateRange[1];
      }
      const response = await getAccountingChartData(params);
      setChartData(response);
    } catch (error) {
      message.error('Ошибка при загрузке диаграммы');
    } finally {
      setLoading(false);
    }
  };

  const fetchTable = async () => {
    setLoading(true);
    try {
      const params: any = { period };
      if (dateRange) {
        params.start_date = dateRange[0];
        params.end_date = dateRange[1];
      }
      let response;
      switch (activeTab) {
        case 'categories':
          response = await getTransposedSumByCategories(params);
          break;
        case 'counterparties':
          response = await getTransposedSumByCounterparties(params);
          break;
        case 'machines':
          response = await getTransposedSumByMachines(params);
          break;
        default:
          return;
      }
      setTableData(response);
    } catch (error) {
      message.error('Ошибка при загрузке таблицы');
    } finally {
      setLoading(false);
    }
  };

  const getTransposedColumns = () => {
    if (!tableData?.periods) return [];
    const columns: any[] = [
      {
        title: activeTab === 'categories' ? 'Категория' : activeTab === 'counterparties' ? 'Контрагент' : 'Автомат',
        dataIndex: 'name',
        key: 'name',
        width: 80,
        fixed: 'left' as const,
        className: 'pivot-col-ellipsis',
        render: (text: string) => (
          <span style={{ 
            fontWeight: ['Доход', 'Расходы', 'Итого'].includes(text) ? 'bold' : 'normal',
            color: text === 'Итого' ? '#1890ff' : 'inherit'
          }}>{text}</span>
        )
      }
    ];
    tableData.periods.forEach(period => {
      columns.push({
        title: period,
        dataIndex: period,
        key: period,
        width: 80,
        align: 'right',
        render: (value: number, record: TransposedSumRow) => {
          if (record.name === 'Доход' || (value > 0 && record.name !== 'Итого')) {
            return <span style={{ color: '#3f8600', fontWeight: record.name === 'Доход' ? 'bold' : undefined }}>{value ? value.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' }) : '-'}</span>;
          }
          if (record.name === 'Расходы' || (value < 0 && record.name !== 'Итого')) {
            return <span style={{ color: '#cf1322', fontWeight: record.name === 'Расходы' ? 'bold' : undefined }}>{value ? value.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' }) : '-'}</span>;
          }
          if (record.name === 'Итого') {
            return <span style={{ color: value >= 0 ? '#3f8600' : '#cf1322', fontWeight: 'bold' }}>{value ? value.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' }) : '-'}</span>;
          }
          return value ? value.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' }) : '-';
        }
      });
    });
    return columns;
  };

  const renderMobileListItem = (record: TransposedSumRow) => {
    const isSummary = ['Доход', 'Расходы', 'Итого'].includes(record.name);
    const totalValue = tableData?.periods?.reduce((sum, period) => {
      const value = (record as any)[period] || 0;
      return sum + value;
    }, 0) || 0;

    return (
      <List.Item
        style={{
          padding: '8px 0',
          borderBottom: '1px solid #f0f0f0',
          backgroundColor: isSummary ? '#fafafa' : 'white'
        }}
      >
        <div style={{ width: '100%' }}>
          {/* Заголовок с названием и общим итогом */}
          <div style={{ 
            marginBottom: 8,
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span style={{ 
              fontSize: isSummary ? 15 : 13,
              fontWeight: isSummary ? 'bold' : 'normal',
              color: record.name === 'Итого' ? '#1890ff' : 'inherit'
            }}>
              {record.name}
            </span>
            <span style={{ 
              fontSize: isSummary ? 15 : 13,
              fontWeight: 'bold',
              color: totalValue >= 0 ? '#3f8600' : '#cf1322'
            }}>
              {totalValue ? totalValue.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' }) : '-'}
            </span>
          </div>

          {/* Детализация по периодам */}
          {tableData?.periods && tableData.periods.length > 0 && (
            <div style={{ marginBottom: 4 }}>
              <div style={{ fontSize: 11, color: '#666', marginBottom: 4 }}>
                Детализация по периодам:
              </div>
              <Space wrap size={[4, 4]}>
                {tableData.periods.map(period => {
                  const value = (record as any)[period] || 0;
                  let color = 'default';
                  if (record.name === 'Доход' || (value > 0 && record.name !== 'Итого')) {
                    color = 'green';
                  } else if (record.name === 'Расходы' || (value < 0 && record.name !== 'Итого')) {
                    color = 'red';
                  } else if (record.name === 'Итого') {
                    color = value >= 0 ? 'green' : 'red';
                  }
                  
                  return (
                    <Tag key={period} color={color} style={{ fontSize: 10, padding: '2px 6px' }}>
                      {period}: {value ? value.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' }) : '-'}
                    </Tag>
                  );
                })}
              </Space>
            </div>
          )}
        </div>
      </List.Item>
    );
  };

  return (
    <PageContainer
      title="Сводные таблицы аккаунтинга"
      subTitle="Анализ доходов и расходов по категориям, контрагентам и автоматам"
      style={isMobile ? { 
        padding: '0px',
        margin: '0 -16px'
      } : {}}
    >
      <Card style={{ 
        marginBottom: isMobile ? 4 : 24,
        marginLeft: isMobile ? '-8px' : 0,
        marginRight: isMobile ? '-8px' : 0,
        borderRadius: isMobile ? '0px' : undefined
      }} size={isMobile ? 'small' : 'default'}>
        {isMobile ? (
          // Мобильная версия фильтров - вертикальное расположение
          <Space direction="vertical" size="small" style={{ width: '100%', marginBottom: 4 }}>
            <Select
              placeholder="Период"
              value={period}
              style={{ width: '100%' }}
              onChange={setPeriod}
              size="small"
            >
              <Select.Option value="daily">По дням</Select.Option>
              <Select.Option value="weekly">По неделям</Select.Option>
              <Select.Option value="monthly">По месяцам</Select.Option>
              <Select.Option value="quarterly">По кварталам</Select.Option>
              <Select.Option value="yearly">По годам</Select.Option>
            </Select>
            <RangePicker
              style={{ width: '100%' }}
              size="small"
              onChange={(dates) => {
                if (dates) {
                  setDateRange([dates[0]!.format('YYYY-MM-DD'), dates[1]!.format('YYYY-MM-DD')]);
                } else {
                  setDateRange(null);
                }
              }}
            />
          </Space>
        ) : (
          // Десктопная версия фильтров - горизонтальное расположение
          <Row gutter={16} style={{ marginBottom: 16 }}>
            <Col span={6}>
              <Select
                placeholder="Период"
                value={period}
                style={{ width: '100%' }}
                onChange={setPeriod}
              >
                <Select.Option value="daily">По дням</Select.Option>
                <Select.Option value="weekly">По неделям</Select.Option>
                <Select.Option value="monthly">По месяцам</Select.Option>
                <Select.Option value="quarterly">По кварталам</Select.Option>
                <Select.Option value="yearly">По годам</Select.Option>
              </Select>
            </Col>
            <Col span={12}>
              <RangePicker
                style={{ width: '100%' }}
                onChange={(dates) => {
                  if (dates) {
                    setDateRange([dates[0]!.format('YYYY-MM-DD'), dates[1]!.format('YYYY-MM-DD')]);
                  } else {
                    setDateRange(null);
                  }
                }}
              />
            </Col>
          </Row>
        )}
        
        <div style={{ height: isMobile ? 250 : 400 }}>
          {chartData?.data ? (
            <Bar
              data={chartData.data}
              options={{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                  legend: { 
                    position: 'top' as const,
                    labels: {
                      font: {
                        size: isMobile ? 10 : 12
                      }
                    }
                  },
                  title: { 
                    display: true, 
                    text: 'Доходы и расходы по периодам',
                    font: {
                      size: isMobile ? 14 : 16
                    }
                  },
                },
                scales: {
                  x: {
                    ticks: {
                      font: {
                        size: isMobile ? 10 : 12
                      }
                    }
                  },
                  y: {
                    beginAtZero: true,
                    ticks: {
                      font: {
                        size: isMobile ? 10 : 12
                      },
                      callback: function(value) {
                        return value.toLocaleString('ru-RU', { style: 'currency', currency: 'RUB' });
                      }
                    }
                  }
                }
              }}
            />
          ) : (
            <div style={{ textAlign: 'center', padding: isMobile ? '30px' : '50px' }}>
              {loading ? <Spin size="large" /> : 'Нет данных для отображения'}
            </div>
          )}
        </div>
      </Card>
      
      <Card size={isMobile ? 'small' : 'default'} style={isMobile ? { 
        padding: '4px',
        marginLeft: '-8px',
        marginRight: '-8px',
        borderRadius: '0px'
      } : {}}>
                  <Tabs
            activeKey={activeTab}
            onChange={setActiveTab}
            size={isMobile ? 'small' : 'middle'}
            style={isMobile ? { margin: '-4px' } : {}}
          items={[
            {
              key: 'categories',
              label: isMobile ? 'Категории' : 'По категориям операций',
              children: isMobile ? (
                <List
                  dataSource={tableData?.rows || []}
                  loading={loading}
                  renderItem={renderMobileListItem}
                  locale={{ emptyText: 'Нет данных для отображения' }}
                />
              ) : (
                <Table
                  columns={getTransposedColumns()}
                  dataSource={tableData?.rows || []}
                  loading={loading}
                  scroll={{ x: 0 }}
                  pagination={false}
                  bordered
                  className="pivot-table-compact"
                  rowClassName={(record: TransposedSumRow) => ['Доход', 'Расходы', 'Итого'].includes(record.name) ? 'ant-table-summary-row' : ''}
                />
              ),
            },
            {
              key: 'counterparties',
              label: isMobile ? 'Контрагенты' : 'По контрагентам',
              children: isMobile ? (
                <List
                  dataSource={tableData?.rows || []}
                  loading={loading}
                  renderItem={renderMobileListItem}
                  locale={{ emptyText: 'Нет данных для отображения' }}
                />
              ) : (
                <Table
                  columns={getTransposedColumns()}
                  dataSource={tableData?.rows || []}
                  loading={loading}
                  scroll={{ x: 0 }}
                  pagination={false}
                  bordered
                  className="pivot-table-compact"
                  rowClassName={(record: TransposedSumRow) => ['Доход', 'Расходы', 'Итого'].includes(record.name) ? 'ant-table-summary-row' : ''}
                />
              ),
            },
            {
              key: 'machines',
              label: isMobile ? 'Автоматы' : 'По автоматам',
              children: isMobile ? (
                <List
                  dataSource={tableData?.rows || []}
                  loading={loading}
                  renderItem={renderMobileListItem}
                  locale={{ emptyText: 'Нет данных для отображения' }}
                />
              ) : (
                <Table
                  columns={getTransposedColumns()}
                  dataSource={tableData?.rows || []}
                  loading={loading}
                  scroll={{ x: 0 }}
                  pagination={false}
                  bordered
                  className="pivot-table-compact"
                  rowClassName={(record: TransposedSumRow) => ['Доход', 'Расходы', 'Итого'].includes(record.name) ? 'ant-table-summary-row' : ''}
                />
              ),
            },
          ]}
        />
      </Card>
    </PageContainer>
  );
};

export default AccountingPivot; 