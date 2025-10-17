export interface Owner {
  id: number;
  name: string;
  inn: string;
  vendista_user?: string;
  vendista_pass?: string;
  start_date: string;
  end_date: string;
}

export interface Terminal {
  id: number;
  terminal?: number;
  name: string;
  owner_id?: number;
  account_id?: number;
  start_date: string;
  end_date: string;
  owner?: Owner;
  account?: Account;
}

export interface Machine {
  id: number;
  name: string;
  game_cost?: number;
  terminal_id?: number;
  rent_id?: number;
  phone_id?: number;
  start_date: string;
  end_date: string;
  terminal?: Terminal;
  rent?: Rent;
  phone?: Phone;
}

export interface Monitoring {
  id: number;
  date: string;
  coins: number;
  toys: number;
  machine_id: number;
  machine?: Machine;
}

export interface Phone {
  id: number;
  pay_date: number;
  phone: string;
  amount: number;
  details?: string;
  start_date: string;
  end_date: string;
  machine?: Machine; // Связь с машиной (если есть)
}

export interface Account {
  id: number;
  name: string;
  balance: number;
  account_type?: {
    id: number;
    name: string;
  };
  owner?: Owner;
}



export interface Rent {
  id: number;
  pay_date: number;
  location: string;
  amount: number;
  details?: string;
  payer?: Owner;
  start_date: string;
  end_date: string;
  latitude?: number;
  longitude?: number;
  machine?: Machine; // Связь с машиной (если есть)
  payerData?: Owner;
}

// Новые типы для аккаунтинга

export interface AccountType {
  id: number;
  name: string;
  description?: string;
  start_date: string;
  end_date: string;
}

export interface Account {
  id: number;
  name: string;
  account_type_id: number;
  owner_id: number;
  balance: number;
  initial_balance: number;
  currency: string;
  account_number?: string;
  bank_name?: string;
  is_active: boolean;
  start_date: string;
  end_date: string;
  accountType?: AccountType;
  owner?: Owner;
}

export interface CounterpartyCategory {
  id: number;
  name: string;
  description?: string;
  start_date: string;
  end_date: string;
}

export interface Counterparty {
  id: number;
  name: string;
  category_id?: number;
  inn?: string;
  kpp?: string;
  address?: string;
  phone?: string;
  email?: string;
  contact_person?: string;
  notes?: string;
  is_active: boolean;
  start_date: string;
  end_date: string;
  category?: CounterpartyCategory;
}

export interface TransactionCategory {
  id: number;
  name: string;
  transaction_type_id: number;
  description?: string;
  is_active: boolean;
  start_date: string;
  end_date: string;
  transactionType?: {
    id: number;
    name: string;
    type: 'income' | 'expense' | 'transfer';
  };
}

export interface Transaction {
  id: number;
  date: string;
  account_id: number;
  to_account_id?: number;
  category_id: number;
  counterparty_id?: number;
  amount: number;
  type: 'income' | 'expense' | 'transfer';
  description?: string;
  machine_id?: number;
  rent_location_id?: number;
  reference_number?: string;
  is_confirmed: boolean;
  created_by?: number;
  created_at: string;
  updated_at: string;
  account?: Account;
  to_account?: Account;
  category?: TransactionCategory;
  counterparty?: Counterparty;
  machine?: Machine;
  rentLocation?: Rent;
}

export interface TransactionSummary {
  income: number;
  expense: number;
  net: number;
  total_transactions: number;
}

// Новые типы для инвентаря

export interface ItemCategory {
  id: number;
  name: string;
  description?: string;
  category_type_id: number;
  parent_id?: number;
  is_active: boolean;
  start_date: string;
  end_date: string;
  category_type?: {
    id: number;
    name: string;
    type: 'inventory' | 'equipment' | 'consumables';
    description?: string;
  };
  parent?: ItemCategory;
  children?: ItemCategory[];
}

export interface Item {
  id: number;
  name: string;
  sku: string;
  category_id: number;
  description?: string;
  unit: string;
  weight?: number;
  dimensions?: string;
  barcode?: string;
  min_stock: number;
  max_stock?: number;
  is_active: boolean;
  start_date: string;
  end_date: string;
  category?: ItemCategory;
  // Вычисляемые поля для остатков
  total_warehouse_quantity?: number;
  total_machine_quantity?: number;
  total_reserved?: number;
  available_quantity?: number;
}

