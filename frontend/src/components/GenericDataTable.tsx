import React, { useState, useEffect, useCallback, useMemo } from 'react';
import dayjs from 'dayjs';
import {
  Table,
  Button,
  Modal,
  Form,
  Input,
  Space,
  Popconfirm,
  message,
  Card,
  Typography,
  Tooltip,
  Select,
  InputNumber,
  DatePicker,
  Switch,
  Row,
  Col,
  List,
  Drawer,
  Upload,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  DownloadOutlined,
  UploadOutlined,
} from '@ant-design/icons';
import DashboardSummary from './DashboardSummary';
import StatsDashboard from './StatsDashboard';
import DetailModal from './DetailModal';

const { Title } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { RangePicker } = DatePicker;

interface FilterConfig {
  key: string;
  label: string;
  type: 'select' | 'input' | 'date' | 'dateRange';
  options?: Array<{ label: string; value: any }>;
  api?: () => Promise<Array<{label: string, value: any}>>;
  placeholder?: string;
  multiple?: boolean;
}

interface FormFieldConfig {
  name: string;
  label: string;
  type: 'input' | 'textarea' | 'select' | 'number' | 'date' | 'datetime' | 'switch' | 'password' | 'file' | 'custom';
  rules?: any[];
  options?: Array<{ label: string; value: any }>;
  api?: () => Promise<Array<{label: string, value: any}>>;
  placeholder?: string;
  dependencies?: string[];
  visible?: (values: any) => boolean;
  mode?: 'multiple' | 'tags';
  showSearch?: boolean;
  onChange?: (value: any) => void;
  min?: number;
  max?: number;
  initialValue?: any;
  customRender?: (field: FormFieldConfig, form: any) => React.ReactNode;
  accept?: string; // Для файловых полей
  multiple?: boolean; // Для файловых полей
  required?: boolean; // Явное указание обязательности поля
}

interface ColumnConfig<T> {
  title: string;
  dataIndex?: string | string[];
  key: string;
  render?: (value: any, record: T) => React.ReactNode;
  width?: number;
  ellipsis?: boolean;
  sorter?: boolean;
  filterable?: boolean;
}

interface RowAction<T> {
  key: string;
  title: string;
  icon: React.ReactNode;
  color?: string;
  visible?: (record: T) => boolean;
  onClick: (record: T) => void;
  confirm?: {
    title: string;
    description?: string;
  };
}

interface BulkAction<T> {
  key: string;
  title: string;
  icon: React.ReactNode;
  color?: string;
  onClick: (selectedKeys: React.Key[], selectedRecords: T[]) => void;
}

interface GenericDataTableProps<T extends { id: number }> {
  title: string;
  icon?: React.ReactNode;
  
  endpoints: {
    list: (params?: any) => Promise<T[]>;
    create: (data: any) => Promise<T>;
    update: (id: number, data: any) => Promise<T>;
    delete: (id: number) => Promise<void>;
  };
  
  columns: ColumnConfig<T>[];
  
  filters?: FilterConfig[];
  
  formConfig: {
    fields: FormFieldConfig[];
    initialValues?: any;
    modalWidth?: number;
  };
  
  rowActions?: RowAction<T>[];
  bulkActions?: BulkAction<T>[];
  
  pagination?: {
    pageSize?: number;
    pageSizeOptions?: string[];
    showSizeChanger?: boolean;
    showQuickJumper?: boolean;
  };
  
  searchable?: boolean;
  exportable?: boolean;
  addButtonText?: string;
  disableCreate?: boolean;
  disableEdit?: boolean;
  disableDelete?: boolean;
  onEditDataTransform?: (record: T) => any; // Кастомная трансформация данных для редактирования
  onActionComplete?: () => void; // Callback для обновления данных после действий
  customFormRender?: (form: any, formConfig: any) => React.ReactNode; // Кастомный рендер формы
  onModalOpen?: (isEditing: boolean) => void; // Callback при открытии модального окна
  onModalClose?: () => void; // Callback при закрытии модального окна
  
