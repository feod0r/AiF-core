import React, { useMemo } from 'react';
import { UserOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { ownersApi } from '../services/api';
import { Owner } from '../types';

const Owners: React.FC = () => {
  // Конфигурация колонок
  const columns = useMemo(() => [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'ИНН',
      dataIndex: 'inn',
      key: 'inn',
      width: 120,
    },
    {
      title: 'Пользователь Vendista',
      dataIndex: 'vendista_user',
      key: 'vendista_user',
      ellipsis: true,
    },
    {
      title: 'Дата начала',
      dataIndex: 'start_date',
      key: 'start_date',
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString('ru-RU'),
    },
    {
      title: 'Дата окончания',
      dataIndex: 'end_date',
      key: 'end_date',
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString('ru-RU'),
    },
  ], []);

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'search',
      label: 'Поиск',
      type: 'input' as const,
      placeholder: 'Поиск по названию или ИНН',
    },
    {
      key: 'start_date_from',
      label: 'Дата начала от',
      type: 'date' as const,
      placeholder: 'Выберите дату от',
    },
    {
      key: 'start_date_to',
      label: 'Дата начала до',
      type: 'date' as const,
      placeholder: 'Выберите дату до',
    },
  ], []);

  // Конфигурация формы
  const formConfig = useMemo(() => ({
    fields: [
      {
        name: 'name',
        label: 'Название',
        type: 'input' as const,
        rules: [{ required: true, message: 'Пожалуйста, введите название' }],
        placeholder: 'Введите название',
      },
      {
        name: 'inn',
        label: 'ИНН',
        type: 'input' as const,
        rules: [{ required: true, message: 'Пожалуйста, введите ИНН' }],
        placeholder: 'Введите ИНН',
      },
      {
        name: 'vendista_user',
        label: 'Пользователь Vendista',
        type: 'input' as const,
        placeholder: 'Введите пользователя Vendista',
      },
      {
        name: 'vendista_pass',
        label: 'Пароль Vendista',
        type: 'password' as const,
        placeholder: 'Введите пароль Vendista',
      },
    ],
  }), []);

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    const response = await ownersApi.getList(params);
    return response.data || response;
  };

  // Переопределяем эндпоинты
  const customEndpoints = {
    list: handleList,
    create: ownersApi.create,
    update: ownersApi.update,
    delete: ownersApi.delete,
  };

  return (
    <GenericDataTable<Owner>
      title="Управление владельцами"
      icon={<UserOutlined />}
      endpoints={customEndpoints}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      searchable={true}
      exportable={true}
      addButtonText="Добавить владельца"
      pagination={{
        pageSize: 100,
        pageSizeOptions: ['100', '200', '500', '800', '1000'],
      }}
    />
  );
};

export default Owners; 