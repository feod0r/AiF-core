import React, { useMemo } from 'react';
import { TeamOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { counterpartyCategoriesApi } from '../services/api';
import { CounterpartyCategory } from '../types';

const CounterpartyCategories: React.FC = () => {
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
      render: (date: string): React.ReactElement => {
        if (!date) return <span style={{ color: '#999' }}>-</span>;
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
        rules: [{ required: true, message: 'Введите название категории' }],
        placeholder: 'Введите название категории',
      },
      {
        name: 'description',
        label: 'Описание',
        type: 'textarea' as const,
        placeholder: 'Введите описание категории',
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
    initialValues: {},
  }), []);

  // Подготовка данных для редактирования
  const prepareDataForEdit = (record: CounterpartyCategory) => {
    return {
      ...record,
      start_date: record.start_date ? new Date(record.start_date) : undefined,
      end_date: record.end_date ? new Date(record.end_date) : undefined,
    };
  };

  return (
    <GenericDataTable<CounterpartyCategory>
      title="Категории контрагентов"
      icon={<TeamOutlined />}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      endpoints={{
        list: counterpartyCategoriesApi.getList,
        create: counterpartyCategoriesApi.create,
        update: counterpartyCategoriesApi.update,
        delete: counterpartyCategoriesApi.delete,
      }}
      onEditDataTransform={prepareDataForEdit}
      searchable={true}
      exportable={true}
      addButtonText="Добавить категорию"
    />
  );
};

export default CounterpartyCategories; 