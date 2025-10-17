import React, { useMemo } from 'react';
import { PhoneOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { phonesApi } from '../services/api';
import { Phone } from '../types';
import dayjs from 'dayjs';

const Phones: React.FC = () => {
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
      title: 'Телефон',
      dataIndex: 'phone',
      key: 'phone',
      width: 150,
    },
    {
      title: 'Сумма',
      dataIndex: 'amount',
      key: 'amount',
      width: 120,
      render: (amount: any) => {
        const num = typeof amount === 'string' ? parseFloat(amount) : amount;
        return isNaN(num) ? '0.00 ₽' : `${num.toFixed(2)} ₽`;
      },
    },
    {
      title: 'Детали',
      dataIndex: 'details',
      key: 'details',
      ellipsis: true,
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
      placeholder: 'Поиск по телефону или деталям',
    },
    {
      key: 'pay_date',
      label: 'День оплаты',
      type: 'input' as const,
      placeholder: 'Введите день (1-31)',
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
        placeholder: 'Например, 5 — платить 5-го числа',
        min: 1,
        max: 31,
      },
      {
        name: 'phone',
        label: 'Телефон',
        type: 'input' as const,
        rules: [{ required: true, message: 'Пожалуйста, введите номер телефона' }],
        placeholder: 'Введите номер телефона',
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
  const prepareDataForEdit = (record: Phone) => {
    return {
      ...record,
      start_date: record.start_date ? dayjs(record.start_date) : dayjs(),
      end_date: record.end_date ? dayjs(record.end_date) : dayjs().add(1, 'year'),
      amount: typeof record.amount === 'string' ? parseFloat(record.amount) : record.amount,
    };
  };

  // Кастомная обработка submit для правильного форматирования дат
  const handleSubmit = async (values: any) => {
    try {
      const submitData = {
        ...values,
        start_date: values.start_date ? values.start_date.toISOString() : dayjs().toISOString(),
        end_date: values.end_date ? values.end_date.toISOString() : dayjs().add(1, 'year').toISOString(),
        amount: typeof values.amount === 'string' ? parseFloat(values.amount) : values.amount,
      };

      return submitData;
    } catch (error) {
      throw error;
    }
  };

  // Кастомная обработка submit для создания
  const handleCreate = async (data: any) => {
    const processedData = await handleSubmit(data);
    return phonesApi.create(processedData);
  };

  // Кастомная обработка submit для обновления
  const handleUpdate = async (id: number, data: any) => {
    const processedData = await handleSubmit(data);
    return phonesApi.update(id, processedData);
  };

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    const response = await phonesApi.getList(params);
    return response; // phonesApi.getList возвращает Phone[] напрямую
  };

  return (
    <GenericDataTable<Phone>
      title="Управление телефонами"
      icon={<PhoneOutlined />}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      onEditDataTransform={prepareDataForEdit}
      endpoints={{
        list: handleList,
        create: handleCreate,
        update: handleUpdate,
        delete: phonesApi.delete,
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

export default Phones; 