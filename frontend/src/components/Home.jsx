import React, { useEffect, useState } from 'react';
import { Box, Typography, Grid, Paper, Button, Avatar, Stack, CircularProgress, Chip } from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import GroupIcon from '@mui/icons-material/Group';
import AssignmentIcon from '@mui/icons-material/Assignment';
import ListAltIcon from '@mui/icons-material/ListAlt';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import TrendingUpIcon from '@mui/icons-material/TrendingUp';
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
  const [stats, setStats] = useState({
    managers: 0,
    volunteers: 0,
    workflows: 0,
    tasks: 0
  });
  const [setActiveVolunteers] = useState([]);
  const [runningWorkflows, setRunningWorkflows] = useState([]);
  const [systemHealth, setSystemHealth] = useState(null);
  const [workflowStatusData, setWorkflowStatusData] = useState([]);
  const [volunteerStatusData, setVolunteerStatusData] = useState([]);
  const [loading, setLoading] = useState(true);

  const COLORS = {
    primary: '#002060',
    secondary: '#00B0F0',
    dark: '#001440',
    light: '#00D4FF',
  };

  const STATUS_COLORS = {
    CREATED: COLORS.primary,
    VALIDATED: COLORS.secondary,
    SUBMITTED: COLORS.light,
    SPLITTING: COLORS.dark,
    ASSIGNING: COLORS.primary,
    PENDING: COLORS.secondary,
    RUNNING: COLORS.light,
    PAUSED: COLORS.dark,
    PARTIAL_FAILURE: COLORS.primary,
    REASSIGNING: COLORS.secondary,
    AGGREGATING: COLORS.light,
    COMPLETED: COLORS.secondary,
    FAILED: COLORS.primary,
    available: COLORS.light,
    busy: COLORS.secondary,
    offline: COLORS.dark,
    maintenance: COLORS.primary,
  };

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
      setStats({ managers, volunteers, workflows, tasks });
      setActiveVolunteers(volunteerData);
      setRunningWorkflows(workflowsData);
      setSystemHealth(healthData);

      const [workflowsChartData, volunteersChartData] = chartsData;
      setWorkflowStatusData(workflowsChartData);
      setVolunteerStatusData(volunteersChartData);
      setLoading(false);
    } catch (error) {
      console.error('Error fetching dashboard data:', error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAllData();
    const interval = setInterval(fetchAllData, 2000);
    return () => clearInterval(interval);
  }, []);

  return (
    <Box sx={{ 
      minHeight: '100vh',
      background: `linear-gradient(135deg, ${COLORS.dark} 0%, ${COLORS.primary} 50%, ${COLORS.dark} 100%)`,
      p: { xs: 2, md: 4 },
      position: 'relative',
      overflow: 'hidden',
      '&::before': {
        content: '""',
        position: 'absolute',
        top: '-50%',
        right: '-10%',
        width: '600px',
        height: '600px',
        borderRadius: '50%',
        background: `radial-gradient(circle, ${COLORS.secondary}15 0%, transparent 70%)`,
        animation: 'pulse 8s ease-in-out infinite',
      },
      '&::after': {
        content: '""',
        position: 'absolute',
        bottom: '-30%',
        left: '-5%',
        width: '500px',
        height: '500px',
        borderRadius: '50%',
        background: `radial-gradient(circle, ${COLORS.light}10 0%, transparent 70%)`,
        animation: 'pulse 6s ease-in-out infinite 1s',
      },
      '@keyframes pulse': {
        '0%, 100%': {
          transform: 'scale(1)',
          opacity: 0.5,
        },
        '50%': {
          transform: 'scale(1.1)',
          opacity: 0.8,
        }
      },
      '@keyframes rotate': {
        from: { transform: 'rotate(0deg)' },
        to: { transform: 'rotate(360deg)' }
      },
      '@keyframes slideIn': {
        from: { 
          opacity: 0,
          transform: 'translateY(20px)'
        },
        to: {
          opacity: 1,
          transform: 'translateY(0)'
        }
      }
    }}>
      {/* Header Section */}
      <Box sx={{ 
        position: 'relative',
        zIndex: 1,
        mb: 4,
        textAlign: 'center',
        animation: 'slideIn 0.8s ease-out'
      }}>
        <Box sx={{ 
          display: 'inline-flex',
          alignItems: 'center',
          gap: 2,
          mb: 2,
          background: `linear-gradient(90deg, ${COLORS.secondary}20 0%, transparent 100%)`,
          borderRadius: '50px',
          px: 4,
          py: 2,
          backdropFilter: 'blur(10px)',
          border: `1px solid ${COLORS.secondary}30`,
        }}>
          <Box sx={{
            width: 60,
            height: 60,
            borderRadius: '50%',
            background: `linear-gradient(135deg, ${COLORS.secondary} 0%, ${COLORS.light} 100%)`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            animation: 'rotate 3s linear infinite',
            boxShadow: `0 0 30px ${COLORS.secondary}50`,
          }}>
            <TrendingUpIcon sx={{ fontSize: 35, color: 'white' }} />
          </Box>
          <Box sx={{ textAlign: 'left' }}>
            <Typography variant="h3" fontWeight={700} sx={{ 
              color: 'white',
              letterSpacing: '1px',
              textShadow: `0 0 20px ${COLORS.light}40`
            }}>
              VolunSys-UY1
            </Typography>
            <Typography variant="body1" sx={{ color: COLORS.light, fontWeight: 300 }}>
              La puissance collective au service du calcul scientifique
            </Typography>
          </Box>
        </Box>
      </Box>

      {/* Stats Grid */}
      <Grid container spacing={3} sx={{ mb: 4, position: 'relative', zIndex: 1 }}>
        {[
          { label: 'Managers', value: stats.managers, icon: <DashboardIcon />, gradient: `linear-gradient(135deg, ${COLORS.primary} 0%, ${COLORS.secondary} 100%)` },
          { label: 'Volunteers', value: stats.volunteers, icon: <GroupIcon />, gradient: `linear-gradient(135deg, ${COLORS.secondary} 0%, ${COLORS.light} 100%)` },
          { label: 'Workflows', value: stats.workflows, icon: <AssignmentIcon />, gradient: `linear-gradient(135deg, ${COLORS.light} 0%, ${COLORS.secondary} 100%)` },
          { label: 'Tasks', value: stats.tasks, icon: <ListAltIcon />, gradient: `linear-gradient(135deg, ${COLORS.dark} 0%, ${COLORS.primary} 100%)` },
        ].map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={stat.label}>
            <Paper 
              elevation={0}
              sx={{ 
                p: 3,
                borderRadius: '20px',
                background: stat.gradient,
                color: 'white',
                position: 'relative',
                overflow: 'hidden',
                border: `1px solid ${COLORS.light}20`,
                backdropFilter: 'blur(10px)',
                transition: 'all 0.3s ease',
                animation: `slideIn 0.6s ease-out ${index * 0.1}s both`,
                '&:hover': {
                  transform: 'translateY(-8px)',
                  boxShadow: `0 15px 40px ${COLORS.secondary}40`,
                },
                '&::before': {
                  content: '""',
                  position: 'absolute',
                  top: '-50%',
                  right: '-50%',
                  width: '200%',
                  height: '200%',
                  background: `radial-gradient(circle, ${COLORS.light}15 0%, transparent 70%)`,
                  animation: 'rotate 6s linear infinite',
                }
              }}
            >
              <Box sx={{ position: 'relative', zIndex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Avatar sx={{ 
                    bgcolor: 'rgba(255,255,255,0.2)', 
                    width: 56, 
                    height: 56,
                    backdropFilter: 'blur(10px)',
                  }}>
                    {stat.icon}
                  </Avatar>
                  <Box sx={{
                    width: 12,
                    height: 12,
                    borderRadius: '50%',
                    bgcolor: COLORS.light,
                    boxShadow: `0 0 15px ${COLORS.light}`,
                    animation: 'pulse 2s ease-in-out infinite',
                  }} />
                </Box>
                <Typography variant="h3" fontWeight={700} sx={{ mb: 0.5 }}>
                  {loading ? <CircularProgress size={24} sx={{ color: 'white' }} /> : stat.value}
                </Typography>
                <Typography variant="body2" sx={{ opacity: 0.9, fontWeight: 500, letterSpacing: '0.5px' }}>
                  {stat.label}
                </Typography>
              </Box>
            </Paper>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3} sx={{ position: 'relative', zIndex: 1 }}>
        {/* Running Workflows */}
        <Grid item xs={12} md={6}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 3,
              borderRadius: '20px',
              background: `linear-gradient(135deg, rgba(0,32,96,0.9) 0%, rgba(0,20,64,0.9) 100%)`,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${COLORS.secondary}30`,
              minHeight: 300,
              position: 'relative',
              overflow: 'hidden',
              animation: 'slideIn 0.8s ease-out 0.4s both',
            }}
          >
            <Box sx={{
              position: 'absolute',
              top: -50,
              right: -50,
              width: 200,
              height: 200,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${COLORS.secondary}10 0%, transparent 70%)`,
              animation: 'pulse 4s ease-in-out infinite',
            }} />
            <Stack direction="row" alignItems="center" spacing={2} mb={3} sx={{ position: 'relative', zIndex: 1 }}>
              <Box sx={{
                width: 48,
                height: 48,
                borderRadius: '12px',
                background: `linear-gradient(135deg, ${COLORS.secondary} 0%, ${COLORS.light} 100%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 0 20px ${COLORS.secondary}50`,
              }}>
                <PlayArrowIcon sx={{ color: 'white' }} />
              </Box>
              <Typography variant="h6" fontWeight={600} sx={{ color: 'white' }}>
                Running Workflows
              </Typography>
              {runningWorkflows.length > 0 && (
                <Chip 
                  label={runningWorkflows.length}
                  size="small"
                  sx={{ 
                    bgcolor: COLORS.light,
                    color: COLORS.dark,
                    fontWeight: 700,
                    animation: 'pulse 2s ease-in-out infinite',
                  }}
                />
              )}
            </Stack>
            <Box sx={{ position: 'relative', zIndex: 1 }}>
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress sx={{ color: COLORS.light }} />
                </Box>
              ) : runningWorkflows.length === 0 ? (
                <Box sx={{ 
                  textAlign: 'center', 
                  py: 4,
                  color: COLORS.light,
                  opacity: 0.7,
                }}>
                  <Typography variant="body2">No workflows currently running</Typography>
                </Box>
              ) : (
                <Stack spacing={2}>
                  {runningWorkflows.map((wf, idx) => (
                    <Box 
                      key={idx}
                      sx={{ 
                        p: 2,
                        borderRadius: '12px',
                        background: `linear-gradient(90deg, ${COLORS.secondary}15 0%, transparent 100%)`,
                        border: `1px solid ${COLORS.secondary}30`,
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          background: `linear-gradient(90deg, ${COLORS.secondary}25 0%, transparent 100%)`,
                          transform: 'translateX(5px)',
                        }
                      }}
                    >
                      <Typography variant="body1" sx={{ color: 'white', fontWeight: 500 }}>
                        {wf.name || wf.title || `Workflow ${idx + 1}`}
                      </Typography>
                      <Typography variant="caption" sx={{ color: COLORS.light, opacity: 0.8 }}>
                        Owner: {wf.owner?.username || 'Unknown'}
                      </Typography>
                    </Box>
                  ))}
                </Stack>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* System Health */}
        <Grid item xs={12} md={6}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 3,
              borderRadius: '20px',
              background: `linear-gradient(135deg, rgba(0,32,96,0.9) 0%, rgba(0,20,64,0.9) 100%)`,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${COLORS.light}30`,
              minHeight: 300,
              position: 'relative',
              overflow: 'hidden',
              animation: 'slideIn 0.8s ease-out 0.5s both',
            }}
          >
            <Box sx={{
              position: 'absolute',
              bottom: -50,
              left: -50,
              width: 200,
              height: 200,
              borderRadius: '50%',
              background: `radial-gradient(circle, ${COLORS.light}10 0%, transparent 70%)`,
              animation: 'pulse 4s ease-in-out infinite 1s',
            }} />
            <Stack direction="row" alignItems="center" spacing={2} mb={3} sx={{ position: 'relative', zIndex: 1 }}>
              <Box sx={{
                width: 48,
                height: 48,
                borderRadius: '12px',
                background: `linear-gradient(135deg, ${COLORS.light} 0%, ${COLORS.secondary} 100%)`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                boxShadow: `0 0 20px ${COLORS.light}50`,
              }}>
                <HealthAndSafetyIcon sx={{ color: 'white' }} />
              </Box>
              <Typography variant="h6" fontWeight={600} sx={{ color: 'white' }}>
                System Health
              </Typography>
            </Stack>
            <Box sx={{ position: 'relative', zIndex: 1 }}>
              {loading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
                  <CircularProgress sx={{ color: COLORS.light }} />
                </Box>
              ) : (
                <Grid container spacing={2}>
                  {[
                    { label: 'Database', value: systemHealth?.details?.database || 'Unknown' },
                    { label: 'Active Volunteers', value: systemHealth?.details?.active_volunteers || 0 },
                    { label: 'Recent Errors', value: systemHealth?.details?.recent_errors || 0 },
                    { label: 'Status', value: systemHealth?.status || 'Unknown' },
                  ].map((item, idx) => (
                    <Grid item xs={6} key={idx}>
                      <Box sx={{ 
                        p: 2,
                        borderRadius: '12px',
                        background: `linear-gradient(135deg, ${COLORS.primary}40 0%, ${COLORS.dark}40 100%)`,
                        border: `1px solid ${COLORS.secondary}20`,
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          transform: 'scale(1.05)',
                          boxShadow: `0 5px 20px ${COLORS.secondary}30`,
                        }
                      }}>
                        <Typography variant="caption" sx={{ color: COLORS.light, opacity: 0.8 }}>
                          {item.label}
                        </Typography>
                        <Typography variant="h6" fontWeight={600} sx={{ color: 'white', mt: 0.5 }}>
                          {item.value}
                        </Typography>
                      </Box>
                    </Grid>
                  ))}
                </Grid>
              )}
            </Box>
          </Paper>
        </Grid>

        {/* Charts */}
        <Grid item xs={12} md={6}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 3,
              borderRadius: '20px',
              background: `linear-gradient(135deg, rgba(0,32,96,0.9) 0%, rgba(0,20,64,0.9) 100%)`,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${COLORS.secondary}30`,
              minHeight: 400,
              animation: 'slideIn 0.8s ease-out 0.6s both',
            }}
          >
            <Typography variant="h6" fontWeight={600} sx={{ color: 'white', mb: 3 }}>
              Workflow Status
            </Typography>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                <CircularProgress sx={{ color: COLORS.light }} />
              </Box>
            ) : workflowStatusData.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8, color: COLORS.light, opacity: 0.7 }}>
                <Typography variant="body2">No data available</Typography>
              </Box>
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
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.name] || COLORS.secondary} />
                    ))}
                  </Pie>
                  <Legend wrapperStyle={{ color: 'white' }} />
                  <RechartsTooltip contentStyle={{ background: COLORS.dark, border: `1px solid ${COLORS.secondary}` }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 3,
              borderRadius: '20px',
              background: `linear-gradient(135deg, rgba(0,32,96,0.9) 0%, rgba(0,20,64,0.9) 100%)`,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${COLORS.light}30`,
              minHeight: 400,
              animation: 'slideIn 0.8s ease-out 0.7s both',
            }}
          >
            <Typography variant="h6" fontWeight={600} sx={{ color: 'white', mb: 3 }}>
              Volunteer Status
            </Typography>
            {loading ? (
              <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
                <CircularProgress sx={{ color: COLORS.light }} />
              </Box>
            ) : volunteerStatusData.length === 0 ? (
              <Box sx={{ textAlign: 'center', py: 8, color: COLORS.light, opacity: 0.7 }}>
                <Typography variant="body2">No data available</Typography>
              </Box>
            ) : (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={volunteerStatusData}>
                  <CartesianGrid strokeDasharray="3 3" stroke={`${COLORS.secondary}30`} />
                  <XAxis dataKey="name" stroke="white" />
                  <YAxis stroke="white" />
                  <RechartsTooltip contentStyle={{ background: COLORS.dark, border: `1px solid ${COLORS.light}` }} />
                  <Legend wrapperStyle={{ color: 'white' }} />
                  <Bar dataKey="value" name="Count" fill={COLORS.secondary}>
                    {volunteerStatusData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={STATUS_COLORS[entry.name] || COLORS.light} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        {/* Quick Actions */}
        <Grid item xs={12}>
          <Paper 
            elevation={0}
            sx={{ 
              p: 3,
              borderRadius: '20px',
              background: `linear-gradient(135deg, rgba(0,32,96,0.9) 0%, rgba(0,20,64,0.9) 100%)`,
              backdropFilter: 'blur(20px)',
              border: `1px solid ${COLORS.secondary}30`,
              animation: 'slideIn 0.8s ease-out 0.8s both',
            }}
          >
            <Typography variant="h6" fontWeight={600} sx={{ color: 'white', mb: 3 }}>
              Quick Actions
            </Typography>
            <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
              {[
                { label: 'View Managers', path: '/manager', color: COLORS.primary },
                { label: 'View Volunteers', path: '/volunteer', color: COLORS.secondary },
                { label: 'View Workflows', path: '/workflows', color: COLORS.light },
              ].map((action, idx) => (
                <Button
                  key={idx}
                  component={Link}
                  to={action.path}
                  variant="contained"
                  sx={{
                    flex: 1,
                    py: 1.5,
                    borderRadius: '12px',
                    background: `linear-gradient(135deg, ${action.color} 0%, ${COLORS.dark} 100%)`,
                    border: `1px solid ${action.color}50`,
                    color: 'white',
                    fontWeight: 600,
                    textTransform: 'none',
                    fontSize: '1rem',
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      background: `linear-gradient(135deg, ${COLORS.light} 0%, ${action.color} 100%)`,
                      transform: 'translateY(-3px)',
                      boxShadow: `0 10px 30px ${action.color}50`,
                    }
                  }}
                >
                  {action.label}
                </Button>
              ))}
            </Stack>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Home;