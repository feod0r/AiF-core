import React, { useState, useEffect, useCallback } from 'react';
import { 
  ProTable, 
  ProColumns 
} from '@ant-design/pro-components';
import { 
  Tabs, 
  Card, 
  Statistic, 
  Row, 
  Col, 
  message, 
  Button, 
  Space, 
  DatePicker, 
  Tag, 
  Modal, 
  Progress,
  List,
  Drawer,
  Typography,
  Select
} from 'antd';
import { 
  DownloadOutlined, 
  ReloadOutlined, 
  PlusOutlined,
  EditOutlined,
  DeleteOutlined
} from '@ant-design/icons';
import { reportsApi, machinesApi } from '../services/api';
import moment from 'moment';

const { TabPane } = Tabs;
const { Title } = Typography;

interface ReportData {
  id: number;
  report_date: string;
  machine_id: number;
  revenue: number;
  toy_consumption: number;
  plays_per_toy: number;
  profit: number;
  days_count: number;
  rent_cost: number;
  machine?: { id: number; name: string };
}

interface AggregateReportData {
  period: string;
  total_revenue: number;
  total_toys_sold: number;
  total_profit: number;
  total_coins_earned: number;
  total_rent_cost: number;
  records_count: number;
}

interface SummaryData {
  totalRevenue: number;
  totalProfit: number;
  totalToys: number;
  totalRent: number;
  avgPercent: number;
}

interface PaginationState {
  current: number;
  pageSize: number;
  total: number;
}

interface Machine {
  id: number;
  name: string;
}

// Переиспользуемые компоненты
const SummaryCards: React.FC<{ summary: SummaryData; isMobile: boolean }> = ({ summary, isMobile }) => (
  <Row gutter={isMobile ? 8 : 16} style={{ marginBottom: 16 }}>
    <Col span={isMobile ? 12 : 6}>
      <Card size={isMobile ? 'small' : 'default'}>
        <Statistic
          title={isMobile ? "Доход" : "Общий доход"}
          value={summary.totalRevenue}
          precision={2}
          suffix="₽"
          valueStyle={{ color: '#3f8600', fontSize: isMobile ? 16 : undefined }}
        />
      </Card>
    </Col>
    <Col span={isMobile ? 12 : 6}>
      <Card size={isMobile ? 'small' : 'default'}>
        <Statistic
          title={isMobile ? "Прибыль" : "Общая прибыль"}
          value={summary.totalProfit}
          precision={2}
          suffix="₽"
          valueStyle={{ 
            color: summary.totalProfit >= 0 ? '#3f8600' : '#cf1322',
            fontSize: isMobile ? 16 : undefined
          }}
        />
      </Card>
    </Col>
    <Col span={isMobile ? 12 : 6}>
      <Card size={isMobile ? 'small' : 'default'}>
        <Statistic
          title={isMobile ? "Игрушки" : "Расход игрушек"}
          value={summary.totalToys}
          suffix="шт"
          valueStyle={{ fontSize: isMobile ? 16 : undefined }}
        />
      </Card>
    </Col>
    <Col span={isMobile ? 12 : 6}>
      <Card size={isMobile ? 'small' : 'default'}>
        <Statistic
          title={isMobile ? "Аренда" : "Общая аренда"}
          value={summary.totalRent}
          precision={2}
          suffix="₽"
          valueStyle={{ color: '#1890ff', fontSize: isMobile ? 16 : undefined }}
        />
      </Card>
    </Col>
    <Col span={isMobile ? 12 : 6}>
      <Card size={isMobile ? 'small' : 'default'}>
        <Statistic
          title={isMobile ? "Рентабельность" : "Средняя рентабельность"}
          value={summary.avgPercent * 100}
          precision={1}
          suffix="%"
          valueStyle={{ 
            color: summary.avgPercent >= 0 ? '#3f8600' : '#cf1322',
            fontSize: isMobile ? 16 : undefined
          }}
        />
      </Card>
    </Col>
  </Row>
);