  // Дашборд
  dashboardConfig?: {
    fetchSummary: (params?: any) => Promise<any>;
    title?: string;
    showDateFilter?: boolean;
    extraParams?: Record<string, any>;
  } | {
    fetchData: (params?: any) => Promise<any>;
    renderStats: (data: any) => Array<{
      title: string;
      value: number | string;
      prefix?: React.ReactNode;
      suffix?: string;
      color?: string;
      formatter?: (value: number | string) => string;
    }>;
    title?: string;
    showDateFilter?: boolean;
    extraParams?: Record<string, any>;
  };
}

// Вспомогательная функция для получения вложенных значений
const getNestedValue = (obj: any, path?: string | string[]): any => {
  if (!path) return undefined;
  
  if (typeof path === 'string') {
    return obj[path];
  }
  
  return path.reduce((current, key) => {
    return current && current[key] !== undefined ? current[key] : undefined;
  }, obj);
};

const GenericDataTable = <T extends { id: number }>({
  title,
  icon,
  endpoints,
  columns,
  filters = [],
  formConfig,
  rowActions = [],
  bulkActions = [],
  pagination: paginationConfig = {},
  searchable = false,
  exportable = false,
  addButtonText = 'Добавить',
  disableCreate = false,
  disableEdit = false,
  disableDelete = false,
  onEditDataTransform,
  onActionComplete,
  customFormRender,
  onModalOpen,
  onModalClose,
  dashboardConfig,
}: GenericDataTableProps<T>) => {
  const [data, setData] = useState<T[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingRecord, setEditingRecord] = useState<T | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<T | null>(null);
  const [drawerVisible, setDrawerVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [isMobile, setIsMobile] = useState(false);
  
  // Состояния для фильтрации и пагинации
  const [filterValues, setFilterValues] = useState<Record<string, any>>({});
  const [searchValue, setSearchValue] = useState('');

  // Мемоизируем параметры для дашборда
  const dashboardExtraParams = useMemo(() => {
    const params = {
      ...dashboardConfig?.extraParams,
      ...filterValues,
    };
    
    // Форматируем даты в ISO формат
    if (params.date_from && dayjs.isDayjs(params.date_from)) {
      params.date_from = params.date_from.toISOString();
    }
    if (params.date_to && dayjs.isDayjs(params.date_to)) {
      params.date_to = params.date_to.toISOString();
    }
    
    return params;
  }, [dashboardConfig?.extraParams, filterValues]);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: paginationConfig.pageSize || 100,
    total: 0,
  });
  
  // Состояния для массовых операций
  const [selectedRowKeys, setSelectedRowKeys] = useState<React.Key[]>([]);

  // Форма для модального окна
  const [form] = Form.useForm();
  const [bulkLoading, setBulkLoading] = useState(false);
  
  // Состояния для опций фильтров
  const [filterOptions, setFilterOptions] = useState<Record<string, any[]>>({});
  const [formOptions, setFormOptions] = useState<Record<string, any[]>>({});
  
  // Состояние для отслеживания значений формы (для условного отображения полей)
  const [formValues, setFormValues] = useState<Record<string, any>>({});

  // Определяем мобильное устройство
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Загружаем опции для фильтров и формы
  const loadOptions = useCallback(async () => {
    // Загружаем опции для фильтров
    for (const filter of filters) {
      if (filter.api) {
        try {
          const options = await filter.api();
          setFilterOptions(prev => {
            // Проверяем, нужно ли обновлять
            if (!prev[filter.key] || prev[filter.key].length === 0) {
              return { ...prev, [filter.key]: options };
            }
            return prev;
          });
        } catch (error) {
          console.error(`Ошибка загрузки опций для фильтра ${filter.key}:`, error);
        }
      }
    }

    // Загружаем опции для полей формы
    for (const field of formConfig.fields) {
      if (field.api) {
        try {
          const options = await field.api();
          setFormOptions(prev => {
            // Проверяем, нужно ли обновлять
            if (!prev[field.name] || prev[field.name].length === 0) {
              return { ...prev, [field.name]: options };
            }
            return prev;
          });
        } catch (error) {
          console.error(`Ошибка загрузки опций для поля ${field.name}:`, error);
        }
      }
    }
  }, [filters, formConfig.fields]);

  useEffect(() => {
    loadOptions();
  }, [loadOptions]);

  const fetchData = async (page = 1, pageSize = pagination.pageSize, params = {}) => {
    setLoading(true);
    try {
      // Преобразуем dayjs объекты в строки для API
      const processedFilters = Object.entries(filterValues).reduce((acc, [key, value]) => {
        if (value && typeof value === 'object' && value.format) {
          // Это dayjs объект - используем toISOString для корректной работы с временными зонами
          acc[key] = value.toISOString();
        } else if (value !== undefined && value !== null && value !== '') {
          acc[key] = value;
        }
        return acc;
      }, {} as Record<string, any>);

      const queryParams = {
        skip: (page - 1) * pageSize,
        limit: pageSize,
        ...processedFilters,
        ...params,
        ...(searchValue && { search: searchValue }),
      };
      
      const result = await endpoints.list(queryParams);
      setData(result);
      setPagination({
        current: page,
        pageSize,
        total: result.length, // Предполагаем, что API возвращает все данные или нужна отдельная функция для подсчета
      });
    } catch (error) {
      message.error('Ошибка при загрузке данных');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [filterValues, searchValue]);

  const handleCreate = () => {
    setEditingRecord(null);
    form.resetFields();
    if (formConfig.initialValues) {
      form.setFieldsValue(formConfig.initialValues);
      setFormValues(formConfig.initialValues);
    } else {
      setFormValues({});
    }
    setModalVisible(true);
    if (onModalOpen) {
      onModalOpen(false); // false = создание нового
    }
  };

  const handleEdit = (record: T) => {
    setEditingRecord(record);
    const formData = onEditDataTransform ? onEditDataTransform(record) : record;
    form.setFieldsValue(formData);
    setFormValues(formData);
    setModalVisible(true);
    if (onModalOpen) {
      onModalOpen(true); // true = редактирование
    }
  };

  const handleDelete = async (id: number) => {
    try {
      await endpoints.delete(id);
      message.success('Запись удалена');
      fetchData(pagination.current, pagination.pageSize);
    } catch (error) {
      message.error('Ошибка при удалении записи');
      console.error(error);
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      if (editingRecord) {
        await endpoints.update(editingRecord.id, values);
        message.success('Запись обновлена');
      } else {
        await endpoints.create(values);
        message.success('Запись создана');
      }
      setModalVisible(false);
      if (onModalClose) {
        onModalClose();
      }
      fetchData(pagination.current, pagination.pageSize);
    } catch (error) {
      message.error('Ошибка при сохранении записи');
      console.error(error);
    }
  };

  const handleTableChange = (paginationInfo: any) => {
    fetchData(paginationInfo.current, paginationInfo.pageSize);
  };



  const handleBulkAction = async (action: BulkAction<T>) => {
    if (selectedRowKeys.length === 0) {
      message.warning('Выберите записи для выполнения операции');
      return;
    }

    setBulkLoading(true);
    try {
      const selectedRecords = data.filter(record => selectedRowKeys.includes(record.id));
      await action.onClick(selectedRowKeys, selectedRecords);
      setSelectedRowKeys([]);
      fetchData(pagination.current, pagination.pageSize);
    } catch (error) {
      message.error('Ошибка при выполнении массовой операции');
      console.error(error);
    } finally {
      setBulkLoading(false);
    }
  };

  const onSelectChange = (newSelectedRowKeys: React.Key[]) => {
    setSelectedRowKeys(newSelectedRowKeys);
  };

  const rowSelection = bulkActions.length > 0 ? {
    selectedRowKeys,
    onChange: onSelectChange,
  } : undefined;

  // Обработка экспорта
  const handleExport = () => {
    message.info('Функция экспорта будет добавлена в следующей версии');
  };

  // Обработчик для rowActions с обновлением данных
  const handleRowAction = async (action: RowAction<T>, record: T) => {
    try {
      await action.onClick(record);
      // Обновляем данные после успешного выполнения действия
      if (onActionComplete) {
        onActionComplete();
      } else {
        // Если callback не передан, обновляем данные напрямую
        fetchData(pagination.current, pagination.pageSize);
      }
    } catch (error) {
      console.error('Ошибка при выполнении действия:', error);
    }
  };

  // Построение колонок с действиями
  const tableColumns = [
    ...columns,
    ...(rowActions.length > 0 || !disableEdit || !disableDelete ? [{
      title: '🛠️',
      key: 'actions',
      width: 120 + (rowActions.length * 40),
      render: (_: any, record: T) => (
        <Space>
          {!disableEdit && (
            <Tooltip title="Редактировать">
              <Button
                type="text"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
              />
            </Tooltip>
          )}
          
          {rowActions.map(action => {
            if (action.visible && !action.visible(record)) return null;
            
            const button = (
              <Tooltip key={action.key} title={action.title}>
                <Button
                  type="text"
                  icon={action.icon}
                  onClick={() => handleRowAction(action, record)}
                  style={action.color ? { color: action.color } : {}}
                />
              </Tooltip>
            );

            if (action.confirm) {
              return (
                <Popconfirm
                  key={action.key}
                  title={action.confirm.title}
                  description={action.confirm.description}
                  onConfirm={() => handleRowAction(action, record)}
                  okText="Да"
                  cancelText="Нет"
                >
                  {button}
                </Popconfirm>
              );
            }

            return button;
          })}
          
          {!disableDelete && (
            <Popconfirm
              title="Удалить запись?"
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
          )}
        </Space>
      ),
    }] : [])
  ];





  // Рендеринг фильтров
  const renderFilters = () => {
    if (!filters || filters.length === 0) return null;

    return (
      <div style={{ marginBottom: 16 }}>
        <Row gutter={[16, 16]}>
          {filters.map(filter => (
            <Col key={filter.key} xs={24} sm={12} md={8} lg={6}>
              <div>
                <label style={{ display: 'block', marginBottom: 4, fontWeight: 'bold' }}>
                  {filter.label}
                </label>
                {renderFilterField(filter)}
              </div>
            </Col>
          ))}
        </Row>
      </div>
    );
  };

  // Рендеринг отдельного поля фильтра
  const renderFilterField = (filter: FilterConfig) => {
    const options = filterOptions[filter.key] || filter.options || [];

    switch (filter.type) {
      case 'select':
        return (
          <Select
            value={filterValues[filter.key]}
            onChange={(value) => setFilterValues(prev => ({ ...prev, [filter.key]: value }))}
            placeholder={filter.placeholder}
            allowClear
            showSearch={true}
            filterOption={(input, option) =>
              (option?.children?.toString().toLowerCase() ?? '').includes(input.toLowerCase())
            }
            style={{ width: '100%' }}
            mode={filter.multiple ? 'multiple' : undefined}
          >
            {options.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        );

      case 'input':
        return (
          <Input
            value={filterValues[filter.key]}
            onChange={(e) => setFilterValues(prev => ({ ...prev, [filter.key]: e.target.value }))}
            placeholder={filter.placeholder}
            allowClear
            style={{ width: '100%' }}
          />
        );

      case 'date':
        return isMobile ? (
          <Input
            type="date"
            value={
              filterValues[filter.key] 
                ? (dayjs.isDayjs(filterValues[filter.key]) 
                    ? filterValues[filter.key].format('YYYY-MM-DD') 
                    : dayjs(filterValues[filter.key]).format('YYYY-MM-DD'))
                : ''
            }
            onChange={(e) => setFilterValues(prev => ({ ...prev, [filter.key]: e.target.value ? dayjs(e.target.value) : null }))}
            placeholder={filter.placeholder}
            style={{ width: '100%' }}
          />
        ) : (
          <DatePicker
            value={filterValues[filter.key]}
            onChange={(date) => setFilterValues(prev => ({ ...prev, [filter.key]: date }))}
            placeholder={filter.placeholder}
            style={{ width: '100%' }}
          />
        );

      case 'dateRange':
        return (
          <RangePicker
            value={filterValues[filter.key]}
            onChange={(dates) => setFilterValues(prev => ({ ...prev, [filter.key]: dates }))}
            placeholder={['Дата от', 'Дата до']}
            style={{ width: '100%' }}
          />
        );

      default:
        return null;
    }
  };

  // Рендеринг поля формы
  const renderFormField = (field: FormFieldConfig, formConfig: any) => {
    const options = formOptions[field.name] || field.options || [];

    // Если есть кастомный рендер, используем его
    if (field.type === 'custom' && field.customRender) {
      return field.customRender(field, form);
    }

    switch (field.type) {
      case 'input':
        return <Input placeholder={field.placeholder} />;
      
      case 'textarea':
        return <TextArea rows={4} placeholder={field.placeholder} />;
      
      case 'select':
        return (
          <Select
            placeholder={field.placeholder}
            allowClear
            showSearch={field.showSearch !== false}
            filterOption={(input, option) =>
              (option?.children?.toString().toLowerCase() ?? '').includes(input.toLowerCase())
            }
            style={{ width: '100%' }}
            mode={field.mode}
            onChange={field.onChange}
          >
            {options.map(option => (
              <Option key={option.value} value={option.value}>
                {option.label}
              </Option>
            ))}
          </Select>
        );
      
      case 'number':
        return (
          <InputNumber
            style={{ width: '100%' }}
            placeholder={field.placeholder}
            min={field.min}
            max={field.max}
          />
        );
      
      case 'date':
        return isMobile ? (
          <Input
            type="date"
            style={{ width: '100%' }}
            placeholder={field.placeholder}
          />
        ) : (
          <DatePicker style={{ width: '100%' }} placeholder={field.placeholder} />
        );
      
      case 'datetime':
        return isMobile ? (
          <Input
            type="datetime-local"
            style={{ width: '100%' }}
            placeholder={field.placeholder}
          />
        ) : (
          <DatePicker showTime style={{ width: '100%' }} placeholder={field.placeholder} />
        );
      
      case 'switch':
        return <Switch />;
      
      case 'password':
        return <Input.Password placeholder={field.placeholder} />;
      
      case 'file':
        // Определяем, редактируем ли мы запись
        const isEditing = editingRecord !== null;
        
        return (
          <Upload
            accept={field.accept}
            multiple={field.multiple}
            beforeUpload={(file) => {
              // Не загружаем файл автоматически, только сохраняем в форме
              return false;
            }}
            onChange={(info) => {
              if (info.fileList && info.fileList.length > 0) {
                const files = info.fileList.map(f => f.originFileObj).filter(Boolean);
                form.setFieldsValue({ [field.name]: files });
                
                // Если есть зависимость от filename, автоматически заполняем имя файла
                const filenameField = formConfig.fields.find((f: any) => f.name === 'filename');
                if (filenameField && filenameField.dependencies?.includes(field.name)) {
                  const file = files[0];
                  if (file && file.name) {
                    // Убираем расширение файла для имени
                    const nameWithoutExt = file.name.replace(/\.[^/.]+$/, '');
                    form.setFieldsValue({ filename: nameWithoutExt });
                  }
                }
              }
            }}
            fileList={form.getFieldValue(field.name)?.map((file: File, index: number) => ({
              uid: index.toString(),
              name: file.name,
              status: 'done',
              originFileObj: file,
            })) || []}
          >
            <Button icon={<UploadOutlined />}>
              {isEditing ? 'Заменить файл (необязательно)' : 'Выбрать файл'}
            </Button>
          </Upload>
        );
      
      default:
        return <Input placeholder={field.placeholder} />;
    }
  };

  // Функция для отображения значений полей в drawer
  const renderFieldValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span style={{ color: '#999' }}>—</span>;
    }
    
    if (typeof value === 'boolean') {
      return value ? 'Да' : 'Нет';
    }
    
    if (typeof value === 'object') {
      // Если это дата
      if (value instanceof Date || (typeof value === 'string' && /^\d{4}-\d{2}-\d{2}/.test(value))) {
        try {
          const date = new Date(value);
          return date.toLocaleString('ru-RU');
        } catch {
          return String(value);
        }
      }
      
      // Если это объект с name или title - показываем его
      if (value.name) return value.name;
      if (value.title) return value.title;
      if (value.label) return value.label;
      
      // Иначе JSON
      return <pre style={{ fontSize: '12px', margin: 0 }}>{JSON.stringify(value, null, 2)}</pre>;
    }
    
    if (typeof value === 'string' && value.length > 100) {
      return (
        <div>
          <div>{value.substring(0, 100)}...</div>
          <details style={{ marginTop: 8 }}>
            <summary style={{ cursor: 'pointer', color: '#1890ff' }}>Показать полностью</summary>
            <div style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>{value}</div>
          </details>
        </div>
      );
    }
    
    return String(value);
  };

  return (
    <div style={{ padding: isMobile ? '16px' : '24px' }}>
      {/* Заголовок и действия */}
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
          {icon} {title}
        </Title>
        <Space size={isMobile ? 'small' : 'middle'}>
          {/* Массовые действия */}
          {selectedRowKeys.length > 0 && bulkActions.map(action => (
            <Button
              key={action.key}
              type="primary"
              icon={action.icon}
              onClick={() => handleBulkAction(action)}
              loading={bulkLoading}
              size={isMobile ? 'small' : 'middle'}
              style={action.color ? { backgroundColor: action.color } : {}}
            >
              {isMobile ? `${action.title} (${selectedRowKeys.length})` : `${action.title} ${selectedRowKeys.length}`}
            </Button>
          ))}
          
          {exportable && (
            <Button
              icon={<DownloadOutlined />}
              onClick={handleExport}
              size={isMobile ? 'small' : 'middle'}
            >
              Экспорт
            </Button>
          )}
          
          {!disableCreate && (
            <Button
              type="primary"
              icon={<PlusOutlined />}
              onClick={handleCreate}
              size={isMobile ? 'small' : 'middle'}
            >
              {isMobile ? addButtonText : addButtonText}
            </Button>
          )}
        </Space>
      </div>

      {/* Дашборд */}
      {dashboardConfig && (
        'fetchSummary' in dashboardConfig ? (
          <DashboardSummary
            fetchSummary={dashboardConfig.fetchSummary}
            title={dashboardConfig.title}
            showDateFilter={dashboardConfig.showDateFilter}
            extraParams={dashboardExtraParams}
            size={isMobile ? 'small' : 'default'}
            columns={isMobile ? 2 : 4}
          />
        ) : (
          <StatsDashboard
            fetchData={dashboardConfig.fetchData}
            renderStats={dashboardConfig.renderStats}
            title={dashboardConfig.title}
            showDateFilter={dashboardConfig.showDateFilter}
            extraParams={dashboardExtraParams}
            size={isMobile ? 'small' : 'default'}
            columns={isMobile ? 2 : 4}
          />
        )
      )}

      <Card size={isMobile ? 'small' : 'default'}>
        {/* Фильтры */}
        {renderFilters()}

        {/* Таблица */}
        {isMobile ? (
          // Мобильная версия - список
          <List
            dataSource={data}
            loading={loading}
            renderItem={(record: T) => (
              <List.Item
                style={{ 
                  padding: '16px 0',
                  borderBottom: '1px solid #f0f0f0'
                }}
              >
                <div style={{ width: '100%' }}>
                  <div style={{ 
                    marginBottom: 12,
                    cursor: 'pointer'
                  }}
                  onClick={() => {
                    setSelectedRecord(record);
                    if (isMobile) {
                      setDrawerVisible(true);
                    } else {
                      setDetailModalVisible(true);
                    }
                  }}
                  >
                    <span style={{ 
                      fontSize: 18,
                      color: '#1890ff',
                      fontWeight: 'bold',
                      display: 'block',
                      width: '100%',
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      whiteSpace: 'nowrap'
                    }}>
                      {/* Отображаем первое поле как заголовок */}
                      {String(getNestedValue(record, columns[0]?.dataIndex || 'id') || record.id)}
                    </span>
                  </div>

                  {/* Основные поля */}
                  {columns.slice(1, 8).map(column => (
                    <div key={column.key} style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        {column.title}:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {column.render 
                          ? column.render(getNestedValue(record, column.dataIndex), record)
                          : getNestedValue(record, column.dataIndex) || '-'
                        }
                      </span>
                    </div>
                  ))}
                </div>
                
                {/* Кнопки действий */}
                <div style={{ 
                  display: 'flex', 
                  flexWrap: 'wrap',
                  gap: 8,
                  justifyContent: 'flex-end',
                  marginTop: 12,
                  paddingTop: 12,
                  borderTop: '1px solid #f0f0f0'
                }}>
                  {!disableEdit && (
                    <Button 
                      type="text" 
                      icon={<EditOutlined />} 
                      size="small"
                      onClick={() => handleEdit(record)}
                    >
                      Изменить
                    </Button>
                  )}
                  
                  {rowActions.map(action => {
                    if (action.visible && !action.visible(record)) return null;
                    
                    const button = (
                      <Button 
                        key={action.key}
                        type="text" 
                        icon={action.icon} 
                        size="small"
                        onClick={() => handleRowAction(action, record)}
                        style={action.color ? { color: action.color } : {}}
                      >
                        {action.title}
                      </Button>
                    );

                    if (action.confirm) {
                      return (
                        <Popconfirm
                          key={action.key}
                          title={action.confirm.title}
                          description={action.confirm.description}
                          onConfirm={() => handleRowAction(action, record)}
                          okText="Да"
                          cancelText="Нет"
                        >
                          {button}
                        </Popconfirm>
                      );
                    }

                    return button;
                  })}
                  
                  {!disableDelete && (
                    <Popconfirm
                      title="Удалить запись?"
                      description="Это действие нельзя отменить."
                      onConfirm={() => handleDelete(record.id)}
                      okText="Да"
                      cancelText="Нет"
                    >
                      <Button 
                        type="text" 
                        danger 
                        icon={<DeleteOutlined />}
                        size="small"
                      >
                        Удалить
                      </Button>
                    </Popconfirm>
                  )}
                </div>
              </List.Item>
            )}
          />
        ) : (
          // Десктопная версия - таблица
          <Table
            columns={tableColumns}
            dataSource={data}
            rowKey="id"
            loading={loading}
            rowSelection={rowSelection}
            onRow={(record) => ({
              onClick: (e) => {
                // Не открываем drawer если клик был на кнопке действия
                const target = e.target as HTMLElement;
                if (target.closest('button') || target.closest('.ant-btn') || target.closest('.ant-popconfirm')) {
                  return;
                }
                setSelectedRecord(record);
                if (isMobile) {
                  setDrawerVisible(true);
                } else {
                  setDetailModalVisible(true);
                }
              },
              style: { cursor: 'pointer' }
            })}
            pagination={{
              current: pagination.current,
              pageSize: pagination.pageSize,
              total: pagination.total,
              showSizeChanger: paginationConfig.showSizeChanger !== false,
              showQuickJumper: paginationConfig.showQuickJumper !== false,
              pageSizeOptions: paginationConfig.pageSizeOptions || ['100', '200', '500'],
              showTotal: (total, range) => `${range?.[0]}-${range?.[1]} из ${total} записей`,
            }}
            onChange={handleTableChange}
          />
        )}

        {/* Drawer для детального просмотра записи */}
        <Drawer
          title={selectedRecord ? String(getNestedValue(selectedRecord, columns[0]?.dataIndex || 'id') || selectedRecord.id) : title}
          placement="right"
          onClose={() => setDrawerVisible(false)}
          open={drawerVisible}
          width={isMobile ? "100%" : 600}
        >
          {selectedRecord && (
            <div>
              {/* Отображаем сначала поля из таблицы */}
              {columns.map(column => (
                <div key={`column-${column.key}`} style={{ marginBottom: 16 }}>
                  <strong>{column.title}:</strong>
                  <div style={{ marginTop: 4 }}>
                    {column.render 
                      ? column.render(getNestedValue(selectedRecord, column.dataIndex), selectedRecord)
                      : getNestedValue(selectedRecord, column.dataIndex) || '-'
                    }
                  </div>
                </div>
              ))}
              
              {/* Отображаем остальные поля объекта */}
              {Object.entries(selectedRecord).map(([key, value]) => {
                // Пропускаем поля, которые уже отображены в столбцах таблицы
                const isDisplayedInColumns = columns.some(column => {
                  if (Array.isArray(column.dataIndex)) {
                    return column.dataIndex.includes(key);
                  }
                  return column.dataIndex === key;
                });
                
                if (isDisplayedInColumns) return null;
                
                // Пропускаем системные поля
                if (['id', 'created_at', 'updated_at'].includes(key)) return null;
                
                return (
                  <div key={`field-${key}`} style={{ marginBottom: 16 }}>
                    <strong>{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong>
                    <div style={{ marginTop: 4 }}>
                      {renderFieldValue(value)}
                    </div>
                  </div>
                );
              })}
              
              {/* Отображаем системные поля в конце */}
              {['id', 'created_at', 'updated_at'].map(sysField => {
                if (!(sysField in selectedRecord)) return null;
                
                return (
                  <div key={`sys-${sysField}`} style={{ marginBottom: 16, opacity: 0.7 }}>
                    <strong>{sysField.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}:</strong>
                    <div style={{ marginTop: 4, fontSize: '12px' }}>
                      {renderFieldValue((selectedRecord as any)[sysField])}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Drawer>

        {/* Модальное окно для создания/редактирования */}
        <Modal
          title={editingRecord ? `Редактировать ${title.toLowerCase()}` : `Создать ${title.toLowerCase()}`}
          open={modalVisible}
          onCancel={() => {
            setModalVisible(false);
            if (onModalClose) {
              onModalClose();
            }
          }}
          footer={null}
          width={formConfig.modalWidth || (isMobile ? '100%' : 800)}
          style={isMobile ? { margin: 16, maxWidth: 'calc(100vw - 32px)' } : {}}
        >
          <Form
            form={form}
            layout="vertical"
            onFinish={handleSubmit}
            onValuesChange={(changedValues, allValues) => {
              setFormValues(allValues);
            }}
          >
            {customFormRender ? customFormRender(form, formConfig) : formConfig.fields.map(field => {
              // Проверяем видимость поля
              if (field.visible && !field.visible(formValues)) {
                return null;
              }

              // Для файловых полей при редактировании делаем правила необязательными
              let fieldRules = field.rules;
              if (field.type === 'file' && editingRecord !== null) {
                fieldRules = field.rules?.map(rule => 
                  rule.required ? { ...rule, required: false } : rule
                ) || [];
              }

              // Для native date/datetime inputs на мобильных нужна конвертация
              const isMobileDateField = isMobile && (field.type === 'date' || field.type === 'datetime');
              const dateFormat = field.type === 'datetime' ? 'YYYY-MM-DDTHH:mm' : 'YYYY-MM-DD';
              
              return (
                <Form.Item
                  key={field.name}
                  name={field.name}
                  label={field.label}
                  rules={fieldRules}
                  dependencies={field.dependencies}
                  valuePropName={field.type === 'switch' ? 'checked' : 'value'}
                  getValueFromEvent={
                    isMobileDateField
                      ? (e) => {
                          // Конвертируем строку из native input в dayjs
                          if (e && e.target) {
                            const value = e.target.value;
                            return value ? dayjs(value) : null;
                          }
                          return e;
                        }
                      : undefined
                  }
                  getValueProps={
                    isMobileDateField
                      ? (value) => {
                          // Конвертируем dayjs в строку для native input
                          return {
                            value: value && dayjs.isDayjs(value) ? value.format(dateFormat) : ''
                          };
                        }
                      : undefined
                  }
                >
                  {renderFormField(field, formConfig)}
                </Form.Item>
              );
            })}

            <Form.Item>
              <Space size={isMobile ? 'small' : 'middle'}>
                <Button type="primary" htmlType="submit" size={isMobile ? 'small' : 'middle'}>
                  {editingRecord ? 'Обновить' : 'Создать'}
                </Button>
                <Button onClick={() => setModalVisible(false)} size={isMobile ? 'small' : 'middle'}>
                  Отмена
                </Button>
              </Space>
            </Form.Item>
          </Form>
        </Modal>

        {/* DetailModal для десктопной версии */}
        <DetailModal
          visible={detailModalVisible}
          onClose={() => setDetailModalVisible(false)}
          record={selectedRecord}
          title={title}
          columns={columns}
        />
      </Card>
    </div>
  );
};

export default GenericDataTable;
