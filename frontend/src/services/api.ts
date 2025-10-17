import axios from 'axios';
import { 
  Owner, Terminal, Machine, Monitoring, Phone, Rent, 
  AccountType, Account, CounterpartyCategory, Counterparty, 
  TransactionCategory, Transaction, TransactionSummary, ApiResponse,
  ItemCategory, Item, Warehouse, WarehouseStock, MachineStock, InventoryMovement
} from '../types';

// Изменяем базовый URL на Python FastAPI бекенд
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // Важно для работы с сессиями
});

// Переменная для хранения функции добавления уведомлений
let addNotificationFunc: ((notification: any) => void) | null = null;

// Функция для установки функции уведомлений
export const setNotificationFunction = (func: (notification: any) => void) => {
  addNotificationFunc = func;
};

// Функция для отправки успешных уведомлений
export const showSuccessNotification = (title: string, message?: string) => {
  if (addNotificationFunc) {
    addNotificationFunc({
      type: 'success',
      title,
      message,
      duration: 4000, // 4 секунды для успеха
    });
  }
};

// Функция для отправки информационных уведомлений
export const showInfoNotification = (title: string, message?: string) => {
  if (addNotificationFunc) {
    addNotificationFunc({
      type: 'info',
      title,
      message,
      duration: 5000, // 5 секунд для информации
    });
  }
};

// Функция для отправки предупреждений
export const showWarningNotification = (title: string, message?: string) => {
  if (addNotificationFunc) {
    addNotificationFunc({
      type: 'warning',
      title,
      message,
      duration: 5000, // 5 секунд для предупреждений
    });
  }
};

// Добавляем интерцептор для обработки ошибок
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    
    // Показываем уведомление об ошибке
    if (addNotificationFunc) {
      let errorMessage = 'Произошла неизвестная ошибка';
      const statusCode = error.response?.status;
      let title = 'Ошибка API';
      
      // Обработка ошибок валидации (422)
      if (statusCode === 422 && error.response?.data?.detail) {
        title = 'Ошибка валидации';
        const details = error.response.data.detail;
        
        if (Array.isArray(details)) {
          // Если это массив ошибок валидации
          const fieldErrors = details.map((err: any) => {
            const field = err.loc?.join('.') || err.loc?.[err.loc.length - 1] || 'неизвестное поле';
            return `${field}: ${err.msg}`;
          });
          errorMessage = fieldErrors.join('\n');
        } else {
          errorMessage = details;
        }
      } else {
        // Обработка других типов ошибок
        errorMessage = error.response?.data?.detail || 
                      error.response?.data?.message || 
                      error.message || 
                      'Произошла неизвестная ошибка';
      }
      
      // Определяем тип ошибки по статус коду
      if (statusCode) {
        switch (statusCode) {
          case 400:
            title = 'Неверный запрос';
            break;
          case 401:
            title = 'Ошибка авторизации';
            break;
          case 403:
            title = 'Доступ запрещен';
            break;
          case 404:
            title = 'Не найдено';
            break;
          case 422:
            title = 'Ошибка валидации';
            break;
          case 500:
            title = 'Ошибка сервера';
            break;
          default:
            title = `Ошибка ${statusCode}`;
        }
      }
      
      // Не показываем уведомления для некоторых эндпоинтов
      const url = error.config?.url || '';
      const skipNotifications = [
        '/auth/login',
        '/auth/me',
      ];
      
      const shouldSkip = skipNotifications.some(endpoint => url.includes(endpoint));
      
      if (!shouldSkip) {
        addNotificationFunc({
          type: 'error',
          title,
          message: errorMessage,
          duration: 8000, // 8 секунд для ошибок валидации
        });
      }
    }
    
    // Для ошибок валидации не делаем страницу белой, просто возвращаем ошибку
    if (error.response?.status === 422) {
      console.warn('Validation error handled gracefully:', error.response?.data);
    }
    
    return Promise.reject(error);
  }
);

// Добавляем интерцептор для добавления токена авторизации
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Auth API
export const authApi = {
  login: (credentials: { username: string; password: string }): Promise<{
    access_token: string;
    token_type: string;
    user: any;
  }> =>
    api.post('/auth/login', credentials).then(res => res.data),
  
  register: (userData: {
    username: string;
    email: string;
    password: string;
    full_name?: string;
    is_admin?: boolean;
  }): Promise<any> =>
    api.post('/auth/register', userData).then(res => res.data),
  
  getCurrentUser: (): Promise<any> =>
    api.get('/auth/me').then(res => res.data),
  
  changePassword: (passwordData: {
    current_password: string;
    new_password: string;
  }): Promise<any> =>
    api.post('/auth/change-password', passwordData).then(res => res.data),
  
  updateProfile: (profileData: {
    username?: string;
    email?: string;
    full_name?: string;
  }): Promise<any> =>
    api.put('/auth/profile', profileData).then(res => res.data),
  
  getUsers: (params?: any): Promise<any[]> =>
    api.get('/auth/users', { params }).then(res => res.data),
  
  activateUser: (userId: number): Promise<any> =>
    api.post(`/auth/users/${userId}/activate`).then(res => res.data),
  
  deactivateUser: (userId: number): Promise<any> =>
    api.post(`/auth/users/${userId}/deactivate`).then(res => res.data),
  
  deleteUser: (userId: number): Promise<void> =>
    api.delete(`/auth/users/${userId}`).then(res => res.data),
};

