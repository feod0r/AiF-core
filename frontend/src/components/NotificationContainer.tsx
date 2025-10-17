import React from 'react';
import { useNotifications, Notification } from '../contexts/NotificationContext';
import { CloseOutlined, CheckCircleOutlined, ExclamationCircleOutlined, InfoCircleOutlined, WarningOutlined } from '@ant-design/icons';

const NotificationItem: React.FC<{ notification: Notification }> = ({ notification }) => {
  const { removeNotification } = useNotifications();

  const getIcon = () => {
    switch (notification.type) {
      case 'success':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'error':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />;
      case 'info':
      default:
        return <InfoCircleOutlined style={{ color: '#1890ff' }} />;
    }
  };

  const getBackgroundColor = () => {
    switch (notification.type) {
      case 'success':
        return '#f6ffed';
      case 'error':
        return '#fff2f0';
      case 'warning':
        return '#fffbe6';
      case 'info':
      default:
        return '#f0f9ff';
    }
  };

  const getBorderColor = () => {
    switch (notification.type) {
      case 'success':
        return '#b7eb8f';
      case 'error':
        return '#ffccc7';
      case 'warning':
        return '#ffe58f';
      case 'info':
      default:
        return '#bae7ff';
    }
  };

  return (
    <div
      style={{
        background: getBackgroundColor(),
        border: `1px solid ${getBorderColor()}`,
        borderRadius: '8px',
        padding: '12px 16px',
        marginBottom: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        minWidth: '320px',
        maxWidth: '400px',
        position: 'relative',
        cursor: 'pointer',
        transition: 'all 0.3s ease',
        animation: 'slideInRight 0.3s ease-out',
      }}
      onClick={() => removeNotification(notification.id)}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
        <div style={{ marginTop: '2px' }}>
          {getIcon()}
        </div>
        <div style={{ flex: 1, minWidth: 0 }}>
          <div style={{
            fontWeight: 600,
            fontSize: '14px',
            color: '#262626',
            marginBottom: notification.message ? '4px' : 0,
            wordBreak: 'break-word',
          }}>
            {notification.title}
          </div>
          {notification.message && (
            <div style={{
              fontSize: '13px',
              color: '#595959',
              lineHeight: '1.4',
              wordBreak: 'break-word',
            }}>
              {notification.message}
            </div>
          )}
        </div>
        <button
          style={{
            background: 'none',
            border: 'none',
            cursor: 'pointer',
            padding: '2px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            borderRadius: '4px',
            color: '#8c8c8c',
            fontSize: '12px',
            transition: 'all 0.2s ease',
          }}
          onClick={(e) => {
            e.stopPropagation();
            removeNotification(notification.id);
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'rgba(0, 0, 0, 0.06)';
            e.currentTarget.style.color = '#595959';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'none';
            e.currentTarget.style.color = '#8c8c8c';
          }}
        >
          <CloseOutlined />
        </button>
      </div>
    </div>
  );
};

const NotificationContainer: React.FC = () => {
  const { notifications } = useNotifications();

  if (notifications.length === 0) {
    return null;
  }

  return (
    <>
      <style>
        {`
          @keyframes slideInRight {
            from {
              transform: translateX(100%);
              opacity: 0;
            }
            to {
              transform: translateX(0);
              opacity: 1;
            }
          }
          
          @keyframes slideOutRight {
            from {
              transform: translateX(0);
              opacity: 1;
            }
            to {
              transform: translateX(100%);
              opacity: 0;
            }
          }
        `}
      </style>
      <div
        style={{
          position: 'fixed',
          bottom: '20px',
          right: '20px',
          zIndex: 9999,
          pointerEvents: 'none',
        }}
      >
        <div style={{ pointerEvents: 'auto' }}>
          {notifications
            .sort((a, b) => b.createdAt - a.createdAt) // Новые уведомления сверху
            .map((notification) => (
              <NotificationItem key={notification.id} notification={notification} />
            ))}
        </div>
      </div>
    </>
  );
};

export default NotificationContainer;