export interface Warehouse {
  id: number;
  name: string;
  address?: string;
  contact_person_id?: number;
  contact_person?: Counterparty;
  owner_id: number;
  is_active: boolean;
  start_date: string;
  end_date: string;
  owner?: Owner;
}

export interface WarehouseStock {
  id: number;
  warehouse_id: number;
  item_id: number;
  quantity: number;
  reserved_quantity: number;
  min_quantity: number;
  max_quantity?: number;
  location?: string;
  last_updated: string;
  warehouse?: Warehouse;
  item?: Item;
  // Вычисляемые поля
  available_quantity?: number;
  utilization_percent?: number;
  is_low_stock?: boolean;
  is_overstock?: boolean;
}

export interface MachineStock {
  id: number;
  machine_id: number;
  item_id: number;
  quantity: number;
  capacity?: number;
  min_quantity: number;
  last_updated: string;
  machine?: Machine;
  item?: Item;
  // Вычисляемые поля
  utilization_percent?: number;
  is_low_stock?: boolean;
  is_full?: boolean;
}

export interface InventoryMovement {
  id: number;
  movement_type: 'receipt' | 'issue' | 'transfer' | 'adjustment' | 'sale' | 'load_machine' | 'unload_machine';
  document_number: string;
  document_date: string;
  status_id: number;
  status?: {
    id: number;
    name: string;
    description?: string;
  };
  description?: string;
  
  // Складские операции
  warehouse_id?: number;
  from_warehouse_id?: number;
  to_warehouse_id?: number;
  warehouse?: Warehouse;
  fromWarehouse?: Warehouse;
  toWarehouse?: Warehouse;
  
  // Автоматные операции
  machine_id?: number;
  from_machine_id?: number;
  to_machine_id?: number;
  machine?: Machine;
  fromMachine?: Machine;
  toMachine?: Machine;
  
  // Контрагенты и ответственные
  counterparty_id?: number;
  counterparty?: Counterparty;
  created_by?: number;
  created_by_user?: {
    id: number;
    username: string;
    full_name: string;
  };
  approved_by?: number;
  approved_by_user?: {
    id: number;
    username: string;
    full_name: string;
  };
  executed_by?: number;
  executed_by_user?: {
    id: number;
    username: string;
    full_name: string;
  };
  
  // Даты
  created_at: string;
  approved_at?: string;
  executed_at?: string;
  
  // Суммы
  total_amount: number;
  currency: string;
  
  // Позиции
  items?: InventoryMovementItem[];
  
  // Дополнительная информация
  is_approved?: boolean;
  is_executed?: boolean;
  can_edit?: boolean;
  can_approve?: boolean;
  can_execute?: boolean;
}

export interface InventoryMovementItem {
  id: number;
  movement_id: number;
  item_id: number;
  quantity: number;
  price: number;
  amount: number;
  description?: string;
  item?: Item;
}

export interface BulkOperationResult {
  success_count: number;
  error_count: number;
  errors: Array<{
    movement_id: string;
    error: string;
  }>;
  message: string;
}

export interface BulkMovementApproval {
  approved_by: number;
  movement_ids: number[];
}

export interface BulkMovementExecution {
  executed_by: number;
  movement_ids: number[];
}

export interface ApiResponse<T> {
  data: T[];
  total: number;
  success: boolean;
  message?: string;
}

// Типы для графиков
export interface ChartDataPoint {
  period: string;
  total_toys?: number;
  total_coins?: number;
  total_profit?: number;
  total_revenue?: number;
  total_toys_sold?: number;
  total_coins_earned?: number;
  records_count: number;
}

export interface ChartData {
  success: boolean;
  data: ChartDataPoint[];
  period: string;
}

export interface ChartParams {
  machine_id?: number;
  period?: 'daily' | 'weekly' | 'monthly';
  start_date?: string;
  end_date?: string;
}