// Reference Tables API (универсальный API для справочников)
export const referenceTablesApi = {
  getList: (tableName: string, params?: any): Promise<any[]> =>
    api.get(`/reference-tables/${tableName}`, { params }).then(res => res.data),
  
  getById: (tableName: string, id: number): Promise<any> =>
    api.get(`/reference-tables/${tableName}/${id}`).then(res => res.data),
  
  create: (tableName: string, data: any): Promise<any> =>
    api.post(`/reference-tables/${tableName}`, data).then(res => res.data),
  
  update: (tableName: string, id: number, data: any): Promise<any> =>
    api.put(`/reference-tables/${tableName}/${id}`, data).then(res => res.data),
  
  delete: (tableName: string, id: number): Promise<void> =>
    api.delete(`/reference-tables/${tableName}/${id}`).then(res => res.data),
};

// Owners API
export const ownersApi = {
  getList: (params?: any): Promise<ApiResponse<Owner>> =>
    api.get('/owners', { params }).then(res => ({
      data: res.data,
      total: res.data.length,
      success: true,
      message: ''
    })),
  
  getById: (id: number): Promise<Owner> =>
    api.get(`/owners/${id}`).then(res => res.data),
  
  create: (data: Omit<Owner, 'id'>): Promise<Owner> =>
    api.post('/owners', data).then(res => res.data),
  
  update: (id: number, data: Partial<Owner>): Promise<Owner> =>
    api.put(`/owners/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/owners/${id}`).then(res => res.data),
};

// Terminals API
export const terminalsApi = {
  getList: (params?: any): Promise<ApiResponse<Terminal>> =>
    api.get('/terminals', { params }).then(res => ({
      data: res.data,
      total: res.data.length,
      success: true,
      message: ''
    })),
  
  getById: (id: number): Promise<Terminal> =>
    api.get(`/terminals/${id}`).then(res => res.data),
  
  create: (data: Omit<Terminal, 'id'>): Promise<Terminal> =>
    api.post('/terminals', data).then(res => res.data),
  
  update: (id: number, data: Partial<Terminal>): Promise<Terminal> =>
    api.put(`/terminals/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/terminals/${id}`).then(res => res.data),
};

// Machines API
export const machinesApi = {
  getList: (params?: any): Promise<ApiResponse<Machine>> =>
    api.get('/machines', { params }).then(res => ({
      data: res.data,
      total: res.data.length,
      success: true,
      message: ''
    })),
  
  getById: (id: number): Promise<Machine> =>
    api.get(`/machines/${id}`).then(res => res.data),
  
  create: (data: Omit<Machine, 'id'>): Promise<Machine> =>
    api.post('/machines', data).then(res => res.data),
  
  update: (id: number, data: Partial<Machine>): Promise<Machine> =>
    api.put(`/machines/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/machines/${id}`).then(res => res.data),
};

// Monitoring API
export const monitoringApi = {
  getList: (params?: any): Promise<ApiResponse<Monitoring>> =>
    api.get('/monitoring/all', { params }).then(res => ({
      data: res.data,
      total: res.data.length,
      success: true,
      message: ''
    })),
  
  getById: (id: number): Promise<Monitoring> =>
    api.get(`/monitoring/${id}`).then(res => res.data),
  
  getByMachine: (machineId: number, params?: any): Promise<ApiResponse<Monitoring>> =>
    api.get(`/monitoring/${machineId}`, { params }).then(res => ({
      data: res.data,
      total: res.data.length,
      success: true,
      message: ''
    })),
  
  getLatestByMachine: (machineId: number): Promise<Monitoring> =>
    api.get(`/monitoring/${machineId}/latest`).then(res => res.data),
  
  getSummary: (machineId: number, startDate: string, endDate: string): Promise<any> =>
    api.get(`/monitoring/${machineId}/summary`, { 
      params: { start_date: startDate, end_date: endDate } 
    }).then(res => res.data),
  
  create: (data: Omit<Monitoring, 'id'>): Promise<Monitoring> =>
    api.post('/monitoring', data).then(res => res.data),
  
  update: (id: number, data: Partial<Monitoring>): Promise<Monitoring> =>
    api.put(`/monitoring/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/monitoring/${id}`).then(res => res.data),
};

// Phones API
export const phonesApi = {
  getList: (params?: any): Promise<Phone[]> =>
    api.get('/phones', { params }).then(res => res.data),
  
  getById: (id: number): Promise<Phone> =>
    api.get(`/phones/${id}`).then(res => res.data),
  
  create: (data: Omit<Phone, 'id'>): Promise<Phone> =>
    api.post('/phones', data).then(res => res.data),
  
  update: (id: number, data: Partial<Phone>): Promise<Phone> =>
    api.put(`/phones/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/phones/${id}`).then(res => res.data),
};


// Rent API
export const rentApi = {
  getList: (params?: any): Promise<Rent[]> =>
    api.get('/rent', { params }).then(res => res.data),
  
  getById: (id: number): Promise<Rent> =>
    api.get(`/rent/${id}`).then(res => res.data),
  
  create: (data: Omit<Rent, 'id'>): Promise<Rent> =>
    api.post('/rent', data).then(res => res.data),
  
  update: (id: number, data: Partial<Rent>): Promise<Rent> =>
    api.put(`/rent/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/rent/${id}`).then(res => res.data),
};

