import {React, useState} from 'react';
import Box from '@mui/material/Box';
import Drawer from '@mui/material/Drawer';
import AppBar from '@mui/material/AppBar';
import CssBaseline from '@mui/material/CssBaseline';
import Toolbar from '@mui/material/Toolbar';
import { IconButton, InputBase, Badge, Avatar, MenuItem, MenuList, Popover } from '@mui/material';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import NotificationsIcon from '@mui/icons-material/Notifications';
import SettingsIcon from '@mui/icons-material/Settings';
import LogoutIcon from '@mui/icons-material/Logout';
import FlashOnIcon from '@mui/icons-material/FlashOn';
import Typography from '@mui/material/Typography';
import Menu from './Menu';
import ShortMenu from './ShortMenu';

const drawerWidth = 280;
const shortDrawerWidth = 80;

export default function Navbar({content}) {
  const [isBigMenu, setIsBigMenu] = useState(true);
  const [anchorEl, setAnchorEl] = useState(null);

  const changeMenu = () => {
     setIsBigMenu(!isBigMenu);
  };

  const handleUserMenuClick = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleUserMenuClose = () => {
    setAnchorEl(null);
  };

  const open = Boolean(anchorEl);

  return (
    <Box sx={{ display: 'flex' }}>
      <CssBaseline />
      
      {/* Global Styles */}
      <Box component="style">{`
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-6px); }
        }
        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }
        @keyframes fadeIn {
          from { opacity: 0; transform: translateY(-10px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</Box>

      {/* AppBar */}
      <AppBar
        position="fixed"
        sx={{
          zIndex: (theme) => theme.zIndex.drawer + 1,
          background: 'rgba(30, 41, 59, 0.9)',
          boxShadow: '0 4px 24px rgba(10, 22, 40, 0.4), 0 0 0 1px rgba(59, 130, 246, 0.2)',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid rgba(71, 85, 105, 0.3)',
        }}
      >
        <Toolbar sx={{ minHeight: '70px !important', px: 3 }}>
          {/* Menu Toggle Button */}
          <IconButton
            onClick={changeMenu}
            sx={{
              width: '48px',
              height: '48px',
              borderRadius: '16px',
              border: '2px solid rgba(59, 130, 246, 0.3)',
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.15) 0%, rgba(96, 165, 250, 0.1) 100%)',
              color: '#60A5FA',
              marginRight: '24px',
              transition: 'all 0.3s cubic-bezier(0.34, 1.56, 0.64, 1)',
              boxShadow: '0 4px 12px rgba(59, 130, 246, 0.2)',
              '&:hover': {
                transform: 'scale(1.1) rotate(5deg)',
                boxShadow: '0 6px 20px rgba(59, 130, 246, 0.4)',
                background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(96, 165, 250, 0.15) 100%)',
              }
            }}
          >
            <MenuIcon />
          </IconButton>

          {/* Logo & Title */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: '16px', flex: 1 }}>
            <Box sx={{
              width: '48px',
              height: '48px',
              borderRadius: '14px',
              background: 'linear-gradient(135deg, rgba(59, 130, 246, 0.25) 0%, rgba(96, 165, 250, 0.15) 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: '2px solid rgba(59, 130, 246, 0.4)',
              animation: 'float 3s ease-in-out infinite',
              boxShadow: '0 4px 16px rgba(59, 130, 246, 0.3)',
            }}>
              <FlashOnIcon sx={{ fontSize: 26, color: '#3B82F6', filter: 'drop-shadow(0 0 8px rgba(59, 130, 246, 0.8))' }} />
            </Box>
            <Box>
              <Typography
                variant="h6"
                noWrap
                sx={{
                  fontSize: '22px',
                  fontWeight: 800,
                  background: 'linear-gradient(135deg, #FFFFFF 0%, #60A5FA 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text',
                  letterSpacing: '0.5px',
                }}
              >
                Coordinator Dashboard
              </Typography>
              <Typography sx={{ fontSize: '12px', color: '#60A5FA', fontWeight: 500, letterSpacing: '0.8px' }}>
                VolunSys-UY1
              </Typography>
            </Box>
          </Box>

          {/* Search Bar */}
          <Box sx={{
            position: 'relative',
            marginRight: '24px',
            width: '320px',
          }}>
            <InputBase
              placeholder="Rechercher..."
              sx={{
                width: '100%',
                height: '44px',
                borderRadius: '14px',
                border: '2px solid rgba(71, 85, 105, 0.5)',
                background: 'rgba(255, 255, 255, 0.1)',
                backdropFilter: 'blur(10px)',
                padding: '0 16px 0 48px',
                fontSize: '14px',
                color: '#FFFFFF',
                transition: 'all 0.3s ease',
                '&:focus-within': {
                  background: 'rgba(255, 255, 255, 0.15)',
                  borderColor: '#3B82F6',
                  boxShadow: '0 4px 16px rgba(59, 130, 246, 0.3)',
                },
                '& input::placeholder': {
                  color: 'rgba(255, 255, 255, 0.6)',
                }
              }}
            />
            <SearchIcon sx={{
              position: 'absolute',
              left: '16px',
              top: '50%',
              transform: 'translateY(-50%)',
              color: '#60A5FA',
              pointerEvents: 'none',
            }} />
          </Box>

          {/* Notifications */}
          <IconButton
            sx={{
              width: '44px',
              height: '44px',
              borderRadius: '12px',
              border: '2px solid rgba(71, 85, 105, 0.5)',
              background: 'rgba(255, 255, 255, 0.1)',
              color: '#3B82F6',
              marginRight: '12px',
              transition: 'all 0.3s ease',
              '&:hover': {
                background: 'rgba(59, 130, 246, 0.15)',
                transform: 'scale(1.1)',
              }
            }}
          >
            <Badge
              badgeContent={3}
              sx={{
                '& .MuiBadge-badge': {
                  background: 'linear-gradient(135deg, #FF4444 0%, #FF0000 100%)',
                  border: '2px solid #1E293B',
                  animation: 'pulse 2s ease-in-out infinite',
                }
              }}
            >
              <NotificationsIcon fontSize="small" />
            </Badge>
          </IconButton>

          {/* User Menu */}
          <Box
            onClick={handleUserMenuClick}
            sx={{
              display: 'flex',
              alignItems: 'center',
              gap: '12px',
              padding: '8px 16px',
              borderRadius: '14px',
              border: '2px solid rgba(71, 85, 105, 0.5)',
              background: 'rgba(255, 255, 255, 0.1)',
              color: '#FFFFFF',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                background: 'rgba(59, 130, 246, 0.15)',
                borderColor: '#3B82F6',
              }
            }}
          >
            <Avatar
              sx={{
                width: 36,
                height: 36,
                borderRadius: '10px',
                background: 'linear-gradient(135deg, #3B82F6 0%, #60A5FA 100%)',
                border: '2px solid rgba(255, 255, 255, 0.2)',
                color: '#FFFFFF',
                fontSize: '16px',
                fontWeight: 700,
              }}
            >
              A
            </Avatar>
            <Box sx={{ textAlign: 'left' }}>
              <Typography sx={{ fontSize: '14px', fontWeight: 600 }}>Admin User</Typography>
              <Typography sx={{ fontSize: '11px', color: '#94A3B8' }}>Coordinator</Typography>
            </Box>
          </Box>

          {/* User Dropdown */}
          <Popover
            open={open}
            anchorEl={anchorEl}
            onClose={handleUserMenuClose}
            anchorOrigin={{
              vertical: 'bottom',
              horizontal: 'right',
            }}
            transformOrigin={{
              vertical: 'top',
              horizontal: 'right',
            }}
            sx={{
              '& .MuiPaper-root': {
                marginTop: '12px',
                borderRadius: '16px',
                boxShadow: '0 8px 32px rgba(10, 22, 40, 0.3)',
                border: '1px solid rgba(71, 85, 105, 0.3)',
                background: 'rgba(30, 41, 59, 0.95)',
                backdropFilter: 'blur(10px)',
                overflow: 'hidden',
                animation: 'fadeIn 0.3s ease',
              }
            }}
          >
            <MenuList sx={{ p: 0 }}>
              <MenuItem
                onClick={handleUserMenuClose}
                sx={{
                  padding: '14px 20px',
                  display: 'flex',
                  gap: '12px',
                  color: '#FFFFFF',
                  fontSize: '14px',
                  fontWeight: 500,
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    background: 'rgba(59, 130, 246, 0.1)',
                  }
                }}
              >
                <SettingsIcon sx={{ fontSize: 18, color: '#60A5FA' }} />
                Settings
              </MenuItem>
              <Box sx={{
                height: '1px',
                background: 'linear-gradient(90deg, transparent 0%, rgba(71, 85, 105, 0.5) 50%, transparent 100%)',
                margin: '0 12px',
              }} />
              <MenuItem
                onClick={handleUserMenuClose}
                sx={{
                  padding: '14px 20px',
                  display: 'flex',
                  gap: '12px',
                  color: '#FFFFFF',
                  fontSize: '14px',
                  fontWeight: 500,
                  transition: 'all 0.2s ease',
                  '&:hover': {
                    background: 'rgba(255, 68, 68, 0.1)',
                    color: '#FF4444',
                  }
                }}
              >
                <LogoutIcon sx={{ fontSize: 18, color: '#FF4444' }} />
                Logout
              </MenuItem>
            </MenuList>
          </Popover>
        </Toolbar>
      </AppBar>

      {/* Sidebar Drawer */}
      <Drawer
        variant="permanent"
        sx={{
          width: isBigMenu ? drawerWidth : shortDrawerWidth,
          flexShrink: 0,
          transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
          [`& .MuiDrawer-paper`]: {
            width: isBigMenu ? drawerWidth : shortDrawerWidth,
            boxSizing: 'border-box',
            transition: 'width 0.4s cubic-bezier(0.4, 0, 0.2, 1)',
            background: 'rgba(30, 41, 59, 0.95)',
            backdropFilter: 'blur(10px)',
            boxShadow: '4px 0 24px rgba(10, 22, 40, 0.3)',
            borderRight: '1px solid rgba(71, 85, 105, 0.3)',
            overflowX: 'hidden',
          },
        }}
      >
        <Toolbar sx={{ minHeight: '70px !important' }} />
        {isBigMenu ? <Menu/> : <ShortMenu/>}
      </Drawer>

      {/* Main Content Area */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 4,
          background: 'transparent', // Le dégradé est dans body via index.css
          minHeight: '100vh',
        }}
      >
        <Toolbar sx={{ minHeight: '70px !important' }} />
        {content}
      </Box>
    </Box>
  );
}