const FilterControls: React.FC<{
  pickerDate: moment.Moment | null;
  setPickerDate: (date: moment.Moment | null) => void;
  filterDate: string | null;
  selectedMachineId: number | null;
  setSelectedMachineId: (id: number | null) => void;
  machines: Machine[];
  applyFilter: () => void;
  clearFilter: () => void;
  setBulkModalOpen: (open: boolean) => void;
  setComputeModalOpen: (open: boolean) => void;
  handleExport: () => void;
  loading: boolean;
  isMobile: boolean;
}> = ({ 
  pickerDate, 
  setPickerDate, 
  filterDate, 
  selectedMachineId,
  setSelectedMachineId,
  machines,
  applyFilter, 
  clearFilter, 
  setBulkModalOpen, 
  setComputeModalOpen,
  handleExport, 
  loading, 
  isMobile 
}) => (
  <div style={{ marginBottom: 16 }}>
    <Space size={isMobile ? 'small' : 'middle'} wrap>
      <DatePicker 
        value={pickerDate}
        onChange={(d) => setPickerDate(d)}
        placeholder="Фильтр по дате"
        allowClear
        style={isMobile ? { width: '100%' } : {}}
      />
      <Select
        value={selectedMachineId}
        onChange={setSelectedMachineId}
        placeholder="Фильтр по автомату"
        allowClear
        style={isMobile ? { width: '100%' } : { width: 200 }}
        options={machines.map(machine => ({
          value: machine.id,
          label: machine.name
        }))}
      />
      <Button 
        onClick={applyFilter} 
        disabled={pickerDate ? filterDate === pickerDate.format('YYYY-MM-DD') : filterDate === null}
        size={isMobile ? 'small' : 'middle'}
      >
        {isMobile ? 'Применить' : 'Применить фильтр'}
      </Button>
      {(filterDate !== null || selectedMachineId !== null) && (
        <Button 
          onClick={clearFilter}
          size={isMobile ? 'small' : 'middle'}
        >
          Сбросить
        </Button>
      )}
      <Button 
        icon={<PlusOutlined />} 
        onClick={() => setComputeModalOpen(true)}
        loading={loading}
        size={isMobile ? 'small' : 'middle'}
      >
        {isMobile ? 'Создать' : 'Создать отчет'}
      </Button>
      <Button 
        icon={<PlusOutlined />} 
        onClick={() => setBulkModalOpen(true)}
        loading={loading}
        size={isMobile ? 'small' : 'middle'}
      >
        {isMobile ? 'За период' : 'Создать за период'}
      </Button>
      <Button 
        icon={<DownloadOutlined />} 
        onClick={handleExport}
        size={isMobile ? 'small' : 'middle'}
      >
        {isMobile ? 'Экспорт' : 'Экспорт'}
      </Button>
    </Space>
    <div style={{ marginTop: 8 }}>
      <Space wrap>
        {filterDate && (
          <Tag color="blue">Фильтр по дате: {moment(filterDate).format('DD.MM.YYYY')}</Tag>
        )}
        {selectedMachineId && (
          <Tag color="green">Фильтр по автомату: {machines.find(m => m.id === selectedMachineId)?.name}</Tag>
        )}
        {!filterDate && !selectedMachineId && (
          <Tag>Отображаются все отчеты</Tag>
        )}
      </Space>
    </div>
  </div>
);

const ViewModeToggle: React.FC<{
  viewMode: 'detailed' | 'aggregate';
  onViewModeChange: (mode: 'detailed' | 'aggregate') => void;
  isMobile: boolean;
}> = ({ viewMode, onViewModeChange, isMobile }) => (
  <div style={{ marginBottom: isMobile ? 12 : 16 }}>
    <Space size={isMobile ? 'small' : 'middle'}>
      <Button 
        type={viewMode === 'detailed' ? 'primary' : 'default'}
        size={isMobile ? 'small' : 'middle'}
        onClick={() => onViewModeChange('detailed')}
      >
        По автоматам
      </Button>
      <Button 
        type={viewMode === 'aggregate' ? 'primary' : 'default'}
        size={isMobile ? 'small' : 'middle'}
        onClick={() => onViewModeChange('aggregate')}
      >
        Сводно
      </Button>
    </Space>
  </div>
);

const PeriodButtons: React.FC<{
  viewMode: 'detailed' | 'aggregate';
  activeTab: string;
  onPeriodChange: (period: string) => void;
  isMobile: boolean;
}> = ({ viewMode, activeTab, onPeriodChange, isMobile }) => {
  const periods = [
    { key: 'daily', label: 'Дни' },
    { key: 'weekly', label: 'Недели' },
    { key: 'monthly', label: 'Месяцы' },
    { key: 'quarterly', label: 'Кварталы' },
    { key: 'halfyear', label: 'Полугодия' },
    { key: 'yearly', label: 'Годы' }
  ];

  const getTabKey = (period: string) => viewMode === 'detailed' ? `detailed_${period}` : period;

  return (
    <Space size="small" wrap style={{ marginBottom: 16 }}>
      {periods.map(({ key, label }) => (
        <Button 
          key={key}
          type={activeTab === getTabKey(key) ? 'primary' : 'default'}
          size="small"
          onClick={() => onPeriodChange(getTabKey(key))}
        >
          {label}
        </Button>
      ))}
    </Space>
  );
};

const ReportsTable: React.FC<{
  data: ReportData[] | AggregateReportData[];
  columns: ProColumns<any>[];
  loading: boolean;
  pagination: PaginationState;
  onTableChange: (pagination: any) => void;
  isMobile: boolean;
}> = ({ data, columns, loading, pagination, onTableChange, isMobile }) => (
  <ProTable<any>
    columns={columns}
    dataSource={data}
    loading={loading}
    rowKey="id"
    search={false}
    pagination={{
      current: pagination.current,
      pageSize: pagination.pageSize,
      total: pagination.total,
      showSizeChanger: true,
      showQuickJumper: true,
      pageSizeOptions: ['100', '200', '500', '800', '1000'],
      showTotal: (total, range) => `${range[0]}-${range[1]} из ${total} записей`,
    }}
    onChange={onTableChange}
    scroll={{ x: 1500 }}
    size="small"
  />
);

