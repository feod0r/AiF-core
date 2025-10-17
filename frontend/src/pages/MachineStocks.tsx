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
  Collapse,
  Badge,
  Switch,
} from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, WarningOutlined, RobotOutlined, DownOutlined, RightOutlined } from '@ant-design/icons';
import { 
  machineStocksApi, 
  machinesApi, 
  itemsApi,
  itemCategoriesApi
} from '../services/api';
import { 
  MachineStock, 
  Machine, 
  Item, 
  ItemCategory
} from '../types';
import dayjs from 'dayjs';

const { Title } = Typography;
const { Option } = Select;
const { Panel } = Collapse;

// Интерфейс для группированных данных
interface GroupedMachineStocks {
  machine: Machine;
  stocks: MachineStock[];
  totalItems: number;
  lowStockItems: number;
  totalQuantity: number;
}

const MachineStocks: React.FC = () => {
  const [stocks, setStocks] = useState<MachineStock[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [items, setItems] = useState<Item[]>([]);
  const [categories, setCategories] = useState<ItemCategory[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingStock, setEditingStock] = useState<MachineStock | null>(null);
  const [isMobile, setIsMobile] = useState(false);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedStock, setSelectedStock] = useState<MachineStock | null>(null);
  // Новое состояние для группировки
  const [groupByMachine, setGroupByMachine] = useState(false);
  const [expandedMachines, setExpandedMachines] = useState<string[]>([]);
  const [groupedData, setGroupedData] = useState<any[]>([]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 50,
    total: 0,
  });
  const [filters, setFilters] = useState({
    machine_id: undefined as number | undefined,
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

  const fetchStocks = async (page = 1, pageSize = 50, filterParams = {}) => {
    setLoading(true);
    try {
      const params = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...filterParams
      };
      
      // Получаем данные и количество одновременно
      const [data, countData] = await Promise.all([
        machineStocksApi.getList(params),
        machineStocksApi.getCount(filterParams)
      ]);
      
      setStocks(data);
      setPagination({
        current: page,
        pageSize,
        total: countData.count,
      });
    } catch (error) {
      message.error('Ошибка при загрузке остатков');
    } finally {
      setLoading(false);
    }
  };

  const fetchGroupedStocks = async (filterParams = {}) => {
    setLoading(true);
    try {
      const params = {
        ...filterParams
      };
      
      const data = await machineStocksApi.getGroupedByMachines(params);
      setGroupedData(data);
    } catch (error) {
      message.error('Ошибка при загрузке группированных остатков');
    } finally {
      setLoading(false);
    }
  };

  const fetchMachines = async () => {
    try {
      const data = await machinesApi.getList();
      setMachines(data.data || data);
    } catch (error) {
      message.error('Ошибка при загрузке автоматов');
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
    fetchMachines();
    fetchItems();
    fetchCategories();
  }, []);

  useEffect(() => {
    if (groupByMachine) {
      fetchGroupedStocks(filters);
    } else {
      fetchStocks(pagination.current, pagination.pageSize, filters);
    }
  }, [groupByMachine, filters]);

  const handleCreate = () => {
    setEditingStock(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: MachineStock) => {
    setEditingStock(record);
    form.setFieldsValue({
      ...record,
      machine_id: record.machine_id || record.machine?.id,
      item_id: record.item_id || record.item?.id,
      quantity: record.quantity.toString(),
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await machineStocksApi.delete(id);
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
      };

      if (editingStock) {
        await machineStocksApi.update(editingStock.id, submitData);
        message.success('Остаток обновлен');
      } else {
        await machineStocksApi.create(submitData);
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
    // Сбрасываем на первую страницу при изменении фильтров
    if (groupByMachine) {
      fetchGroupedStocks(newFilters);
    } else {
      fetchStocks(1, pagination.pageSize, newFilters);
    }
  };

  // Функция для группировки остатков по автоматам
  const groupStocksByMachine = (): GroupedMachineStocks[] => {
    const grouped = new Map<number, GroupedMachineStocks>();
    
    stocks.forEach(stock => {
      const machineId = stock.machine_id;
      const machine = stock.machine || machines.find(m => m.id === machineId);
      
      if (!machine) return;
      
      if (!grouped.has(machineId)) {
        grouped.set(machineId, {
          machine,
          stocks: [],
          totalItems: 0,
          lowStockItems: 0,
          totalQuantity: 0,
        });
      }
      
      const group = grouped.get(machineId)!;
      group.stocks.push(stock);
      group.totalItems++;
      group.totalQuantity += Number(stock.quantity || 0);
      
      // Используем максимальное значение между min_quantity автомата и min_stock товара
      const effectiveMinQuantity = Math.max(stock.min_quantity, stock.item?.min_stock || 0);
      if (stock.quantity <= effectiveMinQuantity) {
        group.lowStockItems++;
      }
    });
    
    return Array.from(grouped.values()).sort((a, b) => 
      a.machine.name.localeCompare(b.machine.name)
    );
  };



  const getStockStatus = (stock: MachineStock) => {
    if (!stock.item) return { color: 'default', text: 'Нет данных' };
    
    // Используем максимальное значение между min_quantity автомата и min_stock товара
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

  const columns = [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Автомат',
      dataIndex: ['machine', 'name'],
      key: 'machine',
      render: (_: any, record: MachineStock) => record.machine?.name || machines.find(m => m.id === record.machine_id)?.name || `ID ${record.machine_id}`,
    },
    {
      title: 'Терминал',
      key: 'terminal',
      render: (_: any, record: MachineStock) => record.machine?.terminal?.name || '-',
    },
    {
      title: 'Товар',
      dataIndex: ['item', 'name'],
      key: 'item',
      render: (_: any, record: MachineStock) => record.item?.name || items.find(i => i.id === record.item_id)?.name || `ID ${record.item_id}`,
    },
    {
      title: 'Категория',
      key: 'category',
      render: (_: any, record: MachineStock) => {
        const categoryName = record.item?.category?.name || '-';
        const typeName = (record.item?.category as any)?.category_type?.name;
        const color = typeName === 'inventory' ? 'blue' : typeName === 'equipment' ? 'green' : 'default';
        return <Tag color={color}>{categoryName}</Tag>;
      },
    },
    {
      title: 'Количество',
      dataIndex: 'quantity',
      key: 'quantity',
      render: (quantity: number, record: MachineStock) => {
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
      title: 'Статус',
      key: 'status',
      render: (_: any, record: MachineStock) => {
        const status = getStockStatus(record);
        return <Tag color={status.color}>{status.text}</Tag>;
      },
    },
    {
      title: 'Последнее обновление',
      dataIndex: 'last_updated',
      key: 'last_updated',
      render: (date: string) => dayjs(date).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      render: (_: any, record: MachineStock) => (
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
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <Title level={isMobile ? 3 : 2} style={{ 
            margin: 0,
            fontSize: isMobile ? 18 : undefined,
            lineHeight: isMobile ? 1.4 : undefined
          }}>
            <RobotOutlined /> Остатки в автоматах
          </Title>
          {!isMobile && (
            <Space>
              <span style={{ fontSize: 14, color: '#666' }}>Группировать по автоматам:</span>
              <Switch
                checked={groupByMachine}
                onChange={setGroupByMachine}
                size="small"
              />
            </Space>
          )}
        </div>
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
          <Col span={isMobile ? 12 : 8}>
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
          <Col span={isMobile ? 12 : 8}>
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
          <Col span={isMobile ? 24 : 8}>
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
              <Form.Item label="Группировать по автоматам" style={{ marginBottom: 8 }}>
                <Switch
                  checked={groupByMachine}
                  onChange={setGroupByMachine}
                  size="small"
                />
              </Form.Item>
              
              <Form.Item label="Автомат" style={{ marginBottom: 8 }}>
                <Select
                  placeholder="Выберите автомат"
                  allowClear
                  value={filters.machine_id}
                  onChange={(value) => handleFilterChange('machine_id', value)}
                  size="small"
                  style={{ width: '100%' }}
                >
                  {machines.map(machine => (
                    <Option key={machine.id} value={machine.id}>
                      {machine.name}
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
                <Form.Item label="Автомат">
                  <Select
                    placeholder="Выберите автомат"
                    allowClear
                    value={filters.machine_id}
                    onChange={(value) => handleFilterChange('machine_id', value)}
                  >
                    {machines.map(machine => (
                      <Option key={machine.id} value={machine.id}>
                        {machine.name}
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

        {groupByMachine ? (
          // Группированное отображение
          <div>
            {groupedData.map((group) => (
              <Card 
                key={group.machine.id} 
                style={{ marginBottom: 16 }}
                size={isMobile ? 'small' : 'default'}
              >
                <Collapse
                  size={isMobile ? 'small' : 'large'}
                  activeKey={expandedMachines}
                  onChange={(keys) => setExpandedMachines(keys as string[])}
                  ghost
                >
                  <Panel
                    header={
                      <div style={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        width: '100%',
                        paddingRight: 24
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                          <RobotOutlined style={{ color: '#1890ff', fontSize: 16 }} />
                          <span style={{ fontWeight: 'bold', fontSize: isMobile ? 14 : 16 }}>
                            {group.machine.name}
                          </span>
                          {group.machine.terminal && (
                            <Tag color="blue">
                              {group.machine.terminal.name}
                            </Tag>
                          )}
                        </div>
                        <div style={{ display: 'flex', gap: isMobile ? 8 : 16, alignItems: 'center' }}>
                          <Badge count={group.total_items} color="#1890ff" />
                          {group.low_stock_items > 0 && (
                            <Badge count={group.low_stock_items} color="#ff4d4f" />
                          )}
                          <span style={{ fontSize: isMobile ? 12 : 14, color: '#666' }}>
                            {group.total_quantity} шт
                          </span>
                        </div>
                      </div>
                    }
                    key={group.machine.id.toString()}
                  >
                    {isMobile ? (
                      // Мобильная версия для группированного отображения
                      <List
                        dataSource={group.stocks}
                        renderItem={(stock: any) => (
                          <List.Item
                            style={{ 
                              padding: '8px 0',
                              borderBottom: '1px solid #f0f0f0'
                            }}
                          >
                            <div style={{ width: '100%' }}>
                              <div style={{ 
                                display: 'flex', 
                                justifyContent: 'space-between', 
                                alignItems: 'center',
                                marginBottom: 8
                              }}>
                                <span style={{ fontWeight: 'bold' }}>
                                  {stock.item?.name || `ID ${stock.item_id}`}
                                </span>
                                {(() => {
                                  const effectiveMinQuantity = Math.max(stock.min_quantity, stock.item?.min_stock || 0);
                                  const isLowStock = stock.quantity <= effectiveMinQuantity;
                                  const status = isLowStock ? { color: 'red', text: 'Критически мало' } : 
                                                stock.quantity <= effectiveMinQuantity * 2 ? { color: 'orange', text: 'Мало' } : 
                                                { color: 'green', text: 'Нормально' };
                                  const unit = stock.item?.unit || 'шт';
                                  return (
                                    <span style={{ fontWeight: 'bold', color: status.color }}>
                                      {stock.quantity} {unit}
                                    </span>
                                  );
                                })()}
                              </div>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                <div>
                                  {(() => {
                                    const categoryName = stock.item?.category?.name || '-';
                                    const typeName = stock.item?.category?.category_type?.name;
                                    const color = typeName === 'inventory' ? 'blue' : typeName === 'equipment' ? 'green' : 'default';
                                    return <Tag color={color}>{categoryName}</Tag>;
                                  })()}
                                   {(() => {
                                     // Используем максимальное значение между min_quantity автомата и min_stock товара
                                     const effectiveMinQuantity = Math.max(stock.min_quantity, stock.item?.min_stock || 0);
                                     const isLowStock = stock.quantity <= effectiveMinQuantity;
                                     const status = isLowStock ? { color: 'red', text: 'Критически мало' } : 
                                                   stock.quantity <= effectiveMinQuantity * 2 ? { color: 'orange', text: 'Мало' } : 
                                                   { color: 'green', text: 'Нормально' };
                                     return <Tag color={status.color}>{status.text}</Tag>;
                                   })()}
                                </div>
                                <Space size="small">
                                  <Button 
                                    type="text" 
                                    icon={<EditOutlined />} 
                                    size="small"
                                    onClick={() => handleEdit(stock)}
                                  />
                                  <Popconfirm
                                    title="Удалить остаток?"
                                    onConfirm={() => handleDelete(stock.id)}
                                    okText="Да"
                                    cancelText="Нет"
                                  >
                                    <Button 
                                      type="text" 
                                      danger 
                                      icon={<DeleteOutlined />}
                                      size="small"
                                    />
                                  </Popconfirm>
                                </Space>
                              </div>
                            </div>
                          </List.Item>
                        )}
                      />
                    ) : (
                      // Десктопная версия для группированного отображения
                      <Table
                        columns={columns.filter(col => col.key !== 'machine' && col.key !== 'terminal')} // Исключаем колонки автомата
                        dataSource={group.stocks}
                        rowKey="id"
                        pagination={false}
                        size="small"
                      />
                    )}
                  </Panel>
                </Collapse>
              </Card>
            ))}
          </div>
        ) : isMobile ? (
          // Мобильная версия - список (обычный режим)
          <List
            dataSource={stocks}
            loading={loading}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showQuickJumper: true,
              defaultPageSize: 50,
              pageSizeOptions: ['50', '100', '200', '300', '500'],
              showTotal: (total, range) => `${range[0]}-${range[1]} из ${total}`,
              onChange: (page, pageSize) => {
                fetchStocks(page, pageSize, filters);
              },
            }}
            renderItem={(stock: MachineStock) => (
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
                        Автомат:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {stock.machine?.name || machines.find(m => m.id === stock.machine_id)?.name || `ID ${stock.machine_id}`}
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Терминал:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {stock.machine?.terminal?.name || '-'}
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Категория:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {(() => {
                          const categoryName = stock.item?.category?.name || '-';
                          const typeName = (stock.item?.category as any)?.category_type?.name;
                          const color = typeName === 'inventory' ? 'blue' : typeName === 'equipment' ? 'green' : 'default';
                          return <Tag color={color}>{categoryName}</Tag>;
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
                        Обновлено:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {dayjs(stock.last_updated).format('DD.MM.YYYY HH:mm')}
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
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: true,
              showQuickJumper: true,
              defaultPageSize: 50,
              pageSizeOptions: ['50', '100', '200', '300', '500'],
              showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} записей`,
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
                  Остатки в автоматах
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
                      🤖 Автомат: {selectedStock.machine?.name || machines.find(m => m.id === selectedStock.machine_id)?.name || `ID ${selectedStock.machine_id}`}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      💳 Терминал: {selectedStock.machine?.terminal?.name || '-'}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      📦 Товар: {selectedStock.item?.name || items.find(i => i.id === selectedStock.item_id)?.name || `ID ${selectedStock.item_id}`}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      🏷️ Категория: {(() => {
                        const categoryName = selectedStock.item?.category?.name || '-';
                        const typeName = (selectedStock.item?.category as any)?.category_type?.name;
                        const color = typeName === 'inventory' ? 'blue' : typeName === 'equipment' ? 'green' : 'default';
                        return <Tag color={color}>{categoryName}</Tag>;
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
                      ⏰ Обновлено: {dayjs(selectedStock.last_updated).format('DD.MM.YYYY HH:mm')}
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
              name="machine_id"
              label="Автомат"
              rules={[{ required: true, message: 'Выберите автомат' }]}
            >
              <Select placeholder="Выберите автомат">
                {machines.map(machine => (
                  <Option key={machine.id} value={machine.id}>
                    {machine.name}
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

export default MachineStocks; 