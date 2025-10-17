import React, { useMemo, useState } from 'react';
import { CreditCardOutlined, ReloadOutlined } from '@ant-design/icons';
import { Tag, Button, message } from 'antd';
import GenericDataTable from '../components/GenericDataTable';
import { accountsApi, accountTypesApi, ownersApi } from '../services/api';
import { Account, AccountType, Owner } from '../types';
import dayjs from 'dayjs';

const Accounts: React.FC = () => {
  const [isUpdatingBalances, setIsUpdatingBalances] = useState(false);
  const [refreshTrigger, setRefreshTrigger] = useState(0);

  // Функция для обновления всех балансов
  const handleUpdateAllBalances = async () => {
    try {
      setIsUpdatingBalances(true);
      const result = await accountsApi.updateAllBalances();
      
      message.success({
        content: result.message,
        duration: 5,
      });

      // Обновляем таблицу после успешного обновления
      setRefreshTrigger(prev => prev + 1);
      
    } catch (error: any) {
      message.error({
        content: error.response?.data?.detail || 'Ошибка при обновлении балансов',
        duration: 5,
      });
    } finally {
      setIsUpdatingBalances(false);
    }
  };

  // Функция для получения цвета тега типа счета
  const getTypeTag = (type: string) => {
    const typeMap: { [key: string]: string } = {
      'Наличные': 'green',
      'Банковский счет': 'blue',
      'Кредитная карта': 'orange',
      'Дебетовая карта': 'purple',
      'Электронный кошелек': 'cyan',
    };
    return typeMap[type] || 'default';
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
    },
    {
      title: 'Тип счета',
      dataIndex: ['accountType', 'name'],
      key: 'accountType',
      render: (_: any, record: Account): React.ReactElement => {
        const typeName = (record as any).account_type?.name || (record as any).accountType?.name;
        return (
          <Tag color={getTypeTag(typeName)}>
            {typeName}
          </Tag>
        );
      },
    },
    {
      title: 'Владелец',
      dataIndex: ['owner', 'name'],
      key: 'owner',
    },
    {
      title: 'Баланс',
      dataIndex: 'balance',
      key: 'balance',
      render: (balance: any, record: Account): React.ReactElement => {
        const num = typeof balance === 'string' ? parseFloat(balance) : balance;
        return (
          <span style={{ fontWeight: 'bold', color: num >= 0 ? 'green' : 'red' }}>
            {num.toLocaleString('ru-RU')} {record.currency}
          </span>
        );
      },
    },
    {
      title: 'Начальный баланс',
      dataIndex: 'initial_balance',
      key: 'initial_balance',
      render: (initial_balance: any, record: Account): React.ReactElement => {
        const num = typeof initial_balance === 'string' ? parseFloat(initial_balance) : initial_balance;
        return (
          <span style={{ fontWeight: 'bold', color: num >= 0 ? 'green' : 'red' }}>
            {num.toLocaleString('ru-RU')} {record.currency}
          </span>
        );
      },
    },
    {
      title: 'Номер счета',
      dataIndex: 'account_number',
      key: 'account_number',
      ellipsis: true,
    },
    {
      title: 'Банк',
      dataIndex: 'bank_name',
      key: 'bank_name',
      ellipsis: true,
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean): React.ReactElement => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Активен' : 'Неактивен'}
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
      placeholder: 'Поиск по названию или номеру счета',
    },
    {
      key: 'account_type_id',
      label: 'Тип счета',
      type: 'select' as const,
      placeholder: 'Выберите тип счета',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const accountTypes = await accountTypesApi.getList();
        return accountTypes.map((type: AccountType) => ({
          label: type.name,
          value: type.id,
        }));
      },
    },
    {
      key: 'owner_id',
      label: 'Владелец',
      type: 'select' as const,
      placeholder: 'Выберите владельца',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const owners = await ownersApi.getList();
        const ownersList = owners.data || owners;
        return ownersList.map((owner: Owner) => ({
          label: owner.name,
          value: owner.id,
        }));
      },
    },
    {
      key: 'is_active',
      label: 'Статус',
      type: 'select' as const,
      placeholder: 'Выберите статус',
      options: [
        { label: 'Активен', value: true },
        { label: 'Неактивен', value: false },
      ],
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
        label: 'Название счета',
        type: 'input' as const,
        rules: [{ required: true, message: 'Введите название счета' }],
        placeholder: 'Введите название счета',
      },
      {
        name: 'account_type_id',
        label: 'Тип счета',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите тип счета' }],
        placeholder: 'Выберите тип счета',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const accountTypes = await accountTypesApi.getList();
          return accountTypes.map((type: AccountType) => ({
            label: type.name,
            value: type.id,
          }));
        },
      },
      {
        name: 'owner_id',
        label: 'Владелец',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите владельца' }],
        placeholder: 'Выберите владельца',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const owners = await ownersApi.getList();
          const ownersList = owners.data || owners;
          return ownersList.map((owner: Owner) => ({
            label: owner.name,
            value: owner.id,
          }));
        },
      },
      {
        name: 'balance',
        label: 'Баланс',
        type: 'number' as const,
        rules: [{ required: true, message: 'Введите баланс' }],
        placeholder: 'Введите баланс',
        step: 0.01,
      },
      {
        name: 'initial_balance',
        label: 'Начальный баланс',
        type: 'number' as const,
        rules: [{ required: true, message: 'Введите начальный баланс' }],
        placeholder: 'Введите начальный баланс',
        step: 0.01,
      },
      {
        name: 'currency',
        label: 'Валюта',
        type: 'input' as const,
        rules: [{ required: true, message: 'Введите валюту' }],
        placeholder: 'Например: RUB, USD, EUR',
      },
      {
        name: 'account_number',
        label: 'Номер счета',
        type: 'input' as const,
        placeholder: 'Введите номер счета',
      },
      {
        name: 'bank_name',
        label: 'Название банка',
        type: 'input' as const,
        placeholder: 'Введите название банка',
      },
      {
        name: 'is_active',
        label: 'Активен',
        type: 'switch' as const,
        initialValue: true,
      },
      {
        name: 'start_date',
        label: 'Дата создания',
        type: 'date' as const,
        placeholder: 'Выберите дату создания',
      },
      {
        name: 'end_date',
        label: 'Дата закрытия',
        type: 'date' as const,
        placeholder: 'Выберите дату закрытия',
      },
    ],
    initialValues: {
      start_date: dayjs(),
      end_date: dayjs().add(10, 'year'),
      is_active: true,
      currency: 'RUB',
    },
  }), []);

  // Кастомная обработка данных для редактирования
  const prepareDataForEdit = (record: Account) => {
    return {
      ...record,
      account_type_id: (record as any).account_type_id ?? record.accountType?.id,
      owner_id: (record as any).owner_id ?? record.owner?.id,
      balance: typeof record.balance === 'string' ? parseFloat(record.balance) : record.balance,
      initial_balance: typeof record.initial_balance === 'string' ? parseFloat(record.initial_balance) : record.initial_balance,
      start_date: record.start_date ? dayjs(record.start_date) : dayjs(),
      end_date: record.end_date ? dayjs(record.end_date) : dayjs().add(10, 'year'),
    };
  };

  // Кастомная обработка submit
  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        balance: typeof values.balance === 'string' ? parseFloat(values.balance) : values.balance,
        initial_balance: typeof values.initial_balance === 'string' ? parseFloat(values.initial_balance) : values.initial_balance,
        is_active: values.is_active !== undefined ? values.is_active : true,
        start_date: values.start_date ? values.start_date.toISOString() : dayjs().toISOString(),
        end_date: values.end_date ? values.end_date.toISOString() : dayjs().add(10, 'year').toISOString(),
      };

      return submitData;
    } catch (error) {
      throw error;
    }
  };

  // Кастомная обработка submit для создания
  const handleCreate = async (data: any) => {
    const processedData = await handleSubmit(data);
    return accountsApi.create(processedData);
  };

  // Кастомная обработка submit для обновления
  const handleUpdate = async (id: number, data: any) => {
    const processedData = await handleSubmit(data);
    return accountsApi.update(id, processedData);
  };

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    const response = await accountsApi.getList(params);
    return response; // accountsApi.getList возвращает Account[] напрямую
  };

  return (
    <div>
      <div style={{ 
        display: 'flex', 
        justifyContent: 'space-between', 
        alignItems: 'center', 
        marginBottom: 16,
        flexWrap: 'wrap',
        gap: 8
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <CreditCardOutlined style={{ fontSize: 20 }} />
          <h2 style={{ margin: 0, fontSize: 18 }}>Счета</h2>
        </div>
        <Button
          type="default"
          icon={<ReloadOutlined />}
          loading={isUpdatingBalances}
          onClick={handleUpdateAllBalances}
          style={{ minWidth: 150 }}
        >
          {isUpdatingBalances ? 'Обновление...' : 'Обновить балансы'}
        </Button>
      </div>
      
      <GenericDataTable<Account>
        title=""
        columns={columns}
        filters={filters}
        formConfig={formConfig}
        onEditDataTransform={prepareDataForEdit}
        onActionComplete={() => setRefreshTrigger(prev => prev + 1)}
        endpoints={{
          list: handleList,
          create: handleCreate,
          update: handleUpdate,
          delete: accountsApi.delete,
        }}
        searchable={true}
        exportable={true}
        addButtonText="Добавить счет"
        pagination={{
          pageSize: 100,
          pageSizeOptions: ['100', '200', '500', '800', '1000'],
        }}
        key={refreshTrigger}
      />
    </div>
  );
};

export default Accounts; 