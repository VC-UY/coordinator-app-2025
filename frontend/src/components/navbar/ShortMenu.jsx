import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AssignmentIcon from '@mui/icons-material/Assignment';
import ListAltIcon from '@mui/icons-material/ListAlt';
import BarChartIcon from '@mui/icons-material/BarChart';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import PeopleIcon from '@mui/icons-material/People';
import { Link, useLocation } from 'react-router-dom';

export default function ShortMenu() {
  const path = useLocation().pathname;

  const item = (to, icon, selected) => (
    <ListItemButton component={Link} to={to} selected={selected} sx={{ display: 'flex', justifyContent: 'center' }}>
      <ListItemIcon sx={{ display: 'flex', justifyContent: 'center', color: selected ? '#00D4FF' : '#94A3B8' }}>
        {icon}
      </ListItemIcon>
    </ListItemButton>
  );

  return (
    <List sx={{ width: '100%', bgcolor: 'transparent' }} component="nav">
      {item('/', <DashboardIcon />, path === '/')}
      {item('/manager', <PeopleIcon />, path === '/manager')}
      {item('/volunteer', <PeopleIcon />, path === '/volunteer')}
      {item('/workflows', <AssignmentIcon />, path === '/workflows')}
      {item('/tasks', <ListAltIcon />, path === '/tasks')}
      {item('/analytics', <BarChartIcon />, path === '/analytics')}
      {item('/system-status', <MonitorHeartIcon />, path === '/system-status')}
    </List>
  );
}
