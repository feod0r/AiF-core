import React, { useMemo } from 'react';
import { CreditCardOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { 
  terminalsApi, 
  ownersApi, 
  accountsApi 
} from '../services/api';
import { 
  Terminal, 
  Owner, 
  Account 
} from '../types';
import dayjs from 'dayjs';

const Terminals: React.FC = () => {
  // Конфигурация колонок
  const columns = useMemo(() => [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Номер терминала',
      dataIndex: 'terminal',
      key: 'terminal',
      width: 120,
    },
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true,
    },
    {
      title: 'ИП (Владелец)',
      dataIndex: ['owner', 'name'],
      key: 'owner',
      width: 250,
      render: (_: any, record: Terminal) => {
        if (record.owner) {
          return `${record.owner.name} (${record.owner.inn})`;
        }
        return '-';
      },
    },
    {
      title: 'Расчетный счет',
      dataIndex: ['account', 'name'],
      key: 'account',
      width: 200,
      render: (_: any, record: Terminal) => {
        if (record.account) {
          return `${record.account.name} (${Number(record.account.balance).toFixed(2)} ₽)`;
        }
        return 'Не указан';
      },
    },
    {
      title: 'Дата начала',
      dataIndex: 'start_date',
      key: 'start_date',
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString('ru-RU'),
    },
  ], []);

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'search',
      label: 'Поиск',
      type: 'input' as const,
      placeholder: 'Поиск по номеру или названию',
    },
    {
      key: 'owner_id',
      label: 'Владелец',
      type: 'select' as const,
      placeholder: 'Выберите владельца',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const owners = await ownersApi.getList({ pageSize: 1000 });
        const ownersList = owners.data || owners;
        return ownersList.map((owner: Owner) => ({
          label: `${owner.name} (${owner.inn})`,
          value: owner.id,
        }));
      },
    },
    {
      key: 'account_id',
      label: 'Расчетный счет',
      type: 'select' as const,
      placeholder: 'Выберите счет',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const accounts = await accountsApi.getList();
        const accountsList = Array.isArray(accounts) ? accounts : (accounts as any).data || [];
        return accountsList.map((account: Account) => ({
          label: `${account.name} (${Number(account.balance).toFixed(2)} ₽)`,
          value: account.id,
        }));
      },
    },
    {
      key: 'start_date_from',
      label: 'Дата начала от',
      type: 'date' as const,
      placeholder: 'Выберите дату от',
    },
    {
      key: 'start_date_to',
      label: 'Дата начала до',
      type: 'date' as const,
      placeholder: 'Выберите дату до',
    },
  ], []);

  // Конфигурация формы
  const formConfig = useMemo(() => ({
    fields: [
      {
        name: 'terminal',
        label: 'Номер терминала',
        type: 'number' as const,
        rules: [{ required: true, message: 'Пожалуйста, введите номер терминала' }],
        placeholder: 'Введите номер терминала',
      },
      {
        name: 'name',
        label: 'Название',
        type: 'input' as const,
        rules: [{ required: true, message: 'Пожалуйста, введите название' }],
        placeholder: 'Введите название',
      },
      {
        name: 'owner_id',
        label: 'ИП (Владелец)',
        type: 'select' as const,
        placeholder: 'Выберите владельца',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const owners = await ownersApi.getList({ pageSize: 1000 });
          const ownersList = owners.data || owners;
          return ownersList.map((owner: Owner) => ({
            label: `${owner.name} (${owner.inn})`,
            value: owner.id,
          }));
        },
      },
      {
        name: 'account_id',
        label: 'Расчетный счет',
        type: 'select' as const,
        placeholder: 'Выберите расчетный счет',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          const accounts = await accountsApi.getList();
          const accountsList = Array.isArray(accounts) ? accounts : (accounts as any).data || [];
          return accountsList.map((account: Account) => ({
            label: `${account.name} (Баланс: ${Number(account.balance).toFixed(2)} ₽)`,
            value: account.id,
          }));
        },
      },
      {
        name: 'start_date',
        label: 'Дата начала',
        type: 'date' as const,
        placeholder: 'Выберите дату начала',
      },
      {
        name: 'end_date',
        label: 'Дата окончания',
        type: 'date' as const,
        placeholder: 'Выберите дату окончания',
      },
    ],
    initialValues: {
      start_date: dayjs(),
      end_date: dayjs().add(1, 'year'),
    },
  }), []);

  // Кастомная обработка данных для редактирования
  const prepareDataForEdit = (record: Terminal) => {
    return {
      ...record,
      start_date: record.start_date ? dayjs(record.start_date) : dayjs(),
      end_date: record.end_date ? dayjs(record.end_date) : dayjs().add(1, 'year'),
      owner_id: (record as any).owner_id ?? record.owner?.id,
      account_id: (record as any).account_id ?? record.account?.id,
    };
  };

  // Кастомная обработка submit для правильного форматирования дат
  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        start_date: values.start_date ? values.start_date.toISOString() : null,
        end_date: values.end_date ? values.end_date.toISOString() : null,
      };

      return submitData;
    } catch (error) {
      throw error;
    }
  };

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    const response = await terminalsApi.getList(params);
    return response.data || response;
  };

  // Переопределяем эндпоинты для кастомной обработки
  const customEndpoints = {
    list: handleList,
    create: async (data: any) => {
      const processedData = await handleSubmit(data);
      return terminalsApi.create(processedData);
    },
    update: async (id: number, data: any) => {
      const processedData = await handleSubmit(data);
      return terminalsApi.update(id, processedData);
    },
    delete: terminalsApi.delete,
  };

  return (
    <GenericDataTable<Terminal>
      title="Управление терминалами"
      icon={<CreditCardOutlined />}
      endpoints={customEndpoints}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      searchable={true}
      exportable={true}
      addButtonText="Добавить терминал"
      pagination={{
        pageSize: 100,
        pageSizeOptions: ['100', '200', '500', '800', '1000'],
      }}
      onEditDataTransform={prepareDataForEdit}
    />
  );
};

export default Terminals; 