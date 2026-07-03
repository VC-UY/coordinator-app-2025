import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import DashboardIcon from '@mui/icons-material/Dashboard';
import AssignmentIcon from '@mui/icons-material/Assignment';
import ListAltIcon from '@mui/icons-material/ListAlt';
import BarChartIcon from '@mui/icons-material/BarChart';
import MonitorHeartIcon from '@mui/icons-material/MonitorHeart';
import PeopleIcon from '@mui/icons-material/People';
import { Link, useLocation } from 'react-router-dom';

const links = [
  { to: '/', label: 'Tableau de bord', icon: <DashboardIcon /> },
  { to: '/manager', label: 'Managers', icon: <PeopleIcon /> },
  { to: '/volunteer', label: 'Volontaires', icon: <PeopleIcon /> },
  { to: '/workflows', label: 'Workflows', icon: <AssignmentIcon /> },
  { to: '/tasks', label: 'Taches', icon: <ListAltIcon /> },
  { to: '/analytics', label: 'Analyses', icon: <BarChartIcon /> },
  { to: '/system-status', label: 'Etat systeme', icon: <MonitorHeartIcon /> },
];

export default function Menu() {
  const path = useLocation().pathname;

  return (
    <List sx={{ px: 1, py: 2 }}>
      {links.map((link) => {
        const selected = path === link.to;
        return (
          <ListItemButton
            key={link.to}
            component={Link}
            to={link.to}
            selected={selected}
            sx={{
              borderRadius: 2,
              mb: 0.5,
              color: selected ? '#00D4FF' : '#cbd5e1',
              '&.Mui-selected': {
                background: 'rgba(0, 180, 240, 0.15)',
                border: '1px solid rgba(0, 212, 255, 0.35)',
              },
            }}
          >
            <ListItemIcon sx={{ color: 'inherit', minWidth: 40 }}>{link.icon}</ListItemIcon>
            <ListItemText primary={link.label} primaryTypographyProps={{ fontSize: 14, fontWeight: selected ? 700 : 500 }} />
          </ListItemButton>
        );
      })}
    </List>
  );
}
