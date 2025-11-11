import * as React from 'react';
import List from '@mui/material/List';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Collapse from '@mui/material/Collapse';
import DashboardIcon from '@mui/icons-material/Dashboard';
import DashboardCustomizeIcon from '@mui/icons-material/DashboardCustomize';
import ExpandLess from '@mui/icons-material/ExpandLess';
import ExpandMore from '@mui/icons-material/ExpandMore';
import HomeIcon from '@mui/icons-material/Home';
import AssignmentIcon from '@mui/icons-material/Assignment';
import BarChartIcon from '@mui/icons-material/BarChart';
import NotificationsIcon from '@mui/icons-material/Notifications';
import ForumIcon from '@mui/icons-material/Forum';
import SettingsIcon from '@mui/icons-material/Settings';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import DevicesIcon from '@mui/icons-material/Devices';
import StarsIcon from '@mui/icons-material/Stars';
import {Link, useLocation} from 'react-router-dom';
import { useState } from 'react';
import { Box } from '@mui/material';

export default function Menu() {
  const [openManager, setOpenManager] = useState(false);
  const [openVolunteer, setOpenVolunteer] = useState(false);
  const [openWorkflows, setOpenWorkflows] = useState(false);
  const [openCommunication, setOpenCommunication] = useState(false);

  const handleManagerClick = () => setOpenManager(!openManager);
  const handleVolunteerClick = () => setOpenVolunteer(!openVolunteer);
  const handleWorkflowsClick = () => setOpenWorkflows(!openWorkflows);
  const handleCommunicationClick = () => setOpenCommunication(!openCommunication);

  const location = useLocation();
  const path = location.pathname;

  const menuItemStyle = {
    borderRadius: '20px',
    margin: '6px 12px',
    padding: '14px 20px',
    transition: 'all 0.4s cubic-bezier(0.34, 1.56, 0.64, 1)',
    position: 'relative',
    overflow: 'hidden',
    '&:hover': {
      background: 'linear-gradient(135deg, rgba(0, 180, 240, 0.12) 0%, rgba(0, 212, 255, 0.08) 100%)',
      transform: 'translateX(8px) scale(1.02)',
      boxShadow: '0 4px 16px rgba(0, 180, 240, 0.2), 0 0 0 1px rgba(0, 180, 240, 0.2)',
    },
    '&.Mui-selected': {
      background: 'linear-gradient(135deg, #002060 0%, #001440 100%)',
      color: '#FFFFFF',
      transform: 'scale(1.02)',
      boxShadow: '0 8px 24px rgba(0, 32, 96, 0.4), 0 0 0 1px rgba(0, 212, 255, 0.3)',
      '&:hover': {
        background: 'linear-gradient(135deg, #002060 0%, #001440 100%)',
        transform: 'scale(1.02)',
      },
      '& .MuiListItemIcon-root': {
        color: '#00D4FF',
        filter: 'drop-shadow(0 0 4px rgba(0, 212, 255, 0.6))',
      },
      '& .MuiListItemText-primary': {
        fontWeight: 700,
        letterSpacing: '0.3px',
      },
      '&::before': {
        content: '""',
        position: 'absolute',
        left: 0,
        top: 0,
        width: '100%',
        height: '100%',
        background: 'radial-gradient(circle at 0% 50%, rgba(0, 212, 255, 0.15) 0%, transparent 60%)',
        animation: 'pulse 2s ease-in-out infinite',
      }
    }
  };

  const iconWrapperStyle = (selected) => ({
    width: '40px',
    height: '40px',
    borderRadius: '12px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: '14px',
    minWidth: 'auto',
    background: selected 
      ? 'linear-gradient(135deg, rgba(0, 212, 255, 0.2) 0%, rgba(0, 180, 240, 0.1) 100%)'
      : 'linear-gradient(135deg, rgba(0, 32, 96, 0.08) 0%, rgba(0, 20, 64, 0.05) 100%)',
    border: selected ? '2px solid rgba(0, 212, 255, 0.4)' : '2px solid rgba(0, 32, 96, 0.1)',
    transition: 'all 0.3s ease',
  });

  const expandIconStyle = (isOpen) => ({
    width: '28px',
    height: '28px',
    borderRadius: '8px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: isOpen ? 'rgba(0, 180, 240, 0.15)' : 'rgba(0, 32, 96, 0.08)',
    transition: 'all 0.3s ease',
    color: isOpen ? '#00B0F0' : '#002060',
  });

  return (
    <Box sx={{ 
      width: '100%', 
      height: '100%',
      background: 'linear-gradient(180deg, #FFFFFF 0%, #F8FCFF 100%)',
      overflowY: 'auto',
      padding: '16px 0',
      '&::-webkit-scrollbar': { width: '8px' },
      '&::-webkit-scrollbar-track': {
        background: 'linear-gradient(180deg, #F5F5F5 0%, #E8F4F8 100%)',
        borderRadius: '10px',
        margin: '8px 0',
      },
      '&::-webkit-scrollbar-thumb': {
        background: 'linear-gradient(180deg, #00B0F0 0%, #00D4FF 100%)',
        borderRadius: '10px',
        border: '2px solid transparent',
        backgroundClip: 'padding-box',
      },
      '&::-webkit-scrollbar-thumb:hover': {
        background: 'linear-gradient(180deg, #002060 0%, #001440 100%)',
        backgroundClip: 'padding-box',
      },
      '@keyframes pulse': {
        '0%, 100%': { opacity: 0.5 },
        '50%': { opacity: 1 },
      },
      '@keyframes float': {
        '0%, 100%': { transform: 'translateY(0px)' },
        '50%': { transform: 'translateY(-4px)' },
      }
    }}>
      
      {/* Header Box */}
      <Box sx={{
        margin: '0 16px 24px 16px',
        padding: '20px',
        background: 'linear-gradient(135deg, #002060 0%, #001440 100%)',
        borderRadius: '24px',
        boxShadow: '0 8px 32px rgba(0, 32, 96, 0.3)',
        position: 'relative',
        overflow: 'hidden',
      }}>
        <Box sx={{
          position: 'absolute',
          top: '-50%',
          right: '-20%',
          width: '200px',
          height: '200px',
          background: 'radial-gradient(circle, rgba(0, 212, 255, 0.15) 0%, transparent 70%)',
          borderRadius: '50%',
          animation: 'float 4s ease-in-out infinite',
        }} />
        
        <Box sx={{ display: 'flex', alignItems: 'center', gap: '12px', position: 'relative', zIndex: 1 }}>
          <Box sx={{
            width: '48px',
            height: '48px',
            borderRadius: '16px',
            background: 'linear-gradient(135deg, rgba(0, 212, 255, 0.25) 0%, rgba(0, 180, 240, 0.15) 100%)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: '2px solid rgba(0, 212, 255, 0.3)',
          }}>
            <StarsIcon sx={{ color: '#00D4FF', filter: 'drop-shadow(0 0 8px rgba(0, 212, 255, 0.8))' }} />
          </Box>
          <Box>
            <Box sx={{ fontSize: '16px', fontWeight: 700, color: '#FFFFFF', letterSpacing: '0.5px' }}>
              VolunSys-UY1
            </Box>
            <Box sx={{ fontSize: '11px', color: '#00B0F0', fontWeight: 500, letterSpacing: '0.3px', mt: 0.5 }}>
              Calcul Scientifique Distribué
            </Box>
          </Box>
        </Box>
      </Box>

      <List component="nav">
        {/* Home */}
        <ListItemButton component={Link} to="/" selected={path === "/"} sx={menuItemStyle}>
          <Box sx={iconWrapperStyle(path === "/")}>
            <HomeIcon sx={{ fontSize: 20 }} />
          </Box>
          <ListItemText primary="Home" primaryTypographyProps={{ fontSize: '15px', fontWeight: 500 }} />
        </ListItemButton>

        {/* Managers */}
        <ListItemButton onClick={handleManagerClick} sx={{
          ...menuItemStyle,
          background: openManager ? 'linear-gradient(135deg, rgba(0, 180, 240, 0.08) 0%, rgba(0, 212, 255, 0.05) 100%)' : 'transparent',
        }}>
          <Box sx={iconWrapperStyle(false)}>
            <DashboardIcon sx={{ fontSize: 20 }} />
          </Box>
          <ListItemText primary="Managers" primaryTypographyProps={{ fontSize: '15px', fontWeight: openManager ? 600 : 500 }} />
          <Box sx={expandIconStyle(openManager)}>
            {openManager ? <ExpandLess sx={{ fontSize: 16 }} /> : <ExpandMore sx={{ fontSize: 16 }} />}
          </Box>
        </ListItemButton>
        
        <Collapse in={openManager} timeout="auto" unmountOnExit>
          <Box sx={{ position: 'relative' }}>
            <Box sx={{
              position: 'absolute',
              left: '32px',
              top: '0',
              bottom: '0',
              width: '2px',
              background: 'linear-gradient(180deg, rgba(0, 180, 240, 0.3) 0%, rgba(0, 212, 255, 0.1) 100%)',
              borderRadius: '2px',
            }} />
            
            <ListItemButton component={Link} to="/manager" selected={path === "/manager"} sx={{ ...menuItemStyle, pl: 7 }}>
              <Box sx={iconWrapperStyle(path === "/manager")}>
                <DashboardCustomizeIcon sx={{ fontSize: 18 }} />
              </Box>
              <ListItemText primary="All managers" primaryTypographyProps={{ fontSize: '14px' }} />
            </ListItemButton>

            <ListItemButton onClick={handleWorkflowsClick} sx={{ ...menuItemStyle, pl: 7 }}>
              <Box sx={iconWrapperStyle(false)}>
                <AssignmentIcon sx={{ fontSize: 18 }} />
              </Box>
              <ListItemText primary="Workflows" primaryTypographyProps={{ fontSize: '14px' }} />
              <Box sx={expandIconStyle(openWorkflows)}>
                {openWorkflows ? <ExpandLess sx={{ fontSize: 14 }} /> : <ExpandMore sx={{ fontSize: 14 }} />}
              </Box>
            </ListItemButton>
            
            <Collapse in={openWorkflows} timeout="auto" unmountOnExit>
              <ListItemButton component={Link} to="/workflows" selected={path === "/workflows"} sx={{ ...menuItemStyle, pl: 11 }}>
                <Box sx={iconWrapperStyle(path === "/workflows")}>
                  <AssignmentIcon sx={{ fontSize: 16 }} />
                </Box>
                <ListItemText primary="All Workflows" primaryTypographyProps={{ fontSize: '13px' }} />
              </ListItemButton>
            </Collapse>

            <ListItemButton sx={{ ...menuItemStyle, pl: 7 }}>
              <Box sx={iconWrapperStyle(false)}>
                <DashboardCustomizeIcon sx={{ fontSize: 18 }} />
              </Box>
              <ListItemText primary="History of workflows" primaryTypographyProps={{ fontSize: '14px' }} />
            </ListItemButton>
          </Box>
        </Collapse>

        {/* Volunteers */}
        <ListItemButton onClick={handleVolunteerClick} sx={{
          ...menuItemStyle,
          background: openVolunteer ? 'linear-gradient(135deg, rgba(0, 180, 240, 0.08) 0%, rgba(0, 212, 255, 0.05) 100%)' : 'transparent',
        }}>
          <Box sx={iconWrapperStyle(false)}>
            <DashboardIcon sx={{ fontSize: 20 }} />
          </Box>
          <ListItemText primary="Volunteers" primaryTypographyProps={{ fontSize: '15px', fontWeight: openVolunteer ? 600 : 500 }} />
          <Box sx={expandIconStyle(openVolunteer)}>
            {openVolunteer ? <ExpandLess sx={{ fontSize: 16 }} /> : <ExpandMore sx={{ fontSize: 16 }} />}
          </Box>
        </ListItemButton>
        
        <Collapse in={openVolunteer} timeout="auto" unmountOnExit>
          <Box sx={{ position: 'relative' }}>
            <Box sx={{
              position: 'absolute',
              left: '32px',
              top: '0',
              bottom: '0',
              width: '2px',
              background: 'linear-gradient(180deg, rgba(0, 180, 240, 0.3) 0%, rgba(0, 212, 255, 0.1) 100%)',
              borderRadius: '2px',
            }} />
            <ListItemButton component={Link} to="/volunteer" selected={path === "/volunteer"} sx={{ ...menuItemStyle, pl: 7 }}>
              <Box sx={iconWrapperStyle(path === "/volunteer")}>
                <DashboardCustomizeIcon sx={{ fontSize: 18 }} />
              </Box>
              <ListItemText primary="All Volunteers" primaryTypographyProps={{ fontSize: '14px' }} />
            </ListItemButton>
          </Box>
        </Collapse>

        {/* Analytics */}
        <ListItemButton component={Link} to="/analytics" selected={path === "/analytics"} sx={menuItemStyle}>
          <Box sx={iconWrapperStyle(path === "/analytics")}>
            <BarChartIcon sx={{ fontSize: 20 }} />
          </Box>
          <ListItemText primary="Performance & Analytics" primaryTypographyProps={{ fontSize: '15px', fontWeight: 500 }} />
        </ListItemButton>

        {/* Notifications */}
        <ListItemButton component={Link} to="/notifications" selected={path === "/notifications"} sx={menuItemStyle}>
          <Box sx={iconWrapperStyle(path === "/notifications")}>
            <NotificationsIcon sx={{ fontSize: 20 }} />
          </Box>
          <ListItemText primary="Notifications" primaryTypographyProps={{ fontSize: '15px', fontWeight: 500 }} />
        </ListItemButton>

        {/* Communication */}
        <ListItemButton onClick={handleCommunicationClick} sx={{
          ...menuItemStyle,
          background: openCommunication ? 'linear-gradient(135deg, rgba(0, 180, 240, 0.08) 0%, rgba(0, 212, 255, 0.05) 100%)' : 'transparent',
        }}>
          <Box sx={iconWrapperStyle(false)}>
            <ForumIcon sx={{ fontSize: 20 }} />
          </Box>
          <ListItemText primary="Communication" primaryTypographyProps={{ fontSize: '15px', fontWeight: openCommunication ? 600 : 500 }} />
          <Box sx={expandIconStyle(openCommunication)}>
            {openCommunication ? <ExpandLess sx={{ fontSize: 16 }} /> : <ExpandMore sx={{ fontSize: 16 }} />}
          </Box>
        </ListItemButton>
        
        <Collapse in={openCommunication} timeout="auto" unmountOnExit>
          <Box sx={{ position: 'relative' }}>
            <Box sx={{
              position: 'absolute',
              left: '32px',
              top: '0',
              bottom: '0',
              width: '2px',
              background: 'linear-gradient(180deg, rgba(0, 180, 240, 0.3) 0%, rgba(0, 212, 255, 0.1) 100%)',
              borderRadius: '2px',
            }} />
            <ListItemButton component={Link} to="/system-status" selected={path === "/system-status"} sx={{ ...menuItemStyle, pl: 7 }}>
              <Box sx={iconWrapperStyle(path === "/system-status")}>
                <DevicesIcon sx={{ fontSize: 18 }} />
              </Box>
              <ListItemText primary="État du Système" primaryTypographyProps={{ fontSize: '14px' }} />
            </ListItemButton>
          </Box>
        </Collapse>

        {/* Settings */}
        <ListItemButton component={Link} to="/settings" selected={path === "/settings"} sx={menuItemStyle}>
          <Box sx={iconWrapperStyle(path === "/settings")}>
            <SettingsIcon sx={{ fontSize: 20 }} />
          </Box>
          <ListItemText primary="Settings" primaryTypographyProps={{ fontSize: '15px', fontWeight: 500 }} />
        </ListItemButton>

        {/* Help */}
        <ListItemButton component={Link} to="/help" selected={path === "/help"} sx={menuItemStyle}>
          <Box sx={iconWrapperStyle(path === "/help")}>
            <HelpOutlineIcon sx={{ fontSize: 20 }} />
          </Box>
          <ListItemText primary="Help" primaryTypographyProps={{ fontSize: '15px', fontWeight: 500 }} />
        </ListItemButton>
      </List>

      {/* Footer */}
      <Box sx={{
        margin: '24px 16px 16px 16px',
        padding: '16px',
        background: 'linear-gradient(135deg, rgba(0, 180, 240, 0.08) 0%, rgba(0, 212, 255, 0.05) 100%)',
        borderRadius: '20px',
        border: '2px solid rgba(0, 180, 240, 0.15)',
        textAlign: 'center',
      }}>
        <Box sx={{ fontSize: '12px', color: '#002060', fontWeight: 600, letterSpacing: '0.3px' }}>
          La puissance collective au service du calcul scientifique
        </Box>
      </Box>
    </Box>
  );
}