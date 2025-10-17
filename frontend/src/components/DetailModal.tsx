import React from 'react';
import { Modal, Descriptions, Tag, Typography, Space, Divider } from 'antd';
import { CalendarOutlined, FileTextOutlined } from '@ant-design/icons';

const { Text } = Typography;

interface DetailModalProps {
  visible: boolean;
  onClose: () => void;
  record: any;
  title?: string;
  columns?: Array<{
    title: string;
    dataIndex?: string | string[];
    key: string;
    render?: (value: any, record: any) => React.ReactNode;
  }>;
}

const DetailModal: React.FC<DetailModalProps> = ({
  visible,
  onClose,
  record,
  title = 'Детальная информация',
  columns = []
}) => {
  if (!record) return null;

  // Функция для получения вложенного значения
  const getNestedValue = (obj: any, path: string | string[]) => {
    if (typeof path === 'string') {
      return obj[path];
    }
    return path.reduce((current, key) => current?.[key], obj);
  };

  // Функция для рендера значения
  const renderValue = (value: any, column: any) => {
    if (column.render) {
      return column.render(value, record);
    }

    if (value === null || value === undefined) {
      return '-';
    }

    if (typeof value === 'boolean') {
      return <Tag color={value ? 'green' : 'red'}>{value ? 'Да' : 'Нет'}</Tag>;
    }

    if (typeof value === 'string' && value.includes('T')) {
      // Попытка распарсить дату
      try {
        const date = new Date(value);
        if (!isNaN(date.getTime())) {
          return date.toLocaleString('ru-RU');
        }
      } catch (e) {
        // Если не удалось распарсить как дату, возвращаем как есть
      }
    }

    if (typeof value === 'object') {
      return <Text code>{JSON.stringify(value, null, 2)}</Text>;
    }

    return String(value);
  };

  // Фильтруем колонки, исключая системные
  const displayColumns = columns.filter(col => 
    !['actions', 'key'].includes(col.key) && 
    col.dataIndex !== 'actions'
  );

  return (
    <Modal
      title={
        <Space>
          <FileTextOutlined />
          {title}
        </Space>
      }
      open={visible}
      onCancel={onClose}
      footer={null}
      width={800}
      destroyOnClose
    >
      <Descriptions
        bordered
        column={1}
        size="small"
        labelStyle={{ fontWeight: 'bold', width: '200px' }}
      >
        {displayColumns.map((column) => {
          const value = column.dataIndex ? getNestedValue(record, column.dataIndex) : undefined;
          const displayValue = renderValue(value, column);

          return (
            <Descriptions.Item
              key={column.key}
              label={column.title}
              span={1}
            >
              {displayValue}
            </Descriptions.Item>
          );
        })}
      </Descriptions>

      {/* Дополнительная информация, если есть */}
      {record.created_at && (
        <>
          <Divider />
          <Space direction="vertical" style={{ width: '100%' }}>
            <Text type="secondary">
              <CalendarOutlined /> Создано: {new Date(record.created_at).toLocaleString('ru-RU')}
            </Text>
            {record.updated_at && (
              <Text type="secondary">
                <CalendarOutlined /> Обновлено: {new Date(record.updated_at).toLocaleString('ru-RU')}
              </Text>
            )}
          </Space>
        </>
      )}
    </Modal>
  );
};

export default DetailModal;
