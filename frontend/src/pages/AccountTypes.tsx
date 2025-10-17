import React, { useMemo } from 'react';
import { BankOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { accountTypesApi } from '../services/api';
import { AccountType } from '../types';
import dayjs from 'dayjs';

const AccountTypes: React.FC = () => {
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
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
    },
    {
      title: 'Дата создания',
      dataIndex: 'start_date',
      key: 'start_date',
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
      placeholder: 'Поиск по названию или описанию',
    },
    {
      key: 'start_date_from',
      label: 'Дата создания от',
      type: 'date' as const,
      placeholder: 'Выберите дату от',
    },
    {
      key: 'start_date_to',
      label: 'Дата создания до',
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
        rules: [{ required: true, message: 'Введите название' }],
        placeholder: 'Введите название типа счета',
      },
      {
        name: 'description',
        label: 'Описание',
        type: 'textarea' as const,
        placeholder: 'Введите описание типа счета',
        rows: 3,
      },
      {
        name: 'start_date',
        label: 'Дата создания',
        type: 'date' as const,
        placeholder: 'Выберите дату создания',
      },
      {
        name: 'end_date',
        label: 'Дата окончания',
        type: 'date' as const,
        placeholder: 'Выберите дату окончания',
      },
    ],
    initialValues: {
      start_date: dayjs(),
      end_date: dayjs().add(10, 'year'),
    },
  }), []);

  // Кастомная обработка данных для редактирования
  const prepareDataForEdit = (record: AccountType) => {
    return {
      ...record,
      start_date: record.start_date ? dayjs(record.start_date) : dayjs(),
      end_date: record.end_date ? dayjs(record.end_date) : dayjs().add(10, 'year'),
    };
  };

  // Кастомная обработка submit
  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        start_date: values.start_date ? values.start_date.toISOString() : dayjs().toISOString(),
        end_date: values.end_date ? values.end_date.toISOString() : dayjs().add(10, 'year').toISOString(),
      };

      return submitData;
    } catch (error) {
      throw error;
    }
  };

  // Кастомная обработка submit для создания
  const handleCreate = async (data: any) => {
    const processedData = await handleSubmit(data);
    return accountTypesApi.create(processedData);
  };

  // Кастомная обработка submit для обновления
  const handleUpdate = async (id: number, data: any) => {
    const processedData = await handleSubmit(data);
    return accountTypesApi.update(id, processedData);
  };

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    const response = await accountTypesApi.getList(params);
    return response; // accountTypesApi.getList теперь поддерживает параметры через referenceTablesApi
  };

  return (
    <GenericDataTable<AccountType>
      title="Типы счетов"
      icon={<BankOutlined />}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      onEditDataTransform={prepareDataForEdit}
      endpoints={{
        list: handleList,
        create: handleCreate,
        update: handleUpdate,
        delete: accountTypesApi.delete,
      }}
      searchable={true}
      exportable={true}
      addButtonText="Добавить тип счета"
      pagination={{
        pageSize: 100,
        pageSizeOptions: ['100', '200', '500', '800', '1000'],
      }}
    />
  );
};

export default AccountTypes; 