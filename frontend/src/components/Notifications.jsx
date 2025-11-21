import React, { useEffect, useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tab,
  Tabs,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Chip,
  IconButton,
  Badge,
  Divider,
  Button,
  Card,
  CardContent
} from '@mui/material';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import InfoIcon from '@mui/icons-material/Info';
import WarningIcon from '@mui/icons-material/Warning';
import ErrorIcon from '@mui/icons-material/Error';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import DeleteIcon from '@mui/icons-material/Delete';
import MarkEmailReadIcon from '@mui/icons-material/MarkEmailRead';
import AssignmentIcon from '@mui/icons-material/Assignment';
import SecurityIcon from '@mui/icons-material/Security';
import SettingsIcon from '@mui/icons-material/Settings';
import AxiosInstance from './axios';

const Notifications = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({
    all: 0,
    workflows: 0,
    tasks: 0,
    security: 0,
    system: 0,
    unread: 0
  });

  // Fetch notifications from backend
  const fetchNotifications = async () => {
    setLoading(true);
    try {
      // In a real implementation, these would be actual API endpoints
      // For now, we'll simulate with empty arrays
      setNotifications([]);
      setStats({
        all: 0,
        workflows: 0,
        tasks: 0,
        security: 0,
        system: 0,
        unread: 0
      });
    } catch (error) {
      console.error('Error fetching notifications:', error);
      setNotifications([]);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchNotifications();
    // Refresh every 30 seconds
    const interval = setInterval(fetchNotifications, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const getIcon = (type) => {
    switch (type) {
      case 'success':
        return <CheckCircleIcon sx={{ color: '#00FF88' }} />;
      case 'warning':
        return <WarningIcon sx={{ color: '#FFA500' }} />;
      case 'error':
        return <ErrorIcon sx={{ color: '#FF4444' }} />;
      case 'info':
      default:
        return <InfoIcon sx={{ color: '#00D4FF' }} />;
    }
  };

  const getCategoryIcon = (category) => {
    switch (category) {
      case 'workflow':
        return <AssignmentIcon sx={{ fontSize: 20 }} />;
      case 'task':
        return <AssignmentIcon sx={{ fontSize: 20 }} />;
      case 'security':
        return <SecurityIcon sx={{ fontSize: 20 }} />;
      case 'system':
      default:
        return <SettingsIcon sx={{ fontSize: 20 }} />;
    }
  };

  const filterNotifications = () => {
    switch (activeTab) {
      case 1:
        return notifications.filter(n => n.category === 'workflow');
      case 2:
        return notifications.filter(n => n.category === 'task');
      case 3:
        return notifications.filter(n => n.category === 'security');
      case 4:
        return notifications.filter(n => n.category === 'system');
      default:
        return notifications;
    }
  };

  const markAsRead = (id) => {
    // In a real implementation, this would make an API call
    setNotifications(notifications.map(n =>
      n.id === id ? { ...n, read: true } : n
    ));
    setStats({ ...stats, unread: Math.max(0, stats.unread - 1) });
  };

  const deleteNotification = (id) => {
    // In a real implementation, this would make an API call
    setNotifications(notifications.filter(n => n.id !== id));
  };

  const markAllAsRead = () => {
    // In a real implementation, this would make an API call
    setNotifications(notifications.map(n => ({ ...n, read: true })));
    setStats({ ...stats, unread: 0 });
  };

  const deleteAll = () => {
    if (window.confirm('Are you sure you want to delete all notifications?')) {
      // In a real implementation, this would make an API call
      setNotifications([]);
      setStats({
        all: 0,
        workflows: 0,
        tasks: 0,
        security: 0,
        system: 0,
        unread: 0
      });
    }
  };

  const filteredNotifications = filterNotifications();

  return (
    <Box sx={{
      p: { xs: 2, md: 4 },
      background: 'linear-gradient(180deg, #001440 0%, #002060 50%, #001440 100%)',
      minHeight: '100vh'
    }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 4,
          mb: 4,
          borderRadius: 3,
          textAlign: 'center',
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.9) 0%, rgba(0, 20, 64, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 180, 240, 0.3)',
          boxShadow: '0 12px 48px rgba(0, 32, 96, 0.6)',
        }}
      >
        <Badge badgeContent={stats.unread} color="error" max={99}>
          <NotificationsActiveIcon sx={{ fontSize: 64, color: '#00D4FF', mb: 2 }} />
        </Badge>
        <Typography variant="h4" fontWeight={700} gutterBottom sx={{
          background: 'linear-gradient(135deg, #FFFFFF 0%, #00D4FF 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '0.5px'
        }}>
          Notifications
        </Typography>
        <Typography variant="subtitle1" sx={{ color: '#00B0F0' }}>
          Stay updated with system events, workflows, and security alerts
        </Typography>
      </Paper>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<MarkEmailReadIcon />}
          onClick={markAllAsRead}
          disabled={stats.unread === 0}
          sx={{
            borderColor: '#00D4FF',
            color: '#00D4FF',
            '&:hover': {
              borderColor: '#00FF88',
              backgroundColor: 'rgba(0, 255, 136, 0.1)'
            }
          }}
        >
          Mark All as Read
        </Button>
        <Button
          variant="outlined"
          startIcon={<DeleteIcon />}
          onClick={deleteAll}
          disabled={notifications.length === 0}
          sx={{
            borderColor: '#FF4444',
            color: '#FF4444',
            '&:hover': {
              borderColor: '#FF0000',
              backgroundColor: 'rgba(255, 68, 68, 0.1)'
            }
          }}
        >
          Delete All
        </Button>
      </Box>

      {/* Tabs */}
      <Paper
        elevation={0}
        sx={{
          mb: 3,
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 180, 240, 0.3)',
          borderRadius: 2
        }}
      >
        <Tabs
          value={activeTab}
          onChange={handleTabChange}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            '& .MuiTab-root': {
              color: '#00B0F0',
              fontWeight: 600,
              '&.Mui-selected': {
                color: '#00FF88'
              }
            },
            '& .MuiTabs-indicator': {
              backgroundColor: '#00FF88'
            }
          }}
        >
          <Tab label={`All (${stats.all})`} />
          <Tab label={`Workflows (${stats.workflows})`} />
          <Tab label={`Tasks (${stats.tasks})`} />
          <Tab label={`Security (${stats.security})`} />
          <Tab label={`System (${stats.system})`} />
        </Tabs>
      </Paper>

      {/* Notifications List */}
      <Paper
        elevation={0}
        sx={{
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 180, 240, 0.3)',
          borderRadius: 2,
          minHeight: 400
        }}
      >
        {loading ? (
          <Box sx={{ p: 4, textAlign: 'center' }}>
            <Typography sx={{ color: '#00B0F0' }}>Loading notifications...</Typography>
          </Box>
        ) : filteredNotifications.length === 0 ? (
          <Box sx={{ p: 6, textAlign: 'center' }}>
            <NotificationsActiveIcon sx={{ fontSize: 80, color: 'rgba(0, 180, 240, 0.3)', mb: 2 }} />
            <Typography variant="h6" sx={{ color: '#00B0F0', mb: 1 }}>
              No notifications
            </Typography>
            <Typography variant="body2" sx={{ color: 'rgba(0, 180, 240, 0.7)' }}>
              You're all caught up! Check back later for updates.
            </Typography>
          </Box>
        ) : (
          <List sx={{ p: 2 }}>
            {filteredNotifications.map((notification, index) => (
              <React.Fragment key={notification.id}>
                <ListItem
                  sx={{
                    mb: 1,
                    borderRadius: 2,
                    background: notification.read
                      ? 'rgba(0, 180, 240, 0.05)'
                      : 'linear-gradient(135deg, rgba(0, 212, 255, 0.1) 0%, rgba(0, 180, 240, 0.1) 100%)',
                    border: notification.read
                      ? '1px solid rgba(0, 180, 240, 0.2)'
                      : '2px solid rgba(0, 212, 255, 0.4)',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      background: 'rgba(0, 180, 240, 0.15)',
                      transform: 'translateX(8px)'
                    }
                  }}
                >
                  <ListItemIcon>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      {getIcon(notification.type)}
                      {getCategoryIcon(notification.category)}
                    </Box>
                  </ListItemIcon>
                  <ListItemText
                    primary={
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                        <Typography fontWeight={notification.read ? 400 : 600} sx={{ color: '#FFFFFF' }}>
                          {notification.title}
                        </Typography>
                        {!notification.read && (
                          <Chip label="New" size="small" sx={{ bgcolor: '#00D4FF', color: '#001440', height: 20 }} />
                        )}
                      </Box>
                    }
                    secondary={
                      <Box>
                        <Typography variant="body2" sx={{ color: '#00B0F0', mt: 0.5 }}>
                          {notification.message}
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'rgba(0, 180, 240, 0.7)', mt: 0.5 }}>
                          {notification.timestamp}
                        </Typography>
                      </Box>
                    }
                  />
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    {!notification.read && (
                      <IconButton
                        size="small"
                        onClick={() => markAsRead(notification.id)}
                        sx={{
                          color: '#00FF88',
                          '&:hover': {
                            backgroundColor: 'rgba(0, 255, 136, 0.1)'
                          }
                        }}
                      >
                        <MarkEmailReadIcon fontSize="small" />
                      </IconButton>
                    )}
                    <IconButton
                      size="small"
                      onClick={() => deleteNotification(notification.id)}
                      sx={{
                        color: '#FF4444',
                        '&:hover': {
                          backgroundColor: 'rgba(255, 68, 68, 0.1)'
                        }
                      }}
                    >
                      <DeleteIcon fontSize="small" />
                    </IconButton>
                  </Box>
                </ListItem>
                {index < filteredNotifications.length - 1 && (
                  <Divider sx={{ borderColor: 'rgba(0, 180, 240, 0.2)', my: 1 }} />
                )}
              </React.Fragment>
            ))}
          </List>
        )}
      </Paper>

      {/* Info Card */}
      <Card
        sx={{
          mt: 4,
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 180, 240, 0.3)',
          borderRadius: 2
        }}
      >
        <CardContent>
          <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
            <InfoIcon sx={{ color: '#00D4FF', mr: 1 }} />
            <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF' }}>
              About Notifications
            </Typography>
          </Box>
          <Typography variant="body2" sx={{ color: '#00B0F0', mb: 2 }}>
            Notifications keep you informed about important events in your coordinator system:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText
                primary="Workflow notifications"
                secondary="Status changes, completions, and errors in workflows"
                primaryTypographyProps={{ sx: { color: '#FFFFFF', fontSize: '0.9rem' } }}
                secondaryTypographyProps={{ sx: { color: '#00B0F0', fontSize: '0.8rem' } }}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Task notifications"
                secondary="Task assignments, progress updates, and completions"
                primaryTypographyProps={{ sx: { color: '#FFFFFF', fontSize: '0.9rem' } }}
                secondaryTypographyProps={{ sx: { color: '#00B0F0', fontSize: '0.8rem' } }}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="Security alerts"
                secondary="Failed login attempts, suspicious activity, and access violations"
                primaryTypographyProps={{ sx: { color: '#FFFFFF', fontSize: '0.9rem' } }}
                secondaryTypographyProps={{ sx: { color: '#00B0F0', fontSize: '0.8rem' } }}
              />
            </ListItem>
            <ListItem>
              <ListItemText
                primary="System notifications"
                secondary="Server status, database connections, and maintenance updates"
                primaryTypographyProps={{ sx: { color: '#FFFFFF', fontSize: '0.9rem' } }}
                secondaryTypographyProps={{ sx: { color: '#00B0F0', fontSize: '0.8rem' } }}
              />
            </ListItem>
          </List>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Notifications;
