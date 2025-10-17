import React, { useState, useEffect, useMemo } from 'react';
import { SwapOutlined, CheckOutlined, PlayCircleOutlined, CloseOutlined, PlusOutlined } from '@ant-design/icons';
import { Tag, message, Button, Form, Input, Select, InputNumber, Card, DatePicker, Modal } from 'antd';
import GenericDataTable from '../components/GenericDataTable';
import { 
  inventoryMovementsApi, 
  itemsApi, 
  warehousesApi, 
  machinesApi,
  counterpartiesApi,
  warehouseStocksApi,
  machineStocksApi,
  itemCategoriesApi,
  referenceTablesApi
} from '../services/api';
import { 
  InventoryMovement, 
  Item, 
  Warehouse, 
  Machine, 
  Counterparty,
  ItemCategory
} from '../types';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

interface MovementItem {
  id: number;
  item_id: number;
  quantity: number;
  price: number;
  amount: number;
  description?: string;
}

const InventoryMovementsNew: React.FC = () => {
  const [items, setItems] = useState<Item[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [counterparties, setCounterparties] = useState<Counterparty[]>([]);
  const [movementItems, setMovementItems] = useState<MovementItem[]>([]);
  const [selectedMovementType, setSelectedMovementType] = useState<string>('');
  const [formValues, setFormValues] = useState<any>({});
  const [isMobile, setIsMobile] = useState(false);
  const [warehouseStocks, setWarehouseStocks] = useState<any[]>([]);
  const [machineStocks, setMachineStocks] = useState<any[]>([]);
  
  // Состояние для модального окна добавления товара
  const [isAddItemModalVisible, setIsAddItemModalVisible] = useState(false);
  const [itemCategories, setItemCategories] = useState<ItemCategory[]>([]);
  const [addItemForm] = Form.useForm();
  const [currentItemIndexForAdd, setCurrentItemIndexForAdd] = useState<number | null>(null);
  
  // Состояние для модального окна добавления категории
  const [isAddCategoryModalVisible, setIsAddCategoryModalVisible] = useState(false);
  const [categoryTypes, setCategoryTypes] = useState<any[]>([]);
  const [addCategoryForm] = Form.useForm();

  // Определяем мобильное устройство
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Загрузка справочных данных
  useEffect(() => {
    const loadReferenceData = async () => {
      try {
        const [itemsData, warehousesData, machinesData, counterpartiesData, categoriesData, categoryTypesData] = await Promise.all([
          itemsApi.getList(),
          warehousesApi.getList(),
          machinesApi.getList(),
          counterpartiesApi.getList(),
          itemCategoriesApi.getList({ include_children: true }),
          referenceTablesApi.getList('item_category_types'),
        ]);
        
        setItems(itemsData);
        setWarehouses(warehousesData);
        setMachines(machinesData.data || machinesData);
        setCounterparties(counterpartiesData);
        setItemCategories(categoriesData);
        setCategoryTypes(categoryTypesData);
      } catch (error) {
        message.error('Ошибка при загрузке справочных данных');
        console.error(error);
      }
    };

    loadReferenceData();
  }, []);

  // Загрузка остатков товаров при изменении места отправления
  useEffect(() => {
    const loadStocks = async () => {
      try {
        // Загружаем остатки для склада отправления
        if (formValues.from_warehouse_id) {
          const stocks = await warehouseStocksApi.getByWarehouse(formValues.from_warehouse_id);
          console.log('Warehouse stocks loaded:', stocks);
          setWarehouseStocks(stocks);
          setMachineStocks([]);
        }
        // Загружаем остатки для автомата отправления
        else if (formValues.from_machine_id) {
          const stocks = await machineStocksApi.getByMachine(formValues.from_machine_id);
          console.log('Machine stocks loaded:', stocks);
          setMachineStocks(stocks);
          setWarehouseStocks([]);
        }
        // Очищаем остатки если нет места отправления
        else {
          setWarehouseStocks([]);
          setMachineStocks([]);
        }
      } catch (error) {
        console.error('Ошибка при загрузке остатков:', error);
        // Не показываем ошибку пользователю, просто логируем
      }
    };

    // Загружаем остатки только для операций расхода
    const needsStockFiltering = ['issue', 'sale', 'transfer', 'load_machine', 'unload_machine'].includes(selectedMovementType);
    if (needsStockFiltering && (formValues.from_warehouse_id || formValues.from_machine_id)) {
      loadStocks();
    } else {
      setWarehouseStocks([]);
      setMachineStocks([]);
    }
  }, [formValues.from_warehouse_id, formValues.from_machine_id, selectedMovementType]);

  // Логика отображения полей на основе типа операции
  const shouldShowFromWarehouse = () => {
    if (['transfer', 'issue', 'sale'].includes(selectedMovementType)) {
      // Для этих типов показываем склад отправления только если не выбран автомат отправления
      return !formValues.from_machine_id;
    }
    return ['load_machine'].includes(selectedMovementType);
  };

  const shouldShowToWarehouse = () => {
    if (selectedMovementType === 'receipt') {
      // Для поступления показываем склад назначения только если не выбран автомат назначения
      return !formValues.to_machine_id;
    }
    if (['transfer', 'adjustment'].includes(selectedMovementType)) {
      // Для перемещения и корректировки показываем склад назначения только если не выбран автомат назначения
      return !formValues.to_machine_id;
    }
    return ['unload_machine'].includes(selectedMovementType);
  };

  const shouldShowFromMachine = () => {
    if (['transfer', 'issue', 'sale'].includes(selectedMovementType)) {
      // Для этих типов показываем автомат отправления только если не выбран склад отправления
      return !formValues.from_warehouse_id;
    }
    return ['unload_machine'].includes(selectedMovementType);
  };

  const shouldShowToMachine = () => {
    if (selectedMovementType === 'receipt') {
      // Для поступления показываем автомат назначения только если не выбран склад назначения
      return !formValues.to_warehouse_id;
    }
    if (['transfer', 'adjustment'].includes(selectedMovementType)) {
      // Для перемещения и корректировки показываем автомат назначения только если не выбран склад назначения
      return !formValues.to_warehouse_id;
    }
    return ['load_machine'].includes(selectedMovementType);
  };

  const shouldShowCounterparty = () => {
    if (selectedMovementType === 'receipt' || selectedMovementType === 'sale') {
      return true;
    }
    if (selectedMovementType === 'load_machine') {
      // Для загрузки автомата показываем контрагента только если не выбран склад отправления
      return !formValues.from_warehouse_id;
    }
    return false;
  };

  // Функции для работы со статусами
  const getStatusColor = (status: any) => {
    if (!status) return 'default';
    const statusName = status.name || 'Неизвестно';
    switch (statusName.toLowerCase()) {
      case 'draft':
      case 'черновик':
        return 'orange';
      case 'approved':
      case 'утвержден':
        return 'blue';
      case 'executed':
      case 'выполнен':
        return 'green';
      case 'cancelled':
      case 'отменен':
        return 'red';
      default:
        return 'default';
    }
  };

  const getStatusLabel = (status: any) => {
    if (!status) return 'Неизвестно';
    const statusName = status.name || 'Неизвестно';
    switch (statusName.toLowerCase()) {
      case 'draft':
        return 'Черновик';
      case 'approved':
        return 'Утвержден';
      case 'executed':
        return 'Выполнен';
      case 'cancelled':
        return 'Отменен';
      default:
        return statusName;
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'receipt': return 'green';
      case 'issue': return 'red';
      case 'transfer': return 'blue';
      case 'sale': return 'orange';
      case 'adjustment': return 'purple';
      case 'load_machine': return 'cyan';
      case 'unload_machine': return 'magenta';
      default: return 'default';
    }
  };

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'receipt': return 'Поступление';
      case 'issue': return 'Выдача';
      case 'transfer': return 'Перемещение';
      case 'sale': return 'Продажа';
      case 'adjustment': return 'Корректировка';
      case 'load_machine': return 'Загрузка автомата';
      case 'unload_machine': return 'Выгрузка автомата';
      default: return type;
    }
  };

  // Обработчики изменения полей формы
  const handleMovementTypeChange = (value: string) => {
    setSelectedMovementType(value);
    setMovementItems([]);
    
    // Очищаем взаимоисключающие поля
    const clearedValues = {
      ...formValues,
      movement_type: value,
      from_warehouse_id: undefined,
      to_warehouse_id: undefined,
      from_machine_id: undefined,
      to_machine_id: undefined,
      counterparty_id: undefined,
    };
    setFormValues(clearedValues);
  };

  const handleFieldChange = (fieldName: string, value: any) => {
    let newValues = { ...formValues, [fieldName]: value };

    // Логика взаимоисключающих полей для всех типов операций
    if (['transfer', 'issue', 'sale'].includes(selectedMovementType)) {
      // Для перемещения, выдачи и продажи - отправление может быть либо склад, либо автомат
      if (fieldName === 'from_warehouse_id' && value) {
        newValues.from_machine_id = undefined;
      } else if (fieldName === 'from_machine_id' && value) {
        newValues.from_warehouse_id = undefined;
      }
    }

    if (['transfer', 'adjustment'].includes(selectedMovementType)) {
      // Для перемещения и корректировки - назначение может быть либо склад, либо автомат
      if (fieldName === 'to_warehouse_id' && value) {
        newValues.to_machine_id = undefined;
      } else if (fieldName === 'to_machine_id' && value) {
        newValues.to_warehouse_id = undefined;
      }
    }

    if (selectedMovementType === 'receipt') {
      // Для поступления - назначение может быть либо склад, либо автомат
      if (fieldName === 'to_warehouse_id' && value) {
        newValues.to_machine_id = undefined;
      } else if (fieldName === 'to_machine_id' && value) {
        newValues.to_warehouse_id = undefined;
      }
    }

    if (selectedMovementType === 'load_machine') {
      // Для загрузки автомата - отправление может быть либо склад, либо контрагент
      if (fieldName === 'from_warehouse_id' && value) {
        newValues.counterparty_id = undefined;
      } else if (fieldName === 'counterparty_id' && value) {
        newValues.from_warehouse_id = undefined;
      }
    }

    setFormValues(newValues);
  };

  // Работа с товарами в операции
  const addMovementItem = () => {
    const newItem: MovementItem = {
      id: Date.now(),
      item_id: 0,
      quantity: 0,
      price: 0,
      amount: 0,
      description: '',
    };
    setMovementItems([...movementItems, newItem]);
  };

  const removeMovementItem = (index: number) => {
    const newItems = movementItems.filter((_, i) => i !== index);
    setMovementItems(newItems);
  };

  const updateMovementItem = (index: number, field: string, value: any) => {
    const newItems = [...movementItems];
    newItems[index] = { ...newItems[index], [field]: value };
    
    // Автоматически рассчитываем сумму
    if (field === 'quantity' || field === 'price') {
      const quantity = field === 'quantity' ? value : newItems[index].quantity;
      const price = field === 'price' ? value : newItems[index].price;
      newItems[index].amount = (quantity || 0) * (price || 0);
    }
    
    setMovementItems(newItems);
  };

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
      addItemForm.setFieldsValue({ category_id: newCategory.id });

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

  // Функции для работы с модальным окном добавления товара
  const handleOpenAddItemModal = (itemIndex: number) => {
    setCurrentItemIndexForAdd(itemIndex);
    setIsAddItemModalVisible(true);
    addItemForm.resetFields();
  };

  const handleCloseAddItemModal = () => {
    setIsAddItemModalVisible(false);
    setCurrentItemIndexForAdd(null);
    addItemForm.resetFields();
  };

  const handleCreateItem = async () => {
    try {
      const values = await addItemForm.validateFields();
      
      // Создаем товар
      const newItem = await itemsApi.create({
        name: values.name,
        sku: values.sku,
        category_id: values.category_id,
        description: values.description || '',
        unit: values.unit || 'шт',
        weight: values.weight,
        dimensions: values.dimensions,
        barcode: values.barcode,
        min_stock: values.min_stock || 0,
        max_stock: values.max_stock,
        is_active: true,
        start_date: new Date().toISOString(),
        end_date: '2099-12-31T23:59:59Z',
      });

      message.success(`Товар "${newItem.name}" успешно создан`);

      // Обновляем список товаров
      const updatedItems = await itemsApi.getList();
      setItems(updatedItems);

      // Если есть индекс текущей позиции, автоматически выбираем созданный товар
      if (currentItemIndexForAdd !== null) {
        updateMovementItem(currentItemIndexForAdd, 'item_id', newItem.id);
      }

      handleCloseAddItemModal();
    } catch (error: any) {
      if (error.errorFields) {
        // Ошибка валидации формы
        console.error('Validation error:', error);
      } else {
        // API ошибка
        console.error('API error:', error);
        message.error('Ошибка при создании товара');
      }
    }
  };

  // Получаем отфильтрованный список товаров на основе остатков
  const getFilteredItems = useMemo(() => {
    // Определяем, нужна ли фильтрация по остаткам
    const needsStockFiltering = ['issue', 'sale', 'transfer', 'load_machine', 'unload_machine'].includes(selectedMovementType);
    const hasSource = formValues.from_warehouse_id || formValues.from_machine_id;
    
    // Если не нужна фильтрация - возвращаем все товары
    if (!needsStockFiltering || !hasSource) {
      return items;
    }

    // Получаем список ID товаров в наличии
    const availableItemIds = new Set<number>();
    
    if (formValues.from_warehouse_id && warehouseStocks.length > 0) {
      console.log('Filtering by warehouse stocks:', warehouseStocks.length);
      warehouseStocks.forEach(stock => {
        // Поддерживаем разные варианты структуры данных
        const itemId = stock.item_id || stock.itemId || (stock.item && stock.item.id);
        const quantity = typeof stock.quantity === 'string' ? parseFloat(stock.quantity) : stock.quantity;
        
        if (quantity > 0 && itemId) {
          availableItemIds.add(itemId);
        }
      });
    } else if (formValues.from_machine_id && machineStocks.length > 0) {
      console.log('Filtering by machine stocks:', machineStocks.length);
      machineStocks.forEach(stock => {
        // Поддерживаем разные варианты структуры данных
        const itemId = stock.item_id || stock.itemId || (stock.item && stock.item.id);
        const quantity = typeof stock.quantity === 'string' ? parseFloat(stock.quantity) : stock.quantity;
        
        if (quantity > 0 && itemId) {
          availableItemIds.add(itemId);
        }
      });
    }

    console.log('Available item IDs:', Array.from(availableItemIds));
    console.log('Total items before filter:', items.length);

    // Фильтруем товары по наличию
    const filtered = items.filter(item => availableItemIds.has(item.id));
    console.log('Filtered items count:', filtered.length);
    
    return filtered;
  }, [items, warehouseStocks, machineStocks, selectedMovementType, formValues.from_warehouse_id, formValues.from_machine_id]);

  // Рендер формы товаров
  const renderMovementItemsForm = () => (
    <div>
             <div style={{ 
         marginBottom: 16, 
         display: 'flex', 
         justifyContent: 'space-between', 
         alignItems: 'center',
         flexDirection: isMobile ? 'column' : 'row',
         gap: isMobile ? 8 : 0
       }}>
         <label style={{ fontWeight: 'bold' }}>Позиции товаров</label>
         <Button 
           type="dashed" 
           onClick={addMovementItem}
           size={isMobile ? 'small' : 'middle'}
           style={{ width: isMobile ? '100%' : 'auto' }}
         >
           Добавить товар
         </Button>
       </div>
      
      {movementItems.map((item, index) => (
        <Card key={item.id} size="small" style={{ marginBottom: 16 }}>
                     <div style={{ 
             display: 'flex', 
             justifyContent: 'space-between', 
             alignItems: 'center', 
             marginBottom: 12,
             flexDirection: isMobile ? 'column' : 'row',
             gap: isMobile ? 8 : 0
           }}>
             <strong>Позиция {index + 1}</strong>
             <Button 
               type="text" 
               danger 
               size={isMobile ? 'small' : 'middle'}
               onClick={() => removeMovementItem(index)}
               style={{ width: isMobile ? '100%' : 'auto' }}
             >
               Удалить
             </Button>
           </div>
          
                     <div style={{ 
             display: 'grid', 
             gridTemplateColumns: isMobile ? '1fr' : '2fr 1fr 1fr 1fr', 
             gap: isMobile ? 8 : 12, 
             marginBottom: 12 
           }}>
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 12 }}>
                Товар *
                {getFilteredItems.length < items.length && (
                  <span style={{ fontSize: 11, color: '#999', marginLeft: 8 }}>
                    (показаны только доступные: {getFilteredItems.length} из {items.length})
                  </span>
                )}
              </label>
              <div style={{ display: 'flex', gap: 8 }}>
                <Select
                  placeholder="Выберите товар"
                  value={item.item_id || undefined}
                  onChange={(value) => updateMovementItem(index, 'item_id', value)}
                  style={{ flex: 1 }}
                  showSearch
                  optionFilterProp="label"
                  filterOption={(input, option) => {
                    const searchText = input.toLowerCase();
                    const labelText = option?.label?.toString().toLowerCase() || '';
                    return labelText.includes(searchText);
                  }}
                  dropdownStyle={{ maxHeight: 300 }}
                  optionLabelProp="label"
                >
                  {getFilteredItems.map(itemOption => (
                    <Option 
                      key={itemOption.id} 
                      value={itemOption.id}
                      label={`${itemOption.name} | ${itemOption.sku}`}
                    >
                      <div style={{ 
                        whiteSpace: 'nowrap', 
                        overflow: 'hidden', 
                        textOverflow: 'ellipsis',
                        maxWidth: '100%'
                      }}>
                        {itemOption.name} | {itemOption.sku}
                      </div>
                    </Option>
                  ))}
                </Select>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={() => handleOpenAddItemModal(index)}
                  title="Добавить новый товар"
                />
              </div>
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 12 }}>Количество *</label>
              <InputNumber
                placeholder="Кол-во"
                value={item.quantity}
                onChange={(value) => updateMovementItem(index, 'quantity', value)}
                min={0.01}
                step={0.01}
                style={{ width: '100%' }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 12 }}>Цена *</label>
              <InputNumber
                placeholder="Цена"
                value={item.price}
                onChange={(value) => updateMovementItem(index, 'price', value)}
                min={0}
                step={0.01}
                style={{ width: '100%' }}
              />
            </div>
            
            <div>
              <label style={{ display: 'block', marginBottom: 4, fontSize: 12 }}>Сумма</label>
              <Input
                value={item.amount ? item.amount.toFixed(2) : '0.00'}
                disabled
                style={{ width: '100%' }}
              />
            </div>
          </div>
          
          <div>
            <label style={{ display: 'block', marginBottom: 4, fontSize: 12 }}>Описание</label>
            <Input
              placeholder="Описание позиции"
              value={item.description}
              onChange={(e) => updateMovementItem(index, 'description', e.target.value)}
            />
          </div>
        </Card>
      ))}
      
      {movementItems.length === 0 && (
        <div style={{ 
          textAlign: 'center', 
          padding: 24, 
          border: '1px dashed #d9d9d9', 
          borderRadius: 6,
          color: '#999'
        }}>
          Нет добавленных товаров
        </div>
      )}
    </div>
  );

  // Функции статусов
  const canApprove = (movement: InventoryMovement) => {
    const statusName = movement.status?.name?.toLowerCase();
    return statusName === 'draft' || statusName === 'черновик';
  };

  const canExecute = (movement: InventoryMovement) => {
    const statusName = movement.status?.name?.toLowerCase();
    return statusName === 'approved' || statusName === 'утвержден';
  };

  const canCancel = (movement: InventoryMovement) => {
    const statusName = movement.status?.name?.toLowerCase();
    return statusName === 'draft' || statusName === 'черновик' || statusName === 'approved' || statusName === 'утвержден';
  };

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'movement_type',
      label: 'Тип движения',
      type: 'select' as const,
      placeholder: 'Выберите тип движения',
      options: [
        { label: 'Поступление', value: 'receipt' },
        { label: 'Продажа', value: 'sale' },
        { label: 'Перемещение', value: 'transfer' },
        { label: 'Корректировка', value: 'adjustment' },
        { label: 'Выдача', value: 'issue' },
        { label: 'Загрузка автомата', value: 'load_machine' },
        { label: 'Выгрузка автомата', value: 'unload_machine' },
      ],
    },
    {
      key: 'status_id',
      label: 'Статус',
      type: 'select' as const,
      placeholder: 'Выберите статус',
      options: [
        { label: 'Черновик', value: 1 },
        { label: 'Утвержден', value: 2 },
        { label: 'Выполнен', value: 3 },
        { label: 'Отменен', value: 4 },
      ],
    },
    {
      key: 'from_warehouse_id',
      label: 'Склад отправления',
      type: 'select' as const,
      placeholder: 'Выберите склад отправления',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        return warehouses.map(warehouse => ({
          label: warehouse.name,
          value: warehouse.id,
        }));
      },
    },
    {
      key: 'to_warehouse_id',
      label: 'Склад назначения',
      type: 'select' as const,
      placeholder: 'Выберите склад назначения',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        return warehouses.map(warehouse => ({
          label: warehouse.name,
          value: warehouse.id,
        }));
      },
    },
    {
      key: 'from_machine_id',
      label: 'Автомат отправления',
      type: 'select' as const,
      placeholder: 'Выберите автомат отправления',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        return machines.map(machine => ({
          label: machine.name,
          value: machine.id,
        }));
      },
    },
    {
      key: 'to_machine_id',
      label: 'Автомат назначения',
      type: 'select' as const,
      placeholder: 'Выберите автомат назначения',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        return machines.map(machine => ({
          label: machine.name,
          value: machine.id,
        }));
      },
    },
    {
      key: 'counterparty_id',
      label: 'Контрагент',
      type: 'select' as const,
      placeholder: 'Выберите контрагента',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        return counterparties.map(counterparty => ({
          label: counterparty.name,
          value: counterparty.id,
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
  ], [warehouses, machines, counterparties]);

  // Конфигурация колонок
  const columns = [
    {
      title: 'Дата',
      dataIndex: 'document_date',
      key: 'document_date',
      render: (date: string) => dayjs(date).format('DD.MM.YYYY HH:mm'),
    },
    {
      title: 'Тип',
      dataIndex: 'movement_type',
      key: 'movement_type',
      render: (type: string) => (
        <Tag color={getTypeColor(type)}>
          {getTypeLabel(type)}
        </Tag>
      ),
    },
    {
      title: 'Статус',
      dataIndex: 'status',
      key: 'status',
      render: (status: any) => (
        <Tag color={getStatusColor(status)}>
          {getStatusLabel(status)}
        </Tag>
      ),
    },
    {
      title: 'Товары',
      key: 'items',
      render: (_: any, record: InventoryMovement) => {
        if (!record.items || record.items.length === 0) return 'Нет товаров';
        return record.items.map((item: any, index: number) => (
          <div key={index}>
            {item.item?.name || 'Неизвестно'} - {item.quantity} {item.item?.unit || 'шт'}
          </div>
        ));
      },
    },
    {
      title: 'Сумма',
      dataIndex: 'total_amount',
      key: 'total_amount',
      render: (amount: number, record: InventoryMovement) => {
        if (!amount) return '-';
        const currency = record.currency || 'RUB';
        return `${amount} ${currency}`;
      },
    },
    {
      title: 'Откуда',
      key: 'from',
      render: (_: any, record: InventoryMovement) => {
        // Проверяем разные варианты именования полей
        const fromWarehouse = record.fromWarehouse || (record as any).from_warehouse;
        const fromMachine = record.fromMachine || (record as any).from_machine;
        
        if (fromWarehouse) return `Склад: ${fromWarehouse.name}`;
        if (fromMachine) return `Автомат: ${fromMachine.name}`;
        if (record.counterparty && ['receipt', 'load_machine'].includes(record.movement_type)) {
          return `Поставщик: ${record.counterparty.name}`;
        }
        return '-';
      },
    },
    {
      title: 'Куда',
      key: 'to',
      render: (_: any, record: InventoryMovement) => {
        // Проверяем разные варианты именования полей
        const toWarehouse = record.toWarehouse || (record as any).to_warehouse;
        const toMachine = record.toMachine || (record as any).to_machine;
        
        if (toWarehouse) return `Склад: ${toWarehouse.name}`;
        if (toMachine) return `Автомат: ${toMachine.name}`;
        if (record.counterparty && ['sale', 'unload_machine'].includes(record.movement_type)) {
          return `Покупатель: ${record.counterparty.name}`;
        }
        return '-';
      },
    },
    {
      title: 'Создал',
      key: 'created_by',
      render: (_: any, record: InventoryMovement) => {
        // Проверяем разные варианты именования и структуры
        const createdByUser = record.created_by_user || (record as any).createdByUser;
        if (createdByUser) {
          return createdByUser.full_name || createdByUser.username || `ID: ${createdByUser.id}`;
        }
        
        // Если есть только ID создателя
        if (record.created_by) {
          return `ID: ${record.created_by}`;
        }
        
        return '-';
      },
    },
  ];

  // Конфигурация формы
  const formConfig = {
    modalWidth: 900,
    initialValues: {
      document_date: dayjs(),
      status_id: 1, // Черновик
      currency: 'RUB', // Рубли
    },
    fields: [
      {
        name: 'document_date',
        label: 'Дата документа',
        type: 'datetime' as const,
        rules: [{ required: true, message: 'Выберите дату' }],
        initialValue: dayjs(),
      },
      {
        name: 'movement_type',
        label: 'Тип движения',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите тип движения' }],
        options: [
          { label: 'Поступление', value: 'receipt' },
          { label: 'Продажа', value: 'sale' },
          { label: 'Перемещение', value: 'transfer' },
          { label: 'Корректировка', value: 'adjustment' },
          { label: 'Выдача', value: 'issue' },
          { label: 'Загрузка автомата', value: 'load_machine' },
          { label: 'Выгрузка автомата', value: 'unload_machine' },
        ],
        onChange: handleMovementTypeChange,
      },
      {
        name: 'status_id',
        label: 'Статус',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите статус' }],
        initialValue: 1,
        options: [
          { label: 'Черновик', value: 1 },
          { label: 'Утвержден', value: 2 },
        ],
      },
      // Поля отправления
      {
        name: 'from_warehouse_id',
        label: 'Склад отправления',
        type: 'select' as const,
        visible: () => shouldShowFromWarehouse(),
        options: warehouses.map(w => ({ label: w.name, value: w.id })),
        onChange: (value: any) => handleFieldChange('from_warehouse_id', value),
        rules: [
          {
            validator: (_: any, value: any) => {
              if (['transfer', 'issue', 'sale'].includes(selectedMovementType) && !value && !formValues.from_machine_id) {
                return Promise.reject(new Error('Выберите склад отправления или автомат отправления'));
              }
              return Promise.resolve();
            }
          }
        ],
      },
      {
        name: 'from_machine_id',
        label: 'Автомат отправления',
        type: 'select' as const,
        visible: () => shouldShowFromMachine(),
        options: machines.map(m => ({ label: m.name, value: m.id })),
        onChange: (value: any) => handleFieldChange('from_machine_id', value),
        rules: [
          {
            validator: (_: any, value: any) => {
              if (['transfer', 'issue', 'sale'].includes(selectedMovementType) && !value && !formValues.from_warehouse_id) {
                return Promise.reject(new Error('Выберите автомат отправления или склад отправления'));
              }
              return Promise.resolve();
            }
          }
        ],
      },
      // Поля назначения
      {
        name: 'to_warehouse_id',
        label: 'Склад назначения',
        type: 'select' as const,
        visible: () => shouldShowToWarehouse(),
        options: warehouses.map(w => ({ label: w.name, value: w.id })),
        onChange: (value: any) => handleFieldChange('to_warehouse_id', value),
        rules: [
          {
            validator: (_: any, value: any) => {
              if (['transfer', 'adjustment'].includes(selectedMovementType) && !value && !formValues.to_machine_id) {
                return Promise.reject(new Error('Выберите склад назначения или автомат назначения'));
              }
              if (selectedMovementType === 'receipt' && !value && !formValues.to_machine_id) {
                return Promise.reject(new Error('Выберите склад назначения или автомат назначения'));
              }
              return Promise.resolve();
            }
          }
        ],
      },
      {
        name: 'to_machine_id',
        label: 'Автомат назначения',
        type: 'select' as const,
        visible: () => shouldShowToMachine(),
        options: machines.map(m => ({ label: m.name, value: m.id })),
        onChange: (value: any) => handleFieldChange('to_machine_id', value),
        rules: [
          {
            validator: (_: any, value: any) => {
              if (['transfer', 'adjustment'].includes(selectedMovementType) && !value && !formValues.to_warehouse_id) {
                return Promise.reject(new Error('Выберите автомат назначения или склад назначения'));
              }
              if (selectedMovementType === 'receipt' && !value && !formValues.to_warehouse_id) {
                return Promise.reject(new Error('Выберите автомат назначения или склад назначения'));
              }
              return Promise.resolve();
            }
          }
        ],
      },
      // Контрагент
      {
        name: 'counterparty_id',
        label: 'Контрагент',
        type: 'select' as const,
        visible: () => shouldShowCounterparty(),
        options: counterparties.map(c => ({ label: c.name, value: c.id })),
        rules: [
          {
            validator: (_: any, value: any) => {
              if (['receipt', 'sale'].includes(selectedMovementType) && !value) {
                return Promise.reject(new Error('Выберите контрагента'));
              }
              if (selectedMovementType === 'load_machine' && !value && !formValues.from_warehouse_id) {
                return Promise.reject(new Error('Выберите контрагента или склад отправления'));
              }
              return Promise.resolve();
            }
          }
        ],
      },
      {
        name: 'currency',
        label: 'Валюта',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите валюту' }],
        initialValue: 'RUB',
        options: [
          { label: 'Рубль (RUB)', value: 'RUB' },
          { label: 'Доллар (USD)', value: 'USD' },
          { label: 'Евро (EUR)', value: 'EUR' },
        ],
      },
      {
        name: 'description',
        label: 'Описание',
        type: 'textarea' as const,
      },

    ],
  };

  // Действия строк
  const rowActions = [
    {
      key: 'approve',
      title: 'Утвердить',
      icon: <CheckOutlined />,
      color: '#1890ff',
      visible: canApprove,
      onClick: async (record: InventoryMovement) => {
        try {
          const userRaw = localStorage.getItem('user');
          const currentUser = userRaw ? JSON.parse(userRaw) : null;
          const approvedBy = currentUser?.id;
          if (!approvedBy) {
            message.error('Не удалось определить пользователя для утверждения');
            return;
          }
          await inventoryMovementsApi.approve(record.id, { approved_by: approvedBy });
          message.success('Движение утверждено');
        } catch (error) {
          message.error('Ошибка при утверждении движения');
        }
      },
    },
    {
      key: 'execute',
      title: 'Выполнить',
      icon: <PlayCircleOutlined />,
      color: '#52c41a',
      visible: canExecute,
      onClick: async (record: InventoryMovement) => {
        try {
          const userRaw = localStorage.getItem('user');
          const currentUser = userRaw ? JSON.parse(userRaw) : null;
          const executedBy = currentUser?.id;
          if (!executedBy) {
            message.error('Не удалось определить пользователя для выполнения');
            return;
          }
          await inventoryMovementsApi.execute(record.id, { executed_by: executedBy });
          message.success('Движение выполнено');
        } catch (error) {
          message.error('Ошибка при выполнении движения');
        }
      },
    },
    {
      key: 'cancel',
      title: 'Отменить',
      icon: <CloseOutlined />,
      color: '#ff4d4f',
      visible: canCancel,
      onClick: async (record: InventoryMovement) => {
        try {
          // Здесь должна быть логика отмены движения
          message.success('Движение отменено');
        } catch (error) {
          message.error('Ошибка при отмене движения');
        }
      },
      confirm: {
        title: 'Отменить движение?',
        description: 'Это действие нельзя отменить.',
      },
    },
  ];

  // Массовые действия
  const bulkActions = [
    {
      key: 'bulk_approve',
      title: 'Утвердить',
      icon: <CheckOutlined />,
                        color: '#1890ff',
      onClick: async (selectedKeys: React.Key[]) => {
        try {
          const result = await inventoryMovementsApi.bulkApprove({
            approved_by: 1, // TODO: Получить ID текущего пользователя
            movement_ids: selectedKeys.map(key => Number(key))
          });

          if (result.success_count > 0) {
            message.success(`Успешно утверждено ${result.success_count} движений`);
          }
          if (result.error_count > 0) {
            message.warning(`Ошибок: ${result.error_count}`);
          }
        } catch (error) {
          message.error('Ошибка при массовом утверждении');
        }
      },
    },
    {
      key: 'bulk_execute',
      title: 'Выполнить',
      icon: <PlayCircleOutlined />,
      color: '#52c41a',
      onClick: async (selectedKeys: React.Key[]) => {
        try {
          const result = await inventoryMovementsApi.bulkExecute({
            executed_by: 1, // TODO: Получить ID текущего пользователя
            movement_ids: selectedKeys.map(key => Number(key))
          });

          if (result.success_count > 0) {
            message.success(`Успешно выполнено ${result.success_count} движений`);
          }
          if (result.error_count > 0) {
            message.warning(`Ошибок: ${result.error_count}`);
          }
        } catch (error) {
          message.error('Ошибка при массовом выполнении');
        }
      },
    },
  ];

  // Callback при открытии модального окна
  const handleModalOpen = (isEditing: boolean) => {
    if (!isEditing) {
      // Если создание нового - очищаем список товаров
      setMovementItems([]);
      setSelectedMovementType('');
      
      // Устанавливаем значения по умолчанию для новой записи
      setFormValues({
        document_date: dayjs(),
        status_id: 1, // Черновик
        currency: 'RUB', // Рубли
      });
    }
  };

  // Callback при закрытии модального окна
  const handleModalClose = () => {
    // Очищаем состояние при закрытии
    setMovementItems([]);
    setSelectedMovementType('');
    setFormValues({});
  };

  // Трансформация данных для редактирования
  const onEditDataTransform = (record: InventoryMovement) => {
    // Нормализуем позиции для формы
    const normalizedItems = (record.items || []).map((it: any, idx: number) => ({
      id: it.id ?? idx,
      item_id: it.item_id ?? it.item?.id,
      quantity: typeof it.quantity === 'string' ? parseFloat(it.quantity) : it.quantity,
      price: typeof it.price === 'string' ? parseFloat(it.price) : it.price,
      amount: typeof it.amount === 'string' ? parseFloat(it.amount) : it.amount,
      description: it.description || '',
    }));
    setMovementItems(normalizedItems);

    // Устанавливаем тип движения для логики видимости
    setSelectedMovementType(record.movement_type || '');

    // Фоллбеки ID из вложенных объектов с учетом разных вариантов именования
    const transformedData = {
      movement_type: record.movement_type,
      document_date: record.document_date ? dayjs(record.document_date) : dayjs(),
      status_id: (record as any).status_id ?? (record as any).status?.id,
      from_warehouse_id: (record as any).from_warehouse_id ?? 
                        (record as any).fromWarehouse?.id ?? 
                        (record as any).from_warehouse?.id,
      to_warehouse_id: (record as any).to_warehouse_id ?? 
                      (record as any).toWarehouse?.id ?? 
                      (record as any).to_warehouse?.id,
      from_machine_id: (record as any).from_machine_id ?? 
                      (record as any).fromMachine?.id ?? 
                      (record as any).from_machine?.id,
      to_machine_id: (record as any).to_machine_id ?? 
                    (record as any).toMachine?.id ?? 
                    (record as any).to_machine?.id,
      counterparty_id: (record as any).counterparty_id ?? (record as any).counterparty?.id,
      currency: record.currency || 'RUB',
      description: record.description,
    };

    setFormValues(transformedData);
    return transformedData;
  };

  // Кастомная обработка сохранения
  const customEndpoints = {
    list: inventoryMovementsApi.getList,
    create: async (values: any) => {
      // Валидация товаров
      if (movementItems.length === 0) {
        throw new Error('Добавьте хотя бы один товар');
      }

      const invalidItems = movementItems.filter(item => !item.item_id || !item.quantity || !item.price);
      if (invalidItems.length > 0) {
        throw new Error('Заполните все обязательные поля для товаров');
      }

      // Бизнес-валидация
      const type = values.movement_type;
      const hasFromWarehouse = !!values.from_warehouse_id;
      const hasToWarehouse = !!values.to_warehouse_id;
      const hasFromMachine = !!values.from_machine_id;
      const hasToMachine = !!values.to_machine_id;
      const hasCounterparty = !!values.counterparty_id;
      
      const hasFrom = hasFromWarehouse || hasFromMachine;
      const hasTo = hasToWarehouse || hasToMachine;

      if (type === 'receipt') {
        if (!hasTo) throw new Error('Для прихода укажите место назначения (склад или автомат)');
        if (!hasCounterparty) throw new Error('Для прихода укажите контрагента (поставщика)');
      }
      
      if (['issue', 'sale'].includes(type)) {
        if (!hasFrom) throw new Error('Для расхода/продажи укажите место отправления (склад или автомат)');
        if (type === 'sale' && !hasCounterparty) throw new Error('Для продажи укажите контрагента (покупателя)');
      }
      
      if (type === 'transfer') {
        if (!hasFrom) throw new Error('Для перемещения укажите место отправления (склад или автомат)');
        if (!hasTo) throw new Error('Для перемещения укажите место назначения (склад или автомат)');
      }
      
      if (type === 'load_machine') {
        if (!hasToMachine) throw new Error('Для загрузки автомата укажите автомат назначения');
        if (!hasFromWarehouse && !hasCounterparty) throw new Error('Для загрузки автомата укажите склад отправления или контрагента');
      }
      
      if (type === 'unload_machine') {
        if (!hasFromMachine) throw new Error('Для выгрузки автомата укажите автомат отправления');
        if (!hasToWarehouse) throw new Error('Для выгрузки автомата укажите склад назначения');
      }
      
      if (type === 'adjustment') {
        if (!hasTo) throw new Error('Для корректировки укажите место назначения (склад или автомат)');
      }

      const totalAmount = movementItems.reduce((sum, item) => sum + Number(item.amount || 0), 0);
      
      const movementData = {
        ...values,
        document_date: values.document_date.toISOString(),
        total_amount: totalAmount,
        items: movementItems.map(item => ({
          item_id: item.item_id,
          quantity: item.quantity,
          price: item.price,
          amount: item.amount,
          description: item.description,
        })),
      };

      return await inventoryMovementsApi.create(movementData);
    },
    update: async (id: number, values: any) => {
      // Аналогичная валидация для обновления
      if (movementItems.length === 0) {
        throw new Error('Добавьте хотя бы один товар');
      }

      const invalidItems = movementItems.filter(item => !item.item_id || !item.quantity || !item.price);
      if (invalidItems.length > 0) {
        throw new Error('Заполните все обязательные поля для товаров');
      }

      const totalAmount = movementItems.reduce((sum, item) => sum + Number(item.amount || 0), 0);
      
      const movementData = {
        ...values,
        document_date: values.document_date.toISOString(),
        total_amount: totalAmount,
        items: movementItems.map(item => ({
          item_id: item.item_id,
          quantity: item.quantity,
          price: item.price,
          amount: item.amount,
          description: item.description,
        })),
      };

      return await inventoryMovementsApi.update(id, movementData);
    },
    delete: inventoryMovementsApi.delete,
  };

  // Кастомный рендер формы
  const customFormRender = (form: any, formConfig: any) => (
    <>
      {formConfig.fields.map((field: any) => {
        // Проверяем видимость поля
        if (field.visible && !field.visible(formValues)) {
          return null;
        }

        return (
          <Form.Item
            key={field.name}
            name={field.name}
            label={field.label}
            rules={field.rules}
            dependencies={field.dependencies}
            valuePropName={field.type === 'switch' ? 'checked' : 'value'}
          >
            {field.type === 'datetime' ? (
              <DatePicker
                showTime
                style={{ width: '100%' }}
                placeholder={field.placeholder}
              />
            ) : field.type === 'select' ? (
                      <Select
                placeholder={field.placeholder}
                allowClear
                showSearch={field.showSearch !== false}
                filterOption={(input: string, option: any) =>
                  (option?.children?.toString().toLowerCase() ?? '').includes(input.toLowerCase())
                }
                        style={{ width: '100%' }}
                mode={field.mode}
                onChange={field.onChange}
              >
                {(field.options || []).map((option: any) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                          </Option>
                        ))}
                      </Select>
            ) : field.type === 'textarea' ? (
              <TextArea rows={4} placeholder={field.placeholder} />
            ) : (
              <Input placeholder={field.placeholder} />
              )}
            </Form.Item>
        );
      })}
      
      {/* Кастомная секция товаров */}
      <Form.Item label="Позиции товаров">
        {renderMovementItemsForm()}
            </Form.Item>
    </>
  );

  return (
    <>
      <GenericDataTable
        title="Движения товаров"
        icon={<SwapOutlined />}
        endpoints={customEndpoints}
        columns={columns}
        filters={filters}
        formConfig={formConfig}
        rowActions={rowActions}
        bulkActions={bulkActions}
        onEditDataTransform={onEditDataTransform}
        customFormRender={customFormRender}
        onModalOpen={handleModalOpen}
        onModalClose={handleModalClose}
        disableEdit={false}
        disableDelete={false}
        pagination={{
          pageSize: 100,
          pageSizeOptions: ['100', '200', '500', '800', '1000'],
        }}
      />

      {/* Модальное окно для добавления нового товара */}
      <Modal
        title="Добавить новый товар"
        open={isAddItemModalVisible}
        onOk={handleCreateItem}
        onCancel={handleCloseAddItemModal}
        width={600}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form
          form={addItemForm}
          layout="vertical"
          initialValues={{
            unit: 'шт',
            min_stock: 0,
            is_active: true,
          }}
        >
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название товара' }]}
          >
            <Input placeholder="Введите название товара" />
          </Form.Item>

          <Form.Item
            name="sku"
            label="SKU"
            rules={[{ required: true, message: 'Введите SKU' }]}
          >
            <Input placeholder="Введите SKU" />
          </Form.Item>

          <div style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
            <Form.Item
              name="category_id"
              label="Категория"
              rules={[{ required: true, message: 'Выберите категорию' }]}
              style={{ flex: 1, marginBottom: 0 }}
            >
              <Select
                placeholder="Выберите категорию"
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
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleOpenAddCategoryModal}
              title="Добавить новую категорию"
              style={{ marginTop: 30 }}
            />
          </div>

          <Form.Item
            name="description"
            label="Описание"
          >
            <TextArea rows={3} placeholder="Введите описание товара" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Form.Item
              name="unit"
              label="Единица измерения"
              rules={[{ required: true, message: 'Введите единицу измерения' }]}
            >
              <Select placeholder="Выберите единицу">
                <Option value="шт">шт</Option>
                <Option value="кг">кг</Option>
                <Option value="л">л</Option>
                <Option value="м">м</Option>
                <Option value="м²">м²</Option>
                <Option value="м³">м³</Option>
                <Option value="упак">упак</Option>
                <Option value="компл">компл</Option>
              </Select>
            </Form.Item>

            <Form.Item
              name="barcode"
              label="Штрихкод"
            >
              <Input placeholder="Введите штрихкод" />
            </Form.Item>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Form.Item
              name="min_stock"
              label="Минимальный остаток"
            >
              <InputNumber
                placeholder="Минимальный остаток"
                min={0}
                step={1}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item
              name="max_stock"
              label="Максимальный остаток"
            >
              <InputNumber
                placeholder="Максимальный остаток"
                min={0}
                step={1}
                style={{ width: '100%' }}
              />
            </Form.Item>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Form.Item
              name="weight"
              label="Вес (г)"
            >
              <InputNumber
                placeholder="Вес в граммах"
                min={0}
                step={1}
                style={{ width: '100%' }}
              />
            </Form.Item>

            <Form.Item
              name="dimensions"
              label="Размеры"
            >
              <Input placeholder="Например: 10x20x30" />
            </Form.Item>
          </div>
        </Form>
      </Modal>

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

export default InventoryMovementsNew;
