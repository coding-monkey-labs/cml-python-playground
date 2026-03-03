import { useAppSelector } from './store';
import { DashboardHeader } from './components/DashboardHeader/DashboardHeader';
import { Dashboard } from './components/Dashboard/Dashboard';
import { Sidebar } from './components/Sidebar/Sidebar';
import { PanelEditor } from './components/PanelEditor/PanelEditor';
import { DashboardSettings } from './components/DashboardSettings/DashboardSettings';
import { Notification } from './components/Notification/Notification';
import './App.css';

function App() {
  const theme = useAppSelector(state => state.theme.mode);
  const editingPanelId = useAppSelector(state => state.dashboard.editingPanelId);
  const sidebarOpen = useAppSelector(state => state.dashboard.sidebarOpen);
  const settingsOpen = useAppSelector(state => state.dashboard.settingsOpen);

  return (
    <div className={`app ${theme}`} data-theme={theme}>
      <Sidebar />
      <div className={`app-main ${sidebarOpen ? 'sidebar-open' : ''}`}>
        <DashboardHeader />
        <Dashboard />
      </div>
      {editingPanelId && <PanelEditor />}
      {settingsOpen && <DashboardSettings />}
      <Notification />
    </div>
  );
}

export default App;
