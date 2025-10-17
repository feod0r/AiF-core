import React, { useMemo } from 'react';
import { Tag, Space, message } from 'antd';
import {
  FileOutlined,
  DownloadOutlined,
  FileTextOutlined,
  FilePdfOutlined,
  FileImageOutlined,
  FileExcelOutlined,
  FileWordOutlined,
  FilePptOutlined,
  FileZipOutlined,
  FileUnknownOutlined,
} from '@ant-design/icons';
import GenericDataTable from '../components/GenericDataTable';
import { documentsApi } from '../services/api';
import type { Document, DocumentType, EntityType } from '../types';
import dayjs from 'dayjs';

// Функция для получения иконки файла по MIME типу
const getFileIcon = (mimeType: string, size: number = 16) => {
  const iconProps = { style: { fontSize: size } };
  
  if (mimeType.startsWith('image/')) {
    return <FileImageOutlined {...iconProps} style={{ color: '#52c41a' }} />;
  } else if (mimeType === 'application/pdf') {
    return <FilePdfOutlined {...iconProps} style={{ color: '#ff4d4f' }} />;
  } else if (mimeType.includes('word') || mimeType.includes('document')) {
    return <FileWordOutlined {...iconProps} style={{ color: '#1890ff' }} />;
  } else if (mimeType.includes('excel') || mimeType.includes('sheet')) {
    return <FileExcelOutlined {...iconProps} style={{ color: '#52c41a' }} />;
  } else if (mimeType.includes('powerpoint') || mimeType.includes('presentation')) {
    return <FilePptOutlined {...iconProps} style={{ color: '#fa8c16' }} />;
  } else if (mimeType.includes('zip') || mimeType.includes('rar')) {
    return <FileZipOutlined {...iconProps} style={{ color: '#722ed1' }} />;
  } else if (mimeType.startsWith('text/')) {
    return <FileTextOutlined {...iconProps} style={{ color: '#666' }} />;
  } else {
    return <FileUnknownOutlined {...iconProps} style={{ color: '#999' }} />;
  }
};

// Функция для форматирования размера файла
const formatFileSize = (bytes: number): string => {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
};

// Цвета для типов документов
const documentTypeColors: Record<DocumentType, string> = {
  receipt: '#52c41a',
  contract: '#1890ff',
  invoice: '#fa8c16',
  certificate: '#722ed1',
  photo: '#eb2f96',
  report: '#13c2c2',
  other: '#999',
};

// Цвета для типов сущностей
const entityTypeColors: Record<EntityType, string> = {
  transaction: '#52c41a',
  machine: '#1890ff',
  counterparty: '#fa8c16',
  user: '#722ed1',
  terminal: '#eb2f96',
  inventory_movement: '#13c2c2',
  rent: '#f5222d',
  general: '#999',
};

