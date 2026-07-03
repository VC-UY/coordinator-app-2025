import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Typography, Paper, CircularProgress, Grid, Stack, Button, Chip,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { fetchSystemHealth, fetchManagersCount, fetchVolunteersCount, fetchWorkflowsCount, fetchTasksCount } from './apiHome';

const cardSx = {
  p: 3,
  borderRadius: 2,
  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
  border: '2px solid rgba(0, 180, 240, 0.3)',
};

export default function SystemStatus() {
  const [health, setHealth] = useState(null);
  const [counts, setCounts] = useState({ managers: 0, volunteers: 0, workflows: 0, tasks: 0 });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const [healthData, managers, volunteers, workflows, tasks] = await Promise.all([
        fetchSystemHealth(),
        fetchManagersCount(),
        fetchVolunteersCount(),
        fetchWorkflowsCount(),
        fetchTasksCount(),
      ]);
      setHealth(healthData);
      setCounts({ managers, volunteers, workflows, tasks });
      setError('');
    } catch (err) {
      console.error(err);
      setError('Impossible de charger l etat systeme.');
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
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress sx={{ color: '#00D4FF' }} />
      </Box>
    );
  }

  const ok = health?.status === 'ok';

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} mb={3}>
        <Box>
          <Typography variant="h4" fontWeight={800} color="#fff">Etat systeme</Typography>
          <Typography color="#00B0F0">Sante du coordinateur et volumes reels</Typography>
        </Box>
        <Button startIcon={<RefreshIcon />} onClick={load} sx={{ color: '#00D4FF' }}>
          Actualiser
        </Button>
      </Stack>

      {error && <Typography color="#FF4444" mb={2}>{error}</Typography>}

      <Paper elevation={0} sx={{ ...cardSx, mb: 3 }}>
        <Stack direction="row" spacing={2} alignItems="center" mb={2}>
          <Typography variant="h6" color="#fff">Statut global</Typography>
          <Chip
            label={health?.status || 'inconnu'}
            sx={{ color: ok ? '#00FF88' : '#FFA500', borderColor: ok ? '#00FF88' : '#FFA500' }}
            variant="outlined"
          />
        </Stack>
        <Grid container spacing={2}>
          {[
            { label: 'Base de donnees', value: health?.details?.database },
            { label: 'Redis', value: health?.details?.redis_connection },
            { label: 'Volontaires actifs', value: health?.details?.active_volunteers },
            { label: 'Erreurs recentes', value: health?.details?.recent_errors },
          ].map((item) => (
            <Grid item xs={12} sm={6} md={3} key={item.label}>
              <Box sx={{ p: 2, borderRadius: 2, background: 'rgba(0,180,240,0.08)' }}>
                <Typography variant="caption" color="#00B0F0">{item.label}</Typography>
                <Typography variant="h6" color="#fff">{item.value ?? '—'}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>

      <Paper elevation={0} sx={cardSx}>
        <Typography variant="h6" color="#fff" mb={2}>Volumes</Typography>
        <Grid container spacing={2}>
          {[
            { label: 'Managers', value: counts.managers },
            { label: 'Volontaires', value: counts.volunteers },
            { label: 'Workflows', value: counts.workflows },
            { label: 'Taches', value: counts.tasks },
          ].map((item) => (
            <Grid item xs={12} sm={6} md={3} key={item.label}>
              <Box sx={{ p: 2, borderRadius: 2, background: 'rgba(0,180,240,0.08)' }}>
                <Typography variant="caption" color="#00B0F0">{item.label}</Typography>
                <Typography variant="h5" color="#fff">{item.value}</Typography>
              </Box>
            </Grid>
          ))}
        </Grid>
      </Paper>
    </Box>
  );
}
