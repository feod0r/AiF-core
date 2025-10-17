import React, { useMemo, useState, useEffect } from 'react';
import { RobotOutlined, PlusOutlined } from '@ant-design/icons';
import { Modal, Form, Input, InputNumber, Select, message, Button, DatePicker } from 'antd';
import GenericDataTable from '../components/GenericDataTable';
import { 
  machinesApi, 
  terminalsApi, 
  rentApi, 
  phonesApi,
  ownersApi,
  accountsApi
} from '../services/api';
import { 
  Machine, 
  Terminal, 
  Rent, 
  Phone,
  Owner,
  Account
} from '../types';
import dayjs from 'dayjs';

const { Option } = Select;
const { TextArea } = Input;

const Machines: React.FC = () => {
  // Состояния для справочных данных
  const [terminals, setTerminals] = useState<Terminal[]>([]);
  const [rents, setRents] = useState<Rent[]>([]);
  const [phones, setPhones] = useState<Phone[]>([]);
  const [owners, setOwners] = useState<Owner[]>([]);
  const [accounts, setAccounts] = useState<Account[]>([]);
  
  // Состояния для модальных окон
  const [isAddTerminalModalVisible, setIsAddTerminalModalVisible] = useState(false);
  const [isAddRentModalVisible, setIsAddRentModalVisible] = useState(false);
  const [isAddPhoneModalVisible, setIsAddPhoneModalVisible] = useState(false);
  
  // Формы для модальных окон
  const [addTerminalForm] = Form.useForm();
  const [addRentForm] = Form.useForm();
  const [addPhoneForm] = Form.useForm();
  const [mainFormRef, setMainFormRef] = useState<any>(null);

  // Загрузка справочных данных
  useEffect(() => {
    const loadReferenceData = async () => {
      try {
        const [terminalsData, rentsData, phonesData, ownersData, accountsData] = await Promise.all([
          terminalsApi.getList({ pageSize: 1000 }),
          rentApi.getList({ pageSize: 1000 }),
          phonesApi.getList({ pageSize: 1000 }),
          ownersApi.getList({ pageSize: 1000 }),
          accountsApi.getList(),
        ]);
        
        setTerminals(terminalsData.data || terminalsData);
        setRents(rentsData);
        setPhones(phonesData);
        setOwners(ownersData.data || ownersData);
        setAccounts(Array.isArray(accountsData) ? accountsData : (accountsData as any).data || []);
      } catch (error) {
        console.error('Error loading reference data:', error);
      }
    };
    loadReferenceData();
  }, []);

  // Функции для работы с модальным окном терминала
  const handleOpenAddTerminalModal = () => {
    setIsAddTerminalModalVisible(true);
    addTerminalForm.resetFields();
  };

  const handleCloseAddTerminalModal = () => {
    setIsAddTerminalModalVisible(false);
    addTerminalForm.resetFields();
  };

  const handleCreateTerminal = async () => {
    try {
      const values = await addTerminalForm.validateFields();
      
      const newTerminal = await terminalsApi.create({
        name: values.name,
        terminal: values.terminal,
        owner_id: values.owner_id,
        account_id: values.account_id,
        start_date: new Date().toISOString(),
        end_date: '2099-12-31T23:59:59Z',
      });

      message.success(`Терминал "${newTerminal.name}" успешно создан`);

      // Обновляем список терминалов
      const updatedTerminals = await terminalsApi.getList({ pageSize: 1000 });
      setTerminals(updatedTerminals.data || updatedTerminals);

      // Автоматически выбираем созданный терминал
      if (mainFormRef) {
        mainFormRef.setFieldsValue({ terminal_id: newTerminal.id });
      }

      handleCloseAddTerminalModal();
    } catch (error: any) {
      if (!error.errorFields) {
        console.error('API error:', error);
        message.error('Ошибка при создании терминала');
      }
    }
  };

  // Функции для работы с модальным окном аренды
  const handleOpenAddRentModal = () => {
    setIsAddRentModalVisible(true);
    addRentForm.resetFields();
  };

  const handleCloseAddRentModal = () => {
    setIsAddRentModalVisible(false);
    addRentForm.resetFields();
  };

  const handleCreateRent = async () => {
    try {
      const values = await addRentForm.validateFields();
      
      const newRent = await rentApi.create({
        pay_date: values.pay_date,
        location: values.location,
        amount: values.amount,
        details: values.details,
        payer_id: values.payer_id,
        latitude: values.latitude,
        longitude: values.longitude,
        start_date: new Date().toISOString(),
        end_date: '2099-12-31T23:59:59Z',
      } as any);

      message.success(`Аренда "${newRent.location}" успешно создана`);

      // Обновляем список аренды
      const updatedRents = await rentApi.getList({ pageSize: 1000 });
      setRents(updatedRents);

      // Автоматически выбираем созданную аренду
      if (mainFormRef) {
        mainFormRef.setFieldsValue({ rent_id: newRent.id });
      }

      handleCloseAddRentModal();
    } catch (error: any) {
      if (!error.errorFields) {
        console.error('API error:', error);
        message.error('Ошибка при создании аренды');
      }
    }
  };

  // Функции для работы с модальным окном телефона
  const handleOpenAddPhoneModal = () => {
    setIsAddPhoneModalVisible(true);
    addPhoneForm.resetFields();
  };

  const handleCloseAddPhoneModal = () => {
    setIsAddPhoneModalVisible(false);
    addPhoneForm.resetFields();
  };

  const handleCreatePhone = async () => {
    try {
      const values = await addPhoneForm.validateFields();
      
      const newPhone = await phonesApi.create({
        pay_date: values.pay_date,
        phone: values.phone,
        amount: values.amount,
        details: values.details,
        start_date: new Date().toISOString(),
        end_date: '2099-12-31T23:59:59Z',
      });

      message.success(`Телефон "${newPhone.phone}" успешно создан`);

      // Обновляем список телефонов
      const updatedPhones = await phonesApi.getList({ pageSize: 1000 });
      setPhones(updatedPhones);

      // Автоматически выбираем созданный телефон
      if (mainFormRef) {
        mainFormRef.setFieldsValue({ phone_id: newPhone.id });
      }

      handleCloseAddPhoneModal();
    } catch (error: any) {
      if (!error.errorFields) {
        console.error('API error:', error);
        message.error('Ошибка при создании телефона');
      }
    }
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
      ellipsis: true,
    },
    {
      title: 'Стоимость игры',
      dataIndex: 'game_cost',
      key: 'game_cost',
      width: 120,
      render: (gameCost: number) => gameCost ? `${gameCost} ₽` : '-',
    },
    {
      title: 'Терминал',
      dataIndex: ['terminal', 'name'],
      key: 'terminal',
      width: 120,
      render: (_: any, record: Machine) => {
        if (record.terminal) {
          return `${record.terminal.name} (${record.terminal.terminal})`;
        }
        return '-';
      },
    },
    {
      title: 'Аренда',
      dataIndex: ['rent', 'location'],
      key: 'rent',
      width: 120,
      render: (_: any, record: Machine) => {
        if (record.rent) {
          return `${record.rent.location} (${Number(record.rent.amount).toLocaleString()} ₽)`;
        }
        return '-';
      },
    },
    {
      title: 'Телефон',
      dataIndex: ['phone', 'phone'],
      key: 'phone',
      width: 120,
      render: (_: any, record: Machine) => {
        if (record.phone) {
          return `${record.phone.phone} (${record.phone.details})`;
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
    {
      title: 'Дата окончания',
      dataIndex: 'end_date',
      key: 'end_date',
      width: 120,
      render: (date: string) => new Date(date).toLocaleDateString('ru-RU'),
    },
  ], []);

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'terminal_id',
      label: 'Терминал',
      type: 'select' as const,
      placeholder: 'Выберите терминал',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const terminals = await terminalsApi.getList({ pageSize: 1000 });
        const terminalsList = terminals.data || terminals;
        return terminalsList.map((terminal: Terminal) => ({
          label: `${terminal.name} (${terminal.terminal})`,
          value: terminal.id,
        }));
      },
    },
    {
      key: 'rent_id',
      label: 'Аренда',
      type: 'select' as const,
      placeholder: 'Выберите аренду',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const rents = await rentApi.getList({ pageSize: 1000 });
        return rents.map((rent: Rent) => ({
          label: `${rent.location} (${Number(rent.amount).toLocaleString()} ₽)`,
          value: rent.id,
        }));
      },
    },
    {
      key: 'phone_id',
      label: 'Телефон',
      type: 'select' as const,
      placeholder: 'Выберите телефон',
      api: async (): Promise<Array<{label: string, value: any}>> => {
        const phones = await phonesApi.getList({ pageSize: 1000 });
        return phones.map((phone: Phone) => ({
          label: `${phone.phone} (${phone.details})`,
          value: phone.id,
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
        name: 'name',
        label: 'Название',
        type: 'input' as const,
        rules: [{ required: true, message: 'Пожалуйста, введите название' }],
        placeholder: 'Введите название машины',
      },
      {
        name: 'game_cost',
        label: 'Стоимость игры',
        type: 'number' as const,
        placeholder: 'Введите стоимость игры',
        min: 0,
      },
      {
        name: 'terminal_id',
        label: 'Терминал',
        type: 'select' as const,
        placeholder: 'Выберите терминал',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          return terminals.map((terminal: Terminal) => ({
            label: `${terminal.name} (${terminal.terminal})`,
            value: terminal.id,
          }));
        },
      },
      {
        name: 'rent_id',
        label: 'Аренда',
        type: 'select' as const,
        placeholder: 'Выберите аренду',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          return rents.map((rent: Rent) => ({
            label: `${rent.location} (${Number(rent.amount).toLocaleString()} ₽)`,
            value: rent.id,
          }));
        },
      },
      {
        name: 'phone_id',
        label: 'Телефон',
        type: 'select' as const,
        placeholder: 'Выберите телефон',
        api: async (): Promise<Array<{label: string, value: any}>> => {
          return phones.map((phone: Phone) => ({
            label: `${phone.phone} (${phone.details})`,
            value: phone.id,
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
  }), [terminals, rents, phones]);

  // Кастомный рендер формы для добавления кнопок
  const customFormRender = (form: any, config: any) => {
    // Сохраняем ссылку на форму
    if (!mainFormRef) {
      setMainFormRef(form);
    }

    return (
      <>
        {config.fields.map((field: any) => {
          // Для полей terminal_id, rent_id, phone_id добавляем кнопки
          if (field.name === 'terminal_id') {
            return (
              <div key={field.name} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <Form.Item
                  name={field.name}
                  label={field.label}
                  rules={field.rules}
                  style={{ flex: 1, marginBottom: 24 }}
                >
                  <Select
                    placeholder={field.placeholder}
                    showSearch
                    optionFilterProp="children"
                    allowClear
                  >
                    {terminals.map((terminal) => (
                      <Option key={terminal.id} value={terminal.id}>
                        {terminal.name} ({terminal.terminal})
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleOpenAddTerminalModal}
                  title="Добавить новый терминал"
                  style={{ marginTop: 30 }}
                />
              </div>
            );
          }

          if (field.name === 'rent_id') {
            return (
              <div key={field.name} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <Form.Item
                  name={field.name}
                  label={field.label}
                  rules={field.rules}
                  style={{ flex: 1, marginBottom: 24 }}
                >
                  <Select
                    placeholder={field.placeholder}
                    showSearch
                    optionFilterProp="children"
                    allowClear
                  >
                    {rents.map((rent) => (
                      <Option key={rent.id} value={rent.id}>
                        {rent.location} ({Number(rent.amount).toLocaleString()} ₽)
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleOpenAddRentModal}
                  title="Добавить новую аренду"
                  style={{ marginTop: 30 }}
                />
              </div>
            );
          }

          if (field.name === 'phone_id') {
            return (
              <div key={field.name} style={{ display: 'flex', gap: 8, alignItems: 'flex-start' }}>
                <Form.Item
                  name={field.name}
                  label={field.label}
                  rules={field.rules}
                  style={{ flex: 1, marginBottom: 24 }}
                >
                  <Select
                    placeholder={field.placeholder}
                    showSearch
                    optionFilterProp="children"
                    allowClear
                  >
                    {phones.map((phone) => (
                      <Option key={phone.id} value={phone.id}>
                        {phone.phone} ({phone.details})
                      </Option>
                    ))}
                  </Select>
                </Form.Item>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleOpenAddPhoneModal}
                  title="Добавить новый телефон"
                  style={{ marginTop: 30 }}
                />
              </div>
            );
          }

          // Для остальных полей используем стандартный рендеринг
          const fieldType = field.type;
          let inputComponent;

          if (fieldType === 'input') {
            inputComponent = <Input placeholder={field.placeholder} />;
          } else if (fieldType === 'number') {
            inputComponent = (
              <InputNumber
                placeholder={field.placeholder}
                style={{ width: '100%' }}
                min={field.min}
              />
            );
          } else if (fieldType === 'date') {
            inputComponent = (
              <DatePicker
                style={{ width: '100%' }}
                placeholder={field.placeholder}
              />
            );
          } else if (fieldType === 'select') {
            inputComponent = (
              <Select placeholder={field.placeholder} allowClear>
                {(field.options || []).map((option: any) => (
                  <Option key={option.value} value={option.value}>
                    {option.label}
                  </Option>
                ))}
              </Select>
            );
          } else {
            inputComponent = <Input placeholder={field.placeholder} />;
          }

          return (
            <Form.Item
              key={field.name}
              name={field.name}
              label={field.label}
              rules={field.rules}
            >
              {inputComponent}
            </Form.Item>
          );
        })}
      </>
    );
  };

  // Кастомная обработка данных для редактирования
  const prepareDataForEdit = (record: Machine) => {
    return {
      ...record,
      start_date: record.start_date ? dayjs(record.start_date) : dayjs(),
      end_date: record.end_date ? dayjs(record.end_date) : dayjs().add(1, 'year'),
      terminal_id: (record as any).terminal_id ?? record.terminal?.id,
      rent_id: (record as any).rent_id ?? record.rent?.id,
      phone_id: (record as any).phone_id ?? record.phone?.id,
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
    const response = await machinesApi.getList(params);
    return response.data || response;
  };

  // Переопределяем эндпоинты для кастомной обработки
  const customEndpoints = {
    list: handleList,
    create: async (data: any) => {
      const processedData = await handleSubmit(data);
      return machinesApi.create(processedData);
    },
    update: async (id: number, data: any) => {
      const processedData = await handleSubmit(data);
      return machinesApi.update(id, processedData);
    },
    delete: machinesApi.delete,
  };

  return (
    <>
      <GenericDataTable<Machine>
        title="Управление машинами"
        icon={<RobotOutlined />}
        endpoints={customEndpoints}
        columns={columns}
        filters={filters}
        formConfig={formConfig}
        customFormRender={customFormRender}
        searchable={true}
        exportable={true}
        addButtonText="Добавить машину"
        pagination={{
          pageSize: 100,
          pageSizeOptions: ['100', '200', '500', '800', '1000'],
        }}
        onEditDataTransform={prepareDataForEdit}
      />

      {/* Модальное окно для добавления терминала */}
      <Modal
        title="Добавить новый терминал"
        open={isAddTerminalModalVisible}
        onOk={handleCreateTerminal}
        onCancel={handleCloseAddTerminalModal}
        width={600}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form
          form={addTerminalForm}
          layout="vertical"
        >
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название терминала' }]}
          >
            <Input placeholder="Введите название терминала" />
          </Form.Item>

          <Form.Item
            name="terminal"
            label="Номер терминала"
          >
            <InputNumber
              placeholder="Введите номер терминала"
              style={{ width: '100%' }}
              min={1}
            />
          </Form.Item>

          <Form.Item
            name="owner_id"
            label="Владелец (ИП)"
          >
            <Select
              placeholder="Выберите владельца"
              showSearch
              optionFilterProp="children"
              allowClear
            >
              {owners.map((owner) => (
                <Option key={owner.id} value={owner.id}>
                  {owner.name} ({owner.inn})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="account_id"
            label="Расчетный счет"
          >
            <Select
              placeholder="Выберите счет"
              showSearch
              optionFilterProp="children"
              allowClear
            >
              {accounts.map((account) => (
                <Option key={account.id} value={account.id}>
                  {account.name} ({Number(account.balance).toFixed(2)} ₽)
                </Option>
              ))}
            </Select>
          </Form.Item>
        </Form>
      </Modal>

      {/* Модальное окно для добавления аренды */}
      <Modal
        title="Добавить новую аренду"
        open={isAddRentModalVisible}
        onOk={handleCreateRent}
        onCancel={handleCloseAddRentModal}
        width={600}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form
          form={addRentForm}
          layout="vertical"
        >
          <Form.Item
            name="location"
            label="Адрес"
            rules={[{ required: true, message: 'Введите адрес' }]}
          >
            <Input placeholder="Введите адрес аренды" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Form.Item
              name="pay_date"
              label="День оплаты (1-31)"
              rules={[{ required: true, message: 'Введите день оплаты' }]}
            >
              <InputNumber
                placeholder="Введите день"
                style={{ width: '100%' }}
                min={1}
                max={31}
              />
            </Form.Item>

            <Form.Item
              name="amount"
              label="Сумма"
              rules={[{ required: true, message: 'Введите сумму' }]}
            >
              <InputNumber
                placeholder="Введите сумму"
                style={{ width: '100%' }}
                min={0}
                step={100}
              />
            </Form.Item>
          </div>

          <Form.Item
            name="payer_id"
            label="Плательщик (ИП)"
          >
            <Select
              placeholder="Выберите плательщика"
              showSearch
              optionFilterProp="children"
              allowClear
            >
              {owners.map((owner) => (
                <Option key={owner.id} value={owner.id}>
                  {owner.name} ({owner.inn})
                </Option>
              ))}
            </Select>
          </Form.Item>

          <Form.Item
            name="details"
            label="Детали"
          >
            <TextArea rows={2} placeholder="Дополнительная информация" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Form.Item
              name="latitude"
              label="Широта"
            >
              <InputNumber
                placeholder="Например: 55.7558"
                style={{ width: '100%' }}
                step={0.0001}
              />
            </Form.Item>

            <Form.Item
              name="longitude"
              label="Долгота"
            >
              <InputNumber
                placeholder="Например: 37.6173"
                style={{ width: '100%' }}
                step={0.0001}
              />
            </Form.Item>
          </div>
        </Form>
      </Modal>

      {/* Модальное окно для добавления телефона */}
      <Modal
        title="Добавить новый телефон"
        open={isAddPhoneModalVisible}
        onOk={handleCreatePhone}
        onCancel={handleCloseAddPhoneModal}
        width={500}
        okText="Создать"
        cancelText="Отмена"
      >
        <Form
          form={addPhoneForm}
          layout="vertical"
        >
          <Form.Item
            name="phone"
            label="Номер телефона"
            rules={[{ required: true, message: 'Введите номер телефона' }]}
          >
            <Input placeholder="Введите номер телефона" />
          </Form.Item>

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <Form.Item
              name="pay_date"
              label="День оплаты (1-31)"
              rules={[{ required: true, message: 'Введите день оплаты' }]}
            >
              <InputNumber
                placeholder="Введите день"
                style={{ width: '100%' }}
                min={1}
                max={31}
              />
            </Form.Item>

            <Form.Item
              name="amount"
              label="Сумма"
              rules={[{ required: true, message: 'Введите сумму' }]}
            >
              <InputNumber
                placeholder="Введите сумму"
                style={{ width: '100%' }}
                min={0}
                step={10}
              />
            </Form.Item>
          </div>

          <Form.Item
            name="details"
            label="Детали"
          >
            <Input placeholder="Оператор или примечание" />
          </Form.Item>
        </Form>
      </Modal>
    </>
  );
};

export default Machines; 