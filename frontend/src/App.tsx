import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ConfigProvider } from 'antd';
import ruRU from 'antd/locale/ru_RU';
import { AuthProvider } from './contexts/AuthContext';
import { NotificationProvider, useNotifications } from './contexts/NotificationContext';
import { ThemeProvider } from './contexts/ThemeContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import NotificationContainer from './components/NotificationContainer';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Owners from './pages/Owners';
import Terminals from './pages/Terminals';
import Machines from './pages/Machines';
import Monitoring from './pages/Monitoring';
import Phones from './pages/Phones';
import Rent from './pages/Rent';
import RentMap from './pages/RentMap';
import AccountTypes from './pages/AccountTypes';
import Accounts from './pages/Accounts';
import CounterpartyCategories from './pages/CounterpartyCategories';
import Counterparties from './pages/Counterparties';
import TransactionCategories from './pages/TransactionCategories';
import Transactions from './pages/Transactions';
import Reports from './pages/Reports';
import Charts from './pages/Charts';
import AccountingPivot from './pages/AccountingPivot';
import ItemCategories from './pages/ItemCategories';
import Items from './pages/Items';
import Warehouses from './pages/Warehouses';
import WarehouseStocks from './pages/WarehouseStocks';
import MachineStocks from './pages/MachineStocks';
import InventoryMovements from './pages/InventoryMovements';

import InfoCards from './pages/InfoCards';
import TerminalOperations from './pages/TerminalOperations';
import Documents from './pages/Documents';
import Users from './pages/Users';
import Audit from './pages/Audit';
import ApiTokens from './pages/ApiTokens';
import TelegramBots from './pages/TelegramBots';
import TelegramNotifications from './pages/TelegramNotifications';
import ScheduledJobs from './pages/ScheduledJobs';
import Profile from './pages/Profile';
import { setNotificationFunction } from './services/api';
import './App.css';

// Компонент для инициализации уведомлений
const AppContent: React.FC = () => {
  const { addNotification } = useNotifications();

  useEffect(() => {
    // Устанавливаем функцию уведомлений для API
    setNotificationFunction(addNotification);
  }, [addNotification]);

  return (
    <AuthProvider>
      <Router basename={process.env.REACT_APP_BASE_PATH || "/"}>
        <Routes>
          {/* Публичный маршрут для входа */}
          <Route path="/login" element={<Login />} />
          
          {/* Защищенные маршруты */}
          <Route path="/" element={
            <ProtectedRoute>
              <Layout />
            </ProtectedRoute>
          }>
            <Route index element={<Dashboard />} />
            <Route path="dashboard" element={<Dashboard />} />
            <Route path="owners" element={<Owners />} />
            <Route path="terminals" element={<Terminals />} />
            <Route path="machines" element={<Machines />} />
            <Route path="monitoring" element={<Monitoring />} />
            <Route path="phones" element={<Phones />} />
            <Route path="rent" element={<Rent />} />
            <Route path="rent-map" element={<RentMap />} />
            <Route path="account-types" element={<AccountTypes />} />
            <Route path="accounts" element={<Accounts />} />
            <Route path="counterparty-categories" element={<CounterpartyCategories />} />
            <Route path="counterparties" element={<Counterparties />} />
            <Route path="transaction-categories" element={<TransactionCategories />} />
            <Route path="transactions" element={<Transactions />} />
            <Route path="reports" element={<Reports />} />
            <Route path="charts" element={<Charts />} />
            <Route path="accounting-pivot" element={<AccountingPivot />} />
            <Route path="item-categories" element={<ItemCategories />} />
            <Route path="items" element={<Items />} />
            <Route path="warehouses" element={<Warehouses />} />
            <Route path="warehouse-stocks" element={<WarehouseStocks />} />
            <Route path="machine-stocks" element={<MachineStocks />} />
            <Route path="inventory-movements" element={<InventoryMovements />} />
    
            <Route path="terminal-operations" element={<TerminalOperations />} />
            <Route path="info-cards" element={<InfoCards />} />
            <Route path="documents" element={<Documents />} />
            
            {/* Административные маршруты */}
            <Route path="users" element={
              <ProtectedRoute requireAdmin>
                <Users />
              </ProtectedRoute>
            } />
            <Route path="audit" element={
              <ProtectedRoute requireAdmin>
                <Audit />
              </ProtectedRoute>
            } />
            <Route path="api-tokens" element={
              <ProtectedRoute>
                <ApiTokens />
              </ProtectedRoute>
            } />
            <Route path="telegram-bots" element={
              <ProtectedRoute>
                <TelegramBots />
              </ProtectedRoute>
            } />
            <Route path="telegram-notifications" element={
              <ProtectedRoute>
                <TelegramNotifications />
              </ProtectedRoute>
            } />
            <Route path="scheduled-jobs" element={
              <ProtectedRoute requireAdmin>
                <ScheduledJobs />
              </ProtectedRoute>
            } />
            <Route path="profile" element={<Profile />} />
          </Route>
          
          {/* Редирект с несуществующих маршрутов */}
          <Route path="*" element={<Login />} />
        </Routes>
        <NotificationContainer />
      </Router>
    </AuthProvider>
  );
};

function App() {
  return (
    <ThemeProvider>
      <ConfigProvider locale={ruRU}>
        <NotificationProvider>
          <AppContent />
        </NotificationProvider>
      </ConfigProvider>
    </ThemeProvider>
  );
}

export default App;
