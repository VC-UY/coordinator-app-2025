import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Typography, Paper, CircularProgress, Grid, Stack, Button,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import {
  PieChart, Pie, Cell, Legend, Tooltip as RechartsTooltip, ResponsiveContainer,
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
} from 'recharts';
import {
  fetchWorkflowsByStatus,
  fetchVolunteersByStatus,
  fetchTaskPerformance,
  fetchResourceUtilization,
} from './apiHome';

const cardSx = {
  p: 3,
  borderRadius: 2,
  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
  border: '2px solid rgba(0, 180, 240, 0.3)',
  minHeight: 320,
};

const COLORS = ['#00B0F0', '#00D4FF', '#00FF88', '#FFA500', '#FF4444', '#DA70D6'];

export default function Analytics() {
  const [workflowChart, setWorkflowChart] = useState([]);
  const [volunteerChart, setVolunteerChart] = useState([]);
  const [taskPerf, setTaskPerf] = useState([]);
  const [resources, setResources] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [wf, vol, perf, res] = await Promise.all([
        fetchWorkflowsByStatus(),
        fetchVolunteersByStatus(),
        fetchTaskPerformance(),
        fetchResourceUtilization(),
      ]);
      setWorkflowChart(wf);
      setVolunteerChart(vol);
      setTaskPerf(perf);
      setResources(res);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Impossible de charger les analyses.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress sx={{ color: '#00D4FF' }} />
      </Box>
    );
  }

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} mb={3}>
        <Box>
          <Typography variant="h4" fontWeight={800} color="#fff">Analyses</Typography>
          <Typography color="#00B0F0">Donnees reelles du coordinateur</Typography>
        </Box>
        <Button startIcon={<RefreshIcon />} onClick={load} sx={{ color: '#00D4FF' }}>
          Actualiser
        </Button>
      </Stack>

      {error && <Typography color="#FF4444" mb={2}>{error}</Typography>}

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={cardSx}>
            <Typography variant="h6" color="#fff" mb={2}>Workflows par statut</Typography>
            {workflowChart.length === 0 ? (
              <Typography color="#94A3B8">Aucune donnee.</Typography>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie data={workflowChart} dataKey="value" nameKey="name" outerRadius={80} label>
                    {workflowChart.map((entry, index) => (
                      <Cell key={entry.name} fill={COLORS[index % COLORS.length]} />
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
          <Paper elevation={0} sx={cardSx}>
            <Typography variant="h6" color="#fff" mb={2}>Volontaires par statut</Typography>
            {volunteerChart.length === 0 ? (
              <Typography color="#94A3B8">Aucune donnee.</Typography>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={volunteerChart}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,240,0.2)" />
                  <XAxis dataKey="name" stroke="#00B0F0" />
                  <YAxis stroke="#00B0F0" allowDecimals={false} />
                  <RechartsTooltip />
                  <Bar dataKey="value" fill="#00D4FF" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={cardSx}>
            <Typography variant="h6" color="#fff" mb={2}>Performance des taches</Typography>
            {taskPerf.length === 0 ? (
              <Typography color="#94A3B8">Aucune tache terminee pour le moment.</Typography>
            ) : (
              <ResponsiveContainer width="100%" height={240}>
                <BarChart data={taskPerf}>
                  <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,180,240,0.2)" />
                  <XAxis dataKey="name" stroke="#00B0F0" />
                  <YAxis stroke="#00B0F0" />
                  <RechartsTooltip />
                  <Bar dataKey="count" name="Nombre" fill="#00B0F0" />
                  <Bar dataKey="successRate" name="Reussite %" fill="#00FF88" />
                </BarChart>
              </ResponsiveContainer>
            )}
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper elevation={0} sx={cardSx}>
            <Typography variant="h6" color="#fff" mb={2}>Volontaires (etat reel)</Typography>
            {resources.length === 0 ? (
              <Typography color="#94A3B8">Aucun volontaire enregistre.</Typography>
            ) : (
              <Stack spacing={1} sx={{ maxHeight: 240, overflow: 'auto' }}>
                {resources.map((item) => (
                  <Box
                    key={item.id || item.name}
                    sx={{
                      p: 1.5,
                      borderRadius: 1,
                      background: 'rgba(0,180,240,0.08)',
                      display: 'flex',
                      justifyContent: 'space-between',
                    }}
                  >
                    <Typography color="#fff">{item.name || item.username}</Typography>
                    <Typography color="#00B0F0">{item.status}</Typography>
                  </Box>
                ))}
              </Stack>
            )}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}
