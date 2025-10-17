import React, { useState, useEffect } from 'react';
import {
  PageContainer,
  ProTable,
  ModalForm,
  ProFormText,
  ProFormTextArea,
  ProFormSelect,
  ProFormSwitch,
} from '@ant-design/pro-components';
import {
  Button,
  message,
  Popconfirm,
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
  Divider,
  Badge,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  SendOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined,
  RobotOutlined,
  MessageOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import { telegramApi } from '../services/api';
import { TelegramBot, TelegramBotCreate, TelegramBotUpdate, NOTIFICATION_TYPES } from '../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;

const TelegramBots: React.FC = () => {
  const [bots, setBots] = useState<TelegramBot[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState<any>(null);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [selectedBot, setSelectedBot] = useState<TelegramBot | null>(null);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [testModalVisible, setTestModalVisible] = useState(false);
  const [testMessage, setTestMessage] = useState('');
  const [testLoading, setTestLoading] = useState(false);

  const fetchBots = async () => {
    setLoading(true);
    try {
      const data = await telegramApi.listBots();
      setBots(data);
    } catch (error) {
      message.error('Ошибка при загрузке ботов');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await telegramApi.getBotStats();
      setStats(data);
    } catch (error) {
      console.error('Ошибка при загрузке статистики:', error);
    }
  };

  useEffect(() => {
    fetchBots();
    fetchStats();
  }, []);

  const handleCreate = async (values: TelegramBotCreate) => {
    try {
      await telegramApi.createBot(values);
      message.success('Бот успешно создан');
      setCreateModalVisible(false);
      fetchBots();
      fetchStats();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при создании бота');
    }
  };

  const handleUpdate = async (values: TelegramBotUpdate) => {
    if (!selectedBot) return;
    try {
      await telegramApi.updateBot(selectedBot.id, values);
      message.success('Бот успешно обновлен');
      setEditModalVisible(false);
      setSelectedBot(null);
      fetchBots();
      fetchStats();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при обновлении бота');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await telegramApi.deleteBot(id);
      message.success('Бот успешно удален');
      fetchBots();
      fetchStats();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при удалении бота');
    }
  };

  const handleToggleActive = async (bot: TelegramBot) => {
    try {
      if (bot.is_active) {
        await telegramApi.deactivateBot(bot.id);
        message.success('Бот деактивирован');
      } else {
        await telegramApi.activateBot(bot.id);
        message.success('Бот активирован');
      }
      fetchBots();
      fetchStats();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при изменении статуса бота');
    }
  };

  const handleTestBot = async (bot: TelegramBot) => {
    setSelectedBot(bot);
    setTestModalVisible(true);
  };

  const sendTestMessage = async () => {
    if (!selectedBot || !testMessage.trim()) return;
    
    setTestLoading(true);
    try {
      await telegramApi.testBot(selectedBot.id, testMessage);
      message.success('Тестовое сообщение отправлено');
      setTestModalVisible(false);
      setTestMessage('');
      fetchBots(); // Обновляем статус тестирования
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при отправке тестового сообщения');
    } finally {
      setTestLoading(false);
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

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      render: (_: any, record: TelegramBot) => (
        <Space>
          <RobotOutlined />
          <Text strong>{record.name}</Text>
          {record.is_active ? (
            <Badge status="success" text="Активен" />
          ) : (
            <Badge status="default" text="Неактивен" />
          )}
        </Space>
      ),
    },
    {
      title: 'Chat ID',
      dataIndex: 'chat_id',
      key: 'chat_id',
      render: (_: any, record: TelegramBot) => (
        <Text code style={{ fontSize: '12px' }}>
          {record.chat_id.length > 20 ? `${record.chat_id.substring(0, 20)}...` : record.chat_id}
        </Text>
      ),
    },
    {
      title: 'Типы уведомлений',
      dataIndex: 'notification_types',
      key: 'notification_types',
      render: (_: any, record: TelegramBot) => (
        <Space wrap>
          {record.notification_types.map(type => (
            <Tag key={type} color={getNotificationTypeColor(type)}>
              {getNotificationTypeName(type)}
            </Tag>
          ))}
        </Space>
      ),
    },
    {
      title: 'Последний тест',
      dataIndex: 'last_test_message_at',
      key: 'last_test_message_at',
      render: (_: any, record: TelegramBot) => {
        if (!record.last_test_message_at) return <Text type="secondary">Не тестировался</Text>;
        return (
          <Space direction="vertical" size={0}>
            <Text>{dayjs(record.last_test_message_at).format('DD.MM.YYYY HH:mm')}</Text>
            {record.test_message_status && (
              <Tag color={record.test_message_status === 'success' ? 'success' : 'error'}>
                {record.test_message_status === 'success' ? 'Успешно' : 'Ошибка'}
              </Tag>
            )}
          </Space>
        );
      },
    },
    {
      title: 'Создан',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (_: any, record: TelegramBot) => dayjs(record.created_at).format('DD.MM.YYYY'),
    },
    {
      title: 'Действия',
      key: 'actions',
      render: (_: any, record: TelegramBot) => (
        <Space>
          <Button
            type="link"
            icon={<SettingOutlined />}
            onClick={() => {
              setSelectedBot(record);
              setDetailDrawerVisible(true);
            }}
          >
            Детали
          </Button>
          <Button
            type="link"
            icon={<MessageOutlined />}
            onClick={() => handleTestBot(record)}
          >
            Тест
          </Button>
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => {
              setSelectedBot(record);
              setEditModalVisible(true);
            }}
          >
            Изменить
          </Button>
          <Button
            type={record.is_active ? 'default' : 'primary'}
            size="small"
            onClick={() => handleToggleActive(record)}
          >
            {record.is_active ? 'Деактивировать' : 'Активировать'}
          </Button>
          <Popconfirm
            title="Удалить бота?"
            description="Это действие нельзя отменить"
            onConfirm={() => handleDelete(record.id)}
            okText="Да"
            cancelText="Нет"
          >
            <Button type="link" danger icon={<DeleteOutlined />}>
              Удалить
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <PageContainer
      title="Telegram Боты"
      subTitle="Управление уведомлениями через Telegram"
      extra={[
        <Button
          key="create"
          type="primary"
          icon={<PlusOutlined />}
          onClick={() => setCreateModalVisible(true)}
        >
          Добавить бота
        </Button>,
      ]}
    >
      {/* Статистика */}
      {stats && (
        <Card style={{ marginBottom: 24 }}>
          <Row gutter={16}>
            <Col span={6}>
              <Statistic
                title="Всего ботов"
                value={stats.total_bots}
                prefix={<RobotOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Активных"
                value={stats.active_bots}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Неактивных"
                value={stats.inactive_bots}
                valueStyle={{ color: '#cf1322' }}
                prefix={<CloseCircleOutlined />}
              />
            </Col>
            <Col span={6}>
              <Statistic
                title="Сообщений отправлено"
                value={stats.total_notifications_sent}
                prefix={<MessageOutlined />}
              />
            </Col>
          </Row>
        </Card>
      )}

      {/* Таблица ботов */}
      <ProTable
        columns={columns}
        dataSource={bots}
        loading={loading}
        rowKey="id"
        search={false}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          showQuickJumper: true,
        }}
        toolBarRender={false}
      />

      {/* Модальное окно создания */}
      <ModalForm
        title="Добавить Telegram бота"
        open={createModalVisible}
        onOpenChange={setCreateModalVisible}
        onFinish={handleCreate}
        modalProps={{
          destroyOnClose: true,
        }}
      >
        <ProFormText
          name="name"
          label="Название бота"
          placeholder="Введите название бота"
          rules={[{ required: true, message: 'Введите название бота' }]}
        />
        <ProFormText
          name="bot_token"
          label="Токен бота"
          placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
          rules={[{ required: true, message: 'Введите токен бота' }]}
        />
        <ProFormText
          name="chat_id"
          label="Chat ID"
          placeholder="-1001234567890"
          rules={[{ required: true, message: 'Введите Chat ID' }]}
        />
        <ProFormSelect
          name="notification_types"
          label="Типы уведомлений"
          mode="multiple"
          options={NOTIFICATION_TYPES.map(type => ({
            label: type.name,
            value: type.id,
          }))}
          rules={[{ required: true, message: 'Выберите типы уведомлений' }]}
        />
        <ProFormTextArea
          name="description"
          label="Описание"
          placeholder="Описание бота (необязательно)"
        />
      </ModalForm>

      {/* Модальное окно редактирования */}
      <ModalForm
        title="Редактировать бота"
        open={editModalVisible}
        onOpenChange={setEditModalVisible}
        onFinish={handleUpdate}
        initialValues={selectedBot || {}}
        modalProps={{
          destroyOnClose: true,
        }}
      >
        <ProFormText
          name="name"
          label="Название бота"
          placeholder="Введите название бота"
          rules={[{ required: true, message: 'Введите название бота' }]}
        />
        <ProFormText
          name="bot_token"
          label="Токен бота"
          placeholder="1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
          rules={[{ required: true, message: 'Введите токен бота' }]}
        />
        <ProFormText
          name="chat_id"
          label="Chat ID"
          placeholder="-1001234567890"
          rules={[{ required: true, message: 'Введите Chat ID' }]}
        />
        <ProFormSelect
          name="notification_types"
          label="Типы уведомлений"
          mode="multiple"
          options={NOTIFICATION_TYPES.map(type => ({
            label: type.name,
            value: type.id,
          }))}
          rules={[{ required: true, message: 'Выберите типы уведомлений' }]}
        />
        <ProFormTextArea
          name="description"
          label="Описание"
          placeholder="Описание бота (необязательно)"
        />
        <ProFormSwitch
          name="is_active"
          label="Активен"
        />
      </ModalForm>

      {/* Модальное окно тестирования */}
      <ModalForm
        title={`Тестирование бота: ${selectedBot?.name}`}
        open={testModalVisible}
        onOpenChange={setTestModalVisible}
        onFinish={sendTestMessage}
        modalProps={{
          destroyOnClose: true,
        }}
      >
        <Alert
          message="Тестовое сообщение"
          description="Отправьте тестовое сообщение для проверки работы бота"
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <ProFormTextArea
          name="message"
          label="Сообщение"
          placeholder="Введите тестовое сообщение"
          rules={[{ required: true, message: 'Введите сообщение' }]}
          fieldProps={{
            value: testMessage,
            onChange: (e) => setTestMessage(e.target.value),
          }}
        />
      </ModalForm>

      {/* Детальный просмотр */}
      <Drawer
        title={`Детали бота: ${selectedBot?.name}`}
        open={detailDrawerVisible}
        onClose={() => setDetailDrawerVisible(false)}
        width={600}
      >
        {selectedBot && (
          <Descriptions column={1} bordered>
            <Descriptions.Item label="ID">{selectedBot.id}</Descriptions.Item>
            <Descriptions.Item label="Название">{selectedBot.name}</Descriptions.Item>
            <Descriptions.Item label="Токен бота">
              <Text code style={{ fontSize: '12px' }}>
                {selectedBot.bot_token}
              </Text>
            </Descriptions.Item>
            <Descriptions.Item label="Chat ID">
              <Text code>{selectedBot.chat_id}</Text>
            </Descriptions.Item>
            <Descriptions.Item label="Статус">
              <Badge
                status={selectedBot.is_active ? 'success' : 'default'}
                text={selectedBot.is_active ? 'Активен' : 'Неактивен'}
              />
            </Descriptions.Item>
            <Descriptions.Item label="Типы уведомлений">
              <Space wrap>
                {selectedBot.notification_types.map(type => (
                  <Tag key={type} color={getNotificationTypeColor(type)}>
                    {getNotificationTypeName(type)}
                  </Tag>
                ))}
              </Space>
            </Descriptions.Item>
            {selectedBot.description && (
              <Descriptions.Item label="Описание">
                {selectedBot.description}
              </Descriptions.Item>
            )}
            <Descriptions.Item label="Создан">
              {dayjs(selectedBot.created_at).format('DD.MM.YYYY HH:mm')}
            </Descriptions.Item>
            <Descriptions.Item label="Обновлен">
              {dayjs(selectedBot.updated_at).format('DD.MM.YYYY HH:mm')}
            </Descriptions.Item>
            {selectedBot.last_test_message_at && (
              <Descriptions.Item label="Последний тест">
                <Space direction="vertical" size={0}>
                  <Text>{dayjs(selectedBot.last_test_message_at).format('DD.MM.YYYY HH:mm')}</Text>
                  {selectedBot.test_message_status && (
                    <Tag color={selectedBot.test_message_status === 'success' ? 'success' : 'error'}>
                      {selectedBot.test_message_status === 'success' ? 'Успешно' : 'Ошибка'}
                    </Tag>
                  )}
                </Space>
              </Descriptions.Item>
            )}
          </Descriptions>
        )}
      </Drawer>
    </PageContainer>
  );
};

export default TelegramBots;
