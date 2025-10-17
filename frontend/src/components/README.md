# GenericDataTable - Универсальный компонент таблицы

`GenericDataTable` - это универсальный компонент для создания CRUD таблиц с фильтрацией, пагинацией и мобильной адаптивностью. Он устраняет дублирование кода между различными страницами администрирования.

## Основные возможности

- ✅ **CRUD операции** - создание, чтение, обновление, удаление через API эндпоинты
- ✅ **Автоматическая фильтрация** - поддержка различных типов фильтров (select, input, date, dateRange)
- ✅ **Мобильная адаптивность** - автоматическое переключение между Table и List на мобильных устройствах
- ✅ **Пагинация** - настраиваемая пагинация с опциями размера страниц
- ✅ **Поиск** - глобальный поиск по всем полям
- ✅ **Экспорт данных** - кнопка экспорта (готова к реализации)
- ✅ **Массовые операции** - выделение множественных записей и применение операций
- ✅ **Кастомные действия** - дополнительные кнопки действий в строках
- ✅ **Типобезопасность** - полная типизация через TypeScript дженерики
- ✅ **Условная видимость** - поля формы могут быть скрыты/показаны в зависимости от других значений

## Быстрый старт

### Простая таблица (пример Counterparties)

```typescript
import GenericDataTable from '../components/GenericDataTable';
import { counterpartiesApi } from '../services/api';
import { Counterparty } from '../types';

const CounterpartiesPage: React.FC = () => {
  return (
    <GenericDataTable<Counterparty>
      title="Контрагенты"
      icon={<UserOutlined />}
      endpoints={{
        list: counterpartiesApi.getList,
        create: counterpartiesApi.create,
        update: counterpartiesApi.update,
        delete: counterpartiesApi.delete,
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
        // ... другие колонки
      ]}
      filters={[
        {
          key: 'is_active',
          label: 'Статус',
          type: 'select',
          options: [
            { label: 'Активен', value: true },
            { label: 'Неактивен', value: false },
          ],
        },
      ]}
      formConfig={{
        fields: [
          {
            name: 'name',
            label: 'Название',
            type: 'input',
            rules: [{ required: true, message: 'Введите название' }],
          },
          // ... другие поля
        ],
      }}
      searchable={true}
      exportable={true}
    />
  );
};
```

### Таблица со сложной логикой (пример Transactions)

```typescript
const TransactionsPage: React.FC = () => {
  // Кастомные действия в строках
  const rowActions = [
    {
      key: 'confirm',
      title: 'Утвердить',
      icon: <CheckCircleOutlined />,
      color: '#52c41a',
      visible: (record: Transaction) => !record.is_confirmed,
      onClick: async (record: Transaction) => {
        await transactionsApi.confirm(record.id);
        message.success('Операция подтверждена');
      },
    },
  ];

  // Кастомная обработка отправки формы
  const customEndpoints = {
    list: transactionsApi.getList,
    create: async (data: any) => {
      const processedData = await processTransactionData(data);
      return transactionsApi.create(processedData);
    },
    update: async (id: number, data: any) => {
      const processedData = await processTransactionData(data);
      return transactionsApi.update(id, processedData);
    },
    delete: transactionsApi.delete,
  };

  return (
    <GenericDataTable<Transaction>
      title="Операции"
      endpoints={customEndpoints}
      columns={transactionColumns}
      filters={transactionFilters}
      formConfig={{
        fields: [
          {
            name: 'to_account_id',
            label: 'Счет назначения',
            type: 'select',
            visible: (values) => values.type === 'transfer', // Условная видимость
            rules: [
              ({ getFieldValue }) => ({
                validator(_, value) {
                  if (getFieldValue('type') === 'transfer' && !value) {
                    return Promise.reject('Для перевода необходимо указать счет назначения');
                  }
                  return Promise.resolve();
                },
              }),
            ],
          },
        ],
      }}
      rowActions={rowActions}
      bulkActions={[
        {
          key: 'bulkConfirm',
          title: 'Утвердить',
          icon: <CheckOutlined />,
          onClick: async (selectedKeys, selectedRecords) => {
            await bulkConfirmTransactions(selectedKeys);
            message.success(`Утверждено ${selectedKeys.length} операций`);
          },
        },
      ]}
    />
  );
};
```

