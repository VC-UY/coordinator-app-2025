import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Typography, Paper, CircularProgress, Chip, Stack, Button,
  Table, TableBody, TableCell, TableHead, TableRow,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { Link } from 'react-router-dom';
import AxiosInstance from './axios';

const cardSx = {
  p: 3,
  borderRadius: 2,
  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
  border: '2px solid rgba(0, 180, 240, 0.3)',
};

export default function Manager() {
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const res = await AxiosInstance.get('managers/');
      setManagers(Array.isArray(res.data) ? res.data : []);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Impossible de charger les managers.');
      setManagers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, [load]);

  const toggleStatus = async (manager) => {
    const next = manager.status === 'active' ? 'suspended' : 'active';
    try {
      await AxiosInstance.patch(`managers/${manager.id}/`, { status: next });
      await load();
    } catch (err) {
      console.error(err);
      setError('Echec de la mise a jour du statut.');
    }
  };

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
          <Typography variant="h4" fontWeight={800} color="#fff">Managers</Typography>
          <Typography color="#00B0F0">Utilisateurs et leurs workflows</Typography>
        </Box>
        <Button startIcon={<RefreshIcon />} onClick={load} sx={{ color: '#00D4FF' }}>
          Actualiser
        </Button>
      </Stack>

      {error && <Typography color="#FF4444" mb={2}>{error}</Typography>}

      <Paper elevation={0} sx={cardSx}>
        {managers.length === 0 ? (
          <Typography color="#94A3B8">Aucun manager enregistre.</Typography>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: '#00B0F0' }}>Nom</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Email</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Statut</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Workflows</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {managers.map((manager) => (
                <TableRow key={manager.id}>
                  <TableCell sx={{ color: '#fff' }}>{manager.username}</TableCell>
                  <TableCell sx={{ color: '#00B0F0' }}>{manager.email}</TableCell>
                  <TableCell>
                    <Chip
                      size="small"
                      label={manager.status}
                      sx={{
                        color: manager.status === 'active' ? '#00FF88' : '#FFA500',
                        borderColor: manager.status === 'active' ? '#00FF88' : '#FFA500',
                      }}
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell sx={{ color: '#fff' }}>{manager.workflow_count ?? 0}</TableCell>
                  <TableCell>
                    <Stack direction="row" spacing={1}>
                      <Button
                        component={Link}
                        to={`/workflows?manager=${encodeURIComponent(manager.email || manager.id)}`}
                        size="small"
                        sx={{ color: '#00D4FF' }}
                      >
                        Workflows
                      </Button>
                      <Button
                        component={Link}
                        to={`/tasks?manager=${manager.id}`}
                        size="small"
                        sx={{ color: '#00D4FF' }}
                      >
                        Taches
                      </Button>
                      <Button size="small" onClick={() => toggleStatus(manager)} sx={{ color: '#FFA500' }}>
                        {manager.status === 'active' ? 'Suspendre' : 'Activer'}
                      </Button>
                    </Stack>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>
    </Box>
  );
}