const MobileReportsList: React.FC<{
  data: any[];
  loading: boolean;
  pagination: PaginationState;
  onPaginationChange: (page: number, pageSize: number) => void;
  onItemClick: (item: any) => void;
  isDetailed: boolean;
  aggregationPeriod: string;
}> = ({ data, loading, pagination, onPaginationChange, onItemClick, isDetailed, aggregationPeriod }) => {
  const renderDetailedItem = (report: ReportData) => (
    <List.Item
      style={{ padding: '16px 0', borderBottom: '1px solid #f0f0f0' }}
    >
      <div style={{ width: '100%' }}>
        <div style={{ marginBottom: 12, cursor: 'pointer' }}
             onClick={() => onItemClick(report)}>
          <span style={{ 
            fontSize: 18, color: '#1890ff', fontWeight: 'bold', 
            display: 'block', width: '100%', overflow: 'hidden', 
            textOverflow: 'ellipsis', whiteSpace: 'nowrap' 
          }}>
            {report.machine ? report.machine.name : `Машина ${report.machine_id}`}
          </span>
        </div>
        <div style={{ marginBottom: 12 }}>
          <div style={{ marginBottom: 8 }}>
            <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Дата:</span>
            <span style={{ fontSize: 14, marginLeft: 8 }}>
              {report.report_date ? moment(report.report_date).format('DD.MM.YYYY') : '-'}
            </span>
          </div>
          {report.revenue && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Доход:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{Number(report.revenue).toFixed(2)} ₽</span>
            </div>
          )}
          {report.profit && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Прибыль:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{Number(report.profit).toFixed(2)} ₽</span>
            </div>
          )}
          {report.plays_per_toy && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Игр/игрушка:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{Number(report.plays_per_toy).toFixed(2)}</span>
            </div>
          )}
          {report.days_count && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Дней:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{report.days_count}</span>
            </div>
          )}
          {report.toy_consumption && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Расход игрушек:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{report.toy_consumption} шт.</span>
            </div>
          )}
        </div>
      </div>
    </List.Item>
  );

  const renderAggregateItem = (report: AggregateReportData) => (
    <List.Item
      style={{ padding: '16px 0', borderBottom: '1px solid #f0f0f0' }}
    >
      <div style={{ width: '100%' }}>
        <div style={{ marginBottom: 12, cursor: 'pointer' }}
             onClick={() => onItemClick(report)}>
          <span style={{ 
            fontSize: 18, color: '#1890ff', fontWeight: 'bold', 
            display: 'block', width: '100%', overflow: 'hidden', 
            textOverflow: 'ellipsis', whiteSpace: 'nowrap' 
          }}>
            {report.period}
          </span>
        </div>
        <div style={{ marginBottom: 12 }}>
          {report.total_revenue && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Доход:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{Number(report.total_revenue).toFixed(2)} ₽</span>
            </div>
          )}
          {report.total_profit && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Прибыль:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{Number(report.total_profit).toFixed(2)} ₽</span>
            </div>
          )}
          {report.total_toys_sold && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Игрушек продано:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{Number(report.total_toys_sold).toFixed(0)} шт.</span>
            </div>
          )}
          {report.total_coins_earned && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Монет заработано:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{Number(report.total_coins_earned).toFixed(0)} шт.</span>
            </div>
          )}
          {report.records_count && (
            <div style={{ marginBottom: 8 }}>
              <span style={{ fontSize: 14, fontWeight: 'bold', color: '#666' }}>Записей:</span>
              <span style={{ fontSize: 14, marginLeft: 8 }}>{report.records_count}</span>
            </div>
          )}
        </div>
      </div>
    </List.Item>
  );

  return (
    <Card title={isDetailed 
      ? `Детальные отчеты по автоматам ${aggregationPeriod !== 'daily' ? `(${aggregationPeriod})` : ''}`
      : `Сводные отчеты ${aggregationPeriod === 'daily' ? 'по дням' : aggregationPeriod === 'weekly' ? 'по неделям' : aggregationPeriod === 'monthly' ? 'по месяцам' : aggregationPeriod === 'quarterly' ? 'по кварталам' : aggregationPeriod === 'halfyear' ? 'по полугодиям' : 'по годам'}`
    }>
      <List
        dataSource={data}
        loading={loading}
        renderItem={(item: any) => isDetailed ? renderDetailedItem(item) : renderAggregateItem(item)}
        pagination={{
          current: pagination.current,
          pageSize: pagination.pageSize,
          total: pagination.total,
          showSizeChanger: false,
          showQuickJumper: false,
          showTotal: (total, range) => `${range[0]}-${range[1]} из ${total}`,
          size: 'small',
          simple: true,
          onChange: onPaginationChange
        }}
      />
    </Card>
  );
};

