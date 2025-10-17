import React, { useMemo } from 'react';
import { Tag } from 'antd';
import { TagsOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { transactionCategoriesApi, referenceTablesApi } from '../services/api';
import { TransactionCategory } from '../types';

const TransactionCategories: React.FC = () => {
  // Вспомогательная функция для отображения типов
  const getTypeTag = (typeName?: string) => {
    const map: Record<string, { color: string; text: string }> = {
      income: { color: 'green', text: 'Доход' },
      expense: { color: 'red', text: 'Расход' },
      transfer: { color: 'blue', text: 'Перевод' },
    };
    const key = (typeName || '').toLowerCase();
    return map[key] || { color: 'default', text: typeName || '-' };
  };

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
      width: 200,
    },
    {
      title: 'Тип',
      key: 'type',
      width: 120,
      render: (_: any, record: TransactionCategory) => {
        const typeName = (record as any).transaction_type?.name || (record as any).transactionType?.name;
        const info = getTypeTag(typeName);
        return <Tag color={info.color}>{info.text}</Tag>;
      },
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (description: string) => description || '-',
    },
    {
      title: 'Активна',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Да' : 'Нет'}
        </Tag>
      ),
    },
  ], []);

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'transaction_type_id',
      label: 'Тип операции',
      type: 'select' as const,
      placeholder: 'Выберите тип операции',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const types = await referenceTablesApi.getList('transaction_types');
        return types.map((type: any) => ({
          label: type.name,
          value: type.id,
        }));
      },
    },
    {
      key: 'is_active',
      label: 'Статус',
      type: 'select' as const,
      placeholder: 'Выберите статус',
      options: [
        { label: 'Активные', value: true },
        { label: 'Неактивные', value: false },
      ],
    },
    {
      key: 'name',
      label: 'Поиск по названию',
      type: 'input' as const,
      placeholder: 'Введите название категории',
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
        name: 'transaction_type_id',
        label: 'Тип операции',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите тип операции' }],
        placeholder: 'Выберите тип операции',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const types = await referenceTablesApi.getList('transaction_types');
          return types.map((type: any) => ({
            label: type.name,
            value: type.id,
          }));
        },
      },
      {
        name: 'description',
        label: 'Описание',
        type: 'textarea' as const,
        placeholder: 'Введите описание категории',
      },
      {
        name: 'is_active',
        label: 'Активна',
        type: 'switch' as const,
        initialValue: true,
      },
    ],
    initialValues: {
      is_active: true,
    },
  }), []);

  // Кастомная обработка данных для редактирования
  const prepareDataForEdit = (record: TransactionCategory) => {
    return {
      ...record,
      transaction_type_id: (record as any).transaction_type_id ?? 
                          (record as any).transactionType?.id ?? 
                          (record as any).transaction_type?.id,
    };
  };

  return (
    <GenericDataTable<TransactionCategory>
      title="Категории операций"
      icon={<TagsOutlined />}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      onEditDataTransform={prepareDataForEdit}
      endpoints={{
        list: transactionCategoriesApi.getList,
        create: transactionCategoriesApi.create,
        update: transactionCategoriesApi.update,
        delete: transactionCategoriesApi.delete,
      }}
      pagination={{
        pageSize: 50,
        pageSizeOptions: ['50', '100', '200'],
        showSizeChanger: true,
        showQuickJumper: true,
      }}
      addButtonText="Добавить категорию"
      searchable={true}
      exportable={false}
    />
  );
};

export default TransactionCategories; 