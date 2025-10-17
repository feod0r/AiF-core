import React, { useState, useEffect } from 'react';
import {
  Card,
  Form,
  Input,
  Button,
  Row,
  Col,
  Typography,
  Divider,
  Space,
  Avatar,
  Descriptions,
  Tag,
  Modal,
  Alert,
  Statistic,
  Badge
} from 'antd';
import {
  UserOutlined,
  EditOutlined,
  SaveOutlined,
  LockOutlined,
  CalendarOutlined,
  MailOutlined,
  KeyOutlined,
  EyeOutlined,
  EyeInvisibleOutlined
} from '@ant-design/icons';
import { useAuth } from '../contexts/AuthContext';
import { authApi, showSuccessNotification } from '../services/api';
import { User, PasswordChange } from '../types';
import dayjs from 'dayjs';

const { Title, Text } = Typography;
const { Password } = Input;

const Profile: React.FC = () => {
  const { user, updateUser } = useAuth();
  const [loading, setLoading] = useState(false);
  const [passwordLoading, setPasswordLoading] = useState(false);
  const [editing, setEditing] = useState(false);
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [form] = Form.useForm();
  const [passwordForm] = Form.useForm();

  const [currentUser, setCurrentUser] = useState<User | null>(null);

  useEffect(() => {
    if (user) {
      setCurrentUser(user);
      form.setFieldsValue({
        username: user.username,
        email: user.email,
        full_name: user.full_name || '',
      });
    }
  }, [user, form]);

  const handleEdit = () => {
    setEditing(true);
  };

  const handleCancel = () => {
    setEditing(false);
    form.setFieldsValue({
      username: currentUser?.username,
      email: currentUser?.email,
      full_name: currentUser?.full_name || '',
    });
  };

  const handleSave = async (values: any) => {
    try {
      setLoading(true);
      
      const updatedUser = await authApi.updateProfile(values);
      
      setCurrentUser(updatedUser);
      updateUser(updatedUser);
      
      showSuccessNotification('Профиль обновлен', 'Данные профиля успешно сохранены');
      setEditing(false);
    } catch (error: any) {
      // Ошибка будет показана автоматически через интерцептор API
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordChange = async (values: PasswordChange) => {
    try {
      setPasswordLoading(true);
      
      await authApi.changePassword(values);
      
      showSuccessNotification('Пароль изменен', 'Пароль успешно обновлен');
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    } catch (error: any) {
      // Ошибка будет показана автоматически через интерцептор API
    } finally {
      setPasswordLoading(false);
    }
  };

  const getRoleColor = (role: string) => {
    switch (role) {
      case 'admin':
        return 'red';
      case 'manager':
        return 'blue';
      case 'user':
        return 'green';
      default:
        return 'default';
    }
  };

  const getRoleName = (role: string) => {
    switch (role) {
      case 'admin':
        return 'Администратор';
      case 'manager':
        return 'Менеджер';
      case 'user':
        return 'Пользователь';
      default:
        return role;
    }
  };

  if (!currentUser) {
    return (
      <div style={{ padding: 24, textAlign: 'center' }}>
        <Card>
          <Text>Загрузка профиля...</Text>
        </Card>
      </div>
    );
  }

  return (
    <div style={{ padding: 24 }}>
      <Title level={2}>
        <UserOutlined /> Профиль пользователя
      </Title>

      <Row gutter={[24, 24]}>
        {/* Основная информация */}
        <Col xs={24} lg={16}>
          <Card title="Основная информация" extra={
            <Space>
              {!editing ? (
                <Button 
                  type="primary" 
                  icon={<EditOutlined />} 
                  onClick={handleEdit}
                >
                  Редактировать
                </Button>
              ) : (
                <Space>
                  <Button onClick={handleCancel}>
                    Отмена
                  </Button>
                  <Button 
                    type="primary" 
                    icon={<SaveOutlined />} 
                    loading={loading}
                    onClick={() => form.submit()}
                  >
                    Сохранить
                  </Button>
                </Space>
              )}
            </Space>
          }>
            <Form
              form={form}
              layout="vertical"
              onFinish={handleSave}
              disabled={!editing}
            >
              <Row gutter={16}>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="username"
                    label="Имя пользователя"
                    rules={[
                      { required: true, message: 'Введите имя пользователя' },
                      { min: 3, message: 'Имя пользователя должно содержать минимум 3 символа' }
                    ]}
                  >
                    <Input prefix={<UserOutlined />} />
                  </Form.Item>
                </Col>
                <Col xs={24} md={12}>
                  <Form.Item
                    name="email"
                    label="Email"
                    rules={[
                      { required: true, message: 'Введите email' },
                      { type: 'email', message: 'Введите корректный email' }
                    ]}
                  >
                    <Input prefix={<MailOutlined />} />
                  </Form.Item>
                </Col>
              </Row>
              
              <Form.Item
                name="full_name"
                label="Полное имя"
                rules={[
                  { required: true, message: 'Введите полное имя' }
                ]}
              >
                <Input prefix={<UserOutlined />} />
              </Form.Item>
            </Form>

            {!editing && (
              <>
                <Divider />
                <Descriptions column={1} size="small">
                  <Descriptions.Item label="Роль">
                    <Tag color={getRoleColor(currentUser.role.name)}>
                      {getRoleName(currentUser.role.name)}
                    </Tag>
                  </Descriptions.Item>
                  <Descriptions.Item label="Статус">
                    <Badge 
                      status={currentUser.is_active ? 'success' : 'error'} 
                      text={currentUser.is_active ? 'Активен' : 'Неактивен'} 
                    />
                  </Descriptions.Item>
                  <Descriptions.Item label="Дата регистрации">
                    <Space>
                      <CalendarOutlined />
                      {dayjs(currentUser.created_at).format('DD.MM.YYYY HH:mm')}
                    </Space>
                  </Descriptions.Item>
                  {currentUser.last_login && (
                    <Descriptions.Item label="Последний вход">
                      <Space>
                        <CalendarOutlined />
                        {dayjs(currentUser.last_login).format('DD.MM.YYYY HH:mm')}
                      </Space>
                    </Descriptions.Item>
                  )}
                </Descriptions>
              </>
            )}
          </Card>
        </Col>

        {/* Боковая панель */}
        <Col xs={24} lg={8}>
          {/* Аватар и основная информация */}
          <Card>
            <div style={{ textAlign: 'center', marginBottom: 24 }}>
              <Avatar 
                size={80} 
                icon={<UserOutlined />} 
                style={{ marginBottom: 16 }}
              />
              <Title level={4} style={{ margin: 0 }}>
                {currentUser.full_name || currentUser.username}
              </Title>
              <Text type="secondary">
                {currentUser.email}
              </Text>
            </div>

            <Space direction="vertical" style={{ width: '100%' }}>
              <Button 
                type="default" 
                icon={<LockOutlined />} 
                block
                onClick={() => setPasswordModalVisible(true)}
              >
                Сменить пароль
              </Button>
            </Space>
          </Card>

          {/* Статистика активности */}
          <Card title="Активность" style={{ marginTop: 16 }}>
            <Row gutter={16}>
              <Col span={12}>
                <Statistic
                  title="Дней в системе"
                  value={dayjs().diff(dayjs(currentUser.created_at), 'day')}
                  suffix="дн."
                />
              </Col>
              <Col span={12}>
                <Statistic
                  title="Последний вход"
                  value={currentUser.last_login ? dayjs().diff(dayjs(currentUser.last_login), 'day') : 0}
                  suffix="дн. назад"
                />
              </Col>
            </Row>
          </Card>
        </Col>
      </Row>

      {/* Модальное окно смены пароля */}
      <Modal
        title="Смена пароля"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={null}
        width={400}
      >
        <Alert
          message="Требования к паролю"
          description="Пароль должен содержать минимум 8 символов, включая буквы и цифры"
          type="info"
          style={{ marginBottom: 16 }}
        />
        
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordChange}
        >
          <Form.Item
            name="current_password"
            label="Текущий пароль"
            rules={[
              { required: true, message: 'Введите текущий пароль' }
            ]}
          >
            <Password 
              prefix={<LockOutlined />}
              iconRender={(visible) => (visible ? <EyeOutlined /> : <EyeInvisibleOutlined />)}
            />
          </Form.Item>

          <Form.Item
            name="new_password"
            label="Новый пароль"
            rules={[
              { required: true, message: 'Введите новый пароль' },
              { min: 8, message: 'Пароль должен содержать минимум 8 символов' },
              {
                pattern: /^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d@$!%*#?&]{8,}$/,
                message: 'Пароль должен содержать буквы и цифры'
              }
            ]}
          >
            <Password 
              prefix={<KeyOutlined />}
              iconRender={(visible) => (visible ? <EyeOutlined /> : <EyeInvisibleOutlined />)}
            />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            label="Подтвердите новый пароль"
            dependencies={['new_password']}
            rules={[
              { required: true, message: 'Подтвердите новый пароль' },
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (!value || getFieldValue('new_password') === value) {
                    return Promise.resolve();
                  }
                  return Promise.reject(new Error('Пароли не совпадают'));
                },
              }),
            ]}
          >
            <Password 
              prefix={<KeyOutlined />}
              iconRender={(visible) => (visible ? <EyeOutlined /> : <EyeInvisibleOutlined />)}
            />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button 
                onClick={() => {
                  setPasswordModalVisible(false);
                  passwordForm.resetFields();
                }}
              >
                Отмена
              </Button>
              <Button 
                type="primary" 
                htmlType="submit"
                loading={passwordLoading}
              >
                Сменить пароль
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default Profile;