const ReportsPage: React.FC = () => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<ReportData[]>([]);
  const [aggregateData, setAggregateData] = useState<AggregateReportData[]>([]);
  const [activeTab, setActiveTab] = useState<string>('detailed_daily');
  const [aggregationPeriod, setAggregationPeriod] = useState<'daily' | 'weekly' | 'monthly' | 'quarterly' | 'halfyear' | 'yearly'>('daily');
  const [viewMode, setViewMode] = useState<'detailed' | 'aggregate'>('detailed');
  const [filterDate, setFilterDate] = useState<string | null>(null);
  const [pickerDate, setPickerDate] = useState<moment.Moment | null>(null);
  const [selectedMachineId, setSelectedMachineId] = useState<number | null>(null);
  const [machines, setMachines] = useState<Machine[]>([]);
  const [summary, setSummary] = useState<SummaryData>({
    totalRevenue: 0,
    totalProfit: 0,
    totalToys: 0,
    totalRent: 0,
    avgPercent: 0
  });
  const [computeModalOpen, setComputeModalOpen] = useState(false);
  const [computeDate, setComputeDate] = useState<moment.Moment | null>(moment());
  const [bulkModalOpen, setBulkModalOpen] = useState(false);
  const [bulkRange, setBulkRange] = useState<[any, any]>([null, null]);
  const [bulkProgress, setBulkProgress] = useState<{ current: number; total: number }>({ current: 0, total: 0 });
  const [isMobile, setIsMobile] = useState(false);
  const [detailDrawerVisible, setDetailDrawerVisible] = useState(false);
  const [selectedReport, setSelectedReport] = useState<ReportData | AggregateReportData | null>(null);
  const [pagination, setPagination] = useState<PaginationState>({
    current: 1,
    pageSize: 100,
    total: 0
  });
  const [mobilePagination, setMobilePagination] = useState<PaginationState>({
    current: 1,
    pageSize: 20,
    total: 0
  });

  // Определение мобильного устройства
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    checkMobile();
    window.addEventListener('resize', checkMobile);
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Загрузка автоматов
  const fetchMachines = useCallback(async () => {
    try {
      const response = await machinesApi.getList();
      setMachines(response.data || response);
    } catch (error) {
      console.error('Ошибка при загрузке автоматов:', error);
      message.error('Ошибка при загрузке списка автоматов');
    }
  }, []);

  // Загрузка данных
  const updatePagination = useCallback((total: number) => {
    setPagination(prev => ({ ...prev, current: 1, total }));
    if (isMobile) {
      setMobilePagination(prev => ({ ...prev, current: 1, total }));
    }
  }, [isMobile]);

  const fetchDetailedReports = useCallback(async () => {
    setLoading(true);
    try {
      const response = await reportsApi.detailedByPeriod({
        period: aggregationPeriod,
        start_date: filterDate ?? undefined,
        end_date: filterDate ?? undefined,
        machine_id: selectedMachineId ?? undefined
      });
      
      const rows = Array.isArray(response) ? response : [];
      setData(rows);
      
      const totalRevenue = rows.reduce((sum: number, item: ReportData) => sum + Number(item.revenue ?? 0), 0);
      const totalProfit = rows.reduce((sum: number, item: ReportData) => sum + Number(item.profit ?? 0), 0);
      const totalToys = rows.reduce((sum: number, item: ReportData) => sum + (item.toy_consumption || 0), 0);
      const avgPercent = totalRevenue > 0 ? (totalProfit / totalRevenue) : 0;
      
      setSummary({
        totalRevenue,
        totalProfit,
        totalToys,
        totalRent: 0,
        avgPercent
      });
      
      updatePagination(rows.length);
    } catch (error) {
      console.error('Ошибка при загрузке детальных отчетов:', error);
      message.error('Ошибка при загрузке детальных отчетов');
      setData([]);
    } finally {
      setLoading(false);
    }
  }, [filterDate, aggregationPeriod, selectedMachineId, updatePagination]);

  const fetchAggregateReports = useCallback(async () => {
    setLoading(true);
    try {
      const response = await reportsApi.aggregate({
        period: aggregationPeriod,
        start_date: filterDate ?? undefined,
        end_date: filterDate ?? undefined
      });
      
      const rows = (response && (response as any).data && Array.isArray((response as any).data)) ? (response as any).data : [];
      setAggregateData(rows);
      
      const totalRevenue = rows.reduce((sum: number, item: AggregateReportData) => sum + Number(item.total_revenue ?? 0), 0);
      const totalProfit = rows.reduce((sum: number, item: AggregateReportData) => sum + Number(item.total_profit ?? 0), 0);
      const totalToys = rows.reduce((sum: number, item: AggregateReportData) => sum + Number(item.total_toys_sold ?? 0), 0);
      const totalRent = rows.reduce((sum: number, item: AggregateReportData) => sum + Number(item.total_rent_cost ?? 0), 0);
      const avgPercent = totalRevenue > 0 ? (totalProfit / totalRevenue) : 0;
      
      setSummary({
        totalRevenue,
        totalProfit,
        totalToys,
        totalRent,
        avgPercent
      });
      
      updatePagination(rows.length);
    } catch (error) {
      console.error('Ошибка при загрузке агрегированных отчетов:', error);
      message.error('Ошибка при загрузке агрегированных отчетов');
      setAggregateData([]);
    } finally {
      setLoading(false);
    }
  }, [aggregationPeriod, filterDate, updatePagination]);

  const fetchData = useCallback(async () => {
    if (viewMode === 'detailed') {
      await fetchDetailedReports();
    } else {
      await fetchAggregateReports();
    }
  }, [viewMode, fetchDetailedReports, fetchAggregateReports]);

  // Загружаем автоматы при монтировании компонента
  useEffect(() => {
    fetchMachines();
  }, [fetchMachines]);

  // Обработчики
  const handleViewModeChange = useCallback((mode: 'detailed' | 'aggregate') => {
    setViewMode(mode);
    if (mode === 'detailed') {
      setActiveTab('detailed_daily');
      setAggregationPeriod('daily');
    } else {
      setActiveTab('daily');
      setAggregationPeriod('daily');
    }
  }, []);

  const handlePeriodChange = useCallback((tabKey: string) => {
    setActiveTab(tabKey);
    if (tabKey.startsWith('detailed_')) {
      const period = tabKey.replace('detailed_', '') as any;
      setAggregationPeriod(period);
    } else {
      setAggregationPeriod(tabKey as any);
    }
  }, []);

  const handleRefresh = useCallback(() => {
    fetchData();
  }, [fetchData]);

  const handleTableChange = useCallback((pagination: any) => {
    setPagination(prev => ({
      ...prev,
      current: pagination.current,
      pageSize: pagination.pageSize
    }));
  }, []);

  const handleMobilePaginationChange = useCallback((page: number, pageSize: number) => {
    setMobilePagination(prev => ({
      ...prev,
      current: page,
      pageSize: pageSize || prev.pageSize
    }));
  }, []);

  const handleCompute = useCallback(async () => {
    setLoading(true);
    try {
      if (!computeDate) {
        message.warning('Выберите дату для расчета отчета');
        return;
      }
      const dateISO = computeDate.format('YYYY-MM-DD');
      console.log('Computing report for date:', dateISO);
      const result = await reportsApi.computeByDate(dateISO);
      console.log('Compute result:', result);
      await fetchData();
      message.success(`Отчет рассчитан. Обработано записей: ${result.processed}`);
      setComputeModalOpen(false);
    } catch (e: any) {
      console.error('Error computing report:', e);
      const errorMessage = e.response?.data?.detail || e.message || 'Ошибка при расчете отчета';
      message.error(`Ошибка при расчете отчета: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  }, [computeDate, fetchData]);

  const applyFilter = useCallback(() => {
    setFilterDate(pickerDate ? pickerDate.format('YYYY-MM-DD') : null);
  }, [pickerDate]);

  const clearFilter = useCallback(() => {
    setPickerDate(null);
    setFilterDate(null);
    setSelectedMachineId(null);
  }, []);

  const handleExport = useCallback(() => {
    message.info('Экспорт будет реализован позже');
  }, []);

  const handleItemClick = useCallback((item: ReportData | AggregateReportData) => {
    setSelectedReport(item);
    setDetailDrawerVisible(true);
  }, []);

  // Эффекты
  useEffect(() => {
    updatePagination(0);
    fetchData();
  }, [filterDate, selectedMachineId, viewMode, aggregationPeriod, fetchData, updatePagination]);

  // Колонки для таблиц
  const detailedColumns: ProColumns<ReportData>[] = [
    {
      title: 'Автомат',
      dataIndex: ['machine', 'name'],
      key: 'machine_name',
      width: 150,
      fixed: 'left',
    },
    {
      title: 'Дата',
      dataIndex: 'report_date',
      key: 'report_date',
      width: 120,
      render: (_, record) => {
        const date = record.report_date;
        return date ? moment(date).format('DD.MM.YYYY') : '-';
      },
    },
    {
      title: 'Доход (₽)',
      dataIndex: 'revenue',
      key: 'revenue',
      width: 120,
      render: (_, record) => `${Number(record.revenue ?? 0).toFixed(2)} ₽`,
      sorter: true,
    },
    {
      title: 'Прибыль (₽)',
      dataIndex: 'profit',
      key: 'profit',
      width: 120,
      render: (_, record) => `${Number(record.profit ?? 0).toFixed(2)} ₽`,
      sorter: true,
    },
    {
      title: 'Игр/игрушка',
      dataIndex: 'plays_per_toy',
      key: 'plays_per_toy',
      width: 120,
      render: (_, record) => Number(record.plays_per_toy ?? 0).toFixed(2),
    },
    {
      title: 'Дней',
      dataIndex: 'days_count',
      key: 'days_count',
      width: 80,
    },
    {
      title: 'Расход игрушек',
      dataIndex: 'toy_consumption',
      key: 'toy_consumption',
      width: 120,
      render: (_, record) => record.toy_consumption || '-',
    },
    {
      title: 'Аренда (₽)',
      dataIndex: 'rent_cost',
      key: 'rent_cost',
      width: 100,
      render: (_, record) => `${Number(record.rent_cost ?? 0).toFixed(2)} ₽`,
    },
  ];

  const aggregateColumns: ProColumns<AggregateReportData>[] = [
    {
      title: 'Период',
      dataIndex: 'period',
      key: 'period',
      width: 150,
      fixed: 'left',
    },
    {
      title: 'Доход (₽)',
      dataIndex: 'total_revenue',
      key: 'total_revenue',
      width: 120,
      render: (_, record) => `${Number(record.total_revenue ?? 0).toFixed(2)} ₽`,
      sorter: true,
    },
    {
      title: 'Прибыль (₽)',
      dataIndex: 'total_profit',
      key: 'total_profit',
      width: 120,
      render: (_, record) => `${Number(record.total_profit ?? 0).toFixed(2)} ₽`,
      sorter: true,
    },
    {
      title: 'Игрушек продано',
      dataIndex: 'total_toys_sold',
      key: 'total_toys_sold',
      width: 120,
      render: (_, record) => Number(record.total_toys_sold ?? 0).toFixed(0),
    },
    {
      title: 'Монет заработано',
      dataIndex: 'total_coins_earned',
      key: 'total_coins_earned',
      width: 120,
      render: (_, record) => Number(record.total_coins_earned ?? 0).toFixed(0),
    },
    {
      title: 'Аренда (₽)',
      dataIndex: 'total_rent_cost',
      key: 'total_rent_cost',
      width: 100,
      render: (_, record) => `${Number(record.total_rent_cost ?? 0).toFixed(2)} ₽`,
    },
    {
      title: 'Записей',
      dataIndex: 'records_count',
      key: 'records_count',
      width: 80,
    },
  ];

  // Создание вкладок для десктопной версии
  const createDetailedTabs = () => {
    const periods = [
      { key: 'daily', label: 'По дням' },
      { key: 'weekly', label: 'По неделям' },
      { key: 'monthly', label: 'По месяцам' },
      { key: 'quarterly', label: 'По кварталам' },
      { key: 'halfyear', label: 'По полугодиям' },
      { key: 'yearly', label: 'По годам' }
    ];

    return periods.map(({ key, label }) => (
      <TabPane tab={label} key={`detailed_${key}`}>
        <ReportsTable
          data={data}
          columns={detailedColumns}
          loading={loading}
          pagination={pagination}
          onTableChange={handleTableChange}
          isMobile={false}
        />
      </TabPane>
    ));
  };

  const createAggregateTabs = () => {
    const periods = [
      { key: 'daily', label: 'По дням' },
      { key: 'weekly', label: 'По неделям' },
      { key: 'monthly', label: 'По месяцам' },
      { key: 'quarterly', label: 'По кварталам' },
      { key: 'halfyear', label: 'По полугодиям' },
      { key: 'yearly', label: 'По годам' }
    ];

    return periods.map(({ key, label }) => (
      <TabPane tab={label} key={key}>
        <ReportsTable
          data={aggregateData}
          columns={aggregateColumns}
          loading={loading}
          pagination={pagination}
          onTableChange={handleTableChange}
          isMobile={false}
        />
      </TabPane>
    ));
  };

  return (
    <div style={{ padding: isMobile ? 8 : 24 }}>
      <div style={{ marginBottom: 16 }}>
        <Space size={isMobile ? 'small' : 'middle'} wrap>
          <Title level={isMobile ? 4 : 2} style={{ margin: 0 }}>
            Отчеты
          </Title>
          <Button 
            icon={<ReloadOutlined />} 
            onClick={handleRefresh}
            loading={loading}
            size={isMobile ? 'small' : 'middle'}
          >
            {isMobile ? 'Обновить' : 'Обновить данные'}
          </Button>
        </Space>
      </div>

      <FilterControls
        pickerDate={pickerDate}
        setPickerDate={setPickerDate}
        filterDate={filterDate}
        selectedMachineId={selectedMachineId}
        setSelectedMachineId={setSelectedMachineId}
        machines={machines}
        applyFilter={applyFilter}
        clearFilter={clearFilter}
        setBulkModalOpen={setBulkModalOpen}
        setComputeModalOpen={setComputeModalOpen}
        handleExport={handleExport}
        loading={loading}
        isMobile={isMobile}
      />

      <SummaryCards summary={summary} isMobile={isMobile} />

      <ViewModeToggle
        viewMode={viewMode}
        onViewModeChange={handleViewModeChange}
        isMobile={isMobile}
      />

      {isMobile ? (
        <PeriodButtons
          viewMode={viewMode}
          activeTab={activeTab}
          onPeriodChange={handlePeriodChange}
          isMobile={isMobile}
        />
      ) : (
        <Tabs 
          activeKey={activeTab} 
          onChange={handlePeriodChange}
          style={{ marginBottom: 16 }}
        >
          {viewMode === 'detailed' ? createDetailedTabs() : createAggregateTabs()}
        </Tabs>
      )}

      {/* Мобильная версия отображения данных */}
      {isMobile && (
        <MobileReportsList
          data={viewMode === 'detailed' ? data : aggregateData}
          loading={loading}
          pagination={mobilePagination}
          onPaginationChange={handleMobilePaginationChange}
          onItemClick={handleItemClick}
          isDetailed={viewMode === 'detailed'}
          aggregationPeriod={aggregationPeriod}
        />
      )}

      {/* Модальные окна */}
      <Modal
        title="Добавить отчет вручную"
        open={computeModalOpen}
        onOk={handleCompute}
        onCancel={() => setComputeModalOpen(false)}
        okButtonProps={{ disabled: !computeDate }}
        confirmLoading={loading}
      >
        <DatePicker
          value={computeDate}
          onChange={(d) => setComputeDate(d)}
          placeholder="Выберите дату"
          style={{ width: '100%' }}
        />
      </Modal>

      <Modal
        title="Создать отчеты за период"
        open={bulkModalOpen}
        onOk={async () => {
          console.log('Bulk modal OK clicked, bulkRange:', bulkRange);
          if (!bulkRange[0] || !bulkRange[1]) {
            message.warning('Выберите диапазон дат');
            return;
          }
          console.log('Starting bulk processing...');
          setLoading(true);
          try {
            // Правильное преобразование из Dayjs в Moment
            const start = moment(bulkRange[0].toDate());
            const end = moment(bulkRange[1].toDate());
            console.log('Processing from', start.format('YYYY-MM-DD'), 'to', end.format('YYYY-MM-DD'));
            const current = start.clone();
            let processed = 0;
            const total = end.diff(start, 'days') + 1;
            console.log('Total days to process:', total);
            setBulkProgress({ current: 0, total });
            
            while (current.isSameOrBefore(end)) {
              try {
                console.log('Processing date:', current.format('YYYY-MM-DD'));
                await reportsApi.computeByDate(current.format('YYYY-MM-DD'));
                processed++;
                console.log('Successfully processed date:', current.format('YYYY-MM-DD'), 'Total processed:', processed);
                setBulkProgress({ current: processed, total });
              } catch (e) {
                console.error(`Ошибка при обработке даты ${current.format('YYYY-MM-DD')}:`, e);
              }
              current.add(1, 'day');
            }
            
            console.log('Bulk processing completed. Processed:', processed, 'Total:', total);
            message.success(`Обработано ${processed} из ${total} дней`);
            await fetchData();
          } catch (e) {
            console.error('Error in bulk processing:', e);
            message.error('Ошибка при создании отчетов за период');
          } finally {
            setLoading(false);
            setBulkProgress({ current: 0, total: 0 });
            setBulkModalOpen(false);
          }
        }}
        onCancel={() => setBulkModalOpen(false)}
        confirmLoading={loading}
      >
        <div style={{ marginBottom: 16 }}>
          <DatePicker.RangePicker
            value={bulkRange}
            onChange={(dates) => {
              console.log('Date range changed:', dates);
              setBulkRange(dates as [moment.Moment | null, moment.Moment | null]);
            }}
            style={{ width: '100%' }}
          />
        </div>
        {bulkProgress.total > 0 && (
          <Progress
            percent={Math.round((bulkProgress.current / bulkProgress.total) * 100)}
            status={bulkProgress.current === bulkProgress.total ? 'success' : 'active'}
            format={() => `${bulkProgress.current} / ${bulkProgress.total}`}
          />
        )}
      </Modal>

      <Drawer
        title={
          <div style={{ 
            display: 'flex', 
            alignItems: 'center', 
            gap: 8,
            minHeight: 'auto',
            padding: '8px 0'
          }}>
            <div style={{ 
              flex: 1,
              minWidth: 0,
              overflow: 'hidden'
            }}>
              <div style={{ 
                fontSize: 16, 
                fontWeight: 'bold',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {selectedReport && ('machine' in selectedReport 
                  ? (selectedReport.machine ? selectedReport.machine.name : `Машина ${selectedReport.machine_id}`)
                  : ('period' in selectedReport ? selectedReport.period : 'Отчет'))
                }
              </div>
              <div style={{ 
                fontSize: 12, 
                color: '#999',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                Отчеты
              </div>
            </div>
          </div>
        }
        placement="right"
        onClose={() => setDetailDrawerVisible(false)}
        open={detailDrawerVisible}
        width="100%"
        styles={{
          header: { 
            padding: '12px 16px',
            minHeight: 'auto',
            borderBottom: '1px solid #f0f0f0'
          },
          body: { 
            padding: '16px',
            paddingBottom: '80px'
          }
        }}
      >
        {selectedReport && (
          <div>
            {/* Основная информация */}
            <div style={{ marginBottom: 24 }}>
              <div style={{ marginBottom: 16 }}>
                <span style={{ fontSize: 14, fontWeight: 'bold', marginBottom: 8, display: 'block' }}>
                  Основная информация:
                </span>
                <div style={{ fontSize: 14, color: '#666' }}>
                  {('machine' in selectedReport) ? (
                    // Детальный отчет
                    <>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        🤖 Машина: {selectedReport.machine ? selectedReport.machine.name : `Машина ${selectedReport.machine_id}`}
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        📅 Дата: {selectedReport.report_date ? moment(selectedReport.report_date).format('DD.MM.YYYY') : '-'}
                      </div>
                      {selectedReport.revenue && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          💰 Доход: {Number(selectedReport.revenue).toFixed(2)} ₽
                        </div>
                      )}
                      {selectedReport.profit && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          💵 Прибыль: {Number(selectedReport.profit).toFixed(2)} ₽
                        </div>
                      )}
                      {selectedReport.plays_per_toy && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          🎮 Игр/игрушка: {Number(selectedReport.plays_per_toy).toFixed(2)}
                        </div>
                      )}
                      {selectedReport.days_count && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          📊 Дней: {selectedReport.days_count}
                        </div>
                      )}
                      {selectedReport.toy_consumption && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          🧸 Расход игрушек: {selectedReport.toy_consumption} шт.
                        </div>
                      )}
                      {selectedReport.rent_cost && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          🏠 Аренда: {Number(selectedReport.rent_cost).toFixed(2)} ₽
                        </div>
                      )}
                    </>
                  ) : (
                    // Агрегированный отчет
                    <>
                      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                        📅 Период: {('period' in selectedReport) ? selectedReport.period : '-'}
                      </div>
                      {('total_revenue' in selectedReport) && selectedReport.total_revenue && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          💰 Доход: {Number(selectedReport.total_revenue).toFixed(2)} ₽
                        </div>
                      )}
                      {('total_profit' in selectedReport) && selectedReport.total_profit && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          💵 Прибыль: {Number(selectedReport.total_profit).toFixed(2)} ₽
                        </div>
                      )}
                      {('total_toys_sold' in selectedReport) && selectedReport.total_toys_sold && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          🧸 Игрушек продано: {Number(selectedReport.total_toys_sold).toFixed(0)} шт.
                        </div>
                      )}
                      {('total_coins_earned' in selectedReport) && selectedReport.total_coins_earned && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          🪙 Монет заработано: {Number(selectedReport.total_coins_earned).toFixed(0)} шт.
                        </div>
                      )}
                      {('total_rent_cost' in selectedReport) && selectedReport.total_rent_cost && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          🏠 Аренда: {Number(selectedReport.total_rent_cost).toFixed(2)} ₽
                        </div>
                      )}
                      {('records_count' in selectedReport) && selectedReport.records_count && (
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                          📊 Записей: {selectedReport.records_count}
                        </div>
                      )}
                    </>
                  )}
                </div>
              </div>
            </div>

            {/* Действия */}
            <div style={{ 
              position: 'fixed', 
              bottom: 0, 
              left: 0, 
              right: 0, 
              background: 'white', 
              padding: '12px 16px',
              borderTop: '1px solid #f0f0f0',
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              zIndex: 1000,
              boxShadow: '0 -2px 8px rgba(0, 0, 0, 0.1)'
            }}>
              <Button 
                icon={<EditOutlined />} 
                onClick={() => {
                  setDetailDrawerVisible(false);
                  // TODO: Добавить логику редактирования
                  message.info('Функция редактирования будет добавлена позже');
                }}
                style={{ 
                  width: '100%',
                  height: '44px',
                  fontSize: '16px'
                }}
              >
                Изменить
              </Button>
              <Button 
                danger 
                icon={<DeleteOutlined />}
                onClick={() => {
                  setDetailDrawerVisible(false);
                  // TODO: Добавить логику удаления
                  message.info('Функция удаления будет добавлена позже');
                }}
                style={{ 
                  width: '100%',
                  height: '44px',
                  fontSize: '16px'
                }}
              >
                Удалить
              </Button>
            </div>
          </div>
        )}
      </Drawer>
    </div>
  );
};

export default ReportsPage; 