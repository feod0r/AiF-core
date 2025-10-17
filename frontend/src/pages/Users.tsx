import React, { useState } from 'react';
import { Tag, Badge, Space, Modal, Form, Input, Button, message } from 'antd';
import { UserOutlined, LockOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import api from '../services/api';

interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: {
    id: number;
    name: string;
    description?: string;
  };
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
  owner_ids?: number[];
}

const Users: React.FC = () => {
  const [passwordModalVisible, setPasswordModalVisible] = useState(false);
  const [changingPasswordUserId, setChangingPasswordUserId] = useState<number | null>(null);
  const [passwordForm] = Form.useForm();

  // Открытие модального окна для смены пароля
  const showPasswordModal = (userId: number) => {
    setChangingPasswordUserId(userId);
    setPasswordModalVisible(true);
    passwordForm.resetFields();
  };

  // Смена пароля
  const handlePasswordChange = async (values: any) => {
    if (!changingPasswordUserId) return;
    
    try {
      await api.patch(`/users/${changingPasswordUserId}/password`, {
        new_password: values.new_password
      });
      message.success('Пароль изменен успешно');
      setPasswordModalVisible(false);
      passwordForm.resetFields();
    } catch (error: any) {
      message.error('Ошибка: ' + (error.response?.data?.error || error.message));
    }
  };

  // Загрузка владельцев для селекта
  const loadOwners = async () => {
    try {
      const response = await api.get('/owners');
      let owners = [];
      
      if (Array.isArray(response.data)) {
        owners = response.data;
      } else if (response.data && Array.isArray(response.data.data)) {
        owners = response.data.data;
      } else if (response.data && Array.isArray(response.data.owners)) {
        owners = response.data.owners;
      }
      
      return owners.map((owner: any) => ({
        label: owner.name,
        value: owner.id
      }));
    } catch (error: any) {
      console.error('Error loading owners:', error);
      return [];
    }
  };

  return (
    <>
      <GenericDataTable<User>
        title="Пользователи системы"
        icon={<UserOutlined />}
        endpoints={{
          list: async (params) => {
            const response = await api.get('/users', { params });
            return response.data;
          },
          create: async (data) => {
            // Преобразуем role в role_id для бэкенда
            const userData = {
              ...data,
              role_id: data.role,
              role: undefined
            };
            const response = await api.post('/users', userData);
            return response.data;
          },
          update: async (id, data) => {
            // Преобразуем role в role_id для бэкенда
            const userData = {
              ...data,
              role_id: data.role,
              role: undefined
            };
            const response = await api.put(`/users/${id}`, userData);
            return response.data;
          },
          delete: async (id) => {
            await api.delete(`/users/${id}`);
          }
        }}
        columns={[
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 60,
    },
    {
      title: 'Имя пользователя',
      dataIndex: 'username',
      key: 'username',
      render: (text: string, record: User) => (
        <Space>
          <UserOutlined />
          <span>{text}</span>
                {record.role?.name === 'admin' && <Tag color="blue">Админ</Tag>}
        </Space>
      ),
    },
    {
      title: 'Полное имя',
      dataIndex: 'full_name',
      key: 'full_name',
            render: (text: string) => text || '-',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      render: (text: string) => text || '-',
    },
    {
      title: 'Роль',
            dataIndex: ['role', 'name'],
      key: 'role',
            render: (roleName: string) => (
              <Tag color={roleName === 'admin' ? 'blue' : roleName === 'readonly' ? 'orange' : 'green'}>
                {roleName === 'admin' ? 'Администратор' : roleName === 'readonly' ? 'Только чтение' : 'Пользователь'}
        </Tag>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (active: boolean) => (
        <Badge 
          status={active ? 'success' : 'error'} 
          text={active ? 'Активен' : 'Неактивен'} 
        />
      ),
    },
    {
      title: 'Последний вход',
      dataIndex: 'last_login',
      key: 'last_login',
      render: (date: string) => date ? new Date(date).toLocaleString('ru-RU') : 'Никогда',
    },
        ]}
        formConfig={{
          fields: [
            {
              name: 'username',
              label: 'Имя пользователя',
              type: 'input',
              placeholder: 'Введите имя пользователя',
              rules: [
                  { required: true, message: 'Введите имя пользователя' },
                  { min: 3, message: 'Минимум 3 символа' }
              ],
            },
            {
              name: 'email',
              label: 'Email',
              type: 'input',
              placeholder: 'Введите email',
              rules: [
                { required: true, message: 'Введите email' },
                  { type: 'email', message: 'Введите корректный email' }
              ],
            },
            {
              name: 'full_name',
              label: 'Полное имя',
              type: 'input',
              placeholder: 'Введите полное имя',
              rules: [
                  { required: true, message: 'Введите полное имя' }
              ],
            },
            {
              name: 'role',
              label: 'Роль',
              type: 'select',
              placeholder: 'Выберите роль',
              options: [
                { label: 'Пользователь', value: 2 },
                { label: 'Администратор', value: 1 },
                { label: 'Только чтение', value: 3 },
              ],
              rules: [
                  { required: true, message: 'Выберите роль' }
              ],
            },
            {
              name: 'password',
              label: 'Пароль',
              type: 'password',
              placeholder: 'Введите пароль',
              rules: [
                { required: true, message: 'Введите пароль' },
                { min: 6, message: 'Минимум 6 символов' }
              ],
              visible: (values) => !values.id, // Показываем только при создании
            },
            {
              name: 'owner_ids',
              label: 'Доступ к владельцам',
              type: 'select',
              placeholder: 'Выберите владельцев',
              mode: 'multiple',
              api: loadOwners,
            },
            {
              name: 'is_active',
              label: 'Активен',
              type: 'switch',
              initialValue: true,
            },
          ],
          modalWidth: 600,
        }}
        rowActions={[
          {
            key: 'change-password',
            title: 'Сменить пароль',
            icon: <LockOutlined />,
            onClick: (record) => {
              showPasswordModal(record.id);
            },
          },
        ]}
        onEditDataTransform={(record) => ({
          ...record,
          role: record.role?.id, // Преобразуем объект role в role_id
        })}
        dashboardConfig={{
          fetchData: async (params) => {
            const response = await api.get('/users', { params });
            return response.data;
          },
          renderStats: (data: User[]) => [
            {
              title: 'Всего пользователей',
              value: data.length,
              prefix: <UserOutlined />,
            },
            {
              title: 'Активных',
              value: data.filter((u: User) => u.is_active).length,
              color: '#3f8600',
            },
            {
              title: 'Администраторов',
              value: data.filter((u: User) => u.role?.name === 'admin').length,
              color: '#1890ff',
            },
            {
              title: 'Обычных пользователей',
              value: data.filter((u: User) => u.role?.name === 'user').length,
              color: '#52c41a',
            },
          ],
        }}
        addButtonText="Добавить пользователя"
      />

      {/* Модальное окно смены пароля */}
      <Modal
        title="Сменить пароль"
        open={passwordModalVisible}
        onCancel={() => {
          setPasswordModalVisible(false);
          passwordForm.resetFields();
        }}
        footer={null}
        width={400}
      >
        <Form
          form={passwordForm}
          layout="vertical"
          onFinish={handlePasswordChange}
        >
          <Form.Item
            name="new_password"
            label="Новый пароль"
            rules={[
              { required: true, message: 'Введите новый пароль' },
              { min: 6, message: 'Минимум 6 символов' }
            ]}
          >
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>

          <Form.Item
            name="confirm_password"
            label="Подтвердите пароль"
            dependencies={['new_password']}
            rules={[
              { required: true, message: 'Подтвердите пароль' },
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
            <Input.Password prefix={<LockOutlined />} />
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit">
                Сменить пароль
              </Button>
              <Button onClick={() => {
                setPasswordModalVisible(false);
                passwordForm.resetFields();
              }}>
                Отмена
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default Users; 