// Account Types API (используем reference tables)
export const accountTypesApi = {
  getList: (params?: any): Promise<AccountType[]> =>
    referenceTablesApi.getList('account_types', params),
  
  getById: (id: number): Promise<AccountType> =>
    referenceTablesApi.getById('account_types', id),
  
  create: (data: Omit<AccountType, 'id'>): Promise<AccountType> =>
    referenceTablesApi.create('account_types', data),
  
  update: (id: number, data: Partial<AccountType>): Promise<AccountType> =>
    referenceTablesApi.update('account_types', id, data),
  
  delete: (id: number): Promise<void> =>
    referenceTablesApi.delete('account_types', id),
};

// Accounts API
export const accountsApi = {
  getList: (params?: any): Promise<Account[]> =>
    api.get('/accounts', { params }).then(res => res.data),
  
  getById: (id: number): Promise<Account> =>
    api.get(`/accounts/${id}`).then(res => res.data),
  
  create: (data: Omit<Account, 'id'>): Promise<Account> =>
    api.post('/accounts', data).then(res => res.data),
  
  update: (id: number, data: Partial<Account>): Promise<Account> =>
    api.put(`/accounts/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/accounts/${id}`).then(res => res.data),
  
  getByOwner: (ownerId: number): Promise<Account[]> =>
    api.get(`/accounts/owner/${ownerId}`).then(res => res.data),
  
  getSummary: (): Promise<any> =>
    api.get('/accounts/summary').then(res => res.data),
  
  updateAllBalances: (): Promise<{message: string, updated_count: number, total_accounts: number}> =>
    api.post('/accounts/update-all-balances').then(res => res.data),
  
  getDetail: (id: number): Promise<any> =>
    api.get(`/accounts/${id}/detail`).then(res => res.data),
  
  getBalance: (id: number): Promise<any> =>
    api.get(`/accounts/${id}/balance`).then(res => res.data),
};

// Counterparty Categories API (используем reference tables)
export const counterpartyCategoriesApi = {
  getList: (params?: any): Promise<CounterpartyCategory[]> =>
    referenceTablesApi.getList('counterparty_categories', params),
  
  getById: (id: number): Promise<CounterpartyCategory> =>
    referenceTablesApi.getById('counterparty_categories', id),
  
  create: (data: Omit<CounterpartyCategory, 'id'>): Promise<CounterpartyCategory> =>
    referenceTablesApi.create('counterparty_categories', data),
  
  update: (id: number, data: Partial<CounterpartyCategory>): Promise<CounterpartyCategory> =>
    referenceTablesApi.update('counterparty_categories', id, data),
  
  delete: (id: number): Promise<void> =>
    referenceTablesApi.delete('counterparty_categories', id),
};

// Counterparties API
export const counterpartiesApi = {
  getList: (params?: any): Promise<Counterparty[]> =>
    api.get('/counterparties', { params }).then(res => res.data),
  
  getById: (id: number): Promise<Counterparty> =>
    api.get(`/counterparties/${id}`).then(res => res.data),
  
  create: (data: Omit<Counterparty, 'id'>): Promise<Counterparty> =>
    api.post('/counterparties', data).then(res => res.data),
  
  update: (id: number, data: Partial<Counterparty>): Promise<Counterparty> =>
    api.put(`/counterparties/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/counterparties/${id}`).then(res => res.data),
  
  getByCategory: (categoryId: number): Promise<Counterparty[]> =>
    api.get(`/counterparties/category/${categoryId}`).then(res => res.data),
  
  getByInn: (inn: string): Promise<Counterparty> =>
    api.get(`/counterparties/inn/${inn}`).then(res => res.data),
};

// Transaction Categories API
export const transactionCategoriesApi = {
  getList: (): Promise<TransactionCategory[]> =>
    api.get('/transaction-categories').then(res => res.data),
  
  getById: (id: number): Promise<TransactionCategory> =>
    api.get(`/transaction-categories/${id}`).then(res => res.data),
  
  create: (data: any): Promise<TransactionCategory> =>
    api.post('/transaction-categories', data).then(res => res.data),
  
  update: (id: number, data: any): Promise<TransactionCategory> =>
    api.put(`/transaction-categories/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/transaction-categories/${id}`).then(res => res.data),
  
  getByName: (name: string): Promise<TransactionCategory> =>
    api.get(`/transaction-categories/name/${name}`).then(res => res.data),
};

// Transactions API
export const transactionsApi = {
  getList: (params?: any): Promise<Transaction[]> =>
    api.get('/transactions', { params }).then(res => res.data),
  
  getById: (id: number): Promise<Transaction> =>
    api.get(`/transactions/${id}`).then(res => res.data),
  
  create: (data: any): Promise<Transaction> =>
    api.post('/transactions', data).then(res => res.data),
  
  update: (id: number, data: any): Promise<Transaction> =>
    api.put(`/transactions/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/transactions/${id}`).then(res => res.data),
  
  getByAccount: (accountId: number): Promise<Transaction[]> =>
    api.get(`/transactions/account/${accountId}`).then(res => res.data),
  
  getAccountBalance: (accountId: number): Promise<any> =>
    api.get(`/transactions/account/${accountId}/balance`).then(res => res.data),
  
  confirm: (id: number): Promise<Transaction> =>
    api.post(`/transactions/${id}/confirm`).then(res => res.data),
  
  getSummary: (params?: any): Promise<TransactionSummary> =>
    api.get('/transactions/summary', { params }).then(res => res.data),
  
  search: (params?: any): Promise<Transaction[]> =>
    api.get('/transactions', { params }).then(res => res.data),
};