const Documents: React.FC = () => {
  // Конфигурация колонок
  const columns = useMemo(() => [
    {
      title: 'Файл',
      dataIndex: 'filename',
      key: 'filename',
      width: 300,
      render: (_: any, record: Document): React.ReactElement => (
        <Space>
          {getFileIcon(record.mime_type, 18)}
          <div>
            <div style={{ fontWeight: 500 }}>{record.filename}</div>
            <div style={{ fontSize: 12, color: '#666' }}>
              {formatFileSize(record.file_size)}
            </div>
          </div>
        </Space>
      ),
    },
    {
      title: 'Тип документа',
      dataIndex: 'document_type',
      key: 'document_type',
      width: 120,
      render: (documentType: DocumentType): React.ReactElement => (
        <Tag color={documentTypeColors[documentType] || '#999'}>
          {documentType.toUpperCase()}
        </Tag>
      ),
    },
    {
      title: 'Привязка',
      dataIndex: 'entity_type',
      key: 'entity_type',
      width: 150,
      render: (_: any, record: Document): React.ReactElement => (
        <div>
          <Tag color={entityTypeColors[record.entity_type] || '#999'}>
            {record.entity_type.toUpperCase()}
          </Tag>
          {record.entity_id && (
            <div style={{ fontSize: 12, color: '#666' }}>
              ID: {record.entity_id}
            </div>
          )}
        </div>
      ),
    },
    {
      title: 'Описание',
      dataIndex: 'description',
      key: 'description',
      ellipsis: true,
      render: (description: string): React.ReactElement => (
        <span>{description || '-'}</span>
      ),
    },
    {
      title: 'Теги',
      dataIndex: 'tags',
      key: 'tags',
      width: 150,
      render: (tags: string[]): React.ReactElement => (
        <div>
          {tags && tags.length > 0 ? (
            tags.map((tag: string, index: number) => (
              <Tag key={index} style={{ marginBottom: 2, fontSize: 12 }}>
                {tag}
              </Tag>
            ))
          ) : (
            <span style={{ color: '#999', fontSize: 12 }}>—</span>
          )}
        </div>
      ),
    },
    {
      title: 'Дата загрузки',
      dataIndex: 'upload_date',
      key: 'upload_date',
      width: 150,
      render: (uploadDate: string): React.ReactElement => (
        <span>{dayjs(uploadDate).format('DD.MM.YYYY HH:mm')}</span>
      ),
    },
  ], []);

  // Конфигурация фильтров
  const filters = useMemo(() => [
    {
      key: 'search',
      label: 'Поиск',
      type: 'input' as const,
      placeholder: 'Поиск по названию файла или описанию',
    },
    {
      key: 'document_type',
      label: 'Тип документа',
      type: 'select' as const,
      placeholder: 'Выберите тип документа',
      options: [
        { label: 'Квитанция', value: 'receipt' },
        { label: 'Договор', value: 'contract' },
        { label: 'Счет', value: 'invoice' },
        { label: 'Сертификат', value: 'certificate' },
        { label: 'Фото', value: 'photo' },
        { label: 'Отчет', value: 'report' },
        { label: 'Другое', value: 'other' },
      ],
    },
    {
      key: 'entity_type',
      label: 'Тип привязки',
      type: 'select' as const,
      placeholder: 'Выберите тип привязки',
      options: [
        { label: 'Транзакция', value: 'transaction' },
        { label: 'Машина', value: 'machine' },
        { label: 'Контрагент', value: 'counterparty' },
        { label: 'Пользователь', value: 'user' },
        { label: 'Терминал', value: 'terminal' },
        { label: 'Движение товаров', value: 'inventory_movement' },
        { label: 'Аренда', value: 'rent' },
        { label: 'Общее', value: 'general' },
      ],
    },
    {
      key: 'upload_date_from',
      label: 'Дата загрузки от',
      type: 'date' as const,
      placeholder: 'Выберите дату от',
    },
    {
      key: 'upload_date_to',
      label: 'Дата загрузки до',
      type: 'date' as const,
      placeholder: 'Выберите дату до',
    },
  ], []);

  // Конфигурация формы
  const formConfig = useMemo(() => ({
    fields: [
      {
        name: 'file',
        label: 'Файл',
        type: 'file' as const,
        rules: [{ required: true, message: 'Выберите файл для загрузки' }],
        accept: '.pdf,.doc,.docx,.xls,.xlsx,.jpg,.jpeg,.png,.gif,.zip,.rar',
        multiple: false,
        required: true,
      },
      {
        name: 'document_type',
        label: 'Тип документа',
        type: 'select' as const,
        rules: [{ required: true, message: 'Выберите тип документа' }],
        placeholder: 'Выберите тип документа',
        options: [
          { label: 'Квитанция', value: 'receipt' },
          { label: 'Договор', value: 'contract' },
          { label: 'Счет', value: 'invoice' },
          { label: 'Сертификат', value: 'certificate' },
          { label: 'Фото', value: 'photo' },
          { label: 'Отчет', value: 'report' },
          { label: 'Другое', value: 'other' },
        ],
      },
      {
        name: 'entity_type',
        label: 'Тип привязки',
        type: 'select' as const,
        placeholder: 'Выберите тип привязки',
        options: [
          { label: 'Транзакция', value: 'transaction' },
          { label: 'Машина', value: 'machine' },
          { label: 'Контрагент', value: 'counterparty' },
          { label: 'Пользователь', value: 'user' },
          { label: 'Терминал', value: 'terminal' },
          { label: 'Движение товаров', value: 'inventory_movement' },
          { label: 'Аренда', value: 'rent' },
          { label: 'Общее', value: 'general' },
        ],
      },
      {
        name: 'entity_id',
        label: 'ID сущности',
        type: 'number' as const,
        placeholder: 'Введите ID сущности',
      },
      {
        name: 'description',
        label: 'Описание',
        type: 'textarea' as const,
        placeholder: 'Введите описание документа',
      },
      {
        name: 'tags',
        label: 'Теги',
        type: 'input' as const,
        placeholder: 'Введите теги через запятую',
      },
    ],
    initialValues: {},
  }), []);

  // Подготовка данных для редактирования
  const prepareDataForEdit = (record: Document) => {
    return {
      ...record,
      tags: record.tags && record.tags.length > 0 ? record.tags.join(', ') : '', // Конвертируем массив тегов в строку
    };
  };

  // Обработка отправки формы
  const handleSubmit = (values: any) => {
    const submitData = { ...values };
    
    // Конвертируем строку тегов в массив только если теги есть
    if (values.tags && values.tags.trim()) {
      const tagsArray = values.tags.split(',').map((tag: string) => tag.trim()).filter(Boolean);
      submitData.tags = tagsArray.length > 0 ? tagsArray : [];
    } else {
      submitData.tags = [];
    }
    
    // Убираем поле file из submitData, так как оно нужно только для загрузки
    delete submitData.file;
    
    return submitData;
  };

  // Кастомные действия для строк
  const rowActions = useMemo(() => [
    {
      key: 'download',
      title: 'Скачать',
      icon: <DownloadOutlined />,
      color: '#1890ff',
      onClick: async (record: Document) => {
        try {
          // Получаем токен для скачивания
          const tokenResponse = await documentsApi.generateDownloadToken(record.id);
          // Открываем ссылку для скачивания с токеном
          window.open(documentsApi.downloadByToken(tokenResponse.token), '_blank');
        } catch (error) {
          console.error('Ошибка при скачивании документа:', error);
          message.error('Ошибка при скачивании документа');
        }
      },
    },
  ], []);

  // Обработка list endpoint для возврата массива
  const handleList = async (params?: any) => {
    // Если есть поисковый запрос, используем search API
    if (params?.search && params.search.trim()) {
      const response = await documentsApi.search(params.search.trim(), {
        skip: params.skip || 0,
        limit: params.limit || 50,
      });
      return response;
    }
    
    // Иначе используем обычный список с фильтрацией
    const listParams = { ...params };
    if (listParams.search) {
      // Переименовываем search в filename_contains для backend
      listParams.filename_contains = listParams.search;
      delete listParams.search;
    }
    
    const response = await documentsApi.list(listParams);
    return response;
  };

  // Обработка create endpoint
  const handleCreate = async (data: any) => {
    // Файл обязателен при создании
    if (!data.file || data.file.length === 0) {
      throw new Error('Файл обязателен при создании документа');
    }
    
    const file = data.file[0];
    const formData = new FormData();
    formData.append('file', file);
    
    // Добавляем обязательные поля
    formData.append('document_type', data.document_type);
    
    // Добавляем опциональные поля
    if (data.entity_type) {
      formData.append('entity_type', data.entity_type);
    }
    if (data.entity_id) {
      formData.append('entity_id', data.entity_id.toString());
    }
    if (data.description) {
      formData.append('description', data.description);
    }
          if (data.tags && data.tags.trim()) {
        // Конвертируем теги в JSON строку
        const tagsArray = data.tags.split(',').map((tag: string) => tag.trim()).filter(Boolean);
        if (tagsArray.length > 0) {
          formData.append('tags', JSON.stringify(tagsArray));
        }
      }
    
    return await documentsApi.upload(formData);
  };

  // Обработка update endpoint
  const handleUpdate = async (id: number, data: any) => {
    const processedData = handleSubmit(data);
    return await documentsApi.update(id, processedData);
  };



  return (
    <GenericDataTable<Document>
      title="Документы"
      icon={<FileOutlined />}
      columns={columns}
      filters={filters}
      formConfig={formConfig}
      endpoints={{
        list: handleList,
        create: handleCreate,
        update: handleUpdate,
        delete: documentsApi.delete,
      }}
      onEditDataTransform={prepareDataForEdit}
      rowActions={rowActions}
      searchable={true}
      exportable={true}
      addButtonText="Добавить документ"
      pagination={{
        pageSize: 50,
        pageSizeOptions: ['50', '100', '200', '500'],
      }}
    />
  );
};

export default Documents;
