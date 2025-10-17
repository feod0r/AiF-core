import React, { Component, ErrorInfo, ReactNode } from 'react';
import { Result, Button } from 'antd';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
  error?: Error;
}

class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): State {
    // Обновляем состояние, чтобы следующий рендер показал fallback UI
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
    
    // Не показываем fallback для ошибок валидации API
    if (error.message.includes('Validation') || error.message.includes('422')) {
      console.warn('Validation error prevented from showing error boundary');
      this.setState({ hasError: false });
      return;
    }
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <Result
          status="error"
          title="Что-то пошло не так"
          subTitle="Произошла неожиданная ошибка. Попробуйте перезагрузить страницу."
          extra={[
            <Button type="primary" key="reload" onClick={this.handleReload}>
              Перезагрузить страницу
            </Button>,
          ]}
        />
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