// Item Categories API
export const itemCategoriesApi = {
  getList: (params?: any): Promise<ItemCategory[]> =>
    api.get('/item-categories', { params }).then(res => res.data),
  
  getById: (id: number): Promise<ItemCategory> =>
    api.get(`/item-categories/${id}`).then(res => res.data),
  
  create: (data: Omit<ItemCategory, 'id'>): Promise<ItemCategory> =>
    api.post('/item-categories', data).then(res => res.data),
  
  update: (id: number, data: Partial<ItemCategory>): Promise<ItemCategory> =>
    api.put(`/item-categories/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/item-categories/${id}`).then(res => res.data),
  
  getByName: (name: string): Promise<ItemCategory> =>
    api.get(`/item-categories/name/${name}`).then(res => res.data),
  
  getRoot: (): Promise<ItemCategory[]> =>
    api.get('/item-categories/root').then(res => res.data),
  
  getChildren: (parentId: number): Promise<ItemCategory[]> =>
    api.get(`/item-categories/${parentId}/children`).then(res => res.data),
  
  getTree: (): Promise<any> =>
    api.get('/item-categories/tree').then(res => res.data),
  
  getPath: (id: number): Promise<any> =>
    api.get(`/item-categories/${id}/path`).then(res => res.data),
  
  getByType: (typeId: number): Promise<ItemCategory[]> =>
    api.get(`/item-categories/type/${typeId}`).then(res => res.data),
  
  getSummary: (): Promise<any> =>
    api.get('/item-categories/summary').then(res => res.data),
};

// Items API
export const itemsApi = {
  getList: (params?: any): Promise<Item[]> =>
    api.get('/items', { params }).then(res => res.data),
  
  getById: (id: number): Promise<Item> =>
    api.get(`/items/${id}`).then(res => res.data),
  
  create: (data: Omit<Item, 'id'>): Promise<Item> =>
    api.post('/items', data).then(res => res.data),
  
  update: (id: number, data: Partial<Item>): Promise<Item> =>
    api.put(`/items/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/items/${id}`).then(res => res.data),
  
  getByCategory: (categoryId: number): Promise<Item[]> =>
    api.get(`/items/category/${categoryId}`).then(res => res.data),
  
  getBySku: (sku: string): Promise<Item> =>
    api.get(`/items/sku/${sku}`).then(res => res.data),
  
  getByBarcode: (barcode: string): Promise<Item> =>
    api.get(`/items/barcode/${barcode}`).then(res => res.data),
  
  getDetail: (id: number): Promise<any> =>
    api.get(`/items/${id}/detail`).then(res => res.data),
  
  getSummary: (): Promise<any> =>
    api.get('/items/summary').then(res => res.data),
  
  getWithStockInfo: (params?: any): Promise<any[]> =>
    api.get('/items/with-stock-info', { params }).then(res => res.data),
  
  getLowStock: (params?: any): Promise<any[]> =>
    api.get('/items/low-stock', { params }).then(res => res.data),
  
  getActive: (params?: any): Promise<Item[]> =>
    api.get('/items/active', { params }).then(res => res.data),
  
  getInactive: (params?: any): Promise<Item[]> =>
    api.get('/items/inactive', { params }).then(res => res.data),
  
  getWithStock: (params?: any): Promise<Item[]> =>
    api.get('/items/with-stock', { params }).then(res => res.data),
  
  getWithoutStock: (params?: any): Promise<Item[]> =>
    api.get('/items/without-stock', { params }).then(res => res.data),
  
  searchByName: (name: string, params?: any): Promise<Item[]> =>
    api.get('/items/search/name', { params: { name, ...params } }).then(res => res.data),
  
  searchBySku: (sku: string, params?: any): Promise<Item[]> =>
    api.get('/items/search/sku', { params: { sku, ...params } }).then(res => res.data),
  
  searchByBarcode: (barcode: string, params?: any): Promise<Item[]> =>
    api.get('/items/search/barcode', { params: { barcode, ...params } }).then(res => res.data),
  
  getUnits: (): Promise<string[]> =>
    api.get('/items/units').then(res => res.data),
  
  bulkCreate: (data: any[]): Promise<Item[]> =>
    api.post('/items/bulk/create', data).then(res => res.data),
  
  bulkUpdate: (data: any[]): Promise<Item[]> =>
    api.put('/items/bulk/update', data).then(res => res.data),
  
  bulkDelete: (ids: number[]): Promise<any> =>
    api.delete('/items/bulk/delete', { data: ids }).then(res => res.data),
};

// Warehouses API
export const warehousesApi = {
  getList: (params?: any): Promise<Warehouse[]> =>
    api.get('/warehouses', { params }).then(res => res.data),
  
  getById: (id: number): Promise<Warehouse> =>
    api.get(`/warehouses/${id}`).then(res => res.data),
  
  create: (data: Omit<Warehouse, 'id'>): Promise<Warehouse> =>
    api.post('/warehouses', data).then(res => res.data),
  
  update: (id: number, data: Partial<Warehouse>): Promise<Warehouse> =>
    api.put(`/warehouses/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/warehouses/${id}`).then(res => res.data),
  
  getByOwner: (ownerId: number): Promise<Warehouse[]> =>
    api.get(`/warehouses/owner/${ownerId}`).then(res => res.data),
  
  getByName: (name: string): Promise<Warehouse> =>
    api.get(`/warehouses/name/${name}`).then(res => res.data),
  
  getByPhone: (phone: string): Promise<Warehouse> =>
    api.get(`/warehouses/phone/${phone}`).then(res => res.data),
  
  getByEmail: (email: string): Promise<Warehouse> =>
    api.get(`/warehouses/email/${email}`).then(res => res.data),
  
  getSummary: (): Promise<any> =>
    api.get('/warehouses/summary').then(res => res.data),
  
  getDetail: (id: number): Promise<any> =>
    api.get(`/warehouses/${id}/detail`).then(res => res.data),
  
  getWithStocks: (): Promise<any[]> =>
    api.get('/warehouses/with-stocks').then(res => res.data),
};

