import React, { useState, useEffect } from 'react';
import {
  PageContainer,
  ProTable,
  ModalForm,
  ProFormText,
  ProFormTextArea,
  ProFormSelect,
  ProFormRadio,
} from '@ant-design/pro-components';
import {
  Button,
  message,
  Space,
  Tag,
  Card,
  Statistic,
  Row,
  Col,
  Alert,
  Drawer,
  Descriptions,
  Typography,
  Badge,
  List,
  Divider,
  Timeline,
} from 'antd';
import {
  SendOutlined,
  MessageOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  HistoryOutlined,
  InfoCircleOutlined,
  BellOutlined,
} from '@ant-design/icons';
import { telegramApi } from '../services/api';
import { SendNotificationRequest, SendNotificationResponse, NOTIFICATION_TYPES } from '../types';
import dayjs from 'dayjs';

const { Title, Text, Paragraph } = Typography;

const TelegramNotifications: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [sendModalVisible, setSendModalVisible] = useState(false);
  const [historyDrawerVisible, setHistoryDrawerVisible] = useState(false);
  const [notificationHistory, setNotificationHistory] = useState<any[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);
  const [lastSendResult, setLastSendResult] = useState<SendNotificationResponse | null>(null);
  const [resultDrawerVisible, setResultDrawerVisible] = useState(false);

  const fetchStats = async () => {
    try {
      const data = await telegramApi.getStats();
      setStats(data);
    } catch (error) {
      console.error('Ошибка при загрузке статистики:', error);
    }
  };

  const fetchHistory = async () => {
    setHistoryLoading(true);
    try {
      const data = await telegramApi.getNotificationHistory();
      setNotificationHistory(data);
    } catch (error) {
      message.error('Ошибка при загрузке истории');
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, []);

  const handleSendNotification = async (values: SendNotificationRequest) => {
    setLoading(true);
    try {
      const result = await telegramApi.sendNotification(values);
      setLastSendResult(result);
      setResultDrawerVisible(true);
      message.success(`Уведомление отправлено в ${result.sent_to} чатов`);
      fetchStats(); // Обновляем статистику
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при отправке уведомления');
    } finally {
      setLoading(false);
    }
  };

  const getNotificationTypeName = (typeId: string) => {
    const type = NOTIFICATION_TYPES.find(t => t.id === typeId);
    return type?.name || typeId;
  };

  const getNotificationTypeColor = (typeId: string) => {
    const type = NOTIFICATION_TYPES.find(t => t.id === typeId);
    switch (type?.category) {
      case 'inventory': return 'orange';
      case 'payments': return 'red';
      case 'technical': return 'purple';
      case 'reports': return 'blue';
      case 'custom': return 'green';
      default: return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'red';
      case 'medium': return 'orange';
      case 'low': return 'green';
      default: return 'default';
    }
  };

  const getPriorityName = (priority: string) => {
    switch (priority) {
      case 'high': return 'Высокий';
      case 'medium': return 'Средний';
      case 'low': return 'Низкий';
      default: return 'Не указан';
    }
  };

  const historyColumns = [
    {
      title: 'Тип уведомления',
      dataIndex: 'notification_type',
      key: 'notification_type',
      render: (_: any, record: any) => (
        <Tag color={getNotificationTypeColor(record.notification_type)}>
          {getNotificationTypeName(record.notification_type)}
        </Tag>
      ),
    },
    {
      title: 'Сообщение',
      dataIndex: 'message',
      key: 'message',
      render: (_: any, record: any) => (
        <Text style={{ maxWidth: 300 }} ellipsis={{ tooltip: record.message }}>
          {record.message}
        </Text>
      ),
    },
    {
      title: 'Приоритет',
      dataIndex: 'priority',
      key: 'priority',
      render: (_: any, record: any) => (
        <Tag color={getPriorityColor(record.priority)}>
          {getPriorityName(record.priority)}
        </Tag>
      ),
    },
    {
      title: 'Отправлено',
      dataIndex: 'sent_to',
      key: 'sent_to',
      render: (_: any, record: any) => (
        <Space>
          <Text>{record.sent_to}</Text>
          {record.failed > 0 && (
            <Text type="danger">({record.failed} ошибок)</Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Дата отправки',
      dataIndex: 'sent_at',
      key: 'sent_at',
      render: (_: any, record: any) => dayjs(record.sent_at).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Статус',
      dataIndex: 'success',
      key: 'success',
      render: (_: any, record: any) => (
        <Badge
          status={record.success ? 'success' : 'error'}
          text={record.success ? 'Успешно' : 'Ошибка'}
        />
      ),
    },
  ];

  return (
    <PageContainer
      title="Telegram Уведомления"
      subTitle="Отправка уведомлений через Telegram"
      extra={[
        <Button
          key="history"
          icon={<HistoryOutlined />}
          onClick={() => {
            setHistoryDrawerVisible(true);
            fetchHistory();
          }}
        >
          История
        </Button>,
        <Button
          key="send"
          type="primary"
          icon={<SendOutlined />}
          onClick={() => setSendModalVisible(true)}
        >
          Отправить уведомление
        </Button>,
      ]}
    >
      {/* Статистика */}
      {stats && (
        <Card style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="Всего уведомлений"
                value={stats.total_notifications_sent}
                prefix={<MessageOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Успешно отправлено"
                value={stats.successful_notifications}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Ошибок отправки"
                value={stats.failed_notifications}
                valueStyle={{ color: '#cf1322' }}
                prefix={<CloseCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Активных ботов"
                value={stats.active_bots}
                prefix={<BellOutlined />}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Информационная карточка */}
      <Card style={{ marginBottom: 24 }}>
        <Alert
          message="Как использовать уведомления"
          description={
            <div>
              <Paragraph>
                1. <strong>Создайте Telegram бота</strong> через @BotFather и получите токен
              </Paragraph>
              <Paragraph>
                2. <strong>Добавьте бота в чат</strong> и получите Chat ID
              </Paragraph>
              <Paragraph>
                3. <strong>Настройте бота</strong> в разделе "Telegram Боты" с нужными типами уведомлений
              </Paragraph>
              <Paragraph>
                4. <strong>Отправляйте уведомления</strong> через эту страницу или используйте API
              </Paragraph>
            </div>
          }
          type="info"
          showIcon
          icon={<InfoCircleOutlined />}
        />
      </Card>

      {/* Предопределенные типы уведомлений */}
      <Card title="Доступные типы уведомлений" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          {NOTIFICATION_TYPES.map(type => (
            <Col span={8} key={type.id}>
              <Card size="small">
                <Space direction="vertical" size={4}>
                  <Tag color={getNotificationTypeColor(type.id)}>
                    {type.name}
                  </Tag>
                  <Text type="secondary" style={{ fontSize: '12px' }}>
                    {type.description}
                  </Text>
                </Space>
              </Card>
            </Col>
          ))}
        </Row>
      </Card>

      {/* Модальное окно отправки */}
      <ModalForm
        title="Отправить уведомление"
        open={sendModalVisible}
        onOpenChange={setSendModalVisible}
        onFinish={handleSendNotification}
        modalProps={{
          destroyOnClose: true,
          width: 600,
        }}
      >
        <Alert
          message="Информация"
          description="Уведомление будет отправлено во все активные чаты, подписанные на выбранный тип уведомлений"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        
        <ProFormSelect
          name="notification_type"
          label="Тип уведомления"
          options={NOTIFICATION_TYPES.map(type => ({
            label: type.name,
            value: type.id,
          }))}
          rules={[{ required: true, message: 'Выберите тип уведомления' }]}
        />
        
        <ProFormText
          name="title"
          label="Заголовок (необязательно)"
          placeholder="Краткий заголовок сообщения"
        />
        
        <ProFormTextArea
          name="message"
          label="Сообщение"
          placeholder="Введите текст уведомления"
          rules={[{ required: true, message: 'Введите сообщение' }]}
          fieldProps={{
            rows: 4,
          }}
        />
        
        <ProFormRadio.Group
          name="priority"
          label="Приоритет"
          options={[
            { label: 'Низкий', value: 'low' },
            { label: 'Средний', value: 'medium' },
            { label: 'Высокий', value: 'high' },
          ]}
          initialValue="medium"
        />
      </ModalForm>

      {/* Детальный результат отправки */}
      <Drawer
        title="Результат отправки уведомления"
        open={resultDrawerVisible}
        onClose={() => setResultDrawerVisible(false)}
        width={600}
      >
        {lastSendResult && (
          <div>
            <Alert
              message={`Отправлено: ${lastSendResult.sent_to} чатов`}
              description={`Ошибок: ${lastSendResult.failed}`}
              type={lastSendResult.success ? 'success' : 'warning'}
              showIcon
              style={{ marginBottom: 16 }}
            />
            
            <Title level={5}>Детали отправки:</Title>
            <List
              dataSource={lastSendResult.details}
              renderItem={(item) => (
                <List.Item>
                  <List.Item.Meta
                    title={item.bot_name}
                    description={
                      <Space>
                        <Badge
                          status={item.status === 'success' ? 'success' : 'error'}
                          text={item.status === 'success' ? 'Успешно' : 'Ошибка'}
                        />
                        {item.error && (
                          <Text type="danger" style={{ fontSize: '12px' }}>
                            {item.error}
                          </Text>
                        )}
                      </Space>
                    }
                  />
                </List.Item>
              )}
            />
          </div>
        )}
      </Drawer>

      {/* История уведомлений */}
      <Drawer
        title="История уведомлений"
        open={historyDrawerVisible}
        onClose={() => setHistoryDrawerVisible(false)}
        width={800}
      >
        <ProTable
          columns={historyColumns}
          dataSource={notificationHistory}
          loading={historyLoading}
          rowKey="id"
          search={false}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
          }}
          toolBarRender={false}
        />
      </Drawer>
    </PageContainer>
  );
};

export default TelegramNotifications;