## API Reference

### Props

#### Основные свойства

| Prop | Type | Required | Description |
|------|------|----------|-------------|
| `title` | `string` | ✅ | Заголовок таблицы |
| `icon` | `React.ReactNode` | ❌ | Иконка рядом с заголовком |
| `endpoints` | `EndpointsConfig` | ✅ | Конфигурация API эндпоинтов |
| `columns` | `ColumnConfig[]` | ✅ | Конфигурация колонок таблицы |
| `formConfig` | `FormConfig` | ✅ | Конфигурация формы создания/редактирования |

#### EndpointsConfig

```typescript
interface EndpointsConfig {
  list: (params?: any) => Promise<T[]>;        // Получение списка
  create: (data: any) => Promise<T>;           // Создание записи
  update: (id: number, data: any) => Promise<T>; // Обновление записи
  delete: (id: number) => Promise<void>;       // Удаление записи
}
```

#### ColumnConfig

```typescript
interface ColumnConfig<T> {
  title: string;                              // Заголовок колонки
  dataIndex: string | string[];               // Путь к данным (поддерживает вложенные объекты)
  key: string;                                // Уникальный ключ
  render?: (value: any, record: T) => React.ReactNode; // Кастомный рендер
  width?: number;                             // Ширина колонки
  ellipsis?: boolean;                         // Обрезка длинного текста
  sorter?: boolean;                           // Включить сортировку
  filterable?: boolean;                       // Включить автофильтрацию
}
```

#### Типы полей формы

- `input` - обычное текстовое поле
- `textarea` - многострочное текстовое поле
- `select` - выпадающий список
- `number` - числовое поле
- `date` - поле даты с временем
- `switch` - переключатель вкл/выкл
- `password` - поле пароля

#### Типы фильтров

- `select` - выпадающий список
- `input` - текстовое поле
- `date` - поле даты
- `dateRange` - диапазон дат

### Дополнительные возможности

#### Фильтры с загрузкой данных из API

```typescript
filters: [
  {
    key: 'category_id',
    label: 'Категория',
    type: 'select',
    api: async () => {
      const categories = await categoriesApi.getList();
      return categories.map(cat => ({
        label: cat.name,
        value: cat.id,
      }));
    },
  },
]
```

#### Поля формы с зависимостями

```typescript
formConfig: {
  fields: [
    {
      name: 'country',
      label: 'Страна',
      type: 'select',
      options: countryOptions,
    },
    {
      name: 'city',
      label: 'Город',
      type: 'select',
      dependencies: ['country'], // Перерендер при изменении страны
      api: async () => {
        const country = form.getFieldValue('country');
        return await getCitiesByCountry(country);
      },
    },
  ],
}
```

#### Массовые операции

```typescript
bulkActions: [
  {
    key: 'activate',
    title: 'Активировать',
    icon: <CheckOutlined />,
    onClick: async (selectedKeys, selectedRecords) => {
      await bulkActivate(selectedKeys);
      message.success(`Активировано ${selectedKeys.length} записей`);
    },
  },
]
```

## Преимущества использования

1. **Сокращение кода на 70-80%** - вместо 1500+ строк кода остается ~200 строк конфигурации
2. **Единообразие UI/UX** - все таблицы выглядят и работают одинаково
3. **Легкость поддержки** - изменения в одном месте применяются ко всем таблицам
4. **Типобезопасность** - полная типизация предотвращает ошибки
5. **Быстрая разработка** - новые CRUD страницы создаются за минуты

## Когда НЕ использовать

- Сложная нестандартная бизнес-логика (лучше создать отдельный компонент)
- Уникальный дизайн, не подходящий под общий шаблон
- Сложные вычисляемые поля, требующие доступа к состоянию компонента
- Интеграция с внешними библиотеками графиков/карт

## Миграция существующих страниц

1. Определите структуру данных и API эндпоинты
2. Создайте конфигурацию колонок
3. Настройте фильтры и форму
4. Добавьте кастомные действия если нужно
5. Протестируйте все функции
6. Замените старый компонент на новый

Пример полной миграции смотрите в файлах:
- `src/pages/CounterpartiesGeneric.tsx` - простая таблица
- `src/pages/TransactionsGeneric.tsx` - сложная таблица с кастомной логикой








