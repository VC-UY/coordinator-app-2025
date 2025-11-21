import React, { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Tab,
  Tabs,
  Switch,
  FormControlLabel,
  FormGroup,
  TextField,
  Button,
  Divider,
  Card,
  CardContent,
  Grid,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Alert,
  Snackbar
} from '@mui/material';
import SettingsIcon from '@mui/icons-material/Settings';
import SaveIcon from '@mui/icons-material/Save';
import RestoreIcon from '@mui/icons-material/Restore';
import SecurityIcon from '@mui/icons-material/Security';
import NotificationsIcon from '@mui/icons-material/Notifications';
import DisplaySettingsIcon from '@mui/icons-material/DisplaySettings';
import StorageIcon from '@mui/icons-material/Storage';

const Settings = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [saveSuccess, setSaveSuccess] = useState(false);

  // General Settings
  const [generalSettings, setGeneralSettings] = useState({
    coordinatorName: 'Coordinator App',
    refreshInterval: 2000,
    maxRetries: 3,
    timeout: 5000,
    enableLogging: true,
    logLevel: 'info'
  });

  // Notification Settings
  const [notificationSettings, setNotificationSettings] = useState({
    enableNotifications: true,
    workflowNotifications: true,
    taskNotifications: true,
    securityNotifications: true,
    systemNotifications: true,
    emailNotifications: false,
    soundEnabled: false
  });

  // Display Settings
  const [displaySettings, setDisplaySettings] = useState({
    theme: 'dark',
    autoRefresh: true,
    showAnimations: true,
    compactMode: false,
    itemsPerPage: 10
  });

  // Security Settings
  const [securitySettings, setSecuritySettings] = useState({
    requireApproval: true,
    autoBlockSuspicious: false,
    maxLoginAttempts: 5,
    sessionTimeout: 3600,
    twoFactorAuth: false
  });

  // Database Settings
  const [databaseSettings, setDatabaseSettings] = useState({
    mongoHost: '127.0.0.1',
    mongoPort: 27017,
    databaseName: 'coordinator_db',
    redisHost: '127.0.0.1',
    redisPort: 6379
  });

  const handleTabChange = (event, newValue) => {
    setActiveTab(newValue);
  };

  const handleSave = () => {
    // In a real implementation, this would save to backend
    console.log('Saving settings...', {
      general: generalSettings,
      notifications: notificationSettings,
      display: displaySettings,
      security: securitySettings,
      database: databaseSettings
    });

    // Save to localStorage for persistence
    localStorage.setItem('coordinatorSettings', JSON.stringify({
      general: generalSettings,
      notifications: notificationSettings,
      display: displaySettings,
      security: securitySettings
    }));

    setSaveSuccess(true);
  };

  const handleReset = () => {
    if (window.confirm('Are you sure you want to reset all settings to default?')) {
      // Reset to default values
      setGeneralSettings({
        coordinatorName: 'Coordinator App',
        refreshInterval: 2000,
        maxRetries: 3,
        timeout: 5000,
        enableLogging: true,
        logLevel: 'info'
      });
      setNotificationSettings({
        enableNotifications: true,
        workflowNotifications: true,
        taskNotifications: true,
        securityNotifications: true,
        systemNotifications: true,
        emailNotifications: false,
        soundEnabled: false
      });
      setDisplaySettings({
        theme: 'dark',
        autoRefresh: true,
        showAnimations: true,
        compactMode: false,
        itemsPerPage: 10
      });
      setSecuritySettings({
        requireApproval: true,
        autoBlockSuspicious: false,
        maxLoginAttempts: 5,
        sessionTimeout: 3600,
        twoFactorAuth: false
      });

      localStorage.removeItem('coordinatorSettings');
      setSaveSuccess(true);
    }
  };

  // Load settings from localStorage on mount
  useEffect(() => {
    const savedSettings = localStorage.getItem('coordinatorSettings');
    if (savedSettings) {
      const settings = JSON.parse(savedSettings);
      if (settings.general) setGeneralSettings(settings.general);
      if (settings.notifications) setNotificationSettings(settings.notifications);
      if (settings.display) setDisplaySettings(settings.display);
      if (settings.security) setSecuritySettings(settings.security);
    }
  }, []);

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
        <SettingsIcon sx={{ fontSize: 64, color: '#00D4FF', mb: 2 }} />
        <Typography variant="h4" fontWeight={700} gutterBottom sx={{
          background: 'linear-gradient(135deg, #FFFFFF 0%, #00D4FF 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '0.5px'
        }}>
          Settings
        </Typography>
        <Typography variant="subtitle1" sx={{ color: '#00B0F0' }}>
          Configure system preferences and application settings
        </Typography>
      </Paper>

      {/* Action Buttons */}
      <Box sx={{ display: 'flex', justifyContent: 'flex-end', gap: 2, mb: 3 }}>
        <Button
          variant="outlined"
          startIcon={<RestoreIcon />}
          onClick={handleReset}
          sx={{
            borderColor: '#FFA500',
            color: '#FFA500',
            '&:hover': {
              borderColor: '#FF8C00',
              backgroundColor: 'rgba(255, 165, 0, 0.1)'
            }
          }}
        >
          Reset to Default
        </Button>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSave}
          sx={{
            background: 'linear-gradient(135deg, #00D4FF 0%, #00B0F0 100%)',
            color: '#001440',
            fontWeight: 600,
            '&:hover': {
              background: 'linear-gradient(135deg, #00B0F0 0%, #00D4FF 100%)'
            }
          }}
        >
          Save Changes
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
          <Tab label="General" icon={<SettingsIcon />} iconPosition="start" />
          <Tab label="Notifications" icon={<NotificationsIcon />} iconPosition="start" />
          <Tab label="Display" icon={<DisplaySettingsIcon />} iconPosition="start" />
          <Tab label="Security" icon={<SecurityIcon />} iconPosition="start" />
          <Tab label="Database" icon={<StorageIcon />} iconPosition="start" />
        </Tabs>
      </Paper>

      {/* Settings Content */}
      <Paper
        elevation={0}
        sx={{
          p: 4,
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 180, 240, 0.3)',
          borderRadius: 2,
          minHeight: 500
        }}
      >
        {/* General Settings */}
        {activeTab === 0 && (
          <Box>
            <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF', mb: 3 }}>
              General Settings
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Coordinator Name"
                  value={generalSettings.coordinatorName}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, coordinatorName: e.target.value })}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' },
                      '&:hover fieldset': { borderColor: '#00D4FF' },
                      '&.Mui-focused fieldset': { borderColor: '#00FF88' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Refresh Interval (ms)"
                  type="number"
                  value={generalSettings.refreshInterval}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, refreshInterval: parseInt(e.target.value) })}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' },
                      '&:hover fieldset': { borderColor: '#00D4FF' },
                      '&.Mui-focused fieldset': { borderColor: '#00FF88' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Max Retries"
                  type="number"
                  value={generalSettings.maxRetries}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, maxRetries: parseInt(e.target.value) })}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' },
                      '&:hover fieldset': { borderColor: '#00D4FF' },
                      '&.Mui-focused fieldset': { borderColor: '#00FF88' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Timeout (ms)"
                  type="number"
                  value={generalSettings.timeout}
                  onChange={(e) => setGeneralSettings({ ...generalSettings, timeout: parseInt(e.target.value) })}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' },
                      '&:hover fieldset': { borderColor: '#00D4FF' },
                      '&.Mui-focused fieldset': { borderColor: '#00FF88' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth sx={{
                  '& .MuiOutlinedInput-root': {
                    color: '#FFFFFF',
                    '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' },
                    '&:hover fieldset': { borderColor: '#00D4FF' },
                    '&.Mui-focused fieldset': { borderColor: '#00FF88' }
                  },
                  '& .MuiInputLabel-root': { color: '#00B0F0' }
                }}>
                  <InputLabel>Log Level</InputLabel>
                  <Select
                    value={generalSettings.logLevel}
                    label="Log Level"
                    onChange={(e) => setGeneralSettings({ ...generalSettings, logLevel: e.target.value })}
                  >
                    <MenuItem value="debug">Debug</MenuItem>
                    <MenuItem value="info">Info</MenuItem>
                    <MenuItem value="warning">Warning</MenuItem>
                    <MenuItem value="error">Error</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={generalSettings.enableLogging}
                      onChange={(e) => setGeneralSettings({ ...generalSettings, enableLogging: e.target.checked })}
                      sx={{
                        '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                        '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                      }}
                    />
                  }
                  label="Enable System Logging"
                  sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' } }}
                />
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Notification Settings */}
        {activeTab === 1 && (
          <Box>
            <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF', mb: 3 }}>
              Notification Preferences
            </Typography>
            <FormGroup>
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.enableNotifications}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, enableNotifications: e.target.checked })}
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                    }}
                  />
                }
                label="Enable Notifications"
                sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF', fontWeight: 600 }, mb: 2 }}
              />
              <Divider sx={{ my: 2, borderColor: 'rgba(0, 180, 240, 0.3)' }} />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.workflowNotifications}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, workflowNotifications: e.target.checked })}
                    disabled={!notificationSettings.enableNotifications}
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                    }}
                  />
                }
                label="Workflow Notifications"
                sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' }, mb: 1 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.taskNotifications}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, taskNotifications: e.target.checked })}
                    disabled={!notificationSettings.enableNotifications}
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                    }}
                  />
                }
                label="Task Notifications"
                sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' }, mb: 1 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.securityNotifications}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, securityNotifications: e.target.checked })}
                    disabled={!notificationSettings.enableNotifications}
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                    }}
                  />
                }
                label="Security Alerts"
                sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' }, mb: 1 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.systemNotifications}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, systemNotifications: e.target.checked })}
                    disabled={!notificationSettings.enableNotifications}
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                    }}
                  />
                }
                label="System Notifications"
                sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' }, mb: 1 }}
              />
              <Divider sx={{ my: 2, borderColor: 'rgba(0, 180, 240, 0.3)' }} />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.emailNotifications}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, emailNotifications: e.target.checked })}
                    disabled={!notificationSettings.enableNotifications}
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                    }}
                  />
                }
                label="Email Notifications"
                sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' }, mb: 1 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={notificationSettings.soundEnabled}
                    onChange={(e) => setNotificationSettings({ ...notificationSettings, soundEnabled: e.target.checked })}
                    disabled={!notificationSettings.enableNotifications}
                    sx={{
                      '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                      '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                    }}
                  />
                }
                label="Sound Notifications"
                sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' } }}
              />
            </FormGroup>
          </Box>
        )}

        {/* Display Settings */}
        {activeTab === 2 && (
          <Box>
            <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF', mb: 3 }}>
              Display & Interface
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth sx={{
                  '& .MuiOutlinedInput-root': {
                    color: '#FFFFFF',
                    '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' },
                    '&:hover fieldset': { borderColor: '#00D4FF' },
                    '&.Mui-focused fieldset': { borderColor: '#00FF88' }
                  },
                  '& .MuiInputLabel-root': { color: '#00B0F0' }
                }}>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={displaySettings.theme}
                    label="Theme"
                    onChange={(e) => setDisplaySettings({ ...displaySettings, theme: e.target.value })}
                  >
                    <MenuItem value="dark">Dark</MenuItem>
                    <MenuItem value="light">Light</MenuItem>
                    <MenuItem value="auto">Auto</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Items Per Page"
                  type="number"
                  value={displaySettings.itemsPerPage}
                  onChange={(e) => setDisplaySettings({ ...displaySettings, itemsPerPage: parseInt(e.target.value) })}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' },
                      '&:hover fieldset': { borderColor: '#00D4FF' },
                      '&.Mui-focused fieldset': { borderColor: '#00FF88' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={displaySettings.autoRefresh}
                        onChange={(e) => setDisplaySettings({ ...displaySettings, autoRefresh: e.target.checked })}
                        sx={{
                          '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                        }}
                      />
                    }
                    label="Auto-refresh Data"
                    sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' }, mb: 1 }}
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={displaySettings.showAnimations}
                        onChange={(e) => setDisplaySettings({ ...displaySettings, showAnimations: e.target.checked })}
                        sx={{
                          '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                        }}
                      />
                    }
                    label="Show Animations"
                    sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' }, mb: 1 }}
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={displaySettings.compactMode}
                        onChange={(e) => setDisplaySettings({ ...displaySettings, compactMode: e.target.checked })}
                        sx={{
                          '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                        }}
                      />
                    }
                    label="Compact Mode"
                    sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' } }}
                  />
                </FormGroup>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Security Settings */}
        {activeTab === 3 && (
          <Box>
            <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF', mb: 3 }}>
              Security & Access Control
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Max Login Attempts"
                  type="number"
                  value={securitySettings.maxLoginAttempts}
                  onChange={(e) => setSecuritySettings({ ...securitySettings, maxLoginAttempts: parseInt(e.target.value) })}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' },
                      '&:hover fieldset': { borderColor: '#00D4FF' },
                      '&.Mui-focused fieldset': { borderColor: '#00FF88' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Session Timeout (seconds)"
                  type="number"
                  value={securitySettings.sessionTimeout}
                  onChange={(e) => setSecuritySettings({ ...securitySettings, sessionTimeout: parseInt(e.target.value) })}
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' },
                      '&:hover fieldset': { borderColor: '#00D4FF' },
                      '&.Mui-focused fieldset': { borderColor: '#00FF88' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <FormGroup>
                  <FormControlLabel
                    control={
                      <Switch
                        checked={securitySettings.requireApproval}
                        onChange={(e) => setSecuritySettings({ ...securitySettings, requireApproval: e.target.checked })}
                        sx={{
                          '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                        }}
                      />
                    }
                    label="Require Manual Approval for New Clients"
                    sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' }, mb: 1 }}
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={securitySettings.autoBlockSuspicious}
                        onChange={(e) => setSecuritySettings({ ...securitySettings, autoBlockSuspicious: e.target.checked })}
                        sx={{
                          '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                        }}
                      />
                    }
                    label="Auto-block Suspicious Activity"
                    sx={{ '& .MuiFormControlLabel-label': { color: '#FFFFFF' }, mb: 1 }}
                  />
                  <FormControlLabel
                    control={
                      <Switch
                        checked={securitySettings.twoFactorAuth}
                        onChange={(e) => setSecuritySettings({ ...securitySettings, twoFactorAuth: e.target.checked })}
                        sx={{
                          '& .MuiSwitch-switchBase.Mui-checked': { color: '#00FF88' },
                          '& .MuiSwitch-switchBase.Mui-checked + .MuiSwitch-track': { backgroundColor: '#00FF88' }
                        }}
                      />
                    }
                    label="Enable Two-Factor Authentication (Coming Soon)"
                    disabled
                    sx={{ '& .MuiFormControlLabel-label': { color: '#888888' } }}
                  />
                </FormGroup>
              </Grid>
            </Grid>
          </Box>
        )}

        {/* Database Settings */}
        {activeTab === 4 && (
          <Box>
            <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF', mb: 3 }}>
              Database Configuration
            </Typography>
            <Alert severity="warning" sx={{ mb: 3, bgcolor: 'rgba(255, 165, 0, 0.1)', color: '#FFA500' }}>
              Changes to database settings require server restart. Contact your system administrator.
            </Alert>
            <Grid container spacing={3}>
              <Grid item xs={12}>
                <Typography variant="subtitle2" fontWeight={600} sx={{ color: '#00D4FF', mb: 2 }}>
                  MongoDB Settings
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="MongoDB Host"
                  value={databaseSettings.mongoHost}
                  disabled
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="MongoDB Port"
                  type="number"
                  value={databaseSettings.mongoPort}
                  disabled
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Database Name"
                  value={databaseSettings.databaseName}
                  disabled
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle2" fontWeight={600} sx={{ color: '#00D4FF', mb: 2, mt: 2 }}>
                  Redis Settings
                </Typography>
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Redis Host"
                  value={databaseSettings.redisHost}
                  disabled
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Redis Port"
                  type="number"
                  value={databaseSettings.redisPort}
                  disabled
                  sx={{
                    '& .MuiOutlinedInput-root': {
                      color: '#FFFFFF',
                      '& fieldset': { borderColor: 'rgba(0, 180, 240, 0.3)' }
                    },
                    '& .MuiInputLabel-root': { color: '#00B0F0' }
                  }}
                />
              </Grid>
            </Grid>
          </Box>
        )}
      </Paper>

      {/* Success Snackbar */}
      <Snackbar
        open={saveSuccess}
        autoHideDuration={3000}
        onClose={() => setSaveSuccess(false)}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSaveSuccess(false)}
          severity="success"
          sx={{ bgcolor: '#00FF88', color: '#001440', fontWeight: 600 }}
        >
          Settings saved successfully!
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Settings;
