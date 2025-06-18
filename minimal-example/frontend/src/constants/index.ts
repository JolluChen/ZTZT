// API接口地址
export const API_ENDPOINTS = {
  // 认证相关
  AUTH: {
    LOGIN: '/auth/login/',
    LOGOUT: '/auth/logout/',
    REGISTER: '/auth/register/',
    PROFILE: '/auth/profile/',
    CHANGE_PASSWORD: '/auth/change-password/',
  },
  
  // 数据中台
  DATA: {
    DATASETS: '/data/datasets/',
    UPLOAD: '/data/upload/',
    PREVIEW: '/data/preview/',
    STATS: '/data/stats/',
  },
  
  // 算法中台
  ALGORITHM: {
    EXPERIMENTS: '/algorithm/experiments/',
    ALGORITHMS: '/algorithm/algorithms/',
    RUN: '/algorithm/run/',
    RESULTS: '/algorithm/results/',
  },
  
  // 模型中台
  MODEL: {
    MODELS: '/model/models/',
    VERSIONS: '/model/versions/',
    DEPLOY: '/model/deploy/',
    METRICS: '/model/metrics/',
  },
  
  // 服务中台
  SERVICE: {
    APPLICATIONS: '/service/applications/',
    DEPLOY: '/service/deploy/',
    STATUS: '/service/status/',
    LOGS: '/service/logs/',
    // Dify 集成 API
    DIFY: {
      APPLICATIONS: '/service/dify/applications/',
      CONVERSATIONS: '/service/dify/conversations/',
      DATASETS: '/service/dify/datasets/',
      CHAT: '/service/dify/chat/',
    },
  },
};

// 状态常量
export const STATUS = {
  DATASET: {
    UPLOADING: 'uploading',
    PROCESSING: 'processing',
    READY: 'ready',
    ERROR: 'error',
  },
  EXPERIMENT: {
    CREATED: 'created',
    RUNNING: 'running',
    COMPLETED: 'completed',
    FAILED: 'failed',
  },
  MODEL: {
    TRAINING: 'training',
    READY: 'ready',
    DEPLOYED: 'deployed',
    ARCHIVED: 'archived',
  },
  APPLICATION: {
    CREATED: 'created',
    DEPLOYING: 'deploying',
    RUNNING: 'running',
    STOPPED: 'stopped',
    ERROR: 'error',
  },
};

// 状态标签配置
export const STATUS_LABELS = {
  [STATUS.DATASET.UPLOADING]: { text: '上传中', color: 'processing' },
  [STATUS.DATASET.PROCESSING]: { text: '处理中', color: 'processing' },
  [STATUS.DATASET.READY]: { text: '就绪', color: 'success' },
  [STATUS.DATASET.ERROR]: { text: '错误', color: 'error' },
  
  [STATUS.EXPERIMENT.CREATED]: { text: '已创建', color: 'default' },
  [STATUS.EXPERIMENT.RUNNING]: { text: '运行中', color: 'processing' },
  [STATUS.EXPERIMENT.COMPLETED]: { text: '已完成', color: 'success' },
  [STATUS.EXPERIMENT.FAILED]: { text: '失败', color: 'error' },
  
  [STATUS.MODEL.TRAINING]: { text: '训练中', color: 'processing' },
  [STATUS.MODEL.READY]: { text: '就绪', color: 'success' },
  [STATUS.MODEL.DEPLOYED]: { text: '已部署', color: 'success' },
  [STATUS.MODEL.ARCHIVED]: { text: '已归档', color: 'default' },
  
  [STATUS.APPLICATION.CREATED]: { text: '已创建', color: 'default' },
  [STATUS.APPLICATION.DEPLOYING]: { text: '部署中', color: 'processing' },
  [STATUS.APPLICATION.RUNNING]: { text: '运行中', color: 'success' },
  [STATUS.APPLICATION.STOPPED]: { text: '已停止', color: 'default' },
  [STATUS.APPLICATION.ERROR]: { text: '错误', color: 'error' },
};

// 算法类型
export const ALGORITHMS = [
  { value: 'linear_regression', label: '线性回归' },
  { value: 'logistic_regression', label: '逻辑回归' },
  { value: 'random_forest', label: '随机森林' },
  { value: 'svm', label: '支持向量机' },
  { value: 'neural_network', label: '神经网络' },
  { value: 'kmeans', label: 'K均值聚类' },
  { value: 'dbscan', label: 'DBSCAN聚类' },
];

// 文件类型配置
export const FILE_TYPES = {
  DATASET: ['csv', 'xlsx', 'json', 'txt'],
  MODEL: ['pkl', 'h5', 'onnx', 'pb'],
  IMAGE: ['jpg', 'jpeg', 'png', 'gif'],
  DOCUMENT: ['pdf', 'doc', 'docx'],
  ARCHIVE: ['zip', 'tar', 'gz'],
};

// 页面路由
export const ROUTES = {
  HOME: '/',
  LOGIN: '/auth/login',
  REGISTER: '/auth/register',
  DASHBOARD: '/dashboard',
  
  // 数据中台
  DATA_OVERVIEW: '/data',
  DATA_DATASETS: '/data/datasets',
  DATA_UPLOAD: '/data/upload',
  DATA_PREVIEW: '/data/preview',
  
  // 算法中台
  ALGORITHM_OVERVIEW: '/algorithm',
  ALGORITHM_EXPERIMENTS: '/algorithm/experiments',
  ALGORITHM_CREATE: '/algorithm/create',
  ALGORITHM_RESULTS: '/algorithm/results',
  
  // 模型中台
  MODEL_OVERVIEW: '/model',
  MODEL_MODELS: '/model/models',
  MODEL_VERSIONS: '/model/versions',
  MODEL_DEPLOY: '/model/deploy',
  
  // 服务中台
  SERVICE_OVERVIEW: '/service',
  SERVICE_APPLICATIONS: '/service/applications',
  SERVICE_CREATE: '/service/create',
  SERVICE_MONITOR: '/service/monitor',
  
  // 设置
  SETTINGS: '/settings',
  SETTINGS_PERMISSIONS: '/settings/permissions',
  SETTINGS_PROFILE: '/settings/profile',
  
  // 演示
  DEMO: '/demo',
};

// 权限配置
export const PERMISSIONS = {
  DATA_VIEW: 'data.view',
  DATA_CREATE: 'data.create',
  DATA_EDIT: 'data.edit',
  DATA_DELETE: 'data.delete',
  
  ALGORITHM_VIEW: 'algorithm.view',
  ALGORITHM_CREATE: 'algorithm.create',
  ALGORITHM_RUN: 'algorithm.run',
  
  MODEL_VIEW: 'model.view',
  MODEL_CREATE: 'model.create',
  MODEL_DEPLOY: 'model.deploy',
  
  SERVICE_VIEW: 'service.view',
  SERVICE_CREATE: 'service.create',
  SERVICE_MANAGE: 'service.manage',
};

// 主题配置
export const THEME_CONFIG = {
  token: {
    colorPrimary: '#1890ff',
    borderRadius: 6,
    wireframe: false,
  },
  components: {
    Layout: {
      headerBg: '#001529',
      siderBg: '#001529',
    },
    Menu: {
      darkItemBg: '#001529',
      darkSubMenuItemBg: '#000c17',
    },
  },
};

// 表格默认配置
export const TABLE_CONFIG = {
  pagination: {
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total: number, range: [number, number]) =>
      `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
    pageSizeOptions: ['10', '20', '50', '100'],
    defaultPageSize: 20,
  },
  scroll: { x: 'max-content' },
  size: 'middle' as const,
};
