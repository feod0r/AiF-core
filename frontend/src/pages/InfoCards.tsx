import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Button, 
  Space, 
  Modal, 
  Form, 
  Input, 
  message,
  Typography,
  Tooltip,
  Divider,
  Switch,
  Popconfirm,
  Tag,
  List,
  Avatar,
  Drawer
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined, 
  EyeOutlined, 
  EyeInvisibleOutlined,
  LinkOutlined,
  SafetyOutlined,
  ReloadOutlined,
  InfoCircleOutlined,
  CalendarOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import { infoCardsApi } from '../services/api';
import { InfoCard, InfoCardCreate, InfoCardUpdate, InfoCardWithSecrets } from '../types';
import moment from 'moment';

const { TextArea } = Input;
const { Title, Text, Paragraph } = Typography;

interface SecretItem {
  key: string;
  value: string;
}

const InfoCardsPage: React.FC = () => {
  const [cards, setCards] = useState<InfoCard[]>([]);
  const [loading, setLoading] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [secretsModalVisible, setSecretsModalVisible] = useState(false);
  const [currentCard, setCurrentCard] = useState<InfoCard | null>(null);
  const [currentSecrets, setCurrentSecrets] = useState<Record<string, string>>({});
  const [showSecrets, setShowSecrets] = useState<Record<number, boolean>>({});
  const [secretsList, setSecretsList] = useState<SecretItem[]>([]);
  const [isMobile, setIsMobile] = useState(false);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();

  const fetchCards = async () => {
    setLoading(true);
    try {
      const data = await infoCardsApi.list();
      setCards(data);
    } catch (error) {
      message.error('Ошибка при загрузке карточек');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCards();
  }, []);

  // Определяем мобильное устройство
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const handleCreate = async (values: any) => {
    try {
      // Преобразуем список секретов в объект
      const secrets: Record<string, string> = {};
      if (secretsList.length > 0) {
        secretsList.forEach(item => {
          if (item.key && item.value) {
            secrets[item.key] = item.value;
          }
        });
      }

      const createData: InfoCardCreate = {
        title: values.title,
        description: values.description,
        external_link: values.external_link,
        secrets: Object.keys(secrets).length > 0 ? secrets : undefined
      };

      await infoCardsApi.create(createData);
      message.success('Карточка создана успешно');
      setCreateModalVisible(false);
      createForm.resetFields();
      setSecretsList([]);
      fetchCards();
    } catch (error) {
      message.error('Ошибка при создании карточки');
    }
  };

  const handleEdit = async (values: any) => {
    if (!currentCard) return;

    try {
      // Преобразуем список секретов в объект
      const secrets: Record<string, string> = {};
      if (secretsList.length > 0) {
        secretsList.forEach(item => {
          if (item.key && item.value) {
            secrets[item.key] = item.value;
          }
        });
      }

      const updateData: InfoCardUpdate = {
        title: values.title,
        description: values.description,
        external_link: values.external_link,
        secrets: Object.keys(secrets).length > 0 ? secrets : undefined
      };

      await infoCardsApi.update(currentCard.id, updateData);
      message.success('Карточка обновлена успешно');
      setEditModalVisible(false);
      editForm.resetFields();
      setCurrentCard(null);
      setSecretsList([]);
      fetchCards();
    } catch (error) {
      message.error('Ошибка при обновлении карточки');
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await infoCardsApi.delete(id);
      message.success('Карточка удалена успешно');
      fetchCards();
    } catch (error) {
      message.error('Ошибка при удалении карточки');
    }
  };

  const handleViewSecrets = async (card: InfoCard) => {
    try {
      const cardWithSecrets: InfoCardWithSecrets = await infoCardsApi.getSecrets(card.id);
      setCurrentCard(card);
      setCurrentSecrets(cardWithSecrets.secrets || {});
      setSecretsModalVisible(true);
    } catch (error) {
      message.error('Ошибка при загрузке секретов');
    }
  };

  const toggleSecretVisibility = (cardId: number) => {
    setShowSecrets(prev => ({
      ...prev,
      [cardId]: !prev[cardId]
    }));
  };

  const openCreateModal = () => {
    createForm.resetFields();
    setSecretsList([]);
    setCreateModalVisible(true);
  };

  const openEditModal = async (card: InfoCard) => {
    setCurrentCard(card);
    editForm.setFieldsValue({
      title: card.title,
      description: card.description,
      external_link: card.external_link
    });

    // Загружаем секреты для редактирования
    if (card.has_secrets) {
      try {
        const cardWithSecrets: InfoCardWithSecrets = await infoCardsApi.getSecrets(card.id);
        const secretsArray: SecretItem[] = Object.entries(cardWithSecrets.secrets || {}).map(([key, value]) => ({
          key,
          value
        }));
        setSecretsList(secretsArray);
      } catch (error) {
        console.error('Error loading secrets for edit:', error);
        setSecretsList([]);
      }
    } else {
      setSecretsList([]);
    }

    setEditModalVisible(true);
  };

  const addSecretField = () => {
    setSecretsList([...secretsList, { key: '', value: '' }]);
  };

  const removeSecretField = (index: number) => {
    const newList = [...secretsList];
    newList.splice(index, 1);
    setSecretsList(newList);
  };

  const updateSecretField = (index: number, field: 'key' | 'value', value: string) => {
    const newList = [...secretsList];
    newList[index] = { ...newList[index], [field]: value };
    setSecretsList(newList);
  };

  const renderSecretsForm = () => (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 16,
        flexDirection: isMobile ? 'column' : 'row',
        gap: isMobile ? 8 : 0
      }}>
        <Text strong>Секреты:</Text>
        <Button 
          type="dashed" 
          onClick={addSecretField} 
          icon={<PlusOutlined />} 
          size={isMobile ? 'middle' : 'small'}
          style={isMobile ? { width: '100%' } : {}}
        >
          Добавить секрет
        </Button>
      </div>
      {secretsList.map((secret, index) => (
        <div key={index} style={{ marginBottom: 16 }}>
          {isMobile ? (
            // Мобильная версия - вертикальное расположение
            <div>
              <div style={{ marginBottom: 8 }}>
                <Input
                  placeholder="Название (например, логин)"
                  value={secret.key}
                  onChange={(e) => updateSecretField(index, 'key', e.target.value)}
                />
              </div>
              <div style={{ display: 'flex', gap: 8 }}>
                <Input.Password
                  placeholder="Значение"
                  value={secret.value}
                  onChange={(e) => updateSecretField(index, 'value', e.target.value)}
                  style={{ flex: 1 }}
                />
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => removeSecretField(index)}
                  size="middle"
                />
              </div>
            </div>
          ) : (
            // Десктопная версия - горизонтальное расположение
            <Row gutter={8} style={{ marginBottom: 8 }}>
              <Col span={10}>
                <Input
                  placeholder="Название (например, логин)"
                  value={secret.key}
                  onChange={(e) => updateSecretField(index, 'key', e.target.value)}
                />
              </Col>
              <Col span={12}>
                <Input.Password
                  placeholder="Значение"
                  value={secret.value}
                  onChange={(e) => updateSecretField(index, 'value', e.target.value)}
                />
              </Col>
              <Col span={2}>
                <Button
                  type="text"
                  danger
                  icon={<DeleteOutlined />}
                  onClick={() => removeSecretField(index)}
                  size="small"
                />
              </Col>
            </Row>
          )}
        </div>
      ))}
    </div>
  );

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
          Информационные карточки
        </Title>
        <Space size={isMobile ? 'small' : 'middle'}>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={fetchCards} 
            loading={loading}
            size={isMobile ? 'small' : 'middle'}
          >
            {isMobile ? 'Обновить' : 'Обновить'}
          </Button>
          <Button 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={openCreateModal}
            size={isMobile ? 'small' : 'middle'}
          >
            {isMobile ? 'Добавить' : 'Добавить карточку'}
          </Button>
        </Space>
      </div>

      {isMobile ? (
        // Мобильная версия - список карточек
        <List
          dataSource={cards}
          loading={loading}
          renderItem={(card) => (
            <List.Item
              style={{ 
                padding: '16px 0',
                borderBottom: '1px solid #f0f0f0'
              }}
              actions={[
                <Button 
                  type="text" 
                  icon={<EditOutlined />} 
                  onClick={() => openEditModal(card)}
                  size="small"
                >
                  Изменить
                </Button>,
                card.has_secrets && (
                  <Button 
                    type="text" 
                    icon={<EyeOutlined />} 
                    onClick={() => handleViewSecrets(card)}
                    size="small"
                  >
                    Секреты
                  </Button>
                ),
                card.external_link && (
                  <Button 
                    type="text" 
                    icon={<LinkOutlined />} 
                    onClick={() => window.open(card.external_link, '_blank')}
                    size="small"
                  >
                    Ссылка
                  </Button>
                ),
                <Popconfirm
                  title="Удалить карточку?"
                  description="Это действие нельзя отменить"
                  onConfirm={() => handleDelete(card.id)}
                  okText="Да"
                  cancelText="Нет"
                >
                  <Button 
                    type="text" 
                    danger 
                    icon={<DeleteOutlined />}
                    size="small"
                  >
                    Удалить
                  </Button>
                </Popconfirm>
              ]}
            >
              <List.Item.Meta
                avatar={
                  <Avatar 
                    icon={<InfoCircleOutlined />} 
                    style={{ 
                      backgroundColor: card.has_secrets ? '#faad14' : '#1890ff',
                      cursor: 'pointer'
                    }}
                    onClick={() => {
                      setCurrentCard(card);
                      setDetailDrawerVisible(true);
                    }}
                  />
                }
                title={
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Text 
                      strong 
                      style={{ 
                        fontSize: 16,
                        cursor: 'pointer',
                        color: '#1890ff'
                      }}
                      onClick={() => {
                        setCurrentCard(card);
                        setDetailDrawerVisible(true);
                      }}
                    >
                      {card.title}
                    </Text>
                    <Space size="small">
                      {card.has_secrets && (
                        <Tag color="orange" icon={<SafetyOutlined />}>
                          Секреты
                        </Tag>
                      )}
                      {!card.is_active && (
                        <Tag color="red">
                          Неактивно
                        </Tag>
                      )}
                    </Space>
                  </div>
                }
                description={
                  <div>
                    <Paragraph 
                      ellipsis={{ rows: 2, expandable: true }}
                      style={{ marginBottom: 8, fontSize: 14 }}
                    >
                      {card.description || 'Нет описания'}
                    </Paragraph>
                    <div style={{ fontSize: 12, color: '#999' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4, marginBottom: 2 }}>
                        <CalendarOutlined />
                        Создано: {moment(card.created_at).format('DD.MM.YYYY')}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 4 }}>
                        <ClockCircleOutlined />
                        Обновлено: {moment(card.updated_at).format('DD.MM.YYYY HH:mm')}
                      </div>
                    </div>
                  </div>
                }
              />
            </List.Item>
          )}
        />
      ) : (
        // Десктопная версия - карточки в сетке
        <Row gutter={[16, 16]}>
          {cards.map((card) => (
            <Col key={card.id} xs={24} sm={12} lg={8} xl={6}>
              <Card
                title={
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <Text strong>{card.title}</Text>
                    <Space>
                      {card.has_secrets && (
                        <Tag color="orange" icon={<SafetyOutlined />}>
                          Секреты
                        </Tag>
                      )}
                      {!card.is_active && (
                        <Tag color="red">
                          Неактивно
                        </Tag>
                      )}
                    </Space>
                  </div>
                }
                actions={[
                  <Tooltip title="Редактировать">
                    <EditOutlined key="edit" onClick={() => openEditModal(card)} />
                  </Tooltip>,
                  card.has_secrets ? (
                    <Tooltip title="Показать секреты">
                      <EyeOutlined key="secrets" onClick={() => handleViewSecrets(card)} />
                    </Tooltip>
                  ) : (
                    <span key="no-secrets" />
                  ),
                  card.external_link ? (
                    <Tooltip title="Открыть ссылку">
                      <LinkOutlined key="link" onClick={() => window.open(card.external_link, '_blank')} />
                    </Tooltip>
                  ) : (
                    <span key="no-link" />
                  ),
                  <Popconfirm
                    title="Удалить карточку?"
                    description="Это действие нельзя отменить"
                    onConfirm={() => handleDelete(card.id)}
                    okText="Да"
                    cancelText="Нет"
                    key="delete"
                  >
                    <Tooltip title="Удалить">
                      <DeleteOutlined style={{ color: '#ff4d4f' }} />
                    </Tooltip>
                  </Popconfirm>
                ]}
                style={{ height: '100%' }}
              >
                <div style={{ minHeight: 120 }}>
                  <Paragraph ellipsis={{ rows: 3, expandable: true }}>
                    {card.description || 'Нет описания'}
                  </Paragraph>
                  <div style={{ marginTop: 16, fontSize: '12px', color: '#999' }}>
                    <div>Создано: {moment(card.created_at).format('DD.MM.YYYY HH:mm')}</div>
                    <div>Обновлено: {moment(card.updated_at).format('DD.MM.YYYY HH:mm')}</div>
                  </div>
                </div>
              </Card>
            </Col>
          ))}
        </Row>
      )}

      {/* Модал создания */}
      <Modal
        title="Создать карточку"
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        onOk={() => createForm.submit()}
        width={isMobile ? '100%' : 600}
        style={isMobile ? { margin: 16, maxWidth: 'calc(100vw - 32px)' } : {}}
      >
        <Form form={createForm} onFinish={handleCreate} layout="vertical">
          <Form.Item
            name="title"
            label="Заголовок"
            rules={[{ required: true, message: 'Введите заголовок' }]}
          >
            <Input placeholder="Название карточки" />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <TextArea rows={4} placeholder="Полезная информация или инструкции" />
          </Form.Item>

          <Form.Item name="external_link" label="Внешняя ссылка">
            <Input placeholder="https://example.com" />
          </Form.Item>

          <Divider />
          {renderSecretsForm()}
        </Form>
      </Modal>

      {/* Модал редактирования */}
      <Modal
        title="Редактировать карточку"
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        onOk={() => editForm.submit()}
        width={isMobile ? '100%' : 600}
        style={isMobile ? { margin: 16, maxWidth: 'calc(100vw - 32px)' } : {}}
      >
        <Form form={editForm} onFinish={handleEdit} layout="vertical">
          <Form.Item
            name="title"
            label="Заголовок"
            rules={[{ required: true, message: 'Введите заголовок' }]}
          >
            <Input placeholder="Название карточки" />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <TextArea rows={4} placeholder="Полезная информация или инструкции" />
          </Form.Item>

          <Form.Item name="external_link" label="Внешняя ссылка">
            <Input placeholder="https://example.com" />
          </Form.Item>

          <Divider />
          {renderSecretsForm()}
        </Form>
      </Modal>

      {/* Модал просмотра секретов */}
      <Modal
        title={`Секреты: ${currentCard?.title}`}
        open={secretsModalVisible}
        onCancel={() => setSecretsModalVisible(false)}
        footer={[
          <Button key="close" onClick={() => setSecretsModalVisible(false)}>
            Закрыть
          </Button>
        ]}
        width={isMobile ? '100%' : 600}
        style={isMobile ? { margin: 16, maxWidth: 'calc(100vw - 32px)' } : {}}
      >
        {Object.entries(currentSecrets).length > 0 ? (
          <div>
            {Object.entries(currentSecrets).map(([key, value]) => (
              <div key={key} style={{ marginBottom: 16 }}>
                <Text strong style={{ display: 'block', marginBottom: 8 }}>{key}:</Text>
                {isMobile ? (
                  // Мобильная версия - вертикальное расположение
                  <div>
                    <div style={{ marginBottom: 8 }}>
                      <Input
                        value={showSecrets[currentCard?.id || 0] ? value : '••••••••'}
                        readOnly
                        style={{ width: '100%' }}
                      />
                    </div>
                    <div style={{ display: 'flex', gap: 8 }}>
                      <Button
                        type="text"
                        icon={showSecrets[currentCard?.id || 0] ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                        onClick={() => toggleSecretVisibility(currentCard?.id || 0)}
                        style={{ flex: 1 }}
                      >
                        {showSecrets[currentCard?.id || 0] ? 'Скрыть' : 'Показать'}
                      </Button>
                      <Button
                        type="text"
                        onClick={() => {
                          navigator.clipboard.writeText(value);
                          message.success('Скопировано в буфер обмена');
                        }}
                        style={{ flex: 1 }}
                      >
                        Копировать
                      </Button>
                    </div>
                  </div>
                ) : (
                  // Десктопная версия - горизонтальное расположение
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                    <Input
                      value={showSecrets[currentCard?.id || 0] ? value : '••••••••'}
                      readOnly
                      style={{ flex: 1 }}
                    />
                    <Button
                      type="text"
                      icon={showSecrets[currentCard?.id || 0] ? <EyeInvisibleOutlined /> : <EyeOutlined />}
                      onClick={() => toggleSecretVisibility(currentCard?.id || 0)}
                    />
                    <Button
                      type="text"
                      onClick={() => {
                        navigator.clipboard.writeText(value);
                        message.success('Скопировано в буфер обмена');
                      }}
                    >
                      Копировать
                    </Button>
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <Text type="secondary">Нет сохраненных секретов</Text>
        )}
      </Modal>

      {/* Drawer для детального просмотра на мобильных */}
      <Drawer
        title={
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 8,
            minHeight: 'auto',
            padding: '8px 0'
          }}>
            <Avatar 
              icon={<InfoCircleOutlined />} 
              size="small"
              style={{ 
                backgroundColor: currentCard?.has_secrets ? '#faad14' : '#1890ff',
                flexShrink: 0
              }}
            />
            <div style={{ 
              flex: 1,
              minWidth: 0,
              overflow: 'hidden'
            }}>
              <div style={{ 
                fontSize: 16, 
                fontWeight: 'bold',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {currentCard?.title}
              </div>
              <div style={{ 
                fontSize: 12, 
                color: '#999',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                Информационная карточка
              </div>
            </div>
          </div>
        }
        placement="right"
        onClose={() => setDetailDrawerVisible(false)}
        open={detailDrawerVisible}
        width="100%"
        styles={{
          header: { 
            padding: '12px 16px',
            minHeight: 'auto',
            borderBottom: '1px solid #f0f0f0'
          },
          body: { 
            padding: '16px',
            paddingBottom: '80px' // Место для фиксированных кнопок
          }
        }}
      >
        {currentCard && (
          <div>
            {/* Статус */}
            <div style={{ marginBottom: 16 }}>
              <Space size="small">
                {currentCard.has_secrets && (
                  <Tag color="orange" icon={<SafetyOutlined />}>
                    Секреты
                  </Tag>
                )}
                {!currentCard.is_active && (
                  <Tag color="red">
                    Неактивно
                  </Tag>
                )}
              </Space>
            </div>

            {/* Описание */}
            <div style={{ marginBottom: 24 }}>
              <Text strong style={{ fontSize: 14, marginBottom: 8, display: 'block' }}>
                Описание:
              </Text>
              <Paragraph style={{ fontSize: 14, lineHeight: 1.6 }}>
                {currentCard.description || 'Нет описания'}
              </Paragraph>
            </div>

            {/* Внешняя ссылка */}
            {currentCard.external_link && (
              <div style={{ marginBottom: 24 }}>
                <Text strong style={{ fontSize: 14, marginBottom: 8, display: 'block' }}>
                  Внешняя ссылка:
                </Text>
                <Button 
                  type="link" 
                  icon={<LinkOutlined />}
                  onClick={() => window.open(currentCard.external_link, '_blank')}
                  style={{ padding: 0, height: 'auto' }}
                >
                  {currentCard.external_link}
                </Button>
              </div>
            )}

            {/* Даты */}
            <div style={{ marginBottom: 24 }}>
              <Text strong style={{ fontSize: 14, marginBottom: 8, display: 'block' }}>
                Информация:
              </Text>
              <div style={{ fontSize: 14, color: '#666' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                  <CalendarOutlined />
                  Создано: {moment(currentCard.created_at).format('DD.MM.YYYY HH:mm')}
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  <ClockCircleOutlined />
                  Обновлено: {moment(currentCard.updated_at).format('DD.MM.YYYY HH:mm')}
                </div>
              </div>
            </div>

            {/* Действия */}
            <div style={{ 
              position: 'fixed', 
              bottom: 0, 
              left: 0, 
              right: 0, 
              background: 'white', 
              padding: '12px 16px',
              borderTop: '1px solid #f0f0f0',
              display: 'flex',
              gap: 8,
              zIndex: 1000,
              boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.1)'
            }}>
              <Button 
                type="primary" 
                icon={<EditOutlined />} 
                onClick={() => {
                  setDetailDrawerVisible(false);
                  openEditModal(currentCard);
                }}
                style={{ flex: 1 }}
              >
                Изменить
              </Button>
              {currentCard.has_secrets && (
                <Button 
                  icon={<EyeOutlined />} 
                  onClick={() => {
                    setDetailDrawerVisible(false);
                    handleViewSecrets(currentCard);
                  }}
                  style={{ flex: 1 }}
                >
                  Секреты
                </Button>
              )}
              {currentCard.external_link && (
                <Button 
                  icon={<LinkOutlined />} 
                  onClick={() => window.open(currentCard.external_link, '_blank')}
                  style={{ flex: 1 }}
                >
                  Открыть
                </Button>
              )}
              <Popconfirm
                title="Удалить карточку?"
                description="Это действие нельзя отменить"
                onConfirm={() => {
                  setDetailDrawerVisible(false);
                  handleDelete(currentCard.id);
                }}
                okText="Да"
                cancelText="Нет"
              >
                <Button 
                  danger 
                  icon={<DeleteOutlined />}
                  style={{ flex: 1 }}
                >
                  Удалить
                </Button>
              </Popconfirm>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default InfoCardsPage;
