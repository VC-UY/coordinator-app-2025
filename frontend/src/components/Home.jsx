import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Typography, Grid, Paper, Button, Stack, CircularProgress, Chip,
} from '@mui/material';
import GroupIcon from '@mui/icons-material/Group';
import AssignmentIcon from '@mui/icons-material/Assignment';
import ListAltIcon from '@mui/icons-material/ListAlt';
import HealthAndSafetyIcon from '@mui/icons-material/HealthAndSafety';
import PeopleIcon from '@mui/icons-material/People';
import { Link } from 'react-router-dom';
import {
  PieChart, Pie, Cell, Legend, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import {
  fetchManagersCount,
  fetchVolunteersCount,
  fetchWorkflowsCount,
  fetchTasksCount,
  fetchSystemHealth,
  fetchWorkflowsByStatus,
  fetchVolunteersByStatus,
  fetchWorkflowsWithTasks,
} from './apiHome';

const COLORS = {
  CREATED: '#00B0F0',
  RUNNING: '#00FF88',
  COMPLETED: '#00D4FF',
  FAILED: '#FF4444',
  PENDING: '#FFA500',
  available: '#00FF88',
  busy: '#FFA500',
  offline: '#888888',
};

const cardSx = {
  p: 3,
  borderRadius: 2,
  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
  border: '2px solid rgba(0, 180, 240, 0.3)',
};

const StatCard = ({ label, value, icon, to }) => (
  <Paper
    component={Link}
    to={to}
    elevation={0}
    sx={{
      ...cardSx,
      textDecoration: 'none',
      display: 'block',
      transition: 'transform 0.2s ease',
      '&:hover': { transform: 'translateY(-4px)', borderColor: '#00D4FF' },
    }}
  >
    <Stack direction="row" spacing={2} alignItems="center">
      <Box sx={{ color: '#00D4FF' }}>{icon}</Box>
      <Box>
        <Typography variant="h4" fontWeight={800} color="#fff">{value}</Typography>
        <Typography variant="body2" color="#00B0F0">{label}</Typography>
      </Box>
    </Stack>
  </Paper>
);

export default function Home() {
  const [stats, setStats] = useState({ managers: 0, volunteers: 0, workflows: 0, tasks: 0 });
  const [health, setHealth] = useState(null);
  const [workflowChart, setWorkflowChart] = useState([]);
  const [volunteerChart, setVolunteerChart] = useState([]);
  const [recentWorkflows, setRecentWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [managers, volunteers, workflows, tasks, healthData, wfChart, volChart, wfList] =
        await Promise.all([
          fetchManagersCount(),
          fetchVolunteersCount(),
          fetchWorkflowsCount(),
          fetchTasksCount(),
          fetchSystemHealth(),
          fetchWorkflowsByStatus(),
          fetchVolunteersByStatus(),
          fetchWorkflowsWithTasks(),
        ]);

      setStats({ managers, volunteers, workflows, tasks });
      setHealth(healthData);
      setWorkflowChart(wfChart);
      setVolunteerChart(volChart);
      setRecentWorkflows(wfList.slice(0, 8));
      setError('');
    } catch (err) {
      console.error(err);
      setError('Impossible de charger les donnees du tableau de bord.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, [load]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress sx={{ color: '#00D4FF' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Typography variant="h4" fontWeight={800} color="#fff" mb={1}>
        Tableau de bord
      </Typography>
      <Typography color="#00B0F0" mb={3}>
        Vue d ensemble du reseau VolunSys-UY1
      </Typography>

      {error && (
        <Paper sx={{ ...cardSx, mb: 3, borderColor: '#FF4444' }}>
          <Typography color="#FF4444">{error}</Typography>
          <Button onClick={load} sx={{ mt: 1, color: '#00D4FF' }}>Reessayer</Button>
        </Paper>
      )}

      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Managers" value={stats.managers} icon={<PeopleIcon fontSize="large" />} to="/manager" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Volontaires" value={stats.volunteers} icon={<GroupIcon fontSize="large" />} to="/volunteer" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Workflows" value={stats.workflows} icon={<AssignmentIcon fontSize="large" />} to="/workflows" />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard label="Taches" value={stats.tasks} icon={<ListAltIcon fontSize="large" />} to="/tasks" />
        </Grid>
      </Grid>

      <Paper elevation={0} sx={{ ...cardSx, mb: 3 }}>
        <Stack direction="row" spacing={1} alignItems="center" mb={2}>
          <HealthAndSafetyIcon sx={{ color: '#00D4FF' }} />
          <Typography variant="h6" color="#fff">Etat du systeme</Typography>
        </Stack>
        <Grid container spacing={2}>
          {[
            { label: 'Base de donnees', value: health?.details?.database || 'inconnu' },
            { label: 'Volontaires actifs', value: health?.details?.active_volunteers ?? 0 },
            { label: 'Erreurs recentes', value: health?.details?.recent_errors ?? 0 },
            { label: 'Statut global', value: health?.status || 'inconnu' },
            { label: 'Redis', value: health?.details?.redis_connection || 'inconnu' },
          ].map((item) => (
            <Grid item xs={12} sm={6} md={2.4} key={item.label}>
              <Box sx={{ p: 2, borderRadius: 2, background: 'rgba(0,180,240,0.08)', border: '1px solid rgba(0,180,240,0.2)' }}>
                <Typography variant="caption" color="#00B0F0">{item.label}</Typography>
                <Typography variant="h6" color="#fff">{item.value}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>

      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={{ ...cardSx, minHeight: 340 }}>
            <Typography variant="h6" color="#fff" mb={2}>Workflows par statut</Typography>
            {workflowChart.length === 0 ? (
              <Typography color="#94A3B8">Aucun workflow pour le moment.</Typography>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <PieChart>
                  <Pie data={workflowChart} dataKey="value" nameKey="name" outerRadius={90} label>
                    {workflowChart.map((entry) => (
                      <Cell key={entry.name} fill={COLORS[entry.name] || '#00B0F0'} />
                    ))}
                  </Pie>
                  <Legend />
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={{ ...cardSx, minHeight: 340 }}>
            <Typography variant="h6" color="#fff" mb={2}>Volontaires par statut</Typography>
            {volunteerChart.length === 0 ? (
              <Typography color="#94A3B8">Aucun volontaire pour le moment.</Typography>
            ) : (
              <ResponsiveContainer width="100%" height={260}>
                <BarChart data={volunteerChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,240,0.2)" />
                  <XAxis dataKey="name" stroke="#00B0F0" />
                  <YAxis stroke="#00B0F0" allowDecimals={false} />
                  <RechartsTooltip />
                  <Bar dataKey="value" name="Nombre">
                    {volunteerChart.map((entry) => (
                      <Cell key={entry.name} fill={COLORS[entry.name] || '#00D4FF'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>
      </Grid>

      <Paper elevation={0} sx={cardSx}>
        <Stack direction="row" justifyContent="space-between" alignItems="center" mb={2}>
          <Typography variant="h6" color="#fff">Workflows recents</Typography>
          <Button component={Link} to="/workflows" sx={{ color: '#00D4FF' }}>Voir tout</Button>
        </Stack>
        {recentWorkflows.length === 0 ? (
          <Typography color="#94A3B8">Aucun workflow enregistre.</Typography>
        ) : (
          <Stack spacing={1.5}>
            {recentWorkflows.map((wf) => (
              <Box
                key={wf.id}
                sx={{
                  p: 2,
                  borderRadius: 2,
                  background: 'rgba(0,180,240,0.08)',
                  border: '1px solid rgba(0,180,240,0.2)',
                  display: 'flex',
                  justifyContent: 'space-between',
                  gap: 2,
                  flexWrap: 'wrap',
                }}
              >
                <Box>
                  <Typography color="#fff" fontWeight={700}>{wf.name}</Typography>
                  <Typography variant="body2" color="#00B0F0">
                    Manager: {wf.owner_email || wf.owner_username || '—'}
                  </Typography>
                </Box>
                <Stack direction="row" spacing={1} alignItems="center">
                  <Chip size="small" label={wf.status} sx={{ color: '#fff', borderColor: '#00B0F0' }} variant="outlined" />
                  <Chip size="small" label={`${(wf.tasks || []).length} taches`} sx={{ color: '#00D4FF' }} />
                </Stack>
              </Box>
            ))}
          </Stack>
        )}
      </Paper>
    </Box>
  );
}
