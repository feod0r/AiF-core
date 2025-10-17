import React, { useState, useEffect } from 'react';
import {
  Table,
  Button,
  Space,
  Modal,
  Form,
  Input,
  Select,
  Switch,
  message,
  Card,
  Statistic,
  Row,
  Col,
  Tag,
  Popconfirm,
  Drawer,
  Typography,
  Divider,
  Tabs,
  InputNumber,
  DatePicker,
} from 'antd';
import {
  PlusOutlined,
  EditOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined,
  ThunderboltOutlined,
  BulbOutlined,
} from '@ant-design/icons';
import { scheduledJobsApi } from '../services/api';
import moment from 'moment';

const { Title, Text } = Typography;
const { TextArea } = Input;
const { Option } = Select;
const { TabPane } = Tabs;

const ScheduledJobs: React.FC = () => {
  const [jobs, setJobs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);
  const [editingJob, setEditingJob] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [templates, setTemplates] = useState<any[]>([]);
  const [templatesDrawerVisible, setTemplatesDrawerVisible] = useState(false);
  const [form] = Form.useForm();

  useEffect(() => {
    fetchJobs();
    fetchStats();
    fetchTemplates();
  }, []);

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const data = await scheduledJobsApi.listJobs();
      setJobs(data);
    } catch (error) {
      message.error('Ошибка при загрузке задач');
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const data = await scheduledJobsApi.getStats();
      setStats(data);
    } catch (error) {
      console.error('Ошибка при загрузке статистики:', error);
    }
  };

  const fetchTemplates = async () => {
    try {
      const data = await scheduledJobsApi.getTemplates();
      setTemplates(data);
    } catch (error) {
      console.error('Ошибка при загрузке шаблонов:', error);
    }
  };

  const handleCreate = () => {
    setEditingJob(null);
    form.resetFields();
    setModalVisible(true);
  };

  const handleEdit = (record: any) => {
    if (isBuiltinJob(record.name)) {
      message.warning('Встроенные задачи нельзя редактировать. Вы можете изменить только статус активности.');
      return;
    }
    
    setEditingJob(record);
    form.setFieldsValue({
      ...record,
      scheduled_time: record.scheduled_time ? moment(record.scheduled_time) : null,
      function_params: record.function_params ? JSON.stringify(record.function_params, null, 2) : '',
    });
    setModalVisible(true);
  };

  const handleDelete = async (id: number, name: string) => {
    if (isBuiltinJob(name)) {
      message.warning('Встроенные задачи нельзя удалить. Вы можете их только деактивировать.');
      return;
    }
    
    try {
      await scheduledJobsApi.deleteJob(id);
      message.success('Задача удалена');
      fetchJobs();
      fetchStats();
    } catch (error) {
      message.error('Ошибка при удалении задачи');
    }
  };

  const handleToggleActive = async (record: any) => {
    try {
      if (record.is_active) {
        await scheduledJobsApi.deactivateJob(record.id);
        message.success('Задача деактивирована');
      } else {
        await scheduledJobsApi.activateJob(record.id);
        message.success('Задача активирована');
      }
      fetchJobs();
      fetchStats();
    } catch (error) {
      message.error('Ошибка при изменении статуса задачи');
    }
  };

  const handleExecuteNow = async (id: number) => {
    try {
      await scheduledJobsApi.executeJob(id);
      message.success('Задача отправлена на выполнение');
      setTimeout(() => fetchJobs(), 2000);
    } catch (error) {
      message.error('Ошибка при запуске задачи');
    }
  };

  const handleSubmit = async (values: any) => {
    try {
      const data = {
        ...values,
        scheduled_time: values.scheduled_time ? values.scheduled_time.toISOString() : null,
        function_params: values.function_params ? JSON.parse(values.function_params) : null,
      };

      if (editingJob) {
        await scheduledJobsApi.updateJob(editingJob.id, data);
        message.success('Задача обновлена');
      } else {
        await scheduledJobsApi.createJob(data);
        message.success('Задача создана');
      }

      setModalVisible(false);
      fetchJobs();
      fetchStats();
    } catch (error: any) {
      message.error(error.response?.data?.detail || 'Ошибка при сохранении задачи');
    }
  };

  const handleUseTemplate = (template: any) => {
    form.setFieldsValue({
      name: template.name,
      description: template.description,
      job_type: template.job_type,
      cron_expression: template.cron_expression,
      interval_seconds: template.interval_seconds,
      function_path: template.function_path,
      function_params: template.function_params ? JSON.stringify(template.function_params, null, 2) : '',
      is_active: true,
    });
    setTemplatesDrawerVisible(false);
    setModalVisible(true);
  };

  const getJobTypeColor = (type: string) => {
    switch (type) {
      case 'cron':
        return 'blue';
      case 'interval':
        return 'green';
      case 'date':
        return 'orange';
      default:
        return 'default';
    }
  };

  const getJobTypeName = (type: string) => {
    switch (type) {
      case 'cron':
        return 'По расписанию';
      case 'interval':
        return 'Интервал';
      case 'date':
        return 'Однократно';
      default:
        return type;
    }
  };

  const isBuiltinJob = (name: string) => {
    return name.includes('(встроенная)');
  };

  const columns = [
    {
      title: 'Название',
      dataIndex: 'name',
      key: 'name',
      width: 250,
      render: (text: string, record: any) => (
        <div>
          <div style={{ fontWeight: 500 }}>
            {text}
            {isBuiltinJob(text) && (
              <Tag color="blue" style={{ marginLeft: '8px' }}>Встроенная</Tag>
            )}
          </div>
          {record.description && (
            <div style={{ fontSize: '12px', color: '#999' }}>{record.description}</div>
          )}
        </div>
      ),
    },
    {
      title: 'Тип',
      dataIndex: 'job_type',
      key: 'job_type',
      width: 120,
      render: (type: string) => (
        <Tag color={getJobTypeColor(type)}>{getJobTypeName(type)}</Tag>
      ),
    },
    {
      title: 'Расписание',
      key: 'schedule',
      width: 200,
      render: (record: any) => {
        if (record.job_type === 'cron') {
          return <Text code>{record.cron_expression}</Text>;
        } else if (record.job_type === 'interval') {
          const hours = Math.floor(record.interval_seconds / 3600);
          const minutes = Math.floor((record.interval_seconds % 3600) / 60);
          return <Text>Каждые {hours > 0 ? `${hours}ч ` : ''}{minutes > 0 ? `${minutes}м` : `${record.interval_seconds}с`}</Text>;
        } else if (record.job_type === 'date') {
          return <Text>{moment(record.scheduled_time).format('DD.MM.YYYY HH:mm')}</Text>;
        }
        return '-';
      },
    },
    {
      title: 'Функция',
      dataIndex: 'function_path',
      key: 'function_path',
      width: 300,
      render: (path: string) => {
        if (!path) {
          return <Text type="secondary">-</Text>;
        }
        const parts = path.split(':');
        return (
          <div>
            <Text code style={{ fontSize: '11px', display: 'block' }}>
              {parts[0]}
            </Text>
            <Text strong style={{ fontSize: '12px' }}>
              {parts[1]}
            </Text>
          </div>
        );
      },
    },
    {
      title: 'Статус',
      dataIndex: 'is_active',
      key: 'is_active',
      width: 100,
      render: (isActive: boolean) => (
        <Tag color={isActive ? 'success' : 'default'}>
          {isActive ? 'Активна' : 'Неактивна'}
        </Tag>
      ),
    },
    {
      title: 'Статистика',
      key: 'stats',
      width: 150,
      render: (record: any) => (
        <div>
          <div style={{ fontSize: '12px' }}>
            <CheckCircleOutlined style={{ color: '#52c41a' }} /> Запусков: {record.run_count}
          </div>
          {record.error_count > 0 && (
            <div style={{ fontSize: '12px', color: '#ff4d4f' }}>
              Ошибок: {record.error_count}
            </div>
          )}
          {record.last_run && (
            <div style={{ fontSize: '12px', color: '#999' }}>
              Последний: {moment(record.last_run).format('DD.MM HH:mm')}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Действия',
      key: 'actions',
      width: 200,
      fixed: 'right' as const,
      render: (record: any) => (
        <Space size="small">
          <Button
            type="link"
            icon={<PlayCircleOutlined />}
            onClick={() => handleExecuteNow(record.id)}
            title="Выполнить сейчас"
          />
          <Button
            type="link"
            icon={record.is_active ? <PauseCircleOutlined /> : <CheckCircleOutlined />}
            onClick={() => handleToggleActive(record)}
            title={record.is_active ? 'Деактивировать' : 'Активировать'}
          />
          {!isBuiltinJob(record.name) && (
            <Button
              type="link"
              icon={<EditOutlined />}
              onClick={() => handleEdit(record)}
            />
          )}
          {!isBuiltinJob(record.name) && (
            <Popconfirm
              title="Удалить задачу?"
              onConfirm={() => handleDelete(record.id, record.name)}
              okText="Да"
              cancelText="Нет"
            >
              <Button type="link" danger icon={<DeleteOutlined />} />
            </Popconfirm>
          )}
        </Space>
      ),
    },
  ];

  return (
    <div style={{ padding: '24px' }}>
      <div style={{ marginBottom: '24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={2}>📅 Запланированные задачи</Title>
        <Space>
          <Button
            icon={<BulbOutlined />}
            onClick={() => setTemplatesDrawerVisible(true)}
          >
            Шаблоны
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={handleCreate}
          >
            Создать задачу
          </Button>
        </Space>
      </div>

      {stats && (
        <Row gutter={16} style={{ marginBottom: '24px' }}>
          <Col span={6}>
            <Card>
              <Statistic
                title="Всего задач"
                value={stats.total_jobs}
                prefix={<ClockCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Активных"
                value={stats.active_jobs}
                valueStyle={{ color: '#3f8600' }}
                prefix={<CheckCircleOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Всего запусков"
                value={stats.total_runs}
                prefix={<ThunderboltOutlined />}
              />
            </Card>
          </Col>
          <Col span={6}>
            <Card>
              <Statistic
                title="Ошибок"
                value={stats.total_errors}
                valueStyle={{ color: stats.total_errors > 0 ? '#cf1322' : undefined }}
              />
            </Card>
          </Col>
        </Row>
      )}

      <Card>
        <Table
          columns={columns}
          dataSource={jobs}
          loading={loading}
          rowKey="id"
          scroll={{ x: 1400 }}
          rowClassName={(record) => isBuiltinJob(record.name) ? 'builtin-job-row' : ''}
          pagination={{
            pageSize: 20,
            showSizeChanger: true,
            showTotal: (total) => `Всего задач: ${total}`,
          }}
        />
      </Card>
      
      <style>{`
        /* Светлая тема */
        .light-theme .builtin-job-row {
          background-color: #f0f5ff !important;
        }
        .light-theme .builtin-job-row:hover td {
          background-color: #e6f0ff !important;
        }
        
        /* Темная тема */
        .dark-theme .builtin-job-row {
          background-color: #111d2c !important;
        }
        .dark-theme .builtin-job-row:hover td {
          background-color: #1a2332 !important;
        }
      `}</style>

      <Modal
        title={editingJob ? 'Редактировать задачу' : 'Создать задачу'}
        open={modalVisible}
        onCancel={() => setModalVisible(false)}
        onOk={() => form.submit()}
        width={800}
        okText="Сохранить"
        cancelText="Отмена"
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSubmit}
          initialValues={{ is_active: true }}
        >
          <Form.Item
            name="name"
            label="Название"
            rules={[{ required: true, message: 'Введите название' }]}
          >
            <Input placeholder="Например: Синхронизация Vendista" />
          </Form.Item>

          <Form.Item name="description" label="Описание">
            <TextArea rows={2} placeholder="Описание задачи" />
          </Form.Item>

          <Form.Item
            name="job_type"
            label="Тип задачи"
            rules={[{ required: true, message: 'Выберите тип задачи' }]}
          >
            <Select placeholder="Выберите тип">
              <Option value="cron">По расписанию (Cron)</Option>
              <Option value="interval">Интервал</Option>
              <Option value="date">Однократно</Option>
            </Select>
          </Form.Item>

          <Form.Item
            noStyle
            shouldUpdate={(prevValues, currentValues) =>
              prevValues.job_type !== currentValues.job_type
            }
          >
            {({ getFieldValue }) => {
              const jobType = getFieldValue('job_type');
              
              if (jobType === 'cron') {
                return (
                  <Form.Item
                    name="cron_expression"
                    label="Cron выражение"
                    rules={[{ required: true, message: 'Введите cron выражение' }]}
                    extra="Формат: минута час день месяц день_недели. Например: '0 0 * * *' - каждый день в полночь"
                  >
                    <Input placeholder="0 0 * * *" />
                  </Form.Item>
                );
              } else if (jobType === 'interval') {
                return (
                  <Form.Item
                    name="interval_seconds"
                    label="Интервал (секунды)"
                    rules={[{ required: true, message: 'Введите интервал' }]}
                    extra="Например: 3600 - каждый час"
                  >
                    <InputNumber min={1} style={{ width: '100%' }} />
                  </Form.Item>
                );
              } else if (jobType === 'date') {
                return (
                  <Form.Item
                    name="scheduled_time"
                    label="Дата и время"
                    rules={[{ required: true, message: 'Выберите дату и время' }]}
                  >
                    <DatePicker showTime format="DD.MM.YYYY HH:mm" style={{ width: '100%' }} />
                  </Form.Item>
                );
              }
              return null;
            }}
          </Form.Item>

          <Divider />

          <Form.Item
            name="function_path"
            label="Путь к функции"
            rules={[{ required: true, message: 'Введите путь к функции' }]}
            extra="Формат: module.path:function_name"
          >
            <Input placeholder="app.api.terminal_operations.controllers:sync_vendista_data" />
          </Form.Item>

          <Form.Item
            name="function_params"
            label="Параметры функции (JSON)"
            extra="Оставьте пустым, если не требуется. Параметр 'db' добавится автоматически."
          >
            <TextArea rows={4} placeholder='{"sync_date": "today"}' />
          </Form.Item>

          <Form.Item name="is_active" label="Активна" valuePropName="checked">
            <Switch />
          </Form.Item>
        </Form>
      </Modal>

      <Drawer
        title="Шаблоны задач"
        placement="right"
        width={600}
        onClose={() => setTemplatesDrawerVisible(false)}
        open={templatesDrawerVisible}
      >
        <Space direction="vertical" style={{ width: '100%' }} size="large">
          {templates.map((template, index) => (
            <Card
              key={index}
              hoverable
              onClick={() => handleUseTemplate(template)}
              style={{ cursor: 'pointer' }}
            >
              <Title level={5}>{template.name}</Title>
              <div style={{ color: '#666', marginBottom: '8px' }}>
                {template.description}
              </div>
              <Space direction="vertical" size="small" style={{ width: '100%' }}>
                <Text type="secondary">
                  <Tag color={getJobTypeColor(template.job_type)}>
                    {getJobTypeName(template.job_type)}
                  </Tag>
                  {template.cron_expression && (
                    <Text code>{template.cron_expression}</Text>
                  )}
                </Text>
                <Text type="secondary" style={{ fontSize: '12px' }}>
                  {template.example_description}
                </Text>
                <Text code style={{ fontSize: '11px', display: 'block' }}>
                  {template.function_path}
                </Text>
              </Space>
            </Card>
          ))}
        </Space>
      </Drawer>
    </div>
  );
};

export default ScheduledJobs;