// Типы для сводных таблиц аккаунтинга
export interface AccountingPivotCategory {
  category_name: string;
  category_type: string;
  total_income: number;
  total_expense: number;
  total_transfer: number;
  transactions_count: number;
}

export interface AccountingPivotCounterparty {
  counterparty_name: string;
  counterparty_category: string;
  total_income: number;
  total_expense: number;
  total_transfer: number;
  transactions_count: number;
}

export interface AccountingPivotMachine {
  machine_name: string;
  total_income: number;
  total_expense: number;
  total_transfer: number;
  transactions_count: number;
}

export interface AccountingPivotSummary {
  total_income: number;
  total_expense: number;
  total_transfer: number;
  transactions_count: number;
}

export interface AccountingPivotPeriod {
  period: string;
  categories?: AccountingPivotCategory[];
  counterparties?: AccountingPivotCounterparty[];
  machines?: AccountingPivotMachine[];
  summary: AccountingPivotSummary;
}

export interface AccountingPivotData {
  success: boolean;
  data: AccountingPivotPeriod[];
  period: string;
}

// Типы для диаграммы доходов/расходов
export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor: string;
  borderColor: string;
  borderWidth: number;
}

export interface AccountingChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface AccountingChartResponse {
  success: boolean;
  data: AccountingChartData;
  period: string;
}

// Типы для транспонированной таблицы
export interface TransposedCellData {
  income: number;
  expense: number;
  transfer: number;
  count: number;
}

export interface TransposedRowData {
  category_name: string;
  [period: string]: TransposedCellData | string;
  total: TransposedCellData;
}

export interface AccountingTransposedData {
  categories: string[];
  periods: string[];
  rows: TransposedRowData[];
}

export interface AccountingTransposedResponse {
  success: boolean;
  data: AccountingTransposedData;
  period: string;
}

// Типы для информационных карточек
export interface InfoCard {
  id: number;
  title: string;
  description?: string;
  external_link?: string;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  has_secrets: boolean;
}

export interface InfoCardWithSecrets extends InfoCard {
  secrets?: Record<string, string>;
}

export interface InfoCardCreate {
  title: string;
  description?: string;
  external_link?: string;
  secrets?: Record<string, string>;
}

export interface InfoCardUpdate {
  title?: string;
  description?: string;
  external_link?: string;
  secrets?: Record<string, string>;
  is_active?: boolean;
}

// Типы для транспонированных таблиц только с суммами
export interface TransposedSumRow {
  name: string;
  [period: string]: string | number;
}

export interface TransposedSumResponse {
  success: boolean;
  periods: string[];
  rows: TransposedSumRow[];
}

// Типы для отчетов по остаткам
export interface StockSummary {
  total_quantity: number;
  total_reserved: number;
  total_available: number;
  items_with_stock: number;
  low_stock_items: number;
}

export interface LowStockItem {
  id: number;
  name: string;
  sku: string;
  category?: ItemCategory;
  current_quantity: number;
  min_quantity: number;
  warehouse?: {
    id: number;
    name: string;
  };
}

export interface LowStockWarehouse {
  warehouse?: Warehouse;
  low_stock_items: {
    item_id: number;
    item_name: string;
    current_quantity: number;
    min_quantity: number;
  }[];
}

// Типы для массовых операций
export interface BulkOperation {
  warehouse_id?: number;
  machine_id?: number;
  item_id: number;
  quantity: number;
}

export interface BulkTransfer {
  from_warehouse_id: number;
  to_warehouse_id: number;
  item_id: number;
  quantity: number;
}

export interface BulkLoad {
  warehouse_id: number;
  machine_id: number;
  item_id: number;
  quantity: number;
}

export interface BulkUnload {
  machine_id: number;
  warehouse_id: number;
  item_id: number;
  quantity: number;
}

// Типы для авторизации
export interface Role {
  id: number;
  name: string;
  description?: string;
  is_active: boolean;
}

export interface User {
  id: number;
  username: string;
  email: string;
  full_name?: string;
  role: Role;
  is_active: boolean;
  last_login?: string;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  full_name?: string;
  role_id?: number;
}

export interface PasswordChange {
  current_password: string;
  new_password: string;
}

