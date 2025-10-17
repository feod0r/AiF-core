import React, { useState, useEffect } from 'react';
import { 
  ProTable, 
  ProColumns,
} from '@ant-design/pro-components';
import { 
  Button, 
  Modal, 
  Form, 
  Select, 
  InputNumber, 
  DatePicker, 
  message, 
  Card, 
  Statistic, 
  Row, 
  Col,
  Tag,
  Popconfirm,
  Space,
  Alert,
  List,
  Drawer,
  Typography,
  Radio
} from 'antd';
import { 
  PlusOutlined, 
  EditOutlined, 
  DeleteOutlined,
  CloseCircleOutlined,
  DollarOutlined,
  CreditCardOutlined,
  SyncOutlined
} from '@ant-design/icons';
import dayjs from 'dayjs';
import { 
  terminalOperationsApi, 
  terminalsApi, 
  accountsApi 
} from '../services/api';
import { 
  TerminalOperation, 
  TerminalOperationCreate, 
  TerminalOperationUpdate,
  TerminalOperationSummary,
  Terminal,
  Account,
  CloseDayResponse,
  VendistaSyncResponse
} from '../types';

const { Option } = Select;
const { Title } = Typography;
const { RangePicker } = DatePicker;

type PeriodType = 'day' | 'week' | 'month' | 'year';

