import React, { useMemo, useState, useEffect } from 'react';
import { ShoppingOutlined, PlusOutlined } from '@ant-design/icons';
import { Tag, Modal, Form, Input, Select, message } from 'antd';
import GenericDataTable from '../components/GenericDataTable';
import { itemsApi, itemCategoriesApi, referenceTablesApi } from '../services/api';
import { Item, ItemCategory } from '../types';

const { TextArea } = Input;
const { Option } = Select;

const Items: React.FC = () => {
  // Состояние для модального окна добавления категории
  const [isAddCategoryModalVisible, setIsAddCategoryModalVisible] = useState(false);
  const [itemCategories, setItemCategories] = useState<ItemCategory[]>([]);
  const [categoryTypes, setCategoryTypes] = useState<any[]>([]);
  const [addCategoryForm] = Form.useForm();
  const [mainFormRef, setMainFormRef] = useState<any>(null);

  // Загрузка категорий и типов категорий
  useEffect(() => {
    const loadData = async () => {
      try {
        const [categories, types] = await Promise.all([
          itemCategoriesApi.getList({ include_children: true }),
          referenceTablesApi.getList('item_category_types'),
        ]);
        setItemCategories(categories);
        setCategoryTypes(types);
      } catch (error) {
        console.error('Error loading categories:', error);
      }
    };
    loadData();
  }, []);

  // Функции для работы с модальным окном добавления категории
  const handleOpenAddCategoryModal = () => {
    setIsAddCategoryModalVisible(true);
    addCategoryForm.resetFields();
  };

  const handleCloseAddCategoryModal = () => {
    setIsAddCategoryModalVisible(false);
    addCategoryForm.resetFields();
  };

  const handleCreateCategory = async () => {
    try {
      const values = await addCategoryForm.validateFields();
      
      // Создаем категорию
      const newCategory = await itemCategoriesApi.create({
        name: values.name,
        description: values.description || '',
        category_type_id: values.category_type_id,
        parent_id: values.parent_id,
        is_active: true,
        start_date: new Date().toISOString(),
        end_date: '2099-12-31T23:59:59Z',
      });

      message.success(`Категория "${newCategory.name}" успешно создана`);

      // Обновляем список категорий
      const updatedCategories = await itemCategoriesApi.getList({ include_children: true });
      setItemCategories(updatedCategories);

      // Автоматически выбираем созданную категорию в форме товара
      if (mainFormRef) {
        mainFormRef.setFieldsValue({ category_id: newCategory.id });
      }

      handleCloseAddCategoryModal();
    } catch (error: any) {
      if (error.errorFields) {
        // Ошибка валидации формы
        console.error('Validation error:', error);
      } else {
        // API ошибка
        console.error('API error:', error);
        message.error('Ошибка при создании категории');
      }
    }
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
      title: 'SKU',
      dataIndex: 'sku',
      key: 'sku',
      width: 150,
      render: (sku: string) => sku || <span style={{ color: '#ff4d4f' }}>Не указан</span>,
    },
    {
      title: 'Категория',
      dataIndex: ['category', 'name'],
      key: 'category',
      width: 180,
      render: (_: any, record: Item) => {
        const category = record.category;
        return (
          <Tag color={category?.category_type?.type === 'inventory' ? 'blue' : 'green'}>
            {category?.name || 'Неизвестно'}
          </Tag>
        );
      },
    },
    {
      title: 'Единица',
      dataIndex: 'unit',
      key: 'unit',
      width: 100,
    },
    {
      title: 'Мин. остаток',
      dataIndex: 'min_stock',
      key: 'min_stock',
      width: 120,
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
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
      key: 'category_id',
      label: 'Категория',
      type: 'select' as const,
      placeholder: 'Выберите категорию',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const categories = await itemCategoriesApi.getList({ include_children: true });
        return categories.map((category: ItemCategory) => ({
          label: category.name,
          value: category.id,
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
      placeholder: 'Введите название товара',
    },
    {
      key: 'sku',
      label: 'Поиск по SKU',
      type: 'input' as const,
      placeholder: 'Введите SKU',
    },
  ], []);

  // Конфигурация формы
  const formConfig = useMemo(() => ({
    fields: [
      {
        name: 'name',
        label: 'Название',
        type: 'input' as const,
        rules: [{ required: true, message: 'Введите название товара' }],
        placeholder: 'Введите название товара',
      },
      {
        name: 'description',
        label: 'Описание',
        type: 'textarea' as const,
        placeholder: 'Введите описание товара',
      },
      {
        name: 'category_id',
        label: 'Категория',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите категорию' }],
        placeholder: 'Выберите категорию',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          return itemCategories.map((category: ItemCategory) => ({
            label: category.name,
            value: category.id,
          }));
        },
      },
      {
        name: 'sku',
        label: 'SKU',
        type: 'input' as const,
        rules: [{ required: true, message: 'Введите SKU' }],
        placeholder: 'Введите SKU',
      },
      {
        name: 'barcode',
        label: 'Штрихкод',
        type: 'input' as const,
        placeholder: 'Введите штрихкод',
      },
      {
        name: 'unit',
        label: 'Единица измерения',
        type: 'input' as const,
        rules: [{ required: true, message: 'Введите единицу измерения' }],
        placeholder: 'шт, кг, м и т.д.',
        initialValue: 'шт',
      },
      {
        name: 'weight',
        label: 'Вес (г)',
        type: 'number' as const,
        placeholder: 'Введите вес в граммах',
        min: 0,
      },
      {
        name: 'dimensions',
        label: 'Размеры',
        type: 'input' as const,
        placeholder: 'Введите размеры (ДxШxВ)',
      },
      {
        name: 'min_stock',
        label: 'Минимальный остаток',
        type: 'number' as const,
        rules: [{ required: true, message: 'Введите минимальный остаток' }],
        placeholder: '0',
        min: 0,
        initialValue: 0,
      },
      {
        name: 'max_stock',
        label: 'Максимальный остаток',
        type: 'number' as const,
        placeholder: 'Не ограничено',
        min: 0,
      },
      {
        name: 'is_active',
        label: 'Статус',
        type: 'select' as const,
        options: [
          { label: 'Активен', value: true },
          { label: 'Неактивен', value: false },
        ],
        initialValue: true,
      },
    ],
    initialValues: {
      unit: 'шт',
      min_stock: 0,
      is_active: true,
    },
  }), [itemCategories]);

  // Кастомный рендер формы для добавления кнопки создания категории
  const customFormRender = (form: any, config: any) => {
    // Сохраняем ссылку на форму
    if (!mainFormRef) {
      setMainFormRef(form);
    }

    return (
      <>
        {config.fields.map((field: any) => {
          // Если это поле category_id, рендерим с кнопкой
          if (field.name === 'category_id') {
            return (
              <div key={field.name} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <Form.Item
                  name={field.name}
                  label={field.label}
                  rules={field.rules}
                  style={{ flex: 1, marginBottom: 24 }}
                >
                  <Select
                    placeholder={field.placeholder}
                    showSearch
                    optionFilterProp="children"
                  >
                    {itemCategories.map((category) => (
                      <Option key={category.id} value={category.id}>
                        {category.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
                <button
                  type="button"
                  onClick={handleOpenAddCategoryModal}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    padding: '4px 15px',
                    border: '1px solid #1890ff',
                    background: '#1890ff',
                    color: 'white',
                    borderRadius: '2px',
                    cursor: 'pointer',
                    fontSize: '14px',
                    marginTop: '30px',
                  }}
                  title="Добавить новую категорию"
                >
                  <PlusOutlined />
                </button>
              </div>
            );
          }

          // Для остальных полей используем стандартный рендеринг
          const fieldType = field.type;
          let inputComponent;

          if (fieldType === 'textarea') {
            inputComponent = <TextArea rows={4} placeholder={field.placeholder} />;
          } else if (fieldType === 'select') {
            inputComponent = (
              <Select placeholder={field.placeholder}>
                {(field.options || []).map((option: any) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            );
          } else if (fieldType === 'number') {
            inputComponent = (
              <Input
                type="number"
                placeholder={field.placeholder}
                min={field.min}
              />
            );
          } else {
            inputComponent = <Input placeholder={field.placeholder} />;
          }

          return (
            <Form.Item
              key={field.name}
              name={field.name}
              label={field.label}
              rules={field.rules}
            >
              {inputComponent}
            </Form.Item>
          );
        })}
      </>
    );
  };

  // Кастомная обработка данных для редактирования
  const prepareDataForEdit = (record: Item) => {
    return {
      ...record,
      category_id: record.category_id || record.category?.id,
    };
  };

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    const response = await itemsApi.getList(params);
    return response;
  };

  return (
    <>
      <GenericDataTable<Item>
        title="Товары"
        icon={<ShoppingOutlined />}
        columns={columns}
        filters={filters}
        formConfig={formConfig}
        onEditDataTransform={prepareDataForEdit}
        customFormRender={customFormRender}
        endpoints={{
          list: handleList,
          create: itemsApi.create,
          update: itemsApi.update,
          delete: itemsApi.delete,
        }}
        pagination={{
          pageSize: 100,
          pageSizeOptions: ['100', '200', '500', '800', '1000'],
          showSizeChanger: true,
          showQuickJumper: true,
        }}
        addButtonText="Добавить товар"
        searchable={true}
        exportable={false}
      />

      {/* Модальное окно для добавления новой категории */}
      <Modal
        title="Добавить новую категорию товара"
        open={isAddCategoryModalVisible}
        onOk={handleCreateCategory}
        onCancel={handleCloseAddCategoryModal}
        width={500}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form
          form={addCategoryForm}
          layout="vertical"
          initialValues={{
            is_active: true,
          }}
        >
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название категории' }]}
          >
            <Input placeholder="Введите название категории" />
          </Form.Item>

          <Form.Item
            name="category_type_id"
            label="Тип категории"
            rules={[{ required: true, message: 'Выберите тип категории' }]}
          >
            <Select
              placeholder="Выберите тип категории"
              showSearch
              optionFilterProp="children"
            >
              {categoryTypes.map((type) => (
                <Option key={type.id} value={type.id}>
                  {type.name} - {type.description}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="parent_id"
            label="Родительская категория"
          >
            <Select
              placeholder="Выберите родительскую категорию (необязательно)"
              showSearch
              optionFilterProp="children"
              allowClear
            >
              {itemCategories.map((category) => (
                <Option key={category.id} value={category.id}>
                  {category.name}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="description"
            label="Описание"
          >
            <TextArea rows={3} placeholder="Введите описание категории" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default Items;