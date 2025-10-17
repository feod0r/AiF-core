import React, { useMemo } from 'react';
import { HomeOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { rentApi, ownersApi } from '../services/api';
import { Rent, Owner } from '../types';
import dayjs from 'dayjs';

const RentPage: React.FC = () => {
  // Конфигурация колонок
  const columns = useMemo(() => [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Дата оплаты',
      dataIndex: 'pay_date',
      key: 'pay_date',
      width: 120,
      render: (pay_date: number) => pay_date ? `${pay_date}-е число` : '-',
    },
    {
      title: 'Местоположение',
      dataIndex: 'location',
      key: 'location',
      ellipsis: true,
    },
    {
      title: 'Координаты',
      key: 'coordinates',
      width: 150,
      render: (_: any, record: Rent): string => {
        if (record.latitude && record.longitude) {
          return `${record.latitude}, ${record.longitude}`;
        }
        return '-';
      },
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: any): string => {
        const num = typeof amount === 'string' ? parseFloat(amount) : amount;
        return isNaN(num) ? '0 ₽' : `${num.toLocaleString()} ₽`;
      },
    },
    {
      title: 'Детали',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
    },
    {
      title: 'Плательщик',
      dataIndex: ['payer', 'name'],
      key: 'payer',
      width: 150,
      render: (_: any, record: Rent): string => {
        if (record.payer) {
          return `${record.payer.name} (${record.payer.inn})`;
        }
        return '-';
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
      placeholder: 'Поиск по местоположению или деталям',
    },
    {
      key: 'pay_date',
      label: 'День оплаты',
      type: 'input' as const,
      placeholder: 'Введите день (1-31)',
    },
    {
      key: 'payer_id',
      label: 'Плательщик',
      type: 'select' as const,
      placeholder: 'Выберите плательщика',
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
        name: 'pay_date',
        label: 'День оплаты (1–31)',
        type: 'number' as const,
        rules: [
          { required: true, message: 'Пожалуйста, введите день оплаты' },
          { type: 'number', min: 1, max: 31, message: 'День должен быть от 1 до 31' }
        ],
        placeholder: 'Например, 10 — платить 10-го числа',
        min: 1,
        max: 31,
      },
      {
        name: 'location',
        label: 'Местоположение',
        type: 'textarea' as const,
        rules: [{ required: true, message: 'Пожалуйста, введите местоположение' }],
        placeholder: 'Введите местоположение',
        rows: 3,
      },
      {
        name: 'amount',
        label: 'Сумма',
        type: 'number' as const,
        rules: [{ required: true, message: 'Пожалуйста, введите сумму' }],
        placeholder: 'Введите сумму',
        min: 0,
        step: 0.01,
        addonAfter: '₽',
      },
      {
        name: 'details',
        label: 'Детали',
        type: 'textarea' as const,
        placeholder: 'Введите детали',
        rows: 3,
      },
      {
        name: 'payer_id',
        label: 'Плательщик',
        type: 'select' as const,
        placeholder: 'Выберите плательщика',
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
        name: 'latitude',
        label: 'Широта',
        type: 'number' as const,
        placeholder: 'Введите широту',
        min: -90,
        max: 90,
        step: 0.000001,
      },
      {
        name: 'longitude',
        label: 'Долгота',
        type: 'number' as const,
        placeholder: 'Введите долготу',
        min: -180,
        max: 180,
        step: 0.000001,
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
  const prepareDataForEdit = (record: Rent) => {
    return {
      ...record,
      start_date: record.start_date ? dayjs(record.start_date) : dayjs(),
      end_date: record.end_date ? dayjs(record.end_date) : dayjs().add(1, 'year'),
      payer_id: (record as any).payer_id ?? record.payer?.id,
      amount: typeof record.amount === 'string' ? parseFloat(record.amount) : record.amount,
      latitude: typeof record.latitude === 'string' ? parseFloat(record.latitude) : record.latitude,
      longitude: typeof record.longitude === 'string' ? parseFloat(record.longitude) : record.longitude,
    };
  };

  // Кастомная обработка submit для правильного форматирования дат и координат
  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        start_date: values.start_date ? values.start_date.toISOString() : dayjs().toISOString(),
        end_date: values.end_date ? values.end_date.toISOString() : dayjs().add(1, 'year').toISOString(),
        amount: typeof values.amount === 'string' ? parseFloat(values.amount) : values.amount,
        latitude: values.latitude ? parseFloat(values.latitude) : null,
        longitude: values.longitude ? parseFloat(values.longitude) : null,
      };

      return submitData;
    } catch (error) {
      throw error;
    }
  };

  // Кастомная обработка submit для создания
  const handleCreate = async (data: any) => {
    const processedData = await handleSubmit(data);
    return rentApi.create(processedData);
  };

  // Кастомная обработка submit для обновления
  const handleUpdate = async (id: number, data: any) => {
    const processedData = await handleSubmit(data);
    return rentApi.update(id, processedData);
  };

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    const response = await rentApi.getList(params);
    return response; // rentApi.getList возвращает Rent[] напрямую
  };

  return (
    <GenericDataTable<Rent>
      title="Управление арендой"
      icon={<HomeOutlined />}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      onEditDataTransform={prepareDataForEdit}
      endpoints={{
        list: handleList,
        create: handleCreate,
        update: handleUpdate,
        delete: rentApi.delete,
      }}
      searchable={true}
      exportable={true}
      addButtonText="Добавить запись"
      pagination={{
        pageSize: 100,
        pageSizeOptions: ['100', '200', '500', '800', '1000'],
      }}
    />
  );
};

export default RentPage; 