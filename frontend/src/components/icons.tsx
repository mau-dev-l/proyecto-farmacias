import {
  BsArrowLeftRight,
  BsArrowRight,
  BsBarChartLine,
  BsBell,
  BsBoxArrowInDown,
  BsBoxArrowRight,
  BsBoxSeam,
  BsBoxes,
  BsCalculator,
  BsCalendarDate,
  BsCalendarX,
  BsCapsule,
  BsCapsulePill,
  BsCartCheck,
  BsCash,
  BsCashCoin,
  BsCheck2,
  BsCheckCircle,
  BsChevronDown,
  BsChevronRight,
  BsChevronUp,
  BsClipboard,
  BsClipboardCheck,
  BsClipboardData,
  BsClockHistory,
  BsDownload,
  BsExclamationCircle,
  BsExclamationTriangle,
  BsEye,
  BsEyeSlash,
  BsGear,
  BsHourglassSplit,
  BsInbox,
  BsInfoCircle,
  BsPeople,
  BsPencil,
  BsPersonPlus,
  BsPlusLg,
  BsQrCode,
  BsSearch,
  BsShieldLock,
  BsShop,
  BsSliders,
  BsTelegram,
  BsToggleOff,
  BsToggleOn,
  BsTrash,
  BsUpcScan,
  BsX,
} from 'react-icons/bs'
import { LuLayoutDashboard } from 'react-icons/lu'

/**
 * Semantic icon registry.
 *
 * Pages never import from `react-icons` directly: they ask for a meaning
 * (`Icons.medicine`) and this file decides which family and glyph represent it.
 * Swapping icon sets is therefore a single-file change.
 */
export const Icons = {
  // Navegación
  dashboard: LuLayoutDashboard,
  inventory: BsBoxSeam,
  medicine: BsCapsulePill,
  movement: BsArrowLeftRight,
  kardex: BsClipboardData,
  alert: BsBell,
  report: BsBarChartLine,
  telegram: BsTelegram,
  admin: BsGear,
  logout: BsBoxArrowRight,

  // Acciones
  close: BsX,
  check: BsCheck2,
  plus: BsPlusLg,
  edit: BsPencil,
  activate: BsToggleOn,
  deactivate: BsToggleOff,
  search: BsSearch,
  download: BsDownload,
  copy: BsClipboard,
  copied: BsClipboardCheck,
  code: BsQrCode,
  calculate: BsCalculator,
  settings: BsSliders,
  userAdd: BsPersonPlus,

  // Navegación secundaria
  chevronUp: BsChevronUp,
  chevronDown: BsChevronDown,
  chevronRight: BsChevronRight,
  arrowRight: BsArrowRight,

  // Estado y feedback
  success: BsCheckCircle,
  warning: BsExclamationTriangle,
  danger: BsExclamationCircle,
  info: BsInfoCircle,
  empty: BsInbox,

  // Indicadores
  units: BsBoxes,
  value: BsCashCoin,
  expiring: BsCalendarX,
  medicineCount: BsCapsule,
  clock: BsClockHistory,
  hourglass: BsHourglassSplit,

  // Movimientos
  entry: BsBoxArrowInDown,
  sale: BsCartCheck,
  waste: BsTrash,

  // Administración
  team: BsPeople,
  branch: BsShop,

  // Formularios y sesión
  security: BsShieldLock,
  eye: BsEye,
  eyeOff: BsEyeSlash,
  barcode: BsUpcScan,
  calendar: BsCalendarDate,
  cash: BsCash,
}
