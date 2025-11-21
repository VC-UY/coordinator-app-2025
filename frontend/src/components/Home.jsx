import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Paper, Button, Avatar, Stack, Divider, CircularProgress, Tooltip } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import GroupIcon from '@mui/icons-material/Group';
import AssignmentIcon from '@mui/icons-material/Assignment';
import ListAltIcon from '@mui/icons-material/ListAlt';
import NotificationsActiveIcon from '@mui/icons-material/NotificationsActive';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import { Link } from 'react-router-dom';
import {
  fetchManagersCount,
  fetchVolunteersCount,
  fetchWorkflowsCount,
  fetchTasksCount,
  fetchActiveVolunteers,
  fetchRunningWorkflows,
  fetchSystemHealth,
  fetchWorkflowsByStatus,
  fetchVolunteersByStatus
} from './apiHome';
import { PieChart, Pie, Cell, Legend, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, XAxis, YAxis, CartesianGrid } from 'recharts';

const Home = () => {
  // State for dashboard stats
  const [stats, setStats] = useState({
    managers: 0,
    volunteers: 0,
    workflows: 0,
    tasks: 0
  });
  const [loadingStats, setLoadingStats] = useState(true);
  const [activeVolunteers, setActiveVolunteers] = useState([]);
  const [loadingVolunteers, setLoadingVolunteers] = useState(true);
  const [errorVolunteers, setErrorVolunteers] = useState(null);
  const [runningWorkflows, setRunningWorkflows] = useState([]);
  const [loadingRunningWorkflows, setLoadingRunningWorkflows] = useState(true);
  const [errorRunningWorkflows, setErrorRunningWorkflows] = useState(null);
  const [systemHealth, setSystemHealth] = useState(null);
  const [loadingHealth, setLoadingHealth] = useState(true);
  const [errorHealth, setErrorHealth] = useState(null);
  const [workflowStatusData, setWorkflowStatusData] = useState([]);
  const [volunteerStatusData, setVolunteerStatusData] = useState([]);
  const [loadingCharts, setLoadingCharts] = useState(true);

  // Color mapping for statuses - Updated with new color scheme
  const STATUS_COLORS = {
    CREATED: '#00B0F0',
    VALIDATED: '#00D4FF',
    SUBMITTED: '#42a5f5',
    SPLITTING: '#7e57c2',
    ASSIGNING: '#8d6e63',
    PENDING: '#FFA500',
    RUNNING: '#00FF88',
    PAUSED: '#ffd600',
    PARTIAL_FAILURE: '#fbc02d',
    REASSIGNING: '#00bcd4',
    AGGREGATING: '#ab47bc',
    COMPLETED: '#00FF88',
    FAILED: '#FF4444',
    available: '#00FF88',
    busy: '#FFA500',
    offline: '#888888',
    maintenance: '#ffd600',
  };

  // Function to fetch all dashboard data
  const fetchAllData = async () => {
    try {
      const [statsData, volunteerData, workflowsData, healthData, chartsData] = await Promise.all([
        Promise.all([
          fetchManagersCount(),
          fetchVolunteersCount(),
          fetchWorkflowsCount(),
          fetchTasksCount()
        ]),
        fetchActiveVolunteers(),
        fetchRunningWorkflows(),
        fetchSystemHealth(),
        Promise.all([
          fetchWorkflowsByStatus(),
          fetchVolunteersByStatus()
        ])
      ]);

      const [managers, volunteers, workflows, tasks] = statsData;
      const currentStats = { managers, volunteers, workflows, tasks };
      if (JSON.stringify(currentStats) !== JSON.stringify(stats)) {
        setStats(currentStats);
      }

      if (JSON.stringify(volunteerData) !== JSON.stringify(activeVolunteers)) {
        setActiveVolunteers(volunteerData);
      }

      if (JSON.stringify(workflowsData) !== JSON.stringify(runningWorkflows)) {
        setRunningWorkflows(workflowsData);
      }

      if (JSON.stringify(healthData) !== JSON.stringify(systemHealth)) {
        setSystemHealth(healthData);
      }

      const [workflowsChartData, volunteersChartData] = chartsData;
      if (JSON.stringify(workflowsChartData) !== JSON.stringify(workflowStatusData)) {
        setWorkflowStatusData(workflowsChartData);
      }
      if (JSON.stringify(volunteersChartData) !== JSON.stringify(volunteerStatusData)) {
        setVolunteerStatusData(volunteersChartData);
      }

    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      // Ne pas utiliser de données de fallback hardcodées
      setErrorVolunteers('Failed to load data');
      setErrorRunningWorkflows('Failed to load data');
      setErrorHealth('Failed to load data');
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ 
      p: { xs: 2, md: 4 }, 
      background: 'linear-gradient(180deg, #001440 0%, #002060 50%, #001440 100%)', 
      minHeight: '100vh' 
    }}>
      {/* Welcome Section */}
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
          color: 'white',
          position: 'relative',
          overflow: 'hidden'
        }}
      >
        <Box sx={{
          position: 'absolute',
          top: 0,
          right: 0,
          width: 256,
          height: 256,
          borderRadius: '50%',
          opacity: 0.1,
          background: 'radial-gradient(circle, rgba(0, 212, 255, 0.3) 0%, transparent 70%)',
          animation: 'pulse 4s ease-in-out infinite'
        }} />
        
        <Typography variant="h4" fontWeight={700} gutterBottom sx={{
          background: 'linear-gradient(135deg, #FFFFFF 0%, #00D4FF 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '0.5px'
        }}>
          Welcome to Coordinator App
        </Typography>
        <Typography variant="subtitle1" sx={{ color: '#00B0F0' }}>
          Manage distributed volunteers, workflows, and tasks with ease.
        </Typography>
      </Paper>

      {/* Quick Stats Section */}
      <Grid container spacing={3} justifyContent="center" mb={4}>
        {[
          { label: 'Managers', value: stats.managers, icon: <DashboardIcon />, color: '#00D4FF' },
          { label: 'Volunteers', value: stats.volunteers, icon: <GroupIcon />, color: '#00FF88' }, 
          { label: 'Workflows', value: stats.workflows, icon: <AssignmentIcon />, color: '#00B0F0' },
          { label: 'Tasks', value: stats.tasks, icon: <ListAltIcon />, color: '#FFA500' },
        ].map((stat) => (
          <Grid item xs={6} sm={3} key={stat.label}>
            <Paper 
              elevation={0}
              sx={{ 
                p: 3, 
                display: 'flex', 
                flexDirection: 'column', 
                alignItems: 'center', 
                borderRadius: 2,
                background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
                backdropFilter: 'blur(20px)',
                border: '2px solid rgba(0, 180, 240, 0.3)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  borderColor: stat.color,
                  boxShadow: `0 12px 40px ${stat.color}50`
                }
              }}
            >
              <Avatar sx={{ 
                bgcolor: `${stat.color}20`, 
                color: stat.color, 
                mb: 2, 
                width: 56, 
                height: 56,
                border: `2px solid ${stat.color}40`
              }}>
                {stat.icon}
              </Avatar>
              <Typography variant="h4" fontWeight={700} sx={{ color: '#FFFFFF', mb: 0.5 }}>
                {stat.value}
              </Typography>
              <Typography variant="body2" sx={{ color: '#00B0F0', letterSpacing: '0.3px' }}>
                {stat.label}
              </Typography>
            </Paper>
          </Grid>
        ))}
      </Grid>
      
      {/* Running Workflows Widget */}
      <Paper 
        elevation={0}
        sx={{ 
          p: 3, 
          mb: 4, 
          borderRadius: 2,
          background: 'linear-gradient(135deg, rgba(255, 165, 0, 0.1) 0%, rgba(255, 140, 0, 0.05) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(255, 165, 0, 0.3)'
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1} mb={2}>
          <PlayArrowIcon sx={{ color: '#FFA500' }} />
          <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF', letterSpacing: '0.3px' }}>
            Running Workflows
          </Typography>
        </Stack>
        {runningWorkflows.length === 0 ? (
          <Typography variant="body2" sx={{ color: '#00B0F0' }}>
            No workflows currently running.
          </Typography>
        ) : (
          <Stack spacing={1.5}>
            {runningWorkflows.map((wf, idx) => (
              <Box key={idx} sx={{
                p: 2,
                borderRadius: 1.5,
                background: 'rgba(0, 180, 240, 0.1)',
                border: '1px solid rgba(0, 180, 240, 0.2)',
                transition: 'all 0.3s ease',
                '&:hover': {
                  background: 'rgba(0, 180, 240, 0.15)',
                  borderColor: '#00D4FF',
                  transform: 'translateX(8px)'
                }
              }}>
                <Typography variant="body2" sx={{ color: '#FFFFFF', fontWeight: 500 }}>
                  {wf.name || wf.title || wf.id || JSON.stringify(wf)}
                </Typography>
              </Box>
            ))}
          </Stack>
        )}
      </Paper>

      {/* Quick Actions Section */}
      <Paper 
        elevation={0}
        sx={{ 
          p: 3, 
          mb: 4, 
          borderRadius: 2,
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 180, 240, 0.3)'
        }}
      >
        <Typography variant="h6" fontWeight={600} mb={2.5} sx={{ 
          color: '#FFFFFF',
          letterSpacing: '0.3px'
        }}>
          Quick Actions
        </Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          {[
            { to: '/manager', label: 'View Managers', color: '#00D4FF' },
            { to: '/volunteer', label: 'View Volunteers', color: '#00FF88' },
            { to: '/workflows', label: 'View Workflows', color: '#00B0F0' }
          ].map((action, idx) => (
            <Button 
              key={idx}
              variant="contained" 
              component={Link} 
              to={action.to}
              sx={{
                background: `linear-gradient(135deg, ${action.color} 0%, ${action.color}CC 100%)`,
                color: action.color === '#00FF88' ? '#001440' : '#FFFFFF',
                fontWeight: 600,
                letterSpacing: '0.3px',
                borderRadius: 2,
                border: `2px solid ${action.color}40`,
                boxShadow: `0 4px 16px ${action.color}30`,
                transition: 'all 0.3s ease',
                '&:hover': {
                  background: `linear-gradient(135deg, ${action.color}CC 0%, ${action.color} 100%)`,
                  transform: 'translateY(-2px)',
                  boxShadow: `0 8px 24px ${action.color}50`
                }
              }}
            >
              {action.label}
            </Button>
          ))}
        </Stack>
      </Paper>

      {/* System Health */}
      <Paper 
        elevation={0}
        sx={{ 
          p: 3, 
          mb: 4, 
          borderRadius: 2,
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 180, 240, 0.3)'
        }}
      >
        <Stack direction="row" alignItems="center" spacing={1} mb={3}>
          <HealthAndSafetyIcon sx={{ 
            color: loadingHealth ? '#888888' : systemHealth?.status === 'ok' ? '#00FF88' : '#FFA500' 
          }} />
          <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF', letterSpacing: '0.3px' }}>
            System Health
          </Typography>
        </Stack>
        {loadingHealth ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress size={40} sx={{ color: '#00D4FF' }} />
          </Box>
        ) : errorHealth ? (
          <Typography variant="body2" sx={{ color: '#FF4444' }}>{errorHealth}</Typography>
        ) : (
          <Grid container spacing={2}>
            {[
              { 
                label: 'Database', 
                value: systemHealth?.details?.database || 'Unknown',
                color: systemHealth?.details?.database === 'connected' ? '#00FF88' : '#FF4444'
              },
              { 
                label: 'Active Volunteers', 
                value: systemHealth?.details?.active_volunteers || 0,
                color: '#00D4FF'
              },
              { 
                label: 'Recent Errors', 
                value: systemHealth?.details?.recent_errors || 0,
                color: systemHealth?.details?.recent_errors > 0 ? '#FF4444' : '#00FF88'
              },
              { 
                label: 'Overall Status', 
                value: systemHealth?.status || 'Unknown',
                color: systemHealth?.status === 'ok' ? '#00FF88' : '#FFA500'
              }
            ].map((item, idx) => (
              <Grid item xs={12} sm={6} md={3} key={idx}>
                <Paper 
                  elevation={0}
                  sx={{ 
                    p: 2.5, 
                    borderRadius: 2,
                    background: 'rgba(0, 180, 240, 0.05)',
                    border: '1px solid rgba(0, 180, 240, 0.2)',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      background: 'rgba(0, 180, 240, 0.1)',
                      borderColor: item.color,
                      transform: 'translateY(-4px)'
                    }
                  }}
                >
                  <Typography variant="body2" sx={{ color: '#00B0F0', mb: 1, letterSpacing: '0.3px' }}>
                    {item.label}
                  </Typography>
                  <Typography variant="h6" fontWeight={600} sx={{ color: item.color }}>
                    {item.value}
                  </Typography>
                </Paper>
              </Grid>
            ))}
          </Grid>
        )}
      </Paper>

      {/* Analytics Section */}
      <Grid container spacing={3} mb={4}>
        {/* Workflow Status Chart */}
        <Grid item xs={12} md={6}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 3, 
              borderRadius: 2, 
              height: '100%',
              background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
              backdropFilter: 'blur(20px)',
              border: '2px solid rgba(0, 180, 240, 0.3)'
            }}
          >
            <Typography variant="h6" fontWeight={600} mb={3} sx={{ 
              color: '#FFFFFF',
              letterSpacing: '0.3px'
            }}>
              Workflow Status Distribution
            </Typography>
            {loadingCharts ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                <CircularProgress size={40} sx={{ color: '#00D4FF' }} />
              </Box>
            ) : workflowStatusData.length === 0 ? (
              <Typography variant="body2" sx={{ color: '#00B0F0' }}>
                No workflow data available.
              </Typography>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={workflowStatusData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={90}
                    fill="#8884d8"
                    dataKey="value"
                    nameKey="name"
                    label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                  >
                    {workflowStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.name] || '#00B0F0'} />
                    ))}
                  </Pie>
                  <Legend wrapperStyle={{ color: '#FFFFFF' }} />
                  <RechartsTooltip 
                    contentStyle={{ 
                      background: 'rgba(0, 20, 64, 0.95)', 
                      border: '2px solid rgba(0, 180, 240, 0.3)',
                      borderRadius: '8px',
                      color: '#FFFFFF'
                    }} 
                  />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        {/* Volunteer Status Chart */}
        <Grid item xs={12} md={6}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 3, 
              borderRadius: 2, 
              height: '100%',
              background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
              backdropFilter: 'blur(20px)',
              border: '2px solid rgba(0, 180, 240, 0.3)'
            }}
          >
            <Typography variant="h6" fontWeight={600} mb={3} sx={{ 
              color: '#FFFFFF',
              letterSpacing: '0.3px'
            }}>
              Volunteer Status Distribution
            </Typography>
            {loadingCharts ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                <CircularProgress size={40} sx={{ color: '#00D4FF' }} />
              </Box>
            ) : volunteerStatusData.length === 0 ? (
              <Typography variant="body2" sx={{ color: '#00B0F0' }}>
                No volunteer data available.
              </Typography>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart
                  data={volunteerStatusData}
                  margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0, 180, 240, 0.2)" />
                  <XAxis dataKey="name" stroke="#00B0F0" />
                  <YAxis stroke="#00B0F0" />
                  <RechartsTooltip 
                    contentStyle={{ 
                      background: 'rgba(0, 20, 64, 0.95)', 
                      border: '2px solid rgba(0, 180, 240, 0.3)',
                      borderRadius: '8px',
                      color: '#FFFFFF'
                    }} 
                  />
                  <Legend wrapperStyle={{ color: '#FFFFFF' }} />
                  <Bar dataKey="value" name="Count" fill="#00D4FF" radius={[8, 8, 0, 0]}>
                    {volunteerStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.name] || '#00B0F0'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Home;