// Типы для операций терминалов
export interface TerminalOperation {
  id: number;
  operation_date: string;
  terminal: Terminal;
  amount: number;
  transaction_count: number;
  commission: number;
  is_closed: boolean;
  closed_at?: string;
  closed_by_user?: {
    id: number;
    username: string;
    full_name: string;
  };
  created_at: string;
  updated_at: string;
}

export interface TerminalOperationCreate {
  operation_date: string;
  terminal_id: number;
  amount: number;
  transaction_count: number;
  commission?: number;
}

export interface TerminalOperationUpdate {
  operation_date?: string;
  amount?: number;
  transaction_count?: number;
  commission?: number;
}

export interface CloseDayRequest {
  operation_date: string;
  closed_by: number;
}

export interface CloseDayResponse {
  success: boolean;
  message: string;
  closed_operations_count: number;
  total_amount_processed: number;
  affected_accounts: Array<{
    account_id: number;
    account_number: string;
    amount: number;
    commission: number;
    operations_count: number;
  }>;
}

export interface TerminalOperationSummary {
  total_operations: number;
  total_amount: number;
  total_commission: number;
  total_transactions: number;
  closed_operations: number;
  open_operations: number;
}

export interface VendistaSyncRequest {
  sync_date: string;
}

export interface VendistaSyncResponse {
  success: boolean;
  message: string;
  synced_terminals: number;
  total_amount: number;
  total_transactions: number;
  errors: string[];
}

export interface VendistaTerminalInfo {
  terminal_id: number;
  terminal_name: string;
  vendista_id: number;
  owner_name: string;
  vendista_user: string;
  vendista_pass: string;
}

// Типы для документов
export type DocumentType = 'receipt' | 'contract' | 'invoice' | 'certificate' | 'photo' | 'report' | 'other';
export type EntityType = 'transaction' | 'machine' | 'counterparty' | 'user' | 'terminal' | 'inventory_movement' | 'rent' | 'general';

export interface Document {
  id: number;
  filename: string;
  original_filename: string;
  file_path: string;
  file_size: number;
  mime_type: string;
  document_type: DocumentType;
  entity_type: EntityType;
  entity_id?: number;
  description?: string;
  tags: string[];
  upload_date: string;
  uploaded_by: number;
  download_url: string;
  uploader?: {
    id: number;
    username: string;
    full_name?: string;
  };
}

export interface DocumentCreate {
  filename: string;
  document_type: DocumentType;
  entity_type?: EntityType;
  entity_id?: number;
  description?: string;
  tags?: string[];
}

export interface DocumentUpdate {
  filename?: string;
  document_type?: DocumentType;
  entity_type?: EntityType;
  entity_id?: number;
  description?: string;
  tags?: string[];
}

export interface DocumentFilter {
  document_type?: DocumentType;
  entity_type?: EntityType;
  entity_id?: number;
  uploaded_by?: number;
  filename_contains?: string;
  tags?: string[];
  date_from?: string;
  date_to?: string;
}

export interface DocumentStats {
  total_documents: number;
  total_size_bytes: number;
  total_size_mb: number;
  documents_by_type: Record<string, number>;
  documents_by_entity: Record<string, number>;
  recent_uploads: Document[];
}

export interface DocumentTypeOption {
  value: string;
  label: string;
}

export interface EntityTypeOption {
  value: string;
  label: string;
}

// API Tokens
export interface ApiToken {
  id: number;
  name: string;
  description?: string;
  token_prefix: string;
  permissions: string[];
  scopes?: string[];
  ip_whitelist?: string[];
  rate_limit?: number;
  is_active: boolean;
  expires_at?: string;
  last_used_at?: string;
  usage_count: number;
  created_at: string;
  updated_at: string;
  created_by: number;
  creator_username?: string;
}

export interface ApiTokenCreate {
  name: string;
  description?: string;
  permissions: string[];
  scopes?: string[];
  ip_whitelist?: string[];
  rate_limit?: number;
  expires_at?: string;
}

export interface ApiTokenUpdate {
  name?: string;
  description?: string;
  permissions?: string[];
  scopes?: string[];
  ip_whitelist?: string[];
  rate_limit?: number;
  is_active?: boolean;
  expires_at?: string;
}

