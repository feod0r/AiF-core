import React, { useMemo } from 'react';
import { Tag } from 'antd';
import { FileTextOutlined, DatabaseOutlined, UserOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { auditApi } from '../services/api';

interface AuditLog {
  id: number;
  user: {
    id: number;
    username: string;
    full_name: string;
    role: {
      name: string;
    };
  } | null;
  action: string;
  table_name?: string;
  record_id?: number;
  old_values?: any;
  new_values?: any;
  ip_address?: string;
  user_agent?: string;
  created_at: string;
}



const Audit: React.FC = () => {
  // Конфигурация колонок
  const columns = useMemo(() => [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Пользователь',
      dataIndex: ['user', 'full_name'],
      key: 'user',
      render: (_: any, record: AuditLog): React.ReactElement => {
        if (record.user) {
          return (
            <div>
              <div style={{ fontWeight: 'bold' }}>{record.user.full_name}</div>
              <div style={{ fontSize: '12px', color: '#666' }}>
                @{record.user.username} • {record.user.role?.name}
              </div>
            </div>
          );
        }
        return <span style={{ color: '#999' }}>Система</span>;
      },
    },
    {
      title: 'Действие',
      dataIndex: 'action',
      key: 'action',
      render: (action: string): React.ReactElement => {
        const actionColors: { [key: string]: string } = {
          'CREATE': 'green',
          'UPDATE': 'blue',
          'DELETE': 'red',
          'LOGIN': 'purple',
          'LOGOUT': 'orange',
        };
        return (
          <Tag color={actionColors[action] || 'default'}>
            {action}
          </Tag>
        );
      },
    },
    {
      title: 'Таблица',
      dataIndex: 'table_name',
      key: 'table_name',
      render: (tableName: string): React.ReactElement => {
        if (!tableName) return <span style={{ color: '#999' }}>-</span>;
        return (
          <Tag color="cyan">
            <DatabaseOutlined /> {tableName}
          </Tag>
        );
      },
    },
    {
      title: 'ID записи',
      dataIndex: 'record_id',
      key: 'record_id',
      render: (recordId: number): React.ReactElement => {
        if (!recordId) return <span style={{ color: '#999' }}>-</span>;
        return <span style={{ fontFamily: 'monospace' }}>#{recordId}</span>;
      },
    },
    {
      title: 'IP адрес',
      dataIndex: 'ip_address',
      key: 'ip_address',
      render: (ipAddress: string): React.ReactElement => {
        if (!ipAddress) return <span style={{ color: '#999' }}>-</span>;
        return <span style={{ fontFamily: 'monospace', fontSize: '12px' }}>{ipAddress}</span>;
      },
    },
    {
      title: 'Дата',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string): React.ReactElement => {
        return (
          <div>
            <div>{new Date(date).toLocaleDateString('ru-RU')}</div>
            <div style={{ fontSize: '12px', color: '#666' }}>
              {new Date(date).toLocaleTimeString('ru-RU')}
            </div>
          </div>
        );
      },
    },
    {
      title: 'Старые значения',
      dataIndex: 'old_values',
      key: 'old_values',
      width: 0, // Полностью скрываем колонку в таблице
      className: 'hidden-column', // Дополнительный класс для скрытия
      render: (oldValues: any): React.ReactElement => {
        if (!oldValues || Object.keys(oldValues).length === 0) {
          return <span style={{ color: '#999' }}>-</span>;
        }
        return (
          <pre style={{ 
            fontSize: '12px', 
            margin: 0, 
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxWidth: '300px'
          }}>
            {JSON.stringify(oldValues, null, 2)}
          </pre>
        );
      },
    },
    {
      title: 'Новые значения',
      dataIndex: 'new_values',
      key: 'new_values',
      width: 0, // Полностью скрываем колонку в таблице
      className: 'hidden-column', // Дополнительный класс для скрытия
      render: (newValues: any): React.ReactElement => {
        if (!newValues || Object.keys(newValues).length === 0) {
          return <span style={{ color: '#999' }}>-</span>;
        }
        return (
          <pre style={{ 
            fontSize: '12px', 
            margin: 0, 
            whiteSpace: 'pre-wrap',
            wordBreak: 'break-word',
            maxWidth: '300px'
          }}>
            {JSON.stringify(newValues, null, 2)}
          </pre>
        );
      },
    },
    {
      title: 'User Agent',
      dataIndex: 'user_agent',
      key: 'user_agent',
      width: 0, // Полностью скрываем колонку в таблице
      className: 'hidden-column', // Дополнительный класс для скрытия
      render: (userAgent: string): React.ReactElement => {
        if (!userAgent) return <span style={{ color: '#999' }}>-</span>;
        return (
          <div style={{ 
            fontSize: '12px', 
            fontFamily: 'monospace',
            wordBreak: 'break-word',
            maxWidth: '300px'
          }}>
            {userAgent}
          </div>
        );
      },
    },
  ], []);

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'search',
      label: 'Поиск',
      type: 'input' as const,
      placeholder: 'Поиск по действию или таблице',
    },
    {
      key: 'user_id',
      label: 'Пользователь',
      type: 'select' as const,
      placeholder: 'Выберите пользователя',
             api: async (): Promise<Array<{label: string, value: any}>> => {
         // Получаем пользователей из статистики аудита
         const stats = await auditApi.getStats();
         const users = stats.user_stats || [];
         return users.map((item: any) => ({
           label: item.user?.full_name || item.user?.username || 'Система',
           value: item.user?.id || null,
         }));
       },
    },
    {
      key: 'action',
      label: 'Действие',
      type: 'select' as const,
      placeholder: 'Выберите действие',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const actions = await auditApi.getActions();
        return actions.map((action: string) => ({
          label: action,
          value: action,
        }));
      },
    },
    {
      key: 'table_name',
      label: 'Таблица',
      type: 'select' as const,
      placeholder: 'Выберите таблицу',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const tables = await auditApi.getTables();
        return tables.map((table: string) => ({
          label: table,
          value: table,
        }));
      },
    },
    {
      key: 'date_from',
      label: 'Дата от',
      type: 'date' as const,
      placeholder: 'Выберите дату от',
    },
    {
      key: 'date_to',
      label: 'Дата до',
      type: 'date' as const,
      placeholder: 'Выберите дату до',
    },
  ], []);

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    const response = await auditApi.getLogs(params);
    return response.logs || response;
  };

  // Получение статистики
  const getStats = async () => {
    try {
      const stats = await auditApi.getStats();
      return stats;
    } catch (error) {
      console.error('Error fetching stats:', error);
      return null;
    }
  };

  // Конфигурация дашборда
  const dashboardConfig = useMemo(() => ({
    fetchData: getStats,
    renderStats: (stats: any) => [
      {
        title: 'Всего записей',
        value: stats.total_count || 0,
        prefix: <FileTextOutlined />,
        color: '#1890ff',
      },
      {
        title: 'Уникальных действий',
        value: stats.action_stats?.length || 0,
        prefix: <DatabaseOutlined />,
        color: '#52c41a',
      },
      {
        title: 'Активных пользователей',
        value: stats.user_stats?.length || 0,
        prefix: <UserOutlined />,
        color: '#722ed1',
      },
      {
        title: 'Затронутых таблиц',
        value: stats.table_stats?.length || 0,
        prefix: <DatabaseOutlined />,
        color: '#fa8c16',
      },
    ],
    title: 'Статистика аудита',
    showDateFilter: true,
  }), []);

  return (
    <div>
      <style>
        {`
          .hidden-column {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
          }
          .ant-table-thead > tr > .hidden-column,
          .ant-table-tbody > tr > .hidden-column {
            display: none !important;
            padding: 0 !important;
            border: none !important;
          }
        `}
      </style>
      <GenericDataTable<AuditLog>
      title="Аудит"
      icon={<FileTextOutlined />}
      columns={columns}
      filters={filters}
      formConfig={{
        fields: [],
        modalWidth: 800,
      }}
      endpoints={{
        list: handleList,
        create: () => Promise.reject(new Error('Создание записей аудита не поддерживается')),
        update: () => Promise.reject(new Error('Редактирование записей аудита не поддерживается')),
        delete: () => Promise.reject(new Error('Удаление записей аудита не поддерживается')),
      }}
      searchable={true}
      exportable={true}
      dashboardConfig={dashboardConfig}
      pagination={{
        pageSize: 50,
        pageSizeOptions: ['50', '100', '200', '500'],
      }}
      disableEdit={true}
      disableDelete={true}
      disableCreate={true}
    />
    </div>
  );
};

export default Audit; 