// Warehouse Stocks API
export const warehouseStocksApi = {
  getList: (params?: any): Promise<WarehouseStock[]> =>
    api.get('/warehouse-stocks', { params }).then(res => res.data),
  
  getById: (id: number): Promise<WarehouseStock> =>
    api.get(`/warehouse-stocks/${id}`).then(res => res.data),
  
  create: (data: Omit<WarehouseStock, 'id'>): Promise<WarehouseStock> =>
    api.post('/warehouse-stocks', data).then(res => res.data),
  
  update: (id: number, data: Partial<WarehouseStock>): Promise<WarehouseStock> =>
    api.put(`/warehouse-stocks/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/warehouse-stocks/${id}`).then(res => res.data),
  
  getByWarehouse: (warehouseId: number): Promise<WarehouseStock[]> =>
    api.get(`/warehouse-stocks/warehouse/${warehouseId}`).then(res => res.data),
  
  getByItem: (itemId: number): Promise<WarehouseStock[]> =>
    api.get(`/warehouse-stocks/item/${itemId}`).then(res => res.data),
  
  getLowStock: (): Promise<WarehouseStock[]> =>
    api.get('/warehouse-stocks/low-stock-items').then(res => res.data),
  
  getSummary: (params?: any): Promise<any> =>
    api.get('/warehouse-stocks/summary', { params }).then(res => res.data),
  
  getDetail: (id: number): Promise<any> =>
    api.get(`/warehouse-stocks/${id}/detail`).then(res => res.data),
  
  addStock: (warehouseId: number, itemId: number, data: any): Promise<WarehouseStock> =>
    api.post(`/warehouse-stocks/warehouse/${warehouseId}/item/${itemId}/add`, data).then(res => res.data),
  
  removeStock: (warehouseId: number, itemId: number, data: any): Promise<WarehouseStock> =>
    api.post(`/warehouse-stocks/warehouse/${warehouseId}/item/${itemId}/remove`, data).then(res => res.data),
  
  reserveStock: (warehouseId: number, itemId: number, data: any): Promise<WarehouseStock> =>
    api.post(`/warehouse-stocks/warehouse/${warehouseId}/item/${itemId}/reserve`, data).then(res => res.data),
  
  releaseStock: (warehouseId: number, itemId: number, data: any): Promise<WarehouseStock> =>
    api.post(`/warehouse-stocks/warehouse/${warehouseId}/item/${itemId}/release`, data).then(res => res.data),
  
  transferStock: (data: any): Promise<any> =>
    api.post('/warehouse-stocks/transfer', data).then(res => res.data),
  
  bulkAdd: (data: any[]): Promise<WarehouseStock[]> =>
    api.post('/warehouse-stocks/bulk/add', data).then(res => res.data),
  
  bulkRemove: (data: any[]): Promise<WarehouseStock[]> =>
    api.post('/warehouse-stocks/bulk/remove', data).then(res => res.data),
  
  bulkTransfer: (data: any[]): Promise<any[]> =>
    api.post('/warehouse-stocks/bulk/transfer', data).then(res => res.data),
  
  getLowStockReport: (params?: any): Promise<any[]> =>
    api.get('/warehouse-stocks/report/low-stock', { params }).then(res => res.data),
  
  getOverstockReport: (params?: any): Promise<any[]> =>
    api.get('/warehouse-stocks/report/overstock', { params }).then(res => res.data),
};

