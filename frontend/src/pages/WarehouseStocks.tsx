import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Modal,
  Form,
  Space,
  Popconfirm,
  message,
  Card,
  Typography,
  Tooltip,
  Select,
  InputNumber,
  Tag,
  Row,
  Col,
  Statistic,
  Alert,
  List,
  Drawer,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, WarningOutlined, InboxOutlined } from '@ant-design/icons';
import { warehouseStocksApi, warehousesApi, itemsApi, itemCategoriesApi } from '../services/api';
import { WarehouseStock, Warehouse, Item, ItemCategory } from '../types';

const { Title } = Typography;
const { Option } = Select;

const WarehouseStocks: React.FC = () => {
  const [stocks, setStocks] = useState<WarehouseStock[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [categories, setCategories] = useState<ItemCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingStock, setEditingStock] = useState<WarehouseStock | null>(null);
  const [isMobile, setIsMobile] = useState(false);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedStock, setSelectedStock] = useState<WarehouseStock | null>(null);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0,
  });
  const [filters, setFilters] = useState({
    warehouse_id: undefined as number | undefined,
    item_id: undefined as number | undefined,
    category_id: undefined as number | undefined,
    low_stock: undefined as boolean | undefined,
  });
  const [form] = Form.useForm();

  // Определяем мобильное устройство
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const fetchStocks = async (page = 1, pageSize = 10, filterParams = {}) => {
    setLoading(true);
    try {
      const params = {
        page,
        limit: pageSize,
        ...filterParams
      };
      const data = await warehouseStocksApi.getList(params);
      setStocks(data);
      setPagination({
        current: page,
        pageSize,
        total: data.length,
      });
    } catch (error) {
      message.error('Ошибка при загрузке остатков');
    } finally {
      setLoading(false);
    }
  };

  const fetchWarehouses = async () => {
    try {
      const data = await warehousesApi.getList();
      setWarehouses(data);
    } catch (error) {
      message.error('Ошибка при загрузке складов');
    }
  };

  const fetchItems = async () => {
    try {
      const data = await itemsApi.getList();
      setItems(data);
    } catch (error) {
      message.error('Ошибка при загрузке товаров');
    }
  };

  const fetchCategories = async () => {
    try {
      const data = await itemCategoriesApi.getList();
      setCategories(data);
    } catch (error) {
      message.error('Ошибка при загрузке категорий');
    }
  };

  useEffect(() => {
    fetchStocks();
    fetchWarehouses();
    fetchItems();
    fetchCategories();
  }, []);

  const handleCreate = () => {
    setEditingStock(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: WarehouseStock) => {
    setEditingStock(record);
    form.setFieldsValue({
      ...record,
      warehouse_id: record.warehouse_id || record.warehouse?.id,
      item_id: record.item_id || record.item?.id,
      quantity: record.quantity.toString(),
      reserved_quantity: record.reserved_quantity.toString(),
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await warehouseStocksApi.delete(id);
      message.success('Остаток удален');
      fetchStocks(pagination.current, pagination.pageSize, filters);
    } catch (error) {
      message.error('Ошибка при удалении остатка');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        quantity: parseInt(values.quantity),
        reserved_quantity: parseInt(values.reserved_quantity),
      };

      if (editingStock) {
        await warehouseStocksApi.update(editingStock.id, submitData);
        message.success('Остаток обновлен');
      } else {
        await warehouseStocksApi.create(submitData);
        message.success('Остаток создан');
      }
      setModalVisible(false);
      fetchStocks(pagination.current, pagination.pageSize, filters);
    } catch (error) {
      message.error('Ошибка при сохранении остатка');
    }
  };

  const handleTableChange = (pagination: any) => {
    fetchStocks(pagination.current, pagination.pageSize, filters);
  };

  const handleFilterChange = (key: string, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    fetchStocks(1, pagination.pageSize, newFilters);
  };

  const getStockStatus = (stock: WarehouseStock) => {
    if (!stock.item) return { color: 'default', text: 'Нет данных' };
    
    // Используем максимальное значение между min_quantity склада и min_stock товара
    const effectiveMinQuantity = Math.max(stock.min_quantity, stock.item.min_stock || 0);
    
    if (stock.quantity <= effectiveMinQuantity) {
      return { color: 'red', text: 'Критически мало' };
    } else if (stock.quantity <= effectiveMinQuantity * 2) {
      return { color: 'orange', text: 'Мало' };
    } else {
      return { color: 'green', text: 'Нормально' };
    }
  };

  const totalItems = stocks.length;
  const lowStockItems = stocks.filter(stock => {
    if (!stock.item) return false;
    const effectiveMinQuantity = Math.max(stock.min_quantity, stock.item.min_stock || 0);
    return stock.quantity <= effectiveMinQuantity;
  }).length;
  const totalQuantity = stocks.reduce((sum, stock) => sum + Number(stock.quantity || 0), 0);
  const totalReserved = stocks.reduce((sum, stock) => sum + Number(stock.reserved_quantity || 0), 0);

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Склад',
      key: 'warehouse',
      render: (_: any, record: WarehouseStock) => {
        const name = record.warehouse?.name || warehouses.find(w => w.id === record.warehouse_id)?.name;
        return name || `ID ${record.warehouse_id}`;
      },
    },
    {
      title: 'Товар',
      key: 'item',
      render: (_: any, record: WarehouseStock) => {
        const name = record.item?.name || items.find(i => i.id === record.item_id)?.name;
        return name || `ID ${record.item_id}`;
      },
    },
    {
      title: 'Категория',
      key: 'category',
      render: (_: any, record: WarehouseStock) => {
        const category = record.item?.category || items.find(i => i.id === record.item_id)?.category;
        const type = (category as any)?.category_type?.type;
        const color = type === 'inventory' ? 'blue' : type === 'equipment' ? 'green' : 'default';
        return <Tag color={color}>{category?.name || '-'}</Tag>;
      },
    },
    {
      title: 'Количество',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number, record: WarehouseStock) => {
        const status = getStockStatus(record);
        const unit = record.item?.unit || items.find(i => i.id === record.item_id)?.unit || 'шт';
        return (
          <span style={{ fontWeight: 'bold', color: status.color }}>
            {quantity} {unit}
          </span>
        );
      },
    },
    {
      title: 'Зарезервировано',
      dataIndex: 'reserved_quantity',
      key: 'reserved_quantity',
      render: (reserved: number, record: WarehouseStock) => {
        const unit = record.item?.unit || items.find(i => i.id === record.item_id)?.unit || 'шт';
        return `${reserved} ${unit}`;
      },
    },
    {
      title: 'Доступно',
      key: 'available',
      render: (_: any, record: WarehouseStock) => {
        const available = record.quantity - record.reserved_quantity;
        const unit = record.item?.unit || items.find(i => i.id === record.item_id)?.unit || 'шт';
        return (
          <span style={{ fontWeight: 'bold', color: available > 0 ? 'green' : 'red' }}>
            {available} {unit}
          </span>
        );
      },
    },
    {
      title: 'Статус',
      key: 'status',
      render: (_: any, record: WarehouseStock) => {
        const status = getStockStatus(record);
        return <Tag color={status.color}>{status.text}</Tag>;
      },
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      render: (_: any, record: WarehouseStock) => (
        <Space>
          <Tooltip title="Редактировать">
            <Button
              type="text"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          </Tooltip>
          <Popconfirm
            title="Удалить остаток?"
            description="Это действие нельзя отменить."
            onConfirm={() => handleDelete(record.id)}
            okText="Да"
            cancelText="Нет"
          >
            <Tooltip title="Удалить">
              <Button
                type="text"
                danger
                icon={<DeleteOutlined />}
              />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: isMobile ? '16px' : '24px' }}>
      <div style={{ 
        marginBottom: 24, 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center',
        flexDirection: isMobile ? 'column' : 'row',
        gap: isMobile ? 12 : 0
      }}>
        <Title level={isMobile ? 3 : 2} style={{ 
          margin: 0,
          fontSize: isMobile ? 18 : undefined,
          lineHeight: isMobile ? 1.4 : undefined
        }}>
          <InboxOutlined /> Остатки на складах
        </Title>
        <Button
          type="primary"
          icon={<PlusOutlined />}
          onClick={handleCreate}
          size={isMobile ? 'small' : 'middle'}
        >
          {isMobile ? 'Добавить' : 'Добавить остаток'}
        </Button>
      </div>

      <Card size={isMobile ? 'small' : 'default'}>
        <Row gutter={isMobile ? 8 : 16} style={{ marginBottom: '16px' }}>
          <Col span={isMobile ? 12 : 6}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Позиций" : "Всего позиций"}
                value={totalItems}
                valueStyle={{ 
                  color: '#1890ff',
                  fontSize: isMobile ? 16 : undefined
                }}
              />
            </Card>
          </Col>
          <Col span={isMobile ? 12 : 6}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Мало" : "Критически мало"}
                value={lowStockItems}
                valueStyle={{ 
                  color: '#cf1322',
                  fontSize: isMobile ? 16 : undefined
                }}
                prefix={<WarningOutlined />}
              />
            </Card>
          </Col>
          <Col span={isMobile ? 12 : 6}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Количество" : "Общее количество"}
                value={totalQuantity}
                valueStyle={{ 
                  color: '#3f8600',
                  fontSize: isMobile ? 16 : undefined
                }}
              />
            </Card>
          </Col>
          <Col span={isMobile ? 12 : 6}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Резерв" : "Зарезервировано"}
                value={totalReserved}
                valueStyle={{ 
                  color: '#faad14',
                  fontSize: isMobile ? 16 : undefined
                }}
              />
            </Card>
          </Col>
        </Row>

        {lowStockItems > 0 && (
          <Alert
            message={isMobile ? `${lowStockItems} позиций с низким остатком` : `Внимание! ${lowStockItems} позиций имеют критически низкий остаток`}
            type="warning"
            showIcon
            style={{ marginBottom: '16px' }}
          />
        )}

        {/* Фильтры */}
        <Card style={{ marginBottom: '16px' }} size={isMobile ? 'small' : 'default'}>
          {isMobile ? (
            // Мобильная версия фильтров - вертикальное расположение
            <Space direction="vertical" size="small" style={{ width: '100%' }}>
              <Form.Item label="Склад" style={{ marginBottom: 8 }}>
                <Select
                  placeholder="Выберите склад"
                  allowClear
                  value={filters.warehouse_id}
                  onChange={(value) => handleFilterChange('warehouse_id', value)}
                  size="small"
                  style={{ width: '100%' }}
                >
                  {warehouses.map(warehouse => (
                    <Option key={warehouse.id} value={warehouse.id}>
                      {warehouse.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              
              <Form.Item label="Категория товара" style={{ marginBottom: 8 }}>
                <Select
                  placeholder="Выберите категорию"
                  allowClear
                  value={filters.category_id}
                  onChange={(value) => handleFilterChange('category_id', value)}
                  size="small"
                  style={{ width: '100%' }}
                >
                  {categories.map(category => (
                    <Option key={category.id} value={category.id}>
                      {category.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              
              <Form.Item label="Товар" style={{ marginBottom: 8 }}>
                <Select
                  placeholder="Выберите товар"
                  allowClear
                  value={filters.item_id}
                  onChange={(value) => handleFilterChange('item_id', value)}
                  size="small"
                  style={{ width: '100%' }}
                >
                  {items.map(item => (
                    <Option key={item.id} value={item.id}>
                      {item.name}
                    </Option>
                  ))}
                </Select>
              </Form.Item>
              
              <Form.Item label="Статус" style={{ marginBottom: 8 }}>
                <Select
                  placeholder="Выберите статус"
                  allowClear
                  value={filters.low_stock}
                  onChange={(value) => handleFilterChange('low_stock', value)}
                  size="small"
                  style={{ width: '100%' }}
                >
                  <Option value={true}>Критически мало</Option>
                  <Option value={false}>Нормально</Option>
                </Select>
              </Form.Item>
            </Space>
          ) : (
            // Десктопная версия фильтров - горизонтальное расположение
            <Row gutter={[16, 16]}>
              <Col span={6}>
                <Form.Item label="Склад">
                  <Select
                    placeholder="Выберите склад"
                    allowClear
                    value={filters.warehouse_id}
                    onChange={(value) => handleFilterChange('warehouse_id', value)}
                  >
                    {warehouses.map(warehouse => (
                      <Option key={warehouse.id} value={warehouse.id}>
                        {warehouse.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              
              <Col span={6}>
                <Form.Item label="Категория товара">
                  <Select
                    placeholder="Выберите категорию"
                    allowClear
                    value={filters.category_id}
                    onChange={(value) => handleFilterChange('category_id', value)}
                  >
                    {categories.map(category => (
                      <Option key={category.id} value={category.id}>
                        {category.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              
              <Col span={6}>
                <Form.Item label="Товар">
                  <Select
                    placeholder="Выберите товар"
                    allowClear
                    value={filters.item_id}
                    onChange={(value) => handleFilterChange('item_id', value)}
                  >
                    {items.map(item => (
                      <Option key={item.id} value={item.id}>
                        {item.name}
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
              </Col>
              
              <Col span={6}>
                <Form.Item label="Статус">
                  <Select
                    placeholder="Выберите статус"
                    allowClear
                    value={filters.low_stock}
                    onChange={(value) => handleFilterChange('low_stock', value)}
                  >
                    <Option value={true}>Критически мало</Option>
                    <Option value={false}>Нормально</Option>
                  </Select>
                </Form.Item>
              </Col>
            </Row>
          )}
        </Card>

        {isMobile ? (
          // Мобильная версия - список
          <List
            dataSource={stocks}
            loading={loading}
            renderItem={(stock: WarehouseStock) => (
              <List.Item
                style={{ 
                  padding: '16px 0',
                  borderBottom: '1px solid #f0f0f0'
                }}
              >
                <div style={{ width: '100%' }}>
                  {/* Заголовок с товаром */}
                  <div style={{ 
                    marginBottom: 12,
                    cursor: 'pointer'
                  }}
                  onClick={() => {
                    setSelectedStock(stock);
                    setDetailDrawerVisible(true);
                  }}
                  >
                    <span 
                      style={{ 
                        fontSize: 18,
                        color: '#1890ff',
                        fontWeight: 'bold',
                        display: 'block',
                        width: '100%',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                        whiteSpace: 'nowrap'
                      }}
                    >
                      {stock.item?.name || items.find(i => i.id === stock.item_id)?.name || `ID ${stock.item_id}`}
                    </span>
                  </div>

                  {/* Основная информация */}
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        ID:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {stock.id}
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Склад:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {stock.warehouse?.name || warehouses.find(w => w.id === stock.warehouse_id)?.name || `ID ${stock.warehouse_id}`}
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Категория:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {(() => {
                          const category = stock.item?.category || items.find(i => i.id === stock.item_id)?.category;
                          const type = (category as any)?.category_type?.type;
                          const color = type === 'inventory' ? 'blue' : type === 'equipment' ? 'green' : 'default';
                          return <Tag color={color}>{category?.name || '-'}</Tag>;
                        })()}
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Количество:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {(() => {
                          const status = getStockStatus(stock);
                          const unit = stock.item?.unit || items.find(i => i.id === stock.item_id)?.unit || 'шт';
                          return (
                            <span style={{ fontWeight: 'bold', color: status.color }}>
                              {stock.quantity} {unit}
                            </span>
                          );
                        })()}
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Зарезервировано:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {(() => {
                          const unit = stock.item?.unit || items.find(i => i.id === stock.item_id)?.unit || 'шт';
                          return `${stock.reserved_quantity} ${unit}`;
                        })()}
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Доступно:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {(() => {
                          const available = stock.quantity - stock.reserved_quantity;
                          const unit = stock.item?.unit || items.find(i => i.id === stock.item_id)?.unit || 'шт';
                          return (
                            <span style={{ fontWeight: 'bold', color: available > 0 ? 'green' : 'red' }}>
                              {available} {unit}
                            </span>
                          );
                        })()}
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      {(() => {
                        const status = getStockStatus(stock);
                        return <Tag color={status.color}>{status.text}</Tag>;
                      })()}
                    </div>
                  </div>
                </div>
                
                {/* Кнопки действий внизу элемента */}
                <div style={{ 
                  display: 'flex', 
                  flexWrap: 'wrap',
                  gap: 8,
                  justifyContent: 'flex-end',
                  marginTop: 12,
                  paddingTop: 12,
                  borderTop: '1px solid #f0f0f0'
                }}>
                  <Button 
                    type="text" 
                    icon={<EditOutlined />} 
                    size="small"
                    style={{ 
                      fontSize: '12px',
                      padding: '4px 8px',
                      minWidth: 'auto',
                      height: '32px'
                    }}
                    onClick={() => handleEdit(stock)}
                  >
                    Изменить
                  </Button>
                  <Popconfirm
                    title="Удалить остаток?"
                    description="Это действие нельзя отменить."
                    onConfirm={() => handleDelete(stock.id)}
                    okText="Да"
                    cancelText="Нет"
                  >
                    <Button 
                      type="text" 
                      danger 
                      icon={<DeleteOutlined />}
                      size="small"
                      style={{ 
                        fontSize: '12px',
                        padding: '4px 8px',
                        minWidth: 'auto',
                        height: '32px'
                      }}
                    >
                      Удалить
                    </Button>
                  </Popconfirm>
                </div>
              </List.Item>
            )}
          />
        ) : (
          // Десктопная версия - таблица
          <Table
            columns={columns}
            dataSource={stocks}
            rowKey="id"
            loading={loading}
            pagination={{
              pageSize: 100,
              showSizeChanger: true,
              showQuickJumper: true,
              pageSizeOptions: ['100', '200', '500', '800', '1000'],
              showTotal: (total) => `Всего: ${total}`,
            }}
            onChange={handleTableChange}
          />
        )}

        {/* Drawer для детального просмотра на мобильных */}
        <Drawer
          title={
            <div style={{ 
              display: 'flex', 
              alignItems: 'center', 
              gap: 8,
              minHeight: 'auto',
              padding: '8px 0'
            }}>
              <div style={{ 
                flex: 1,
                minWidth: 0,
                overflow: 'hidden'
              }}>
                <div style={{ 
                  fontSize: 16, 
                  fontWeight: 'bold',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  {selectedStock?.item?.name || items.find(i => i.id === selectedStock?.item_id)?.name || `ID ${selectedStock?.item_id}`}
                </div>
                <div style={{ 
                  fontSize: 12, 
                  color: '#999',
                  whiteSpace: 'nowrap',
                  overflow: 'hidden',
                  textOverflow: 'ellipsis'
                }}>
                  Остатки на складах
                </div>
              </div>
            </div>
          }
          placement="right"
          onClose={() => setDetailDrawerVisible(false)}
          open={detailDrawerVisible}
          width="100%"
          styles={{
            header: { 
              padding: '12px 16px',
              minHeight: 'auto',
              borderBottom: '1px solid #f0f0f0'
            },
            body: { 
              padding: '16px',
              paddingBottom: '80px'
            }
          }}
        >
          {selectedStock && (
            <div>
              {/* Основная информация */}
              <div style={{ marginBottom: 24 }}>
                <div style={{ marginBottom: 16 }}>
                  <span style={{ fontSize: 14, fontWeight: 'bold', marginBottom: 8, display: 'block' }}>
                    Основная информация:
                  </span>
                  <div style={{ fontSize: 14, color: '#666' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      🆔 ID: {selectedStock.id}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      📦 Товар: {selectedStock.item?.name || items.find(i => i.id === selectedStock.item_id)?.name || `ID ${selectedStock.item_id}`}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      🏠 Склад: {selectedStock.warehouse?.name || warehouses.find(w => w.id === selectedStock.warehouse_id)?.name || `ID ${selectedStock.warehouse_id}`}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      🏷️ Категория: {(() => {
                        const category = selectedStock.item?.category || items.find(i => i.id === selectedStock.item_id)?.category;
                        const type = (category as any)?.category_type?.type;
                        const color = type === 'inventory' ? 'blue' : type === 'equipment' ? 'green' : 'default';
                        return <Tag color={color}>{category?.name || '-'}</Tag>;
                      })()}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      📊 Количество: {(() => {
                        const status = getStockStatus(selectedStock);
                        const unit = selectedStock.item?.unit || items.find(i => i.id === selectedStock.item_id)?.unit || 'шт';
                        return (
                          <span style={{ fontWeight: 'bold', color: status.color }}>
                            {selectedStock.quantity} {unit}
                          </span>
                        );
                      })()}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      🔒 Зарезервировано: {(() => {
                        const unit = selectedStock.item?.unit || items.find(i => i.id === selectedStock.item_id)?.unit || 'шт';
                        return `${selectedStock.reserved_quantity} ${unit}`;
                      })()}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      ✅ Доступно: {(() => {
                        const available = selectedStock.quantity - selectedStock.reserved_quantity;
                        const unit = selectedStock.item?.unit || items.find(i => i.id === selectedStock.item_id)?.unit || 'шт';
                        return (
                          <span style={{ fontWeight: 'bold', color: available > 0 ? 'green' : 'red' }}>
                            {available} {unit}
                          </span>
                        );
                      })()}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      {(() => {
                        const status = getStockStatus(selectedStock);
                        return <Tag color={status.color}>{status.text}</Tag>;
                      })()}
                    </div>
                  </div>
                </div>
              </div>

              {/* Действия */}
              <div style={{ 
                position: 'fixed', 
                bottom: 0, 
                left: 0, 
                right: 0, 
                background: 'white', 
                padding: '12px 16px',
                borderTop: '1px solid #f0f0f0',
                display: 'flex',
                flexDirection: 'column',
                gap: 8,
                zIndex: 1000,
                boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.1)'
              }}>
                <Button 
                  icon={<EditOutlined />} 
                  style={{ 
                    width: '100%',
                    height: '44px',
                    fontSize: '16px'
                  }}
                  onClick={() => {
                    setDetailDrawerVisible(false);
                    handleEdit(selectedStock);
                  }}
                >
                  Изменить
                </Button>
                <Popconfirm
                  title="Удалить остаток?"
                  description="Это действие нельзя отменить."
                  onConfirm={() => {
                    setDetailDrawerVisible(false);
                    handleDelete(selectedStock.id);
                  }}
                  okText="Да"
                  cancelText="Нет"
                >
                  <Button 
                    danger 
                    icon={<DeleteOutlined />}
                    style={{ 
                      width: '100%',
                      height: '44px',
                      fontSize: '16px'
                    }}
                  >
                    Удалить
                  </Button>
                </Popconfirm>
              </div>
            </div>
          )}
        </Drawer>

        <Modal
          title={editingStock ? 'Редактировать остаток' : 'Создать остаток'}
          open={modalVisible}
          onCancel={() => setModalVisible(false)}
          footer={null}
          width={isMobile ? '100%' : 600}
          style={isMobile ? { margin: 16, maxWidth: 'calc(100vw - 32px)' } : {}}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
          >
            <Form.Item
              name="warehouse_id"
              label="Склад"
              rules={[{ required: true, message: 'Выберите склад' }]}
            >
              <Select placeholder="Выберите склад">
                {warehouses.map(warehouse => (
                  <Option key={warehouse.id} value={warehouse.id}>
                    {warehouse.name}
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="item_id"
              label="Товар"
              rules={[{ required: true, message: 'Выберите товар' }]}
            >
              <Select placeholder="Выберите товар">
                {items.map(item => (
                  <Option key={item.id} value={item.id}>
                    {item.name} ({item.category?.name})
                  </Option>
                ))}
              </Select>
            </Form.Item>

            <Form.Item
              name="quantity"
              label="Количество"
              rules={[{ required: true, message: 'Введите количество' }]}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="Введите количество"
                min={0}
              />
            </Form.Item>

            <Form.Item
              name="reserved_quantity"
              label="Зарезервировано"
              rules={[{ required: true, message: 'Введите зарезервированное количество' }]}
              initialValue={0}
            >
              <InputNumber
                style={{ width: '100%' }}
                placeholder="Введите зарезервированное количество"
                min={0}
              />
            </Form.Item>

            <Form.Item>
              <Space size={isMobile ? 'small' : 'middle'}>
                <Button type="primary" htmlType="submit" size={isMobile ? 'small' : 'middle'}>
                  {editingStock ? 'Обновить' : 'Создать'}
                </Button>
                <Button onClick={() => setModalVisible(false)} size={isMobile ? 'small' : 'middle'}>
                  Отмена
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>
      </Card>
    </div>
  );
};

export default WarehouseStocks; 