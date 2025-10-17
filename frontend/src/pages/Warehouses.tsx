import React from 'react';
import { Tag } from 'antd';
import { HomeOutlined } from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { warehousesApi, ownersApi, counterpartiesApi } from '../services/api';
import { Warehouse, Owner, Counterparty } from '../types';

const Warehouses: React.FC = () => {
  // Загрузка владельцев для селекта
  const loadOwners = async () => {
    try {
      const data = await ownersApi.getList();
      const owners = data.data || data;
      return owners.map((owner: Owner) => ({
        label: owner.name,
        value: owner.id
      }));
    } catch (error) {
      console.error('Error loading owners:', error);
      return [];
    }
  };

  // Загрузка контрагентов для селекта
  const loadCounterparties = async () => {
    try {
      const data = await counterpartiesApi.getList();
      return data.map((counterparty: Counterparty) => ({
        label: counterparty.name,
        value: counterparty.id
      }));
    } catch (error) {
      console.error('Error loading counterparties:', error);
      return [];
    }
  };

  return (
    <GenericDataTable<Warehouse>
      title="Склады"
      icon={<HomeOutlined />}
      endpoints={{
        list: async (params) => {
          return await warehousesApi.getList(params);
        },
        create: async (data) => {
          return await warehousesApi.create(data);
        },
        update: async (id, data) => {
          return await warehousesApi.update(id, data);
        },
        delete: async (id) => {
      await warehousesApi.delete(id);
        }
      }}
      columns={[
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
      title: 'Адрес',
      dataIndex: 'address',
      key: 'address',
      render: (address: string) => address || '-',
    },
    {
      title: 'Владелец',
          dataIndex: ['owner', 'name'],
      key: 'owner',
          render: (ownerName: string) => ownerName || 'Неизвестно',
    },
    {
      title: 'Контактное лицо',
          dataIndex: ['contact_person', 'name'],
      key: 'contact_person',
          render: (contactPersonName: string) => contactPersonName || '-',
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'green' : 'red'}>
          {isActive ? 'Активен' : 'Неактивен'}
        </Tag>
      ),
        },
      ]}
      formConfig={{
        fields: [
          {
            name: 'name',
            label: 'Название',
            type: 'input',
            placeholder: 'Введите название склада',
            rules: [{ required: true, message: 'Введите название склада' }],
          },
          {
            name: 'address',
            label: 'Адрес',
            type: 'textarea',
            placeholder: 'Введите адрес склада',
          },
          {
            name: 'owner_id',
            label: 'Владелец',
            type: 'select',
            placeholder: 'Выберите владельца',
            api: loadOwners,
            rules: [{ required: true, message: 'Выберите владельца' }],
          },
          {
            name: 'contact_person_id',
            label: 'Контактное лицо',
            type: 'select',
            placeholder: 'Выберите контактное лицо',
            api: loadCounterparties,
          },
          {
            name: 'is_active',
            label: 'Статус',
            type: 'select',
            placeholder: 'Выберите статус',
            options: [
              { label: 'Активен', value: true },
              { label: 'Неактивен', value: false },
            ],
            initialValue: true,
          },
        ],
        modalWidth: 600,
      }}
      onEditDataTransform={(record) => ({
        ...record,
        owner_id: record.owner_id || record.owner?.id,
        contact_person_id: record.contact_person_id || record.contact_person?.id,
      })}
      addButtonText="Добавить склад"
    />
  );
};

export default Warehouses; 