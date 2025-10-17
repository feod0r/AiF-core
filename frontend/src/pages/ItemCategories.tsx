import React, { useMemo } from 'react';
import { Tag } from 'antd';
import { TagsOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { itemCategoriesApi, referenceTablesApi } from '../services/api';
import type { ItemCategory } from '../types';

const ItemCategories: React.FC = () => {

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
      render: (name: string, record: ItemCategory): React.ReactElement => {
        // Показываем отступы для вложенных категорий
        const indent = record.parent_id ? '  ' : '';
        return (
          <span style={{ 
            paddingLeft: record.parent_id ? '20px' : '0',
            fontWeight: record.parent_id ? 'normal' : 'bold'
          }}>
            {indent}{name}
          </span>
        );
      },
    },
    {
      title: 'Родительская категория',
      dataIndex: 'parent',
      key: 'parent',
      render: (_: any, record: ItemCategory): React.ReactElement => {
        if (record.parent) {
          return <span>{record.parent.name}</span>;
        }
        return <Tag color="blue">Корневая</Tag>;
      },
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      render: (description: string): React.ReactElement => (
        <span>{description || '-'}</span>
      ),
    },
    {
      title: 'Тип',
      dataIndex: 'category_type',
      key: 'category_type',
      render: (_: any, record: ItemCategory): React.ReactElement => {
        if (record.category_type) {
          return (
            <span>
              {record.category_type.name} ({record.category_type.description})
            </span>
          );
        }
        return <span>-</span>;
      },
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean): React.ReactElement => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Активна' : 'Неактивна'}
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
      placeholder: 'Поиск по названию и описанию',
    },
    {
      key: 'parent_id',
      label: 'Родительская категория',
      type: 'select' as const,
      placeholder: 'Выберите родительскую категорию',
      options: [
        { label: 'Корневые категории', value: null },
      ],
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const categories = await itemCategoriesApi.getList({ include_children: true });
        return [
          { label: 'Корневые категории', value: null },
          ...categories.map((category: ItemCategory) => ({ 
            label: category.name, 
            value: category.id 
          }))
        ];
      },
    },
    {
      key: 'category_type_id',
      label: 'Тип категории',
      type: 'select' as const,
      placeholder: 'Выберите тип категории',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const types = await referenceTablesApi.getList('item_category_types');
        return types.map((type: any) => ({ 
          label: type.name, 
          value: type.id 
        }));
      },
    },
    {
      key: 'is_active',
      label: 'Статус',
      type: 'select' as const,
      placeholder: 'Выберите статус',
      options: [
        { label: 'Активна', value: true },
        { label: 'Неактивна', value: false },
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
        name: 'category_type_id',
        label: 'Тип категории',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите тип категории' }],
        placeholder: 'Выберите тип категории',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const types = await referenceTablesApi.getList('item_category_types');
          return types.map((type: any) => ({ 
            label: type.name, 
            value: type.id 
          }));
        },
      },
      {
        name: 'parent_id',
        label: 'Родительская категория',
        type: 'select' as const,
        placeholder: 'Выберите родительскую категорию (необязательно)',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const categories = await itemCategoriesApi.getList({ include_children: true });
          return categories.map((category: ItemCategory) => ({ 
            label: category.name, 
            value: category.id 
          }));
        },
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

  // Подготовка данных для редактирования
  const prepareDataForEdit = (record: ItemCategory) => {
    return {
      ...record,
      category_type_id: record.category_type_id || record.category_type?.id,
      is_active: record.is_active !== undefined ? record.is_active : true,
    };
  };

  // Дашборд конфигурация
  const dashboardConfig = useMemo(() => ({
    fetchData: itemCategoriesApi.getSummary,
    renderStats: (summary: any) => [
      {
        title: 'Всего категорий',
        value: summary.total_categories || 0,
        prefix: <TagsOutlined />,
        color: '#1890ff',
      },
      {
        title: 'Активных',
        value: summary.active_categories || 0,
        prefix: <TagsOutlined />,
        color: '#52c41a',
      },
      {
        title: 'Типов категорий',
        value: summary.category_types?.length || 0,
        prefix: <TagsOutlined />,
        color: '#722ed1',
      },
      {
        title: 'Корневых категорий',
        value: summary.root_categories || 0,
        prefix: <TagsOutlined />,
        color: '#fa8c16',
      },
    ],
    title: 'Статистика категорий товаров',
  }), []);

  return (
    <GenericDataTable<ItemCategory>
      title="Категории товаров"
      icon={<TagsOutlined />}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      endpoints={{
        list: (params?: any) => itemCategoriesApi.getList({ ...params, include_children: true }),
        create: itemCategoriesApi.create,
        update: itemCategoriesApi.update,
        delete: itemCategoriesApi.delete,
      }}
      onEditDataTransform={prepareDataForEdit}
      dashboardConfig={dashboardConfig}
      searchable={true}
      exportable={true}
      addButtonText="Добавить категорию"
      pagination={{
        pageSize: 20,
        pageSizeOptions: ['20', '50', '100'],
      }}
    />
  );
};

export default ItemCategories; 