const TerminalOperations: React.FC = () => {
  const [operations, setOperations] = useState<TerminalOperation[]>([]);
  const [terminals, setTerminals] = useState<Terminal[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  const [summary, setSummary] = useState<TerminalOperationSummary | null>(null);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [closeDayModalVisible, setCloseDayModalVisible] = useState(false);
  const [editingOperation, setEditingOperation] = useState<TerminalOperation | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(dayjs().format('YYYY-MM-DD'));
  const [dateRange, setDateRange] = useState<[string, string]>([dayjs().format('YYYY-MM-DD'), dayjs().format('YYYY-MM-DD')]);
  const [periodType, setPeriodType] = useState<PeriodType>('day');
  const [isMobile, setIsMobile] = useState(false);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedOperation, setSelectedOperation] = useState<TerminalOperation | null>(null);
  const [form] = Form.useForm();
  const [closeDayForm] = Form.useForm();
  const [syncLoading, setSyncLoading] = useState(false);

  // Определяем мобильное устройство
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  const fetchOperations = async () => {
    try {
      setLoading(true);
      
      let params: any = {};
      
      if (periodType === 'day') {
        params.operation_date = selectedDate;
      } else {
        params.date_from = dateRange[0];
        params.date_to = dateRange[1];
      }
      
      const [operationsRes, summaryRes] = await Promise.all([
        terminalOperationsApi.list(params),
        terminalOperationsApi.getSummary({ 
          date_from: periodType === 'day' ? selectedDate : dateRange[0], 
          date_to: periodType === 'day' ? selectedDate : dateRange[1]
        })
      ]);
      setOperations(operationsRes);
      setSummary(summaryRes);
    } catch (error) {
      message.error('Ошибка при загрузке операций терминалов');
    } finally {
      setLoading(false);
    }
  };

  const fetchTerminals = async () => {
    try {
      const response = await terminalsApi.getList();
      setTerminals(Array.isArray(response) ? response : response.data || []);
    } catch (error) {
      message.error('Ошибка при загрузке терминалов');
    }
  };

  const fetchAccounts = async () => {
    try {
      const response = await accountsApi.getList();
      setAccounts(response);
    } catch (error) {
      message.error('Ошибка при загрузке счетов');
    }
  };

  useEffect(() => {
    fetchOperations();
  }, [selectedDate, dateRange, periodType]);

  useEffect(() => {
    fetchTerminals();
    fetchAccounts();
  }, []);

  const handlePeriodChange = (value: PeriodType) => {
    setPeriodType(value);
    
    const today = dayjs();
    let newDateRange: [string, string];
    
    switch (value) {
      case 'day':
        setSelectedDate(today.format('YYYY-MM-DD'));
        break;
      case 'week':
        newDateRange = [today.startOf('week').format('YYYY-MM-DD'), today.endOf('week').format('YYYY-MM-DD')];
        setDateRange(newDateRange);
        break;
      case 'month':
        newDateRange = [today.startOf('month').format('YYYY-MM-DD'), today.endOf('month').format('YYYY-MM-DD')];
        setDateRange(newDateRange);
        break;
      case 'year':
        newDateRange = [today.startOf('year').format('YYYY-MM-DD'), today.endOf('year').format('YYYY-MM-DD')];
        setDateRange(newDateRange);
        break;
    }
  };

  const handleDateChange = (date: any) => {
    if (periodType === 'day') {
      setSelectedDate(date?.format('YYYY-MM-DD') || dayjs().format('YYYY-MM-DD'));
    }
  };

  const handleDateRangeChange = (dates: any) => {
    if (dates && dates.length === 2) {
      setDateRange([dates[0].format('YYYY-MM-DD'), dates[1].format('YYYY-MM-DD')]);
    }
  };

  const handleCreate = () => {
    setEditingOperation(null);
    form.resetFields();
    form.setFieldsValue({
      operation_date: dayjs(selectedDate),
      commission: 0
    });
    setModalVisible(true);
  };

  const handleEdit = (record: TerminalOperation) => {
    setEditingOperation(record);
    form.setFieldsValue({
      ...record,
      operation_date: dayjs(record.operation_date),
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number) => {
    try {
      await terminalOperationsApi.delete(id);
      message.success('Операция удалена');
      fetchOperations();
    } catch (error) {
      message.error('Ошибка при удалении операции');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const data = {
        ...values,
        operation_date: values.operation_date.format('YYYY-MM-DD'),
      };

      if (editingOperation) {
        await terminalOperationsApi.update(editingOperation.id, data);
        message.success('Операция обновлена');
      } else {
        await terminalOperationsApi.create(data);
        message.success('Операция создана');
      }

      setModalVisible(false);
      fetchOperations();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Ошибка при сохранении операции';
      message.error(errorMsg);
    }
  };

  const handleCloseDay = () => {
    const closeDate = periodType === 'day' ? selectedDate : dateRange[0];
    closeDayForm.setFieldsValue({
      operation_date: dayjs(closeDate),
      closed_by: 1 // TODO: получать ID текущего пользователя
    });
    setCloseDayModalVisible(true);
  };

  const handleCloseDaySubmit = async (values: any) => {
    try {
      const data = {
        operation_date: values.operation_date.format('YYYY-MM-DD'),
        closed_by: values.closed_by,
      };

      const response: CloseDayResponse = await terminalOperationsApi.closeDay(data);
      
      Modal.success({
        title: 'День закрыт',
        content: (
          <div>
            <p>{response.message}</p>
            <p>Обработано операций: {response.closed_operations_count}</p>
            <p>Общая сумма: {response.total_amount_processed} ₽</p>
            {response.affected_accounts.length > 0 && (
              <div>
                <p><strong>Затронутые счета:</strong></p>
                {response.affected_accounts.map((acc) => (
                  <div key={acc.account_id}>
                    Счет {acc.account_number}: +{acc.amount} ₽ (операций: {acc.operations_count})
                  </div>
                ))}
              </div>
            )}
          </div>
        ),
      });

      setCloseDayModalVisible(false);
      fetchOperations();
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Ошибка при закрытии дня';
      message.error(errorMsg);
    }
  };

  const handleSyncVendista = async () => {
    try {
      setSyncLoading(true);
      
      const syncDate = periodType === 'day' ? selectedDate : dateRange[0];
      
      const response: VendistaSyncResponse = await terminalOperationsApi.syncVendista({
        sync_date: syncDate
      });
      
      if (response.success) {
        Modal.success({
          title: 'Синхронизация завершена',
          content: (
            <div>
              <p>{response.message}</p>
              <p>Синхронизировано терминалов: {response.synced_terminals}</p>
              <p>Общая сумма: {response.total_amount.toFixed(2)} ₽</p>
              <p>Общее количество транзакций: {response.total_transactions}</p>
              {response.errors.length > 0 && (
                <div>
                  <p><strong>Ошибки ({response.errors.length}):</strong></p>
                  <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                    {response.errors.map((error, index) => (
                      <div key={index} style={{ fontSize: '12px', color: '#ff4d4f', marginBottom: '4px' }}>
                        {error}
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ),
          onOk: async () => {
            // Обновляем данные после закрытия модального окна
            message.loading('Обновление данных...', 1);
            await fetchOperations();
            message.success('Данные обновлены');
          }
        });
      } else {
        message.error(response.message);
        // Даже при ошибке обновляем данные, возможно что-то синхронизировалось
        message.loading('Обновление данных...', 1);
        await fetchOperations();
      }
    } catch (error: any) {
      const errorMsg = error.response?.data?.detail || 'Ошибка при синхронизации';
      message.error(errorMsg);
      // При ошибке тоже обновляем данные
      message.loading('Обновление данных...', 1);
      await fetchOperations();
    } finally {
      setSyncLoading(false);
    }
  };

  const columns: ProColumns<TerminalOperation>[] = [
    {
      title: 'Дата',
      dataIndex: 'operation_date',
      key: 'operation_date',
      render: (_, record) => dayjs(record.operation_date).format('DD.MM.YYYY'),
      sorter: true,
    },
    {
      title: 'Терминал',
      dataIndex: ['terminal', 'name'],
      key: 'terminal',
      render: (_, record) => (
        <div>
          <div>{record.terminal.name}</div>
          {record.terminal.terminal && (
            <small style={{ color: '#666' }}>№{record.terminal.terminal}</small>
          )}
        </div>
      ),
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      render: (_, record) => `${Number(record.amount || 0).toFixed(2)} ₽`,
      sorter: true,
    },
    {
      title: 'Транзакций',
      dataIndex: 'transaction_count',
      key: 'transaction_count',
      sorter: true,
    },
    {
      title: 'Комиссия',
      dataIndex: 'commission',
      key: 'commission',
      render: (_, record) => `${Number(record.commission || 0).toFixed(2)} ₽`,
    },
    {
      title: 'К зачислению',
      key: 'net_amount',
      render: (_, record) => {
        const netAmount = Number(record.amount || 0) - Number(record.commission || 0);
        return `${netAmount.toFixed(2)} ₽`;
      },
    },
    {
      title: 'Статус',
      dataIndex: 'is_closed',
      key: 'is_closed',
      render: (_, record) => (
        <div>
          <Tag color={record.is_closed ? 'green' : 'orange'}>
            {record.is_closed ? 'Закрыт' : 'Открыт'}
          </Tag>
          {record.is_closed && record.closed_at && (
            <div style={{ fontSize: '12px', color: '#666' }}>
              {dayjs(record.closed_at).format('DD.MM.YYYY HH:mm')}
            </div>
          )}
        </div>
      ),
      filters: [
        { text: 'Открыт', value: false },
        { text: 'Закрыт', value: true },
      ],
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 150,
      render: (_, record) => (
        <Space>
          {!record.is_closed && (
            <>
              <Button
                type="link"
                icon={<EditOutlined />}
                onClick={() => handleEdit(record)}
                size="small"
              >
                Изменить
              </Button>
              <Popconfirm
                title="Удалить операцию?"
                description="Это действие нельзя отменить"
                onConfirm={() => handleDelete(record.id)}
                okText="Да"
                cancelText="Нет"
              >
                <Button
                  type="link"
                  danger
                  icon={<DeleteOutlined />}
                  size="small"
                >
                  Удалить
                </Button>
              </Popconfirm>
            </>
          )}
        </Space>
      ),
    },
  ];

  const hasOpenOperations = operations.some(op => !op.is_closed);
  const canCloseDay = periodType === 'day' && hasOpenOperations;

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
          <CreditCardOutlined /> Операции терминалов
        </Title>
      </div>
      
      {summary && (
        <Row gutter={isMobile ? 8 : 16} style={{ marginBottom: 24 }}>
          <Col span={isMobile ? 12 : 4}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Операций" : "Операций"}
                value={summary.total_operations}
                prefix={<DollarOutlined />}
                valueStyle={{ fontSize: isMobile ? 16 : undefined }}
              />
            </Card>
          </Col>
          <Col span={isMobile ? 12 : 4}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Сумма" : "Общая сумма"}
                value={Number(summary.total_amount || 0).toFixed(2)}
                suffix="₽"
                valueStyle={{ fontSize: isMobile ? 16 : undefined }}
              />
            </Card>
          </Col>
          <Col span={isMobile ? 12 : 4}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Комиссия" : "Комиссия"}
                value={Number(summary.total_commission || 0).toFixed(2)}
                suffix="₽"
                valueStyle={{ fontSize: isMobile ? 16 : undefined }}
              />
            </Card>
          </Col>
          <Col span={isMobile ? 12 : 4}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Транзакций" : "Транзакций"}
                value={summary.total_transactions}
                valueStyle={{ fontSize: isMobile ? 16 : undefined }}
              />
            </Card>
          </Col>
          <Col span={isMobile ? 12 : 4}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Открыто" : "Открыто"}
                value={summary.open_operations}
                valueStyle={{ 
                  color: '#cf1322',
                  fontSize: isMobile ? 16 : undefined
                }}
              />
            </Card>
          </Col>
          <Col span={isMobile ? 12 : 4}>
            <Card size={isMobile ? 'small' : 'default'}>
              <Statistic
                title={isMobile ? "Закрыто" : "Закрыто"}
                value={summary.closed_operations}
                valueStyle={{ 
                  color: '#3f8600',
                  fontSize: isMobile ? 16 : undefined
                }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Row justify="space-between" align="middle" style={{ marginBottom: 16 }}>
        <Col>
          <Space size={isMobile ? 'small' : 'middle'} direction={isMobile ? 'vertical' : 'horizontal'}>
            <Space size={isMobile ? 'small' : 'middle'}>
              <span style={{ fontSize: isMobile ? 14 : 16 }}>Период:</span>
              <Radio.Group 
                value={periodType} 
                onChange={(e) => handlePeriodChange(e.target.value)}
                size={isMobile ? 'small' : 'middle'}
                buttonStyle="solid"
              >
                <Radio.Button value="day">День</Radio.Button>
                <Radio.Button value="week">Неделя</Radio.Button>
                <Radio.Button value="month">Месяц</Radio.Button>
                <Radio.Button value="year">Год</Radio.Button>
              </Radio.Group>
            </Space>
            
            {periodType === 'day' ? (
              <Space size={isMobile ? 'small' : 'middle'}>
                <span style={{ fontSize: isMobile ? 14 : 16 }}>Дата:</span>
                <DatePicker
                  value={dayjs(selectedDate)}
                  onChange={handleDateChange}
                  size={isMobile ? 'small' : 'middle'}
                />
              </Space>
            ) : (
              <Space size={isMobile ? 'small' : 'middle'}>
                <span style={{ fontSize: isMobile ? 14 : 16 }}>Период:</span>
                <RangePicker
                  value={[dayjs(dateRange[0]), dayjs(dateRange[1])]}
                  onChange={handleDateRangeChange}
                  size={isMobile ? 'small' : 'middle'}
                />
              </Space>
            )}
          </Space>
        </Col>
        <Col>
          <Space size={isMobile ? 'small' : 'middle'} wrap>
            <Button 
              type="primary" 
              icon={<PlusOutlined />} 
              onClick={handleCreate}
              size={isMobile ? 'small' : 'middle'}
            >
              {isMobile ? 'Добавить' : 'Добавить операцию'}
            </Button>
            <Button 
              type="default" 
              icon={<SyncOutlined />} 
              onClick={handleSyncVendista}
              loading={syncLoading}
              size={isMobile ? 'small' : 'middle'}
            >
              {isMobile ? 'Синхр.' : 'Синхронизировать Vendista'}
            </Button>
            {canCloseDay && (
              <Button 
                type="default" 
                danger
                icon={<CloseCircleOutlined />} 
                onClick={handleCloseDay}
                size={isMobile ? 'small' : 'middle'}
              >
                {isMobile ? 'Закрыть' : 'Закрыть день'}
              </Button>
            )}
          </Space>
        </Col>
      </Row>

      {!hasOpenOperations && operations.length > 0 && periodType === 'day' && (
        <Alert
          message="День закрыт"
          description="Все операции за выбранную дату закрыты. Средства зачислены на расчетные счета."
          type="success"
          style={{ marginBottom: 16 }}
        />
      )}

      {periodType !== 'day' && operations.length > 0 && (
        <Alert
          message={`Период: ${dayjs(dateRange[0]).format('DD.MM.YYYY')} - ${dayjs(dateRange[1]).format('DD.MM.YYYY')}`}
          description={`Отображено ${operations.length} операций за выбранный период. Кнопка "Закрыть день" доступна только для просмотра по дням.`}
          type="info"
          style={{ marginBottom: 16 }}
        />
      )}

      {isMobile ? (
        // Мобильная версия - список
        <Card title="Операции терминалов" size="small">
          <List
            dataSource={operations}
            loading={loading}
            renderItem={(operation: TerminalOperation) => (
              <List.Item
                style={{ 
                  padding: '16px 0',
                  borderBottom: '1px solid #f0f0f0'
                }}
              >
                <div style={{ width: '100%' }}>
                  {/* Заголовок с терминалом */}
                  <div style={{ 
                    marginBottom: 12,
                    cursor: 'pointer'
                  }}
                  onClick={() => {
                    setSelectedOperation(operation);
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
                      {operation.terminal.name}
                    </span>
                  </div>

                  {/* Основная информация */}
                  <div style={{ marginBottom: 12 }}>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Дата:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {dayjs(operation.operation_date).format('DD.MM.YYYY')}
                      </span>
                    </div>
                    {operation.terminal.terminal && (
                      <div style={{ marginBottom: 8 }}>
                        <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                          Номер:
                        </span>
                        <span style={{ fontSize: 14, marginLeft: 8 }}>
                          №{operation.terminal.terminal}
                        </span>
                      </div>
                    )}
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Сумма:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {Number(operation.amount || 0).toFixed(2)} ₽
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Транзакций:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {operation.transaction_count}
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        Комиссия:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {Number(operation.commission || 0).toFixed(2)} ₽
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>
                        К зачислению:
                      </span>
                      <span style={{ fontSize: 14, marginLeft: 8 }}>
                        {(Number(operation.amount || 0) - Number(operation.commission || 0)).toFixed(2)} ₽
                      </span>
                    </div>
                    <div style={{ marginBottom: 8 }}>
                      <Tag color={operation.is_closed ? 'green' : 'orange'}>
                        {operation.is_closed ? 'Закрыт' : 'Открыт'}
                      </Tag>
                      {operation.is_closed && operation.closed_at && (
                        <span style={{ fontSize: 12, color: '#666', marginLeft: 8 }}>
                          {dayjs(operation.closed_at).format('DD.MM.YYYY HH:mm')}
                        </span>
                      )}
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
                  {!operation.is_closed && (
                    <>
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
                        onClick={() => handleEdit(operation)}
                      >
                        Изменить
                      </Button>
                      <Popconfirm
                        title="Удалить операцию?"
                        description="Это действие нельзя отменить"
                        onConfirm={() => handleDelete(operation.id)}
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
                    </>
                  )}
                  
                  {/* Кнопка закрытия дня для каждого элемента (только для дня) */}
                  {periodType === 'day' && !operation.is_closed && (
                    <Button 
                      type="default" 
                      danger
                      icon={<CloseCircleOutlined />} 
                      size="small"
                      style={{ 
                        fontSize: '12px',
                        padding: '4px 8px',
                        minWidth: 'auto',
                        height: '32px'
                      }}
                      onClick={handleCloseDay}
                    >
                      Закрыть
                    </Button>
                  )}
                </div>
              </List.Item>
            )}
          />
        </Card>
      ) : (
        // Десктопная версия - таблица
        <div style={{ position: 'relative' }}>
          <ProTable<TerminalOperation>
            columns={columns}
            dataSource={operations}
            rowKey="id"
            loading={loading}
            search={false}
            pagination={{
              pageSize: 20,
              showSizeChanger: true,
              showQuickJumper: true,
            }}
            options={{
              reload: () => fetchOperations(),
            }}
          />
          
          {/* Кнопка закрытия дня справа от таблицы */}
          {canCloseDay && (
            <div style={{
              position: 'absolute',
              right: '-60px',
              top: '50%',
              transform: 'translateY(-50%)',
              display: 'flex',
              flexDirection: 'column',
              gap: '8px'
            }}>
              <Button 
                type="default" 
                danger
                icon={<CloseCircleOutlined />} 
                onClick={handleCloseDay}
                style={{
                  height: 'auto',
                  minHeight: '120px',
                  writingMode: 'vertical-rl',
                  textOrientation: 'mixed',
                  padding: '16px 8px',
                  fontSize: '14px',
                  fontWeight: 'bold'
                }}
              >
                Закрыть день
              </Button>
            </div>
          )}
        </div>
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
                {selectedOperation?.terminal.name}
              </div>
              <div style={{ 
                fontSize: 12, 
                color: '#999',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                Операции терминалов
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
        {selectedOperation && (
          <div>
            {/* Основная информация */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 16 }}>
                <span style={{ fontSize: 14, fontWeight: 'bold', marginBottom: 8, display: 'block' }}>
                  Основная информация:
                </span>
                <div style={{ fontSize: 14, color: '#666' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    🏦 Терминал: {selectedOperation.terminal.name}
                  </div>
                  {selectedOperation.terminal.terminal && (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                      🔢 Номер: №{selectedOperation.terminal.terminal}
                    </div>
                  )}
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    📅 Дата: {dayjs(selectedOperation.operation_date).format('DD.MM.YYYY')}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    💰 Сумма: {Number(selectedOperation.amount || 0).toFixed(2)} ₽
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    💳 Транзакций: {selectedOperation.transaction_count}
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    💸 Комиссия: {Number(selectedOperation.commission || 0).toFixed(2)} ₽
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    💵 К зачислению: {(Number(selectedOperation.amount || 0) - Number(selectedOperation.commission || 0)).toFixed(2)} ₽
                  </div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    {selectedOperation.is_closed ? '✅ Закрыт' : '🟡 Открыт'}
                    {selectedOperation.is_closed && selectedOperation.closed_at && (
                      <span style={{ fontSize: 12, color: '#666' }}>
                        {dayjs(selectedOperation.closed_at).format('DD.MM.YYYY HH:mm')}
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* Действия */}
            {!selectedOperation.is_closed && (
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
                    handleEdit(selectedOperation);
                  }}
                >
                  Изменить
                </Button>
                <Popconfirm
                  title="Удалить операцию?"
                  description="Это действие нельзя отменить"
                  onConfirm={() => {
                    setDetailDrawerVisible(false);
                    handleDelete(selectedOperation.id);
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
            )}
          </div>
        )}
      </Drawer>

      {/* Модальное окно создания/редактирования */}
      <Modal
        title={editingOperation ? 'Редактировать операцию' : 'Создать операцию'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={isMobile ? '100%' : 600}
        style={isMobile ? { margin: 16, maxWidth: 'calc(100vw - 32px)' } : {}}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
        >
          <Form.Item
            name="operation_date"
            label="Дата операции"
            rules={[{ required: true, message: 'Выберите дату' }]}
          >
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="terminal_id"
            label="Терминал"
            rules={[{ required: true, message: 'Выберите терминал' }]}
          >
            <Select placeholder="Выберите терминал">
              {terminals.map(terminal => (
                <Option key={terminal.id} value={terminal.id}>
                  {terminal.name}
                  {terminal.terminal && ` (№${terminal.terminal})`}
                  {terminal.account && ` - ${terminal.account.account_number}`}
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="amount"
            label="Сумма покупок"
            rules={[{ required: true, message: 'Укажите сумму' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              step={0.01}
              precision={2}
              addonAfter="₽"
            />
          </Form.Item>

          <Form.Item
            name="transaction_count"
            label="Количество транзакций"
            rules={[{ required: true, message: 'Укажите количество транзакций' }]}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              step={1}
            />
          </Form.Item>

          <Form.Item
            name="commission"
            label="Комиссия"
            rules={[{ required: true, message: 'Укажите комиссию' }]}
            initialValue={0}
          >
            <InputNumber
              style={{ width: '100%' }}
              min={0}
              step={0.01}
              precision={2}
              addonAfter="₽"
            />
          </Form.Item>
        </Form>
      </Modal>

      {/* Модальное окно закрытия дня */}
      <Modal
        title="Закрыть день"
        open={closeDayModalVisible}
        onCancel={() => setCloseDayModalVisible(false)}
        onOk={() => closeDayForm.submit()}
        okText="Закрыть день"
        okButtonProps={{ danger: true }}
        width={isMobile ? '100%' : 600}
        style={isMobile ? { margin: 16, maxWidth: 'calc(100vw - 32px)' } : {}}
      >
        <Alert
          message="Внимание!"
          description="При закрытии дня все открытые операции будут обработаны, и средства будут зачислены на расчетные счета терминалов. Это действие нельзя отменить."
          type="warning"
          style={{ marginBottom: '16px' }}
        />
        
        <Form
          form={closeDayForm}
          layout="vertical"
          onFinish={handleCloseDaySubmit}
        >
          <Form.Item
            name="operation_date"
            label="Дата закрытия"
            rules={[{ required: true, message: 'Выберите дату' }]}
          >
            <DatePicker style={{ width: '100%' }} disabled />
          </Form.Item>

          <Form.Item
            name="closed_by"
            label="Пользователь"
            rules={[{ required: true, message: 'Выберите пользователя' }]}
          >
            <InputNumber style={{ width: '100%' }} disabled value={1} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default TerminalOperations;