// Machine Stocks API
export const machineStocksApi = {
  getList: (params?: any): Promise<MachineStock[]> =>
    api.get('/machine-stocks', { params }).then(res => res.data),
  
  getCount: (params?: any): Promise<{count: number}> =>
    api.get('/machine-stocks/count', { params }).then(res => res.data),
  
  getById: (id: number): Promise<MachineStock> =>
    api.get(`/machine-stocks/${id}`).then(res => res.data),
  
  create: (data: Omit<MachineStock, 'id'>): Promise<MachineStock> =>
    api.post('/machine-stocks', data).then(res => res.data),
  
  update: (id: number, data: Partial<MachineStock>): Promise<MachineStock> =>
    api.put(`/machine-stocks/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/machine-stocks/${id}`).then(res => res.data),
  
  getByMachine: (machineId: number): Promise<MachineStock[]> =>
    api.get(`/machine-stocks/machine/${machineId}`).then(res => res.data),
  
  getByItem: (itemId: number): Promise<MachineStock[]> =>
    api.get(`/machine-stocks/item/${itemId}`).then(res => res.data),
  
  getLowStock: (): Promise<MachineStock[]> =>
    api.get('/machine-stocks/low-stock-items').then(res => res.data),
  
  getSummary: (params?: any): Promise<any> =>
    api.get('/machine-stocks/summary', { params }).then(res => res.data),
  
  getGroupedByMachines: (params?: any): Promise<any[]> =>
    api.get('/machine-stocks/grouped-by-machines', { params }).then(res => res.data),
  
  getDetail: (id: number): Promise<any> =>
    api.get(`/machine-stocks/${id}/detail`).then(res => res.data),
  
  addStock: (machineId: number, itemId: number, data: any): Promise<MachineStock> =>
    api.post(`/machine-stocks/machine/${machineId}/item/${itemId}/add`, data).then(res => res.data),
  
  removeStock: (machineId: number, itemId: number, data: any): Promise<MachineStock> =>
    api.post(`/machine-stocks/machine/${machineId}/item/${itemId}/remove`, data).then(res => res.data),
  
  transferStock: (data: any): Promise<any> =>
    api.post('/machine-stocks/transfer', data).then(res => res.data),
  
  loadFromWarehouse: (machineId: number, itemId: number, data: any): Promise<any> =>
    api.post(`/machine-stocks/machine/${machineId}/item/${itemId}/load`, data).then(res => res.data),
  
  unloadToWarehouse: (machineId: number, itemId: number, data: any): Promise<any> =>
    api.post(`/machine-stocks/machine/${machineId}/item/${itemId}/unload`, data).then(res => res.data),
  
  getUtilization: (params?: any): Promise<any[]> =>
    api.get('/machine-stocks/utilization', { params }).then(res => res.data),
  
  bulkAdd: (data: any[]): Promise<MachineStock[]> =>
    api.post('/machine-stocks/bulk/add', data).then(res => res.data),
  
  bulkRemove: (data: any[]): Promise<MachineStock[]> =>
    api.post('/machine-stocks/bulk/remove', data).then(res => res.data),
  
  bulkTransfer: (data: any[]): Promise<any[]> =>
    api.post('/machine-stocks/bulk/transfer', data).then(res => res.data),
  
  bulkLoad: (data: any[]): Promise<any[]> =>
    api.post('/machine-stocks/bulk/load', data).then(res => res.data),
  
  bulkUnload: (data: any[]): Promise<any[]> =>
    api.post('/machine-stocks/bulk/unload', data).then(res => res.data),
  
  getLowStockReport: (params?: any): Promise<any[]> =>
    api.get('/machine-stocks/report/low-stock', { params }).then(res => res.data),
  
  getFullMachinesReport: (params?: any): Promise<any[]> =>
    api.get('/machine-stocks/report/full-machines', { params }).then(res => res.data),
  
  getUtilizationReport: (params?: any): Promise<any[]> =>
    api.get('/machine-stocks/report/utilization', { params }).then(res => res.data),
};

// Inventory Movements API
export const inventoryMovementsApi = {
  getList: (params?: any): Promise<InventoryMovement[]> =>
    api.get('/inventory-movements', { params }).then(res => res.data),

  getCount: (params?: any): Promise<number> =>
    api.get('/inventory-movements/count', { params }).then(res => res.data),

  getById: (id: number): Promise<InventoryMovement> =>
    api.get(`/inventory-movements/${id}`).then(res => res.data),

  create: (data: any): Promise<InventoryMovement> =>
    api.post('/inventory-movements/', data).then(res => res.data),

  update: (id: number, data: any): Promise<InventoryMovement> =>
    api.put(`/inventory-movements/${id}`, data).then(res => res.data),

  delete: (id: number): Promise<void> =>
    api.delete(`/inventory-movements/${id}`).then(res => res.data),

  getByNumber: (number: string): Promise<InventoryMovement> =>
    api.get(`/inventory-movements/number/${number}`).then(res => res.data),

  getItems: (id: number): Promise<any[]> =>
    api.get(`/inventory-movements/${id}/items`).then(res => res.data),

  getByItem: (itemId: number): Promise<InventoryMovement[]> =>
    api.get(`/inventory-movements/item/${itemId}`).then(res => res.data),

  getByWarehouse: (warehouseId: number): Promise<InventoryMovement[]> =>
    api.get(`/inventory-movements/warehouse/${warehouseId}`).then(res => res.data),

  getByMachine: (machineId: number): Promise<InventoryMovement[]> =>
    api.get(`/inventory-movements/machine/${machineId}`).then(res => res.data),

  approve: (id: number, data: { approved_by: number }): Promise<InventoryMovement> =>
    api.post(`/inventory-movements/${id}/approve`, data).then(res => res.data),

  execute: (id: number, data: { executed_by: number }): Promise<InventoryMovement> =>
    api.post(`/inventory-movements/${id}/execute`, data).then(res => res.data),

  bulkApprove: (data: { approved_by: number; movement_ids: number[] }): Promise<any> =>
    api.post('/inventory-movements/bulk-approve', data).then(res => res.data),

  bulkExecute: (data: { executed_by: number; movement_ids: number[] }): Promise<any> =>
    api.post('/inventory-movements/bulk-execute', data).then(res => res.data),

  getSummary: (): Promise<any> =>
    api.get('/inventory-movements/summary').then(res => res.data),

  getDetail: (id: number): Promise<any> =>
    api.get(`/inventory-movements/${id}/detail`).then(res => res.data),
};

// Reports API (DB-backed daily reports)
export const reportsApi = {
  list: (reportDate?: string): Promise<any[]> =>
    api
      .get('/reports', { params: reportDate ? { report_date: reportDate } : undefined })
      .then(res => res.data),
  computeByDate: (dateISO: string): Promise<{ processed: number; report_date: string }> =>
    api
      .post(`/reports/compute-by-date`, null, { params: { date: dateISO } })
      .then(res => res.data),
  compute: (report_date: string): Promise<{ processed: number; report_date: string }> =>
    api
      .post(`/reports/compute`, { report_date })
      .then(res => res.data),
  aggregate: (params: {
    machine_id?: number;
    period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'halfyear' | 'yearly';
    start_date?: string;
    end_date?: string;
  }): Promise<any[]> =>
    api.get('/reports/aggregate', { params }).then(res => res.data),
  detailedByPeriod: (params: {
    period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'halfyear' | 'yearly';
    start_date?: string;
    end_date?: string;
    machine_id?: number;
  }): Promise<any[]> =>
    api.get('/reports/detailed-by-period', { params }).then(res => res.data),
};

