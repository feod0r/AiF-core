import React, { useMemo, useState, useEffect } from 'react';
import { DollarOutlined, CheckCircleOutlined } from '@ant-design/icons';
import { Tag, message } from 'antd';
import GenericDataTable from '../components/GenericDataTable';
import { 
  transactionsApi, 
  accountsApi, 
  transactionCategoriesApi, 
  counterpartiesApi,
  machinesApi,
  rentApi,

} from '../services/api';
import { 
  Transaction, 
  Account, 
  TransactionCategory, 
  Counterparty,
  Machine,
  Rent
} from '../types';
import dayjs from 'dayjs';

const Transactions: React.FC = () => {
  const [isMobile, setIsMobile] = useState(false);

  // Определяем мобильное устройство
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Вспомогательные функции
  const getTypeKey = (t: any): 'income' | 'expense' | 'transfer' | 'unknown' => {
    const name = (t?.transaction_type?.name || (t as any).type || '').toString().toLowerCase();
    if (name === 'income' || name === 'expense' || name === 'transfer') return name;
    return 'unknown';
  };

  const getTypeTag = (type: string) => {
    const typeMap: { [key: string]: { color: string; text: string } } = {
      'income': { color: 'green', text: 'Доход' },
      'expense': { color: 'red', text: 'Расход' },
      'transfer': { color: 'blue', text: 'Перевод' },
      'unknown': { color: 'default', text: '—' },
    };
    return typeMap[type] || { color: 'default', text: type };
  };

  const toNumber = (v: any): number => {
    if (v === null || v === undefined) return 0;
    if (typeof v === 'number') return v;
    const n = parseFloat(String(v));
    return isNaN(n) ? 0 : n;
  };

  // Конфигурация колонок
  const columns = useMemo(() => {
    const baseColumns = [
      {
        title: 'ID',
        dataIndex: 'id',
        key: 'id',
        width: 80,
      },
      {
        title: 'Дата',
        dataIndex: 'date',
        key: 'date',
        render: (date: string) => dayjs(date).format('DD.MM.YYYY HH:mm'),
      },
      {
        title: 'Тип',
        key: 'type',
        render: (_: any, record: Transaction) => {
          const tk = getTypeKey(record);
          const typeInfo = getTypeTag(tk);
          return <Tag color={typeInfo.color}>{typeInfo.text}</Tag>;
        },
      },
      {
        title: 'Категория',
        dataIndex: ['category', 'name'],
        key: 'category',
        render: (_: any, record: Transaction) => {
          const category = record.category as TransactionCategory;
          if (!category) return '-';
          const typeInfo = getTypeTag(category.transactionType?.type || 'unknown');
          return (
            <Tag color={typeInfo.color}>
              {category.name}
            </Tag>
          );
        },
      },
      {
        title: 'Счет',
        dataIndex: ['account', 'name'],
        key: 'account',
      },
      {
        title: 'Счет назначения',
        dataIndex: ['to_account', 'name'],
        key: 'to_account',
        render: (_: any, record: Transaction) => {
          const toAccount = record.to_account as Account;
          if (!toAccount) return '-';
          return toAccount.name;
        },
      },
      {
        title: 'Сумма',
        dataIndex: 'amount',
        key: 'amount',
        render: (amount: number, record: Transaction) => {
          const val = toNumber(amount);
          const tk = getTypeKey(record);
          
          if (tk === 'transfer') {
            const abs = Math.abs(val);
            return (
              <span style={{ fontWeight: 'bold', color: 'blue' }}>
                {abs.toLocaleString('ru-RU')} ₽
              </span>
            );
          } else {
            const color = val > 0 ? 'green' : val < 0 ? 'red' : 'blue';
            const sign = val < 0 ? '-' : '+';
            const abs = Math.abs(val);
            return (
              <span style={{ fontWeight: 'bold', color }}>
                {sign}{abs.toLocaleString('ru-RU')} ₽
              </span>
            );
          }
        },
      },
      {
        title: 'Контрагент',
        dataIndex: ['counterparty', 'name'],
        key: 'counterparty',
        ellipsis: true,
      },
      {
        title: 'Автомат',
        dataIndex: ['machine', 'name'],
        key: 'machine',
        ellipsis: true,
        render: (_: any, record: Transaction) => {
          const machine = record.machine;
          return machine?.name || '-';
        },
      },
      {
        title: 'Подтверждена',
        dataIndex: 'is_confirmed',
        key: 'is_confirmed',
        render: (isConfirmed: boolean) => (
          <Tag color={isConfirmed ? 'green' : 'orange'}>
            {isConfirmed ? 'Да' : 'Нет'}
          </Tag>
        ),
      },
      {
        title: 'Описание',
        dataIndex: 'description',
        key: 'description',
        className: 'hidden-column', // Скрываем колонку в таблице
        width: 0,
        render: (description: string) => description || '-',
      },
      {
        title: 'Номер документа',
        dataIndex: 'reference_number',
        key: 'reference_number',
        className: 'hidden-column', // Скрываем колонку в таблице
        width: 0,
        render: (refNumber: string) => refNumber || '-',
      },
    ];

    // Для мобильной версии перемещаем важные колонки в начало и заменяем ID на Автомат
    if (isMobile) {
      const sumColumn = baseColumns.find(col => col.key === 'amount');
      const dateColumn = baseColumns.find(col => col.key === 'date');
      const typeColumn = baseColumns.find(col => col.key === 'type');
      const accountColumn = baseColumns.find(col => col.key === 'account');
      const machineColumn = baseColumns.find(col => col.key === 'machine');
      const otherColumns = baseColumns.filter(col => 
        col.key !== 'amount' && col.key !== 'date' && col.key !== 'type' && 
        col.key !== 'account' && col.key !== 'machine' && col.key !== 'id' &&
        col.key !== 'description' && col.key !== 'reference_number' // Исключаем скрытые поля из основного списка
      );
      const mobileColumns = [sumColumn, dateColumn, typeColumn, accountColumn, machineColumn, ...otherColumns].filter(Boolean);
      return mobileColumns as any;
    }

    return baseColumns;
  }, [isMobile]);

  // Конфигурация фильтров (соответствуют API бэкенда)
  const filters = useMemo(() => [
    {
      key: 'account_id',
      label: 'Счет',
      type: 'select' as const,
      placeholder: 'Выберите счет',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const accounts = await accountsApi.getList();
        return accounts.map((account: Account) => ({
          label: `${account.name} (${account.owner?.name})`,
          value: account.id,
        }));
      },
    },
    {
      key: 'category_id',
      label: 'Категория',
      type: 'select' as const,
      placeholder: 'Выберите категорию',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const categories = await transactionCategoriesApi.getList();
        return categories.map((category: TransactionCategory) => ({
          label: category.name,
          value: category.id,
        }));
      },
    },
    {
      key: 'counterparty_id',
      label: 'Контрагент',
      type: 'select' as const,
      placeholder: 'Выберите контрагента',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const counterparties = await counterpartiesApi.getList();
        return counterparties.map((counterparty: Counterparty) => ({
          label: counterparty.name,
          value: counterparty.id,
        }));
      },
    },
    {
      key: 'machine_id',
      label: 'Автомат',
      type: 'select' as const,
      placeholder: 'Выберите автомат',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const machines = await machinesApi.getList();
        const machinesList = machines.data || machines;
        return machinesList.map((machine: Machine) => ({
          label: machine.name,
          value: machine.id,
        }));
      },
    },
    {
      key: 'rent_location_id',
      label: 'Точка аренды',
      type: 'select' as const,
      placeholder: 'Выберите точку аренды',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const rents = await rentApi.getList();
        return rents.map((rent: any) => ({
          label: rent.location,
          value: rent.id,
        }));
      },
    },
    {
      key: 'is_confirmed',
      label: 'Статус подтверждения',
      type: 'select' as const,
      placeholder: 'Выберите статус',
      options: [
        { label: 'Подтверждена', value: true },
        { label: 'Не подтверждена', value: false },
      ],
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
  ], []);

  // Конфигурация формы
  const formConfig = useMemo(() => ({
    fields: [
      {
        name: 'date',
        label: 'Дата',
        type: 'datetime' as const,
        rules: [{ required: true, message: 'Выберите дату' }],
        placeholder: 'Выберите дату и время',
      },
      {
        name: 'type',
        label: 'Тип операции',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите тип операции' }],
        options: [
          { label: 'Доход', value: 'income' },
          { label: 'Расход', value: 'expense' },
          { label: 'Перевод', value: 'transfer' },
        ],
      },
      {
        name: 'account_id',
        label: 'Счет',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите счет' }],
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const accounts = await accountsApi.getList();
          return accounts.map((account: Account) => ({
            label: `${account.name} (${account.owner?.name})`,
            value: account.id,
          }));
        },
      },
      {
        name: 'to_account_id',
        label: 'Счет назначения',
        type: 'select' as const,
        placeholder: 'Выберите счет назначения',
        visible: (values: any) => values.type === 'transfer',
        rules: [
          ({ getFieldValue }: any) => ({
            validator(_: any, value: any) {
                          if (getFieldValue('type') === 'transfer' && !value) {
                            return Promise.reject(new Error('Для перевода необходимо указать счет назначения'));
                          }
                          return Promise.resolve();
                        },
                      }),
        ],
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const accounts = await accountsApi.getList();
          return accounts.map((account: Account) => ({
            label: `${account.name} (${account.owner?.name})`,
            value: account.id,
          }));
        },
      },
      {
        name: 'category_id',
        label: 'Категория',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите категорию' }],
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const categories = await transactionCategoriesApi.getList();
          return categories.map((category: TransactionCategory) => ({
            label: category.name,
            value: category.id,
          }));
        },
      },
      {
        name: 'amount',
        label: 'Сумма',
        type: 'number' as const,
        rules: [{ required: true, message: 'Введите сумму' }],
        placeholder: 'Введите сумму',
      },
      {
        name: 'counterparty_id',
        label: 'Контрагент',
        type: 'select' as const,
        placeholder: 'Выберите контрагента',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const counterparties = await counterpartiesApi.getList();
          return counterparties.map((counterparty: Counterparty) => ({
            label: counterparty.name,
            value: counterparty.id,
          }));
        },
      },
      {
        name: 'machine_id',
        label: 'Автомат',
        type: 'select' as const,
        placeholder: 'Выберите автомат',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const machines = await machinesApi.getList();
          const machinesList = machines.data || machines;
          return machinesList.map((machine: Machine) => ({
            label: machine.name,
            value: machine.id,
          }));
        },
      },
      {
        name: 'rent_location_id',
        label: 'Точка аренды',
        type: 'select' as const,
        placeholder: 'Выберите точку аренды',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const rentLocations = await rentApi.getList();
          return rentLocations.map((rent: Rent) => ({
            label: rent.location,
            value: rent.id,
          }));
        },
      },
      {
        name: 'description',
        label: 'Описание',
        type: 'textarea' as const,
        placeholder: 'Введите описание операции',
      },
      {
        name: 'reference_number',
        label: 'Номер документа',
        type: 'input' as const,
        placeholder: 'Введите номер документа',
      },
    ],
    initialValues: {
      date: dayjs(),
      is_confirmed: false,
    },
  }), []);

  // Дополнительные действия для строк
  const rowActions = useMemo(() => [
    {
      key: 'confirm',
      title: 'Утвердить',
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      visible: (record: Transaction) => !record.is_confirmed,
      onClick: async (record: Transaction) => {
        try {
          await transactionsApi.confirm(record.id);
          message.success('Операция подтверждена');
        } catch (error) {
          message.error('Ошибка при подтверждении операции');
          throw error; // Пробрасываем ошибку, чтобы GenericDataTable знал о неудаче
        }
      },
    },
  ], []);

  // Кастомная обработка submit для правильного расчета суммы
  const handleSubmit = async (values: any) => {
    try {
      const rawAmount = toNumber(values.amount);
      let signedAmount;
      
      if (values.type === 'transfer') {
        signedAmount = -Math.abs(rawAmount);
      } else {
        signedAmount = values.type === 'expense' ? -Math.abs(rawAmount) : Math.abs(rawAmount);
      }
      
      // Убеждаемся, что date является dayjs объектом перед вызовом toISOString
      const formattedDate = dayjs.isDayjs(values.date) 
        ? values.date.toISOString()
        : dayjs(values.date).toISOString();
      
      const submitData = {
        ...values,
        date: formattedDate,
        amount: signedAmount,
        transaction_type_id: values.type === 'income' ? 1 : values.type === 'expense' ? 2 : 3,
        is_confirmed: values.is_confirmed !== undefined ? values.is_confirmed : false,
      };

      return submitData;
    } catch (error) {
      throw error;
    }
  };

  // Кастомная обработка данных для редактирования
  const prepareDataForEdit = (record: Transaction) => {
    return {
      ...record,
      date: record.date ? dayjs(record.date) : dayjs(),
      type: getTypeKey(record),
      account_id: (record as any).account_id ?? record.account?.id,
      to_account_id: (record as any).to_account_id ?? record.to_account?.id,
      category_id: (record as any).category_id ?? record.category?.id,
      counterparty_id: (record as any).counterparty_id ?? record.counterparty?.id,
      machine_id: (record as any).machine_id ?? record.machine?.id,
      rent_location_id: (record as any).rent_location_id ?? (record as any).rent_location?.id,
      amount: Math.abs(toNumber(record.amount)), // Показываем абсолютное значение в форме
    };
  };

  // Переопределяем эндпоинты для кастомной обработки
  const customEndpoints = {
    list: transactionsApi.getList,
    create: async (data: any) => {
      const processedData = await handleSubmit(data);
      return transactionsApi.create(processedData);
    },
    update: async (id: number, data: any) => {
      const processedData = await handleSubmit(data);
      return transactionsApi.update(id, processedData);
    },
    delete: transactionsApi.delete,
  };

  return (
    <div>
      <style>
        {`
          .hidden-column {
            display: none !important;
            width: 0 !important;
            min-width: 0 !important;
            max-width: 0 !important;
          }
          .ant-table-thead > tr > .hidden-column,
          .ant-table-tbody > tr > .hidden-column {
            display: none !important;
            padding: 0 !important;
            border: none !important;
          }
        `}
      </style>
      <GenericDataTable<Transaction>
      title="Операции"
      icon={<DollarOutlined />}
      endpoints={customEndpoints}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      rowActions={rowActions}
      searchable={true}
      exportable={true}
      addButtonText="Добавить операцию"
      pagination={{
        pageSize: 100,
        pageSizeOptions: ['100', '200', '500', '800', '1000'],
      }}
      onEditDataTransform={prepareDataForEdit}
      dashboardConfig={{
        fetchSummary: transactionsApi.getSummary,
        title: 'Финансовая сводка по операциям',
        showDateFilter: true,
      }}
    />
    </div>
  );
};

export default Transactions; 