export interface ApiTokenCreateResponse {
  token_info: ApiToken;
  token: string; // Полный токен - показывается только один раз!
}

export interface ApiTokenStats {
  total_tokens: number;
  active_tokens: number;
  expired_tokens: number;
  inactive_tokens: number;
  total_usage: number;
  tokens_by_user: Record<string, number>;
  most_used_tokens: Array<{
    id: number;
    name: string;
    usage_count: number;
    last_used_at?: string;
  }>;
  recent_usage: Array<{
    id: number;
    name: string;
    last_used_at?: string;
    usage_count: number;
  }>;
} 

// Telegram Notifications
export interface TelegramBot {
  id: number;
  name: string;
  bot_token: string;
  chat_id: string;
  is_active: boolean;
  notification_types: string[];
  description?: string;
  created_at: string;
  updated_at: string;
  created_by: number;
  creator_username?: string;
  last_test_message_at?: string;
  test_message_status?: 'success' | 'failed' | null;
}

export interface TelegramBotCreate {
  name: string;
  bot_token: string;
  chat_id: string;
  notification_types: string[];
  description?: string;
}

export interface TelegramBotUpdate {
  name?: string;
  bot_token?: string;
  chat_id?: string;
  notification_types?: string[];
  description?: string;
  is_active?: boolean;
}

export interface TelegramBotStats {
  total_bots: number;
  active_bots: number;
  inactive_bots: number;
  total_notifications_sent: number;
  bots_by_type: Record<string, number>;
  most_active_bots: Array<{
    id: number;
    name: string;
    notifications_sent: number;
    last_message_at?: string;
  }>;
  recent_messages: Array<{
    id: number;
    bot_name: string;
    message_type: string;
    sent_at: string;
    status: 'success' | 'failed';
  }>;
}

export interface NotificationType {
  id: string;
  name: string;
  description: string;
  category: string;
  is_active: boolean;
}

export interface SendNotificationRequest {
  notification_type: string;
  message: string;
  title?: string;
  priority?: 'low' | 'medium' | 'high';
  data?: Record<string, any>;
}

export interface SendNotificationResponse {
  success: boolean;
  sent_to: number;
  failed: number;
  details: Array<{
    bot_id: number;
    bot_name: string;
    status: 'success' | 'failed';
    error?: string;
  }>;
}

// Предопределенные типы уведомлений
export const NOTIFICATION_TYPES: NotificationType[] = [
  {
    id: 'low_stock',
    name: 'Низкий остаток игрушек',
    description: 'Уведомление о низком остатке игрушек в автомате',
    category: 'inventory',
    is_active: true
  },
  {
    id: 'payment_due_phone',
    name: 'День оплаты телефона',
    description: 'Наступил день оплаты по телефону',
    category: 'payments',
    is_active: true
  },
  {
    id: 'payment_due_rent',
    name: 'День оплаты аренды',
    description: 'Наступил день оплаты по аренде',
    category: 'payments',
    is_active: true
  },
  {
    id: 'machine_error',
    name: 'Ошибка автомата',
    description: 'Обнаружена ошибка в работе автомата',
    category: 'technical',
    is_active: true
  },
  {
    id: 'daily_report',
    name: 'Ежедневный отчет',
    description: 'Ежедневный отчет по выручке и остаткам',
    category: 'reports',
    is_active: true
  },
  {
    id: 'weekly_report',
    name: 'Еженедельный отчет',
    description: 'Еженедельный отчет по выручке и остаткам',
    category: 'reports',
    is_active: true
  },
  {
    id: 'monthly_report',
    name: 'Ежемесячный отчет',
    description: 'Ежемесячный отчет по выручке и остаткам',
    category: 'reports',
    is_active: true
  },
  {
    id: 'custom',
    name: 'Пользовательское сообщение',
    description: 'Отправка пользовательского сообщения',
    category: 'custom',
    is_active: true
  }
];

// Типы для мониторинга
export interface Monitoring {
  id: number;
  date: string;
  coins: number;
  toys: number;
  machine_id: number;
  machine?: Machine;
}