// API для графиков
export const getToysChartData = async (params: {
  machine_id?: number;
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'halfyear' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/aggregate', { params }).then(res => res.data);
};

export const getCoinsChartData = async (params: {
  machine_id?: number;
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'halfyear' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/aggregate', { params }).then(res => res.data);
};

export const getProfitChartData = async (params: {
  machine_id?: number;
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'halfyear' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/aggregate', { params }).then(res => res.data);
};

// API для сводных таблиц аккаунтинга
export const getAccountingPivotByCategories = async (params: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/accounting/pivot/categories', { params }).then(res => res.data);
};

export const getAccountingPivotByCounterparties = async (params: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/accounting/pivot/counterparties', { params }).then(res => res.data);
};

export const getAccountingPivotByMachines = async (params: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/accounting/pivot/machines', { params }).then(res => res.data);
};

// API для диаграммы доходов/расходов
export const getAccountingChartData = async (params: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/accounting/chart', { params }).then(res => res.data);
};

// API для транспонированной таблицы
export const getAccountingTransposedData = async (params: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/accounting/transposed', { params }).then(res => res.data);
};

// API для транспонированных таблиц только с суммами
export const getTransposedSumByCategories = async (params: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/accounting/pivot-transposed/categories', { params }).then(res => res.data);
};

export const getTransposedSumByCounterparties = async (params: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/accounting/pivot-transposed/counterparties', { params }).then(res => res.data);
};

export const getTransposedSumByMachines = async (params: {
  period?: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly';
  start_date?: string;
  end_date?: string;
}) => {
  return api.get('/reports/accounting/pivot-transposed/machines', { params }).then(res => res.data);
};

// Info Cards API
export const infoCardsApi = {
  list: (includeInactive: boolean = false): Promise<any[]> =>
    api.get('/info-cards', { params: { include_inactive: includeInactive } }).then(res => res.data),
  
  get: (id: number): Promise<any> =>
    api.get(`/info-cards/${id}`).then(res => res.data),
  
  create: (data: any): Promise<any> =>
    api.post('/info-cards', data).then(res => res.data),
  
  update: (id: number, data: any): Promise<any> =>
    api.put(`/info-cards/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/info-cards/${id}`).then(() => {}),
  
  getSecrets: (id: number, password?: string): Promise<any> =>
    api.post(`/info-cards/${id}/secrets`, { action: 'view', password }).then(res => res.data),
};

// Terminal Operations API
export const terminalOperationsApi = {
  list: (params?: any): Promise<any[]> =>
    api.get('/terminal-operations', { params }).then(res => res.data),
  
  get: (id: number): Promise<any> =>
    api.get(`/terminal-operations/${id}`).then(res => res.data),
  
  create: (data: any): Promise<any> =>
    api.post('/terminal-operations', data).then(res => res.data),
  
  update: (id: number, data: any): Promise<any> =>
    api.put(`/terminal-operations/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/terminal-operations/${id}`).then(() => {}),
  
  closeDay: (data: { operation_date: string; closed_by: number }): Promise<any> =>
    api.post('/terminal-operations/close-day', data).then(res => res.data),
  
  getSummary: (params?: any): Promise<any> =>
    api.get('/terminal-operations/summary/stats', { params }).then(res => res.data),
  
  syncVendista: (data: { sync_date: string }): Promise<any> =>
    api.post('/terminal-operations/sync-vendista', data).then(res => res.data),
};

// Documents API
export const documentsApi = {
  list: (params?: any): Promise<any[]> =>
    api.get('/documents', { params }).then(res => res.data),
  
  get: (id: number): Promise<any> =>
    api.get(`/documents/${id}`).then(res => res.data),
  
  upload: (formData: FormData): Promise<any> =>
    api.post('/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    }).then(res => res.data),
  
  update: (id: number, data: any): Promise<any> =>
    api.put(`/documents/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/documents/${id}`).then(res => res.data),
  
  download: (id: number): string =>
    `${API_BASE_URL}/documents/${id}/download`,
  
  generateDownloadToken: (id: number): Promise<any> =>
    api.post(`/documents/${id}/download-token`).then(res => res.data),
  
  downloadByToken: (token: string): string =>
    `${API_BASE_URL}/documents/download/${token}`,
  
  search: (query: string, params?: any): Promise<any[]> =>
    api.get(`/documents/search/${encodeURIComponent(query)}`, { params }).then(res => res.data),
  
  getByEntity: (entityType: string, entityId: number, params?: any): Promise<any[]> =>
    api.get(`/entities/${entityType}/${entityId}/documents`, { params }).then(res => res.data),
  
  getStats: (): Promise<any> =>
    api.get('/documents/stats/summary').then(res => res.data),
  
  getTypes: (): Promise<any> =>
    api.get('/documents/types/list').then(res => res.data),
};

// API Tokens API
export const apiTokensApi = {
  list: (params?: any): Promise<any[]> =>
    api.get('/api-tokens', { params }).then(res => res.data),
  
  get: (id: number): Promise<any> =>
    api.get(`/api-tokens/${id}`).then(res => res.data),
  
  create: (data: any): Promise<any> =>
    api.post('/api-tokens', data).then(res => res.data),
  
  update: (id: number, data: any): Promise<any> =>
    api.put(`/api-tokens/${id}`, data).then(res => res.data),
  
  delete: (id: number): Promise<void> =>
    api.delete(`/api-tokens/${id}`).then(() => {}),
  
  revoke: (id: number): Promise<void> =>
    api.post(`/api-tokens/${id}/revoke`).then(() => {}),
  
  regenerate: (id: number): Promise<any> =>
    api.post(`/api-tokens/${id}/regenerate`).then(res => res.data),
  
  getStats: (): Promise<any> =>
    api.get('/api-tokens/stats/summary').then(res => res.data),
  
  getPresets: (): Promise<any> =>
    api.get('/api-tokens/presets/permissions').then(res => res.data),
  
  getScopes: (): Promise<any> =>
    api.get('/api-tokens/scopes/available').then(res => res.data),
  
  getPermissions: (): Promise<any> =>
    api.get('/api-tokens/permissions/available').then(res => res.data),
};

// Audit API
export const auditApi = {
  getLogs: (params?: any): Promise<any> =>
    api.get('/audit/logs', { params }).then(res => res.data),
  
  getLog: (id: number): Promise<any> =>
    api.get(`/audit/logs/${id}`).then(res => res.data),
  
  createLog: (data: any): Promise<any> =>
    api.post('/audit/logs', data).then(res => res.data),
  
  getStats: (params?: any): Promise<any> =>
    api.get('/audit/stats', { params }).then(res => res.data),
  
  getActions: (): Promise<string[]> =>
    api.get('/audit/actions').then(res => res.data),
  
  getTables: (): Promise<string[]> =>
    api.get('/audit/tables').then(res => res.data),
  
  cleanup: (daysToKeep: number = 90): Promise<any> =>
    api.delete('/audit/cleanup', { params: { days_to_keep: daysToKeep } }).then(res => res.data),
};

// Telegram Notifications API
export const telegramApi = {
  // Управление ботами
  listBots: (params?: any): Promise<any[]> =>
    api.get('/telegram/bots', { params }).then(res => res.data),
  
  getBot: (id: number): Promise<any> =>
    api.get(`/telegram/bots/${id}`).then(res => res.data),
  
  createBot: (data: any): Promise<any> =>
    api.post('/telegram/bots', data).then(res => res.data),
  
  updateBot: (id: number, data: any): Promise<any> =>
    api.put(`/telegram/bots/${id}`, data).then(res => res.data),
  
  deleteBot: (id: number): Promise<void> =>
    api.delete(`/telegram/bots/${id}`).then(() => {}),
  
  activateBot: (id: number): Promise<any> =>
    api.post(`/telegram/bots/${id}/activate`).then(res => res.data),
  
  deactivateBot: (id: number): Promise<any> =>
    api.post(`/telegram/bots/${id}/deactivate`).then(res => res.data),
  
  testBot: (id: number, message: string): Promise<any> =>
    api.post(`/telegram/bots/${id}/test`, { message }).then(res => res.data),
  
  getBotStats: (): Promise<any> =>
    api.get('/telegram/bots/stats/summary').then(res => res.data),
  
  // Управление уведомлениями
  sendNotification: (data: any): Promise<any> =>
    api.post('/telegram/notifications/send', data).then(res => res.data),
  
  sendTestMessage: (data: any): Promise<any> =>
    api.post('/telegram/notifications/test', data).then(res => res.data),
  
  getNotificationTypes: (): Promise<any[]> =>
    api.get('/telegram/notifications/types').then(res => res.data),
  
  getNotificationHistory: (params?: any): Promise<any> =>
    api.get('/telegram/notifications/history', { params }).then(res => res.data),
  
  // Статистика
  getStats: (): Promise<any> =>
    api.get('/telegram/stats/summary').then(res => res.data),
};

// Scheduled Jobs API
export const scheduledJobsApi = {
  listJobs: (params?: any): Promise<any[]> =>
    api.get('/scheduled/jobs', { params }).then(res => res.data),
  
  getJob: (id: number): Promise<any> =>
    api.get(`/scheduled/jobs/${id}`).then(res => res.data),
  
  createJob: (data: any): Promise<any> =>
    api.post('/scheduled/jobs', data).then(res => res.data),
  
  updateJob: (id: number, data: any): Promise<any> =>
    api.put(`/scheduled/jobs/${id}`, data).then(res => res.data),
  
  deleteJob: (id: number): Promise<void> =>
    api.delete(`/scheduled/jobs/${id}`).then(() => {}),
  
  activateJob: (id: number): Promise<any> =>
    api.post(`/scheduled/jobs/${id}/activate`).then(res => res.data),
  
  deactivateJob: (id: number): Promise<any> =>
    api.post(`/scheduled/jobs/${id}/deactivate`).then(res => res.data),
  
  executeJob: (id: number): Promise<any> =>
    api.post(`/scheduled/jobs/${id}/execute`).then(res => res.data),
  
  getStats: (): Promise<any> =>
    api.get('/scheduled/stats').then(res => res.data),
  
  getTemplates: (): Promise<any[]> =>
    api.get('/scheduled/templates').then(res => res.data),
  
  getActiveJobs: (): Promise<any[]> =>
    api.get('/scheduled/active-jobs').then(res => res.data),
};

export default api; 