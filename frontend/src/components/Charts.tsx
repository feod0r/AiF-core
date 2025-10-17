import React, { useState, useEffect } from 'react';
import { Card, Select, DatePicker, Row, Col, Spin, message, Space } from 'antd';
import { Line } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { getToysChartData, getCoinsChartData, getProfitChartData, machinesApi } from '../services/api';
import { ChartData, ChartParams, Machine } from '../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

const { RangePicker } = DatePicker;

interface ChartsProps {
  title: string;
  type: 'toys' | 'coins' | 'profit';
  color: string;
  isMobile?: boolean;
}

const Charts: React.FC<ChartsProps> = ({ title, type, color, isMobile = false }) => {
  const [data, setData] = useState<ChartData | null>(null);
  const [loading, setLoading] = useState(false);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [params, setParams] = useState<ChartParams>({
    period: 'daily',
  });

  useEffect(() => {
    fetchMachines();
  }, []);

  useEffect(() => {
    fetchChartData();
  }, [params, type]);

  const fetchMachines = async () => {
    try {
      const response = await machinesApi.getList();
      setMachines(response.data || []);
    } catch (error) {
      console.error('Error fetching machines:', error);
    }
  };

  const fetchChartData = async () => {
    setLoading(true);
    try {
      let response;
      switch (type) {
        case 'toys':
          response = await getToysChartData(params);
          break;
        case 'coins':
          response = await getCoinsChartData(params);
          break;
        case 'profit':
          response = await getProfitChartData(params);
          break;
        default:
          return;
      }
      if (response && Array.isArray(response.data)) {
        response.data = response.data.reverse();
      }
      setData(response);
    } catch (error) {
      console.error(`Error fetching ${type} chart data:`, error);
      message.error(`Ошибка при загрузке данных для графика ${title}`);
    } finally {
      setLoading(false);
    }
  };

  const getChartData = () => {
    if (!data?.data) return { labels: [], datasets: [] };

    const labels = data.data.map(item => item.period);
    let values: number[] = [];

    switch (type) {
      case 'toys':
        values = data.data.map(item => item.total_toys_sold || 0);
        break;
      case 'coins':
        values = data.data.map(item => item.total_coins_earned || 0);
        break;
      case 'profit':
        values = data.data.map(item => item.total_profit || 0);
        break;
    }

    return {
      labels,
      datasets: [
        {
          label: title,
          data: values,
          borderColor: color,
          backgroundColor: color + '20',
          tension: 0.1,
          fill: true,
        },
      ],
    };
  };

  const getYAxisLabel = () => {
    switch (type) {
      case 'toys':
        return 'Продано игрушек';
      case 'coins':
        return 'Заработано монет';
      case 'profit':
        return 'Прибыль (руб.)';
      default:
        return '';
    }
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
        labels: {
          font: {
            size: isMobile ? 12 : 14
          }
        }
      },
      title: {
        display: true,
        text: title,
        font: {
          size: isMobile ? 14 : 16
        }
      },
    },
    scales: {
      y: {
        beginAtZero: true,
        title: {
          display: true,
          text: getYAxisLabel(),
          font: {
            size: isMobile ? 12 : 14
          }
        },
        ticks: {
          font: {
            size: isMobile ? 10 : 12
          }
        }
      },
      x: {
        title: {
          display: true,
          text: 'Период',
          font: {
            size: isMobile ? 12 : 14
          }
        },
        ticks: {
          font: {
            size: isMobile ? 10 : 12
          }
        }
      },
    },
  };

  return (
    <Card 
      title={title} 
      style={{ 
        marginBottom: 16,
        fontSize: isMobile ? 14 : 16
      }}
      size={isMobile ? 'small' : 'default'}
    >
      {isMobile ? (
        // Мобильная версия - вертикальное расположение фильтров
        <Space direction="vertical" size="small" style={{ width: '100%', marginBottom: 16 }}>
          <Select
            placeholder="Выберите автомат"
            allowClear
            style={{ width: '100%' }}
            size="small"
            value={params.machine_id || undefined}
            onChange={(value) => {
              setParams(prev => ({ ...prev, machine_id: value }));
            }}
          >
            <Select.Option value="">Все автоматы</Select.Option>
            {machines.map(machine => (
              <Select.Option key={machine.id} value={machine.id}>
                {machine.name}
              </Select.Option>
            ))}
          </Select>
          
          <Select
            placeholder="Период"
            value={params.period}
            style={{ width: '100%' }}
            size="small"
            onChange={(value) => setParams(prev => ({ ...prev, period: value }))}
          >
            <Select.Option value="daily">По дням</Select.Option>
            <Select.Option value="weekly">По неделям</Select.Option>
            <Select.Option value="monthly">По месяцам</Select.Option>
            <Select.Option value="quarterly">По кварталам</Select.Option>
            <Select.Option value="halfyear">По полугодиям</Select.Option>
            <Select.Option value="yearly">По годам</Select.Option>
          </Select>
          
          <RangePicker
            style={{ width: '100%' }}
            size="small"
            onChange={(dates) => {
              if (dates) {
                setParams(prev => ({
                  ...prev,
                  start_date: dates[0]?.toISOString().split('T')[0],
                  end_date: dates[1]?.toISOString().split('T')[0],
                }));
              } else {
                setParams(prev => ({ ...prev, start_date: undefined, end_date: undefined }));
              }
            }}
          />
        </Space>
      ) : (
        // Десктопная версия - горизонтальное расположение фильтров
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={6}>
            <Select
              placeholder="Выберите автомат"
              allowClear
              style={{ width: '100%' }}
              value={params.machine_id || undefined}
              onChange={(value) => {
                setParams(prev => ({ ...prev, machine_id: value }));
              }}
            >
              <Select.Option value="">Все автоматы</Select.Option>
              {machines.map(machine => (
                <Select.Option key={machine.id} value={machine.id}>
                  {machine.name}
                </Select.Option>
              ))}
            </Select>
          </Col>
          <Col span={6}>
            <Select
              placeholder="Период"
              value={params.period}
              style={{ width: '100%' }}
              onChange={(value) => setParams(prev => ({ ...prev, period: value }))}
            >
              <Select.Option value="daily">По дням</Select.Option>
              <Select.Option value="weekly">По неделям</Select.Option>
              <Select.Option value="monthly">По месяцам</Select.Option>
              <Select.Option value="quarterly">По кварталам</Select.Option>
              <Select.Option value="halfyear">По полугодиям</Select.Option>
              <Select.Option value="yearly">По годам</Select.Option>
            </Select>
          </Col>
          <Col span={12}>
            <RangePicker
              style={{ width: '100%' }}
              onChange={(dates) => {
                if (dates) {
                  setParams(prev => ({
                    ...prev,
                    start_date: dates[0]?.toISOString().split('T')[0],
                    end_date: dates[1]?.toISOString().split('T')[0],
                  }));
                } else {
                  setParams(prev => ({ ...prev, start_date: undefined, end_date: undefined }));
                }
              }}
            />
          </Col>
        </Row>
      )}

      {loading ? (
        <div style={{ textAlign: 'center', padding: isMobile ? '30px' : '50px' }}>
          <Spin size={isMobile ? 'default' : 'large'} />
        </div>
      ) : (
        <div style={{ height: isMobile ? '300px' : '400px' }}>
          <Line data={getChartData()} options={options} />
        </div>
      )}
    </Card>
  );
};

export default Charts; 