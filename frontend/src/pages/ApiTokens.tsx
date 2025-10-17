import React, { useMemo, useState, useEffect, useCallback } from 'react';
import { Tag, Space, Button, message, Modal, Form, Alert, Card, Descriptions, Input } from 'antd';
import {
  KeyOutlined,
  StopOutlined,
  ReloadOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  CopyOutlined,
  DatabaseOutlined,
} from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { apiTokensApi } from '../services/api';
import type { ApiToken, ApiTokenCreateResponse } from '../types';
import dayjs from 'dayjs';



const ApiTokens: React.FC = () => {
  const [availableScopes, setAvailableScopes] = useState<Array<{value: string, label: string}>>([]);
  const [availablePermissions, setAvailablePermissions] = useState<string[]>([]);
  const [permissionPresets, setPermissionPresets] = useState<Record<string, string[]>>({});

  const [newTokenResponse, setNewTokenResponse] = useState<ApiTokenCreateResponse | null>(null);
  const [tokenModalVisible, setTokenModalVisible] = useState(false);
  const [form] = Form.useForm();

  // Загрузка данных для форм
  const loadFormData = async () => {
    try {
      const [scopesData, permissionsData, presetsData] = await Promise.all([
        apiTokensApi.getScopes(),
        apiTokensApi.getPermissions(), 
        apiTokensApi.getPresets()
      ]);
      
      setAvailableScopes(scopesData.scopes);
      setAvailablePermissions(permissionsData.permissions);
      setPermissionPresets(presetsData);
    } catch (error: any) {
      message.error('Ошибка загрузки данных формы: ' + error.message);
    }
  };

  useEffect(() => {
    loadFormData();
  }, []);

  // Обработка выбора предустановленных разрешений
  const handlePresetChange = useCallback((preset: string) => {
    if (preset && permissionPresets[preset]) {
      form.setFieldsValue({
        permissions: permissionPresets[preset]
      });
    }
  }, [permissionPresets, form]);

  // Копирование в буфер обмена
  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text).then(() => {
      message.success('Скопировано в буфер обмена');
    });
  };

  // Конфигурация колонок
  const columns = useMemo(() => [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 200,
      render: (_: any, record: ApiToken): React.ReactElement => (
        <Space direction="vertical" size={0}>
          <span style={{ fontWeight: 500 }}>{record.name}</span>
          <span style={{ fontSize: 12, color: '#666', fontFamily: 'monospace' }}>
            {record.token_prefix}...
          </span>
        </Space>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'status',
      width: 100,
      render: (_: any, record: ApiToken): React.ReactElement => {
        const isExpired = record.expires_at && dayjs(record.expires_at).isBefore(dayjs());
        
        if (!record.is_active) {
          return <Tag color="red" icon={<StopOutlined />}>Отозван</Tag>;
        }
        if (isExpired) {
          return <Tag color="orange" icon={<ClockCircleOutlined />}>Истек</Tag>;
        }
        return <Tag color="green" icon={<CheckCircleOutlined />}>Активен</Tag>;
      },
    },
    {
      title: 'Разрешения',
      dataIndex: 'permissions',
      key: 'permissions',
      width: 200,
      render: (permissions: string[]): React.ReactElement => (
        <Space wrap size={4}>
          {permissions.slice(0, 3).map(perm => (
            <Tag key={perm} style={{ fontSize: 11 }}>
              {perm.split(':')[0]}
            </Tag>
          ))}
          {permissions.length > 3 && (
            <span style={{ color: '#666' }}>+{permissions.length - 3}</span>
          )}
        </Space>
      ),
    },
    {
      title: 'Использований',
      dataIndex: 'usage_count',
      key: 'usage_count',
      width: 100,
      align: 'center' as const,
      render: (count: number): React.ReactElement => <span style={{ fontWeight: 500 }}>{count}</span>,
    },
    {
      title: 'Последнее использование',
      dataIndex: 'last_used_at',
      key: 'last_used_at',
      width: 150,
      render: (date: string): React.ReactElement => (
        <span>{date ? dayjs(date).format('DD.MM.YYYY HH:mm') : 'Не использовался'}</span>
      ),
    },
    {
      title: 'Истекает',
      dataIndex: 'expires_at',
      key: 'expires_at', 
      width: 120,
      render: (date: string): React.ReactElement => (
        <span>{date ? dayjs(date).format('DD.MM.YYYY') : 'Бессрочно'}</span>
      ),
    },
    {
      title: 'Создатель',
      dataIndex: 'creator_username',
      key: 'creator_username',
      width: 120,
      render: (username: string): React.ReactElement => (
        <span>{username || 'Неизвестно'}</span>
      ),
    },
    {
      title: 'Лимит запросов',
      dataIndex: 'rate_limit',
      key: 'rate_limit',
      width: 120,
      align: 'center' as const,
      render: (limit: number): React.ReactElement => (
        <span>{limit || 'Не ограничено'}</span>
      ),
    },
  ], []);

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'name_contains',
      label: 'Поиск по названию',
      type: 'input' as const,
      placeholder: 'Введите название токена',
    },
    {
      key: 'is_active',
      label: 'Статус',
      type: 'select' as const,
      placeholder: 'Выберите статус',
      options: [
        { label: 'Активен', value: true },
        { label: 'Отозван', value: false },
      ],
    },
    {
      key: 'has_scope',
      label: 'Область доступа',
      type: 'select' as const,
      placeholder: 'Выберите область доступа',
      api: () => apiTokensApi.getScopes().then(data => 
        data.scopes.map((scope: any) => ({ label: scope.label, value: scope.value }))
      ),
    },
    {
      key: 'created_by',
      label: 'Создан пользователем',
      type: 'input' as const,
      placeholder: 'Введите ID пользователя',
    },
  ], []);

  // Конфигурация формы  
  const formConfig = useMemo(() => ({
    fields: [
      {
        name: 'name',
        label: 'Название токена',
        type: 'input' as const,
        rules: [
          { required: true, message: 'Введите название токена' },
          { min: 3, message: 'Минимум 3 символа' }
        ],
        placeholder: 'Например: API для мобильного приложения',
      },
      {
        name: 'description',
        label: 'Описание',
        type: 'textarea' as const,
        placeholder: 'Опишите для чего будет использоваться токен',
      },
      {
        name: 'preset',
        label: 'Предустановленные разрешения',
        type: 'select' as const,
        placeholder: 'Выберите готовый набор разрешений',
        options: Object.keys(permissionPresets).map(preset => ({
          label: preset.charAt(0).toUpperCase() + preset.slice(1).replace('_', ' '),
          value: preset
        })),
        onChange: (value: string) => handlePresetChange(value),
      },
      {
        name: 'permissions',
        label: 'Разрешения',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите хотя бы одно разрешение' }],
        placeholder: 'Выберите разрешения',
        mode: 'multiple' as const,
        showSearch: true,
        options: availablePermissions.map(permission => ({
          label: permission,
          value: permission
        })),
      },
      {
        name: 'scopes',
        label: 'Области доступа',
        type: 'select' as const,
        placeholder: 'Оставьте пустым для доступа ко всем областям',
        mode: 'multiple' as const,
        options: availableScopes.map(scope => ({
          label: scope.label,
          value: scope.value
        })),
      },
      {
        name: 'rate_limit',
        label: 'Лимит запросов в час',
        type: 'number' as const,
        placeholder: '1000',
        initialValue: 1000,
        min: 1,
        max: 10000,
      },
      {
        name: 'expires_at',
        label: 'Дата истечения',
        type: 'datetime' as const,
        placeholder: 'Оставьте пустым для бессрочного токена',
      },
      {
        name: 'ip_whitelist',
        label: 'Белый список IP',
        type: 'textarea' as const,
        placeholder: 'Введите IP адреса, по одному на строку\nОставьте пустым для разрешения всех IP',
      },
    ],
    initialValues: {
      rate_limit: 1000,
      permissions: [],
      scopes: [],
      ip_whitelist: ''
    },
  }), [availablePermissions, availableScopes, permissionPresets, handlePresetChange]);

  // Подготовка данных для редактирования
  const prepareDataForEdit = (record: ApiToken) => {
    return {
      ...record,
      expires_at: record.expires_at ? dayjs(record.expires_at) : undefined,
      ip_whitelist: record.ip_whitelist?.join('\n') || '',
    };
  };

  // Обработка отправки формы
  const handleSubmit = (values: any) => {
    const submitData = { ...values };
    
    // Убираем preset из данных
    delete submitData.preset;
    
    // Конвертируем дату
    if (values.expires_at) {
      submitData.expires_at = values.expires_at.toISOString();
    }
    
    // Конвертируем IP whitelist
    if (values.ip_whitelist && values.ip_whitelist.trim()) {
      submitData.ip_whitelist = values.ip_whitelist.split('\n').filter((ip: string) => ip.trim());
    } else {
      submitData.ip_whitelist = [];
    }
    
    return submitData;
  };

  // Кастомные действия для строк
  const rowActions = useMemo(() => [
    {
      key: 'regenerate',
      title: 'Перегенерировать',
      icon: <ReloadOutlined />,
      color: '#1890ff',
      onClick: async (record: ApiToken) => {
        try {
          const response = await apiTokensApi.regenerate(record.id);
          setNewTokenResponse(response);
          setTokenModalVisible(true);
          message.success('Токен успешно перегенерирован');
        } catch (error: any) {
          message.error('Ошибка перегенерации: ' + error.message);
        }
      },
    },
    {
      key: 'revoke',
      title: 'Отозвать',
      icon: <StopOutlined />,
      color: '#ff4d4f',
      danger: true,
      condition: (record: ApiToken) => record.is_active,
      confirm: {
        title: 'Отозвать токен?',
        description: 'Токен будет деактивирован и перестанет работать',
      },
      onClick: async (record: ApiToken) => {
        try {
          await apiTokensApi.revoke(record.id);
          message.success('Токен успешно отозван');
        } catch (error: any) {
          message.error('Ошибка отзыва: ' + error.message);
        }
      },
    },
  ], []);

  // Дашборд конфигурация
  const dashboardConfig = useMemo(() => ({
    fetchData: apiTokensApi.getStats,
    renderStats: (stats: any) => [
      {
        title: 'Всего токенов',
        value: stats.total_tokens || 0,
        prefix: <KeyOutlined />,
        color: '#1890ff',
      },
      {
        title: 'Активных',
        value: stats.active_tokens || 0,
        prefix: <CheckCircleOutlined />,
        color: '#52c41a',
      },
      {
        title: 'Истекших',
        value: stats.expired_tokens || 0,
        prefix: <ClockCircleOutlined />,
        color: '#ff4d4f',
      },
      {
        title: 'Всего использований',
        value: stats.total_usage || 0,
        prefix: <DatabaseOutlined />,
        color: '#722ed1',
      },
    ],
    title: 'Статистика токенов',
  }), []);

  // Обработка создания с новым токеном
  const handleCreate = async (data: any) => {
    const processedData = handleSubmit(data);
    const response = await apiTokensApi.create(processedData);
    setNewTokenResponse(response);
    setTokenModalVisible(true);
    return response.token_info;
  };

  // Обработка update endpoint
  const handleUpdate = async (id: number, data: any) => {
    const processedData = handleSubmit(data);
    return await apiTokensApi.update(id, processedData);
  };

  return (
    <>
      <GenericDataTable<ApiToken>
        title="API Токены"
        icon={<KeyOutlined />}
        columns={columns}
        filters={filters}
        formConfig={formConfig}
        endpoints={{
          list: apiTokensApi.list,
          create: handleCreate,
          update: handleUpdate,
          delete: apiTokensApi.delete,
        }}
        onEditDataTransform={prepareDataForEdit}
        rowActions={rowActions}
        dashboardConfig={dashboardConfig}
        searchable={true}
        exportable={true}
        addButtonText="Создать токен"
        pagination={{
          pageSize: 20,
          pageSizeOptions: ['20', '50', '100'],
        }}
        onActionComplete={() => {
          // Сбрасываем форму после действий
          form.resetFields();
        }}
      />

      {/* Модал с новым токеном */}
      <Modal
        title="Токен успешно создан!"
        open={tokenModalVisible}
        onCancel={() => {
          setTokenModalVisible(false);
          setNewTokenResponse(null);
        }}
        footer={[
          <Button 
            key="close" 
            onClick={() => {
              setTokenModalVisible(false);
              setNewTokenResponse(null);
            }}
          >
            Закрыть
          </Button>
        ]}
        width={800}
        destroyOnClose
      >
        {newTokenResponse && (
          <div>
            <Alert
              message="Токен успешно создан!"
              description="Сохраните токен в безопасном месте. Он больше не будет показан."
              type="success"
              showIcon
              style={{ marginBottom: 16 }}
            />
            <Card>
              <Descriptions title="Информация о токене" bordered column={1}>
                <Descriptions.Item label="Название">
                  {newTokenResponse.token_info.name}
                </Descriptions.Item>
                <Descriptions.Item label="Токен">
                  <Space direction="vertical" style={{ width: '100%' }}>
                    <Input.TextArea
                      value={newTokenResponse.token}
                      rows={3}
                      readOnly
                      style={{ fontFamily: 'monospace' }}
                    />
                    <Button
                      icon={<CopyOutlined />}
                      onClick={() => copyToClipboard(newTokenResponse.token)}
                      type="primary"
                    >
                      Копировать токен
                    </Button>
                  </Space>
                </Descriptions.Item>
              </Descriptions>
            </Card>
          </div>
        )}
      </Modal>
    </>
  );
};

export default ApiTokens;
