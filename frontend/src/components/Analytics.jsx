
import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, CircularProgress, Grid, Tab, Tabs, Card, CardContent } from '@mui/material';
import { 
  PieChart, Pie, Cell, Legend, Tooltip as RechartsTooltip, ResponsiveContainer, 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, LineChart, Line, AreaChart, Area,
  RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, ScatterChart, Scatter
} from 'recharts';
import { 
  fetchWorkflowsByStatus, fetchVolunteersByStatus, fetchTaskPerformance,
  fetchResourceUtilization, fetchCommunicationStats
} from './apiHome';
import AssessmentIcon from '@mui/icons-material/Assessment';
import MemoryIcon from '@mui/icons-material/Memory';
import MessageIcon from '@mui/icons-material/Message';
import SpeedIcon from '@mui/icons-material/Speed';

function TabPanel(props) {
  const { children, value, index, ...other } = props;
  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`analytics-tabpanel-${index}`}
      aria-labelledby={`analytics-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ pt: 4 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

const BRAND_COLORS = {
  primary: '#002060',
  secondary: '#00B0F0',
  dark: '#001440',
  accent: '#00D4FF',
  white: '#FFFFFF',
  black: '#000000',
  gray: '#F5F7FA'
};

const STATUS_COLORS = {
  CREATED: '#002060',
  VALIDATED: '#00B0F0',
  SUBMITTED: '#00D4FF',
  SPLITTING: '#001440',
  ASSIGNING: '#002060',
  PENDING: '#00B0F0',
  RUNNING: '#00D4FF',
  PAUSED: '#001440',
  PARTIAL_FAILURE: '#002060',
  REASSIGNING: '#00B0F0',
  AGGREGATING: '#00D4FF',
  COMPLETED: '#001440',
  FAILED: '#002060',
  available: '#00D4FF',
  busy: '#00B0F0',
  offline: '#001440',
  maintenance: '#002060',
};

const Analytics = () => {
  const [tabValue, setTabValue] = useState(0);
  const [ setWorkflowStatusData] = useState([]);
  const [ setVolunteerStatusData] = useState([]);
  const [ setTaskPerformanceData] = useState([]);
  const [ setResourceUtilizationData] = useState([]);
  const [communicationStatsData, setCommunicationStatsData] = useState({
    hourlyData: [],
    messageTypes: []
  });
  const [loadingCharts, setLoadingCharts] = useState(true);

  const handleTabChange = (event, newValue) => {
    setTabValue(newValue);
  };

  useEffect(() => {
    setLoadingCharts(true);
    Promise.all([
      fetchWorkflowsByStatus(),
      fetchVolunteersByStatus(),
      fetchTaskPerformance(),
      fetchResourceUtilization(),
      fetchCommunicationStats()
    ]).then(([wfData, volData, taskData, resourceData, commData]) => {
      setWorkflowStatusData(wfData);
      setVolunteerStatusData(volData);
      setTaskPerformanceData(taskData);
      setResourceUtilizationData(resourceData);
      setCommunicationStatsData(commData);
      setLoadingCharts(false);
    }).catch(error => {
      console.error("Error fetching analytics data:", error);
      setLoadingCharts(false);
    });
  }, []);

  return (
    <Box sx={{ 
      p: { xs: 2, md: 4 }, 
      background: `linear-gradient(135deg, ${BRAND_COLORS.gray} 0%, ${BRAND_COLORS.white} 100%)`, 
      minHeight: '100vh' 
    }}>
      {/* Header avec animation */}
      <Paper 
        elevation={0} 
        sx={{ 
          p: 4, 
          mb: 4, 
          borderRadius: 4,
          background: `linear-gradient(135deg, ${BRAND_COLORS.primary} 0%, ${BRAND_COLORS.dark} 50%, ${BRAND_COLORS.secondary} 100%)`,
          color: BRAND_COLORS.white,
          position: 'relative',
          overflow: 'hidden',
          '&::before': {
            content: '""',
            position: 'absolute',
            top: '-50%',
            right: '-50%',
            width: '200%',
            height: '200%',
            background: `radial-gradient(circle, ${BRAND_COLORS.accent}22 0%, transparent 70%)`,
            animation: 'rotate 20s linear infinite',
          },
          '@keyframes rotate': {
            '0%': { transform: 'rotate(0deg)' },
            '100%': { transform: 'rotate(360deg)' }
          }
        }}
      >
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Typography variant="h3" fontWeight={700} gutterBottom sx={{ letterSpacing: 1 }}>
            VolunSys-UY1
          </Typography>
          <Typography variant="h6" sx={{ opacity: 0.95, fontWeight: 300, mt: 1 }}>
            La puissance collective au service du calcul scientifique
          </Typography>
        </Box>
      </Paper>

      {/* Tabs avec style moderne */}
      <Paper 
        elevation={0} 
        sx={{ 
          mb: 4, 
          borderRadius: 4,
          overflow: 'hidden',
          border: `1px solid ${BRAND_COLORS.secondary}22`
        }}
      >
        <Tabs 
          value={tabValue} 
          onChange={handleTabChange} 
          variant="fullWidth"
          sx={{
            bgcolor: BRAND_COLORS.white,
            '& .MuiTab-root': {
              color: BRAND_COLORS.primary,
              fontWeight: 600,
              py: 2.5,
              transition: 'all 0.3s ease',
              '&:hover': {
                bgcolor: `${BRAND_COLORS.secondary}11`,
                transform: 'translateY(-2px)'
              },
              '&.Mui-selected': {
                color: BRAND_COLORS.white,
                bgcolor: BRAND_COLORS.primary,
              }
            },
            '& .MuiTabs-indicator': {
              display: 'none'
            }
          }}
        >
          <Tab icon={<AssessmentIcon />} label="Vue d'ensemble" />
          <Tab icon={<SpeedIcon />} label="Performances" />
          <Tab icon={<MemoryIcon />} label="Ressources" />
          <Tab icon={<MessageIcon />} label="Communications" />
        </Tabs>

        {/* Status Overview Tab */}
        <TabPanel value={tabValue} index={0}>
          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Paper 
                  elevation={0} 
                  sx={{ 
                    p: 3, 
                    borderRadius: 3, 
                    height: '100%',
                    bgcolor: BRAND_COLORS.white,
                    border: `1px solid ${BRAND_COLORS.secondary}22`,
                    transition: 'all 0.3s ease',
                    '&:hover': {
                      boxShadow: `0 8px 32px ${BRAND_COLORS.secondary}33`,
                      transform: 'translateY(-4px)'
                    }
                  }}
                >
                  <Typography variant="h6" fontWeight={600} mb={3} color={BRAND_COLORS.primary}>
                    Résumé des communications
                  </Typography>
                  <Box sx={{ mt: 2 }}>
                    {loadingCharts ? (
                      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 300 }}>
                        <CircularProgress sx={{ color: BRAND_COLORS.secondary }} size={40} />
                      </Box>
                    ) : (
                      <Grid container spacing={2}>
                        {[
                          { 
                            title: 'Total Messages Aujourd\'hui', 
                            value: communicationStatsData.hourlyData?.reduce((sum, hour) => sum + (hour.total || 0), 0) || 0, 
                            color: BRAND_COLORS.primary,
                            gradient: `linear-gradient(135deg, ${BRAND_COLORS.primary} 0%, ${BRAND_COLORS.dark} 100%)`
                          },
                          { 
                            title: 'Messages Manager', 
                            value: communicationStatsData.hourlyData?.reduce((sum, hour) => sum + (hour.managerMessages || 0), 0) || 0, 
                            color: BRAND_COLORS.secondary,
                            gradient: `linear-gradient(135deg, ${BRAND_COLORS.secondary} 0%, ${BRAND_COLORS.accent} 100%)`
                          },
                          { 
                            title: 'Messages Volontaires', 
                            value: communicationStatsData.hourlyData?.reduce((sum, hour) => sum + (hour.volunteerMessages || 0), 0) || 0, 
                            color: BRAND_COLORS.accent,
                            gradient: `linear-gradient(135deg, ${BRAND_COLORS.accent} 0%, ${BRAND_COLORS.secondary} 100%)`
                          },
                          { 
                            title: 'Messages Système', 
                            value: communicationStatsData.hourlyData?.reduce((sum, hour) => sum + (hour.systemMessages || 0), 0) || 0, 
                            color: BRAND_COLORS.dark,
                            gradient: `linear-gradient(135deg, ${BRAND_COLORS.dark} 0%, ${BRAND_COLORS.primary} 100%)`
                          }
                        ].map((stat, index) => (
                          <Grid item xs={6} key={index}>
                            <Card 
                              sx={{ 
                                background: stat.gradient,
                                height: '100%',
                                borderRadius: 3,
                                position: 'relative',
                                overflow: 'hidden',
                                transition: 'all 0.3s ease',
                                '&:hover': {
                                  transform: 'translateY(-8px) scale(1.02)',
                                  boxShadow: `0 12px 40px ${stat.color}44`
                                },
                                '&::before': {
                                  content: '""',
                                  position: 'absolute',
                                  top: '-50%',
                                  right: '-50%',
                                  width: '200%',
                                  height: '200%',
                                  background: `radial-gradient(circle, ${BRAND_COLORS.white}11 0%, transparent 70%)`,
                                  animation: `rotate${index} 15s linear infinite`,
                                },
                                [`@keyframes rotate${index}`]: {
                                  '0%': { transform: 'rotate(0deg)' },
                                  '100%': { transform: 'rotate(360deg)' }
                                }
                              }}
                            >
                              <CardContent sx={{ position: 'relative', zIndex: 1 }}>
                                <Typography variant="subtitle2" sx={{ color: BRAND_COLORS.white, opacity: 0.9, fontWeight: 500 }} gutterBottom>
                                  {stat.title}
                                </Typography>
                                <Typography 
                                  variant="h3" 
                                  sx={{ 
                                    color: BRAND_COLORS.white, 
                                    fontWeight: 700,
                                    mt: 1,
                                    textShadow: `0 2px 10px ${BRAND_COLORS.black}33`
                                  }}
                                >
                                  {stat.value}
                                </Typography>
                              </CardContent>
                            </Card>
                          </Grid>
                        ))}
                      </Grid>
                    )}
                  </Box>
                </Paper>
              </Grid>
            </Grid>
          </Box>
        </TabPanel>
      </Paper>

      {/* Footer avec branding */}
      <Box 
        sx={{ 
          mt: 4, 
          p: 3, 
          textAlign: 'center',
          borderTop: `2px solid ${BRAND_COLORS.secondary}22`
        }}
      >
        <Typography variant="body2" sx={{ color: BRAND_COLORS.primary, fontWeight: 500 }}>
          VolunSys-UY1 - La puissance collective au service du calcul scientifique
        </Typography>
        <Typography variant="caption" sx={{ color: BRAND_COLORS.black, opacity: 0.6, mt: 1, display: 'block' }}>
          Plateforme de calcul distribué pour la recherche scientifique
        </Typography>
      </Box>
    </Box>
  );
};

export default Analytics;