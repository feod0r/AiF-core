import React, { useMemo } from 'react';
import { MonitorOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { monitoringApi, machinesApi } from '../services/api';
import { Monitoring, Machine } from '../types';
import dayjs from 'dayjs';

const MonitoringPage: React.FC = () => {
  // Конфигурация колонок
  const columns = useMemo(() => [
    {
      title: 'ID',
      dataIndex: 'id',
      key: 'id',
      width: 80,
    },
    {
      title: 'Машина',
      dataIndex: ['machine', 'name'],
      key: 'machine',
      width: 200,
      render: (_: any, record: Monitoring) => {
        if (record.machine) {
          return record.machine.name;
        }
        return '-';
      },
    },
    {
      title: 'Монеты',
      dataIndex: 'coins',
      key: 'coins',
      width: 120,
      render: (coins: any) => {
        const num = typeof coins === 'string' ? parseFloat(coins) : coins;
        return isNaN(num) ? '0.00 ₽' : `${num.toFixed(2)} ₽`;
      },
    },
    {
      title: 'Игрушки',
      dataIndex: 'toys',
      key: 'toys',
      width: 120,
    },
    {
      title: 'Дата',
      dataIndex: 'date',
      key: 'date',
      width: 150,
      render: (date: string) => new Date(date).toLocaleString('ru-RU'),
      ellipsis: true,
    },
  ], []);

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'machine_id',
      label: 'Машина',
      type: 'select' as const,
      placeholder: 'Выберите машину',
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
        name: 'machine_id',
        label: 'Машина',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите машину' }],
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
        name: 'date',
        label: 'Дата',
        type: 'datetime' as const,
        placeholder: 'Выберите дату и время (необязательно)',
      },
      {
        name: 'coins',
        label: 'Монеты',
        type: 'number' as const,
        rules: [{ required: true, message: 'Введите количество монет' }],
        placeholder: 'Введите количество монет',
        min: 0,
        step: 0.01,
      },
      {
        name: 'toys',
        label: 'Игрушки',
        type: 'number' as const,
        rules: [{ required: true, message: 'Введите количество игрушек' }],
        placeholder: 'Введите количество игрушек',
        min: 0,
      },
    ],
    initialValues: {
      // Не устанавливаем дату по умолчанию, чтобы поле было пустым
    },
  }), []);

  // Кастомная обработка данных для редактирования
  const prepareDataForEdit = (record: Monitoring) => {
    return {
      ...record,
      date: record.date ? dayjs(record.date) : dayjs(),
      machine_id: (record as any).machine_id ?? record.machine?.id,
      coins: typeof record.coins === 'string' ? parseFloat(record.coins) : record.coins,
    };
  };

  // Кастомная обработка submit
  const handleSubmit = async (values: any) => {
    try {
      const submitData: any = {
        ...values,
        coins: typeof values.coins === 'string' ? parseFloat(values.coins) : values.coins,
      };

      // Обрабатываем дату в ISO формате
      if (values.date) {
        try {
          // Проверяем, является ли объект dayjs
          if (dayjs.isDayjs(values.date)) {
            submitData.date = values.date.toISOString();
          } else if (values.date instanceof Date) {
            submitData.date = values.date.toISOString();
          } else if (typeof values.date === 'string') {
            // Если это строка, пытаемся преобразовать в dayjs и затем в ISO
            submitData.date = dayjs(values.date).toISOString();
          } else {
            // Если это другой тип объекта, пытаемся преобразовать в dayjs
            submitData.date = dayjs(values.date).toISOString();
          }
        } catch (dateError) {
          console.warn('Ошибка при обработке даты:', dateError);
          // Если не удается обработать дату, не включаем её в данные
          delete submitData.date;
        }
      } else {
        // Если дата не указана, не включаем её в данные
        delete submitData.date;
      }

      return submitData;
    } catch (error) {
      throw error;
    }
  };

  // Кастомная обработка submit для создания
  const handleCreate = async (data: any) => {
    const processedData = await handleSubmit(data);
    return monitoringApi.create(processedData);
  };

  // Кастомная обработка submit для обновления
  const handleUpdate = async (id: number, data: any) => {
    const processedData = await handleSubmit(data);
    return monitoringApi.update(id, processedData);
  };

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    const response = await monitoringApi.getList(params);
    return response.data || response;
  };

  return (
    <GenericDataTable<Monitoring>
      title="Мониторинг"
      icon={<MonitorOutlined />}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      onEditDataTransform={prepareDataForEdit}
      endpoints={{
        list: handleList,
        create: handleCreate,
        update: handleUpdate,
        delete: monitoringApi.delete,
      }}
      disableEdit={false}
      disableDelete={false}
    />
  );
};

export default MonitoringPage; 