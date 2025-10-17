import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Spin, 
  message, 
  Typography, 
  Space, 
  Tag, 
  Button,
  Modal,
  Descriptions,
  Statistic,
  Row,
  Col
} from 'antd';
import { 
  EnvironmentOutlined, 
  HomeOutlined, 
  DollarOutlined,
  CalendarOutlined,
  UserOutlined
} from '@ant-design/icons';
import { MapContainer, TileLayer, Marker, Popup } from 'react-leaflet';
import { Icon } from 'leaflet';
import { rentApi } from '../services/api';
import { Rent } from '../types';
import 'leaflet/dist/leaflet.css';

const { Title, Text } = Typography;

// Исправляем проблему с иконками Leaflet
delete (Icon.Default.prototype as any)._getIconUrl;
Icon.Default.mergeOptions({
  iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
  iconUrl: require('leaflet/dist/images/marker-icon.png'),
  shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const RentMap: React.FC = () => {
  const [rents, setRents] = useState<Rent[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedRent, setSelectedRent] = useState<Rent | null>(null);
  const [modalVisible, setModalVisible] = useState(false);
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

  // Функция для очистки и валидации координат
  const cleanAndValidateCoordinates = (lat: any, lng: any): { lat: number | null, lng: number | null } => {
    try {
      // Очищаем от переносов строк и лишних символов
      const cleanLat = String(lat).replace(/[\n\r\t\s]+/g, '').trim();
      const cleanLng = String(lng).replace(/[\n\r\t\s]+/g, '').trim();
      
      // Парсим координаты
      const parsedLat = parseFloat(cleanLat);
      const parsedLng = parseFloat(cleanLng);
      
      // Проверяем валидность
      if (isNaN(parsedLat) || isNaN(parsedLng)) {
        return { lat: null, lng: null };
      }
      
      // Проверяем диапазон координат
      if (parsedLat < -90 || parsedLat > 90 || parsedLng < -180 || parsedLng > 180) {
        return { lat: null, lng: null };
      }
      
      return { lat: parsedLat, lng: parsedLng };
    } catch (error) {
      console.error('Ошибка парсинга координат:', error);
      return { lat: null, lng: null };
    }
  };

  // Загрузка данных аренды
  const fetchRents = async () => {
    setLoading(true);
    try {
      const response = await rentApi.getList({});
      console.log('Загруженные данные аренды:', response);
      
      // Фильтруем и очищаем координаты
      const rentsWithCoords = response.filter(rent => {
        const { lat, lng } = cleanAndValidateCoordinates(rent.latitude, rent.longitude);
        
        if (lat === null || lng === null) {
          console.log('Запись без валидных координат:', rent.id, rent.location, 'lat:', rent.latitude, 'lng:', rent.longitude);
          return false;
        }
        
        // Обновляем координаты в объекте
        rent.latitude = lat;
        rent.longitude = lng;
        
        return true;
      });
      
      console.log('Записи с валидными координатами:', rentsWithCoords);
      setRents(rentsWithCoords);
    } catch (error: any) {
      console.error('Ошибка загрузки данных аренды:', error);
      message.error('Ошибка загрузки данных аренды: ' + (error.response?.data?.error || error.message));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRents();
  }, []);

  // Показать детали аренды
  const showRentDetails = (rent: Rent) => {
    setSelectedRent(rent);
    setModalVisible(true);
  };

  // Получить цвет для статуса аренды
  const getRentStatusColor = (rent: Rent) => {
    const now = new Date();
    const endDate = new Date(rent.end_date);
    const startDate = new Date(rent.start_date);
    
    if (now < startDate) return 'blue'; // Будущая
    if (now > endDate) return 'red'; // Завершенная
    return 'green'; // Активная
  };

  // Получить текст статуса аренды
  const getRentStatusText = (rent: Rent) => {
    const now = new Date();
    const endDate = new Date(rent.end_date);
    const startDate = new Date(rent.start_date);
    
    if (now < startDate) return 'Будущая';
    if (now > endDate) return 'Завершенная';
    return 'Активная';
  };

  // Статистика
  const stats = {
    total: rents.length,
    active: rents.filter(rent => {
      const now = new Date();
      const endDate = new Date(rent.end_date);
      const startDate = new Date(rent.start_date);
      return now >= startDate && now <= endDate;
    }).length,
    totalAmount: rents.reduce((sum, rent) => sum + Number(rent.amount), 0)
  };

  console.log('Статистика карты:', stats);
  console.log('Количество записей с координатами:', rents.length);

  // Центр карты (Москва по умолчанию)
  const defaultCenter: [number, number] = [55.7558, 37.6176];

  // Вычисляем центр карты на основе данных
  const getMapCenter = (): [number, number] => {
    if (rents.length === 0) return defaultCenter;
    
    // Координаты уже очищены в fetchRents, поэтому просто проверяем их наличие
    const validRents = rents.filter(rent => 
      rent.latitude !== null && rent.longitude !== null && 
      rent.latitude !== undefined && rent.longitude !== undefined &&
      !isNaN(rent.latitude) && !isNaN(rent.longitude)
    );
    
    if (validRents.length === 0) return defaultCenter;
    
    const avgLat = validRents.reduce((sum, rent) => sum + (rent.latitude as number), 0) / validRents.length;
    const avgLng = validRents.reduce((sum, rent) => sum + (rent.longitude as number), 0) / validRents.length;
    
    return [avgLat, avgLng];
  };

  return (
    <div style={{ padding: isMobile ? 16 : 24 }}>
      <Title level={isMobile ? 3 : 2}>
        <EnvironmentOutlined /> Карта аренды
      </Title>
      
      {/* Статистика */}
      <Row gutter={isMobile ? 8 : 16} style={{ marginBottom: 16 }}>
        <Col span={isMobile ? 12 : 8}>
          <Card size="small">
            <Statistic
              title="Всего точек"
              value={stats.total}
              prefix={<EnvironmentOutlined />}
              valueStyle={{ fontSize: isMobile ? '16px' : undefined }}
            />
          </Card>
        </Col>
        <Col span={isMobile ? 12 : 8}>
          <Card size="small">
            <Statistic
              title="Активных"
              value={stats.active}
              prefix={<HomeOutlined />}
              valueStyle={{ color: '#3f8600', fontSize: isMobile ? '16px' : undefined }}
            />
          </Card>
        </Col>
        {!isMobile && (
          <Col span={8}>
            <Card size="small">
              <Statistic
                title="Общая сумма"
                value={stats.totalAmount}
                prefix={<DollarOutlined />}
                valueStyle={{ color: '#1890ff' }}
              />
            </Card>
          </Col>
        )}
      </Row>

      {/* Карта */}
      <Card 
        title="Точки аренды на карте" 
        size={isMobile ? 'small' : 'default'}
        style={{ height: isMobile ? '60vh' : '70vh' }}
        bodyStyle={{ height: 'calc(100% - 57px)', padding: 0 }}
      >
        {loading ? (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100%' 
          }}>
            <Spin size="large" />
          </div>
        ) : rents.length === 0 ? (
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            alignItems: 'center', 
            height: '100%',
            flexDirection: 'column',
            gap: 16
          }}>
            <EnvironmentOutlined style={{ fontSize: 48, color: '#ccc' }} />
            <div style={{ textAlign: 'center', color: '#666' }}>
              <div style={{ fontSize: 16, marginBottom: 8 }}>Нет данных с координатами</div>
              <div style={{ fontSize: 14 }}>Добавьте координаты в записи аренды для отображения на карте</div>
            </div>
          </div>
        ) : (
          <MapContainer
            center={getMapCenter()}
            zoom={10}
            style={{ height: '100%', width: '100%', minHeight: '400px' }}
          >
            <TileLayer
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
            />
            
            {rents.map((rent) => {
              // Координаты уже очищены в fetchRents
              const lat = rent.latitude as number;
              const lng = rent.longitude as number;
              
              console.log('Рендеринг маркера:', rent.id, 'координаты:', lat, lng);
              
              return (
                <Marker
                  key={rent.id}
                  position={[lat, lng]}
                  eventHandlers={{
                    click: () => showRentDetails(rent),
                  }}
                >
                  <Popup>
                    <div style={{ minWidth: 200 }}>
                      <h4 style={{ margin: '0 0 8px 0' }}>
                        <HomeOutlined /> {rent.location}
                      </h4>
                      <p style={{ margin: '4px 0' }}>
                        <DollarOutlined /> Сумма: {Number(rent.amount).toLocaleString()} ₽
                      </p>
                      <p style={{ margin: '4px 0' }}>
                        <CalendarOutlined /> {new Date(rent.start_date).toLocaleDateString()} - {new Date(rent.end_date).toLocaleDateString()}
                      </p>
                      <p style={{ margin: '4px 0' }}>
                        <UserOutlined /> {rent.payer?.name || 'Не указан'}
                      </p>
                      <Tag color={getRentStatusColor(rent)} style={{ marginTop: 8 }}>
                        {getRentStatusText(rent)}
                      </Tag>
                      <div style={{ marginTop: 8 }}>
                        <Button 
                          size="small" 
                          type="primary"
                          onClick={() => showRentDetails(rent)}
                        >
                          Подробнее
                        </Button>
                      </div>
                    </div>
                  </Popup>
                </Marker>
              );
            })}
          </MapContainer>
        )}
      </Card>

      {/* Модальное окно с деталями */}
      <Modal
        title="Детали аренды"
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setModalVisible(false)} size={isMobile ? "middle" : undefined}>
            Закрыть
          </Button>
        ]}
        width={isMobile ? '100%' : 600}
        style={isMobile ? { margin: 16 } : {}}
      >
        {selectedRent && (
          <Descriptions bordered column={isMobile ? 1 : 2}>
            <Descriptions.Item label="ID">{selectedRent.id}</Descriptions.Item>
            <Descriptions.Item label="Местоположение">{selectedRent.location}</Descriptions.Item>
            <Descriptions.Item label="Сумма">{Number(selectedRent.amount).toLocaleString()} ₽</Descriptions.Item>
            <Descriptions.Item label="Статус">
              <Tag color={getRentStatusColor(selectedRent)}>
                {getRentStatusText(selectedRent)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="Дата начала">
              {new Date(selectedRent.start_date).toLocaleDateString()}
            </Descriptions.Item>
            <Descriptions.Item label="Дата окончания">
              {new Date(selectedRent.end_date).toLocaleDateString()}
            </Descriptions.Item>
            <Descriptions.Item label="Плательщик">
              {selectedRent.payer?.name || 'Не указан'}
            </Descriptions.Item>
            <Descriptions.Item label="Координаты">
              {Number(selectedRent.latitude).toFixed(6)}, {Number(selectedRent.longitude).toFixed(6)}
            </Descriptions.Item>
            {selectedRent.details && (
              <Descriptions.Item label="Детали" span={isMobile ? 1 : 2}>
                {selectedRent.details}
              </Descriptions.Item>
            )}
            {selectedRent.machine && (
              <Descriptions.Item label="Автомат" span={isMobile ? 1 : 2}>
                {selectedRent.machine.name}
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Modal>
    </div>
  );
};

export default RentMap;
