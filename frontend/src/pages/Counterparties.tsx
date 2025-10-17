import React, { useMemo } from 'react';
import { UserOutlined } from '@ant-design/icons';
import { Tag } from 'antd';
import GenericDataTable from '../components/GenericDataTable';
import { counterpartiesApi, counterpartyCategoriesApi } from '../services/api';
import { Counterparty, CounterpartyCategory } from '../types';
import dayjs from 'dayjs';

const Counterparties: React.FC = () => {
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
      title: 'Категория',
      dataIndex: ['category', 'name'],
      key: 'category',
      render: (category: string) => (
        <Tag color="blue">{category || '-'}</Tag>
      ),
    },
    {
      title: 'ИНН',
      dataIndex: 'inn',
      key: 'inn',
    },
    {
      title: 'КПП',
      dataIndex: 'kpp',
      key: 'kpp',
    },
    {
      title: 'Телефон',
      dataIndex: 'phone',
      key: 'phone',
    },
    {
      title: 'Email',
      dataIndex: 'email',
      key: 'email',
      ellipsis: true,
    },
    {
      title: 'Контактное лицо',
      dataIndex: 'contact_person',
      key: 'contact_person',
      ellipsis: true,
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Активен' : 'Неактивен'}
        </Tag>
      ),
    },
  ], []);

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'search',
      label: 'Поиск',
      type: 'input' as const,
      placeholder: 'Поиск по названию, ИНН, контактному лицу',
    },
    {
      key: 'category_id',
      label: 'Категория',
      type: 'select' as const,
      placeholder: 'Выберите категорию',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const categories = await counterpartyCategoriesApi.getList();
        return categories.map((cat: CounterpartyCategory) => ({
          label: cat.name,
          value: cat.id,
        }));
      },
    },
    {
      key: 'is_active',
      label: 'Статус',
      type: 'select' as const,
      placeholder: 'Выберите статус',
      options: [
        { label: 'Активен', value: true },
        { label: 'Неактивен', value: false },
      ],
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
        placeholder: 'Введите название контрагента',
      },
      {
        name: 'category_id',
        label: 'Категория',
        type: 'select' as const,
        placeholder: 'Выберите категорию',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const categories = await counterpartyCategoriesApi.getList();
          return categories.map((cat: CounterpartyCategory) => ({
            label: cat.name,
            value: cat.id,
          }));
        },
      },
      {
        name: 'inn',
        label: 'ИНН',
        type: 'input' as const,
        placeholder: 'Введите ИНН',
      },
      {
        name: 'kpp',
        label: 'КПП',
        type: 'input' as const,
        placeholder: 'Введите КПП',
      },
      {
        name: 'address',
        label: 'Адрес',
        type: 'textarea' as const,
        placeholder: 'Введите адрес',
      },
      {
        name: 'phone',
        label: 'Телефон',
        type: 'input' as const,
        placeholder: 'Введите телефон',
      },
      {
        name: 'email',
        label: 'Email',
        type: 'input' as const,
        rules: [
          { type: 'email', message: 'Введите корректный email' }
        ],
        placeholder: 'Введите email',
      },
      {
        name: 'contact_person',
        label: 'Контактное лицо',
        type: 'input' as const,
        placeholder: 'Введите контактное лицо',
      },
      {
        name: 'notes',
        label: 'Примечания',
        type: 'textarea' as const,
        placeholder: 'Введите примечания',
      },
      {
        name: 'is_active',
        label: 'Активен',
        type: 'switch' as const,
      },
      {
        name: 'start_date',
        label: 'Дата начала',
        type: 'date' as const,
        placeholder: 'Выберите дату начала',
      },
      {
        name: 'end_date',
        label: 'Дата окончания',
        type: 'date' as const,
        placeholder: 'Выберите дату окончания',
      },
    ],
    initialValues: {
      is_active: true,
    },
  }), []);

  // Подготовка данных для редактирования
  const prepareDataForEdit = (record: Counterparty) => {
    return {
      ...record,
      start_date: record.start_date ? dayjs(record.start_date) : undefined,
      end_date: record.end_date ? dayjs(record.end_date) : undefined,
    };
  };



  return (
    <GenericDataTable<Counterparty>
      title="Контрагенты"
      icon={<UserOutlined />}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      endpoints={{
        list: counterpartiesApi.getList,
        create: counterpartiesApi.create,
        update: counterpartiesApi.update,
        delete: counterpartiesApi.delete,
      }}
      onEditDataTransform={prepareDataForEdit}
      searchable={true}
      exportable={true}
      addButtonText="Добавить контрагента"
    />
  );
};

export default Counterparties; 
