import React, { useState, useEffect } from 'react';
import { PageContainer } from '@ant-design/pro-components';
import { Typography } from 'antd';
import { BarChartOutlined } from '@ant-design/icons';
import Charts from '../components/Charts';

const { Title } = Typography;

const ChartsPage: React.FC = () => {
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

  return (
    <div style={{ padding: isMobile ? '16px' : '24px' }}>
      <div style={{ 
        marginBottom: 24, 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        flexDirection: isMobile ? 'column' : 'row',
        gap: isMobile ? 12 : 0
      }}>
        <Title level={isMobile ? 3 : 2} style={{ 
          margin: 0,
          fontSize: isMobile ? 18 : undefined,
          lineHeight: isMobile ? 1.4 : undefined
        }}>
          <BarChartOutlined /> Графики
        </Title>
        <div style={{ 
          fontSize: isMobile ? 14 : 16, 
          color: '#666',
          textAlign: isMobile ? 'center' : 'left'
        }}>
          Аналитика по игрушкам, монетам и прибыли
        </div>
      </div>

      <Charts 
        title="Продажа игрушек" 
        type="toys" 
        color="#1890ff" 
        isMobile={isMobile}
      />
      <Charts 
        title="Заработок монет" 
        type="coins" 
        color="#52c41a" 
        isMobile={isMobile}
      />
      <Charts 
        title="Прибыль" 
        type="profit" 
        color="#fa8c16" 
        isMobile={isMobile}
      />
    </div>
  );
};

export default ChartsPage; 