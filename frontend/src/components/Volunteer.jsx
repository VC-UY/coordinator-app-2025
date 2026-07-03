import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Typography, Paper, CircularProgress, Chip, Stack, Button,
  Table, TableBody, TableCell, TableHead, TableRow,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AxiosInstance from './axios';

const cardSx = {
  p: 3,
  borderRadius: 2,
  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
  border: '2px solid rgba(0, 180, 240, 0.3)',
};

const statusColor = (status) => {
  const map = { available: '#00FF88', busy: '#FFA500', offline: '#888888', maintenance: '#ffd600' };
  return map[status] || '#94A3B8';
};

export default function Volunteer() {
  const [volunteers, setVolunteers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const load = useCallback(async () => {
    try {
      const res = await AxiosInstance.get('volunteers/');
      setVolunteers(Array.isArray(res.data) ? res.data : []);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Impossible de charger les volontaires.');
      setVolunteers([]);
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

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" spacing={2} mb={3}>
        <Box>
          <Typography variant="h4" fontWeight={800} color="#fff">Volontaires</Typography>
          <Typography color="#00B0F0">Machines du reseau de calcul</Typography>
        </Box>
        <Button startIcon={<RefreshIcon />} onClick={load} sx={{ color: '#00D4FF' }}>
          Actualiser
        </Button>
      </Stack>

      {error && <Typography color="#FF4444" mb={2}>{error}</Typography>}

      <Paper elevation={0} sx={cardSx}>
        {volunteers.length === 0 ? (
          <Typography color="#94A3B8">Aucun volontaire enregistre.</Typography>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: '#00B0F0' }}>Nom</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Identifiant</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Statut</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {volunteers.map((volunteer) => {
                const status = volunteer.current_status || volunteer.status || 'unknown';
                return (
                  <TableRow key={volunteer.id}>
                    <TableCell sx={{ color: '#fff' }}>{volunteer.name || volunteer.username}</TableCell>
                    <TableCell sx={{ color: '#00B0F0' }}>{volunteer.username}</TableCell>
                    <TableCell>
                      <Chip
                        size="small"
                        label={status}
                        sx={{ color: statusColor(status), borderColor: statusColor(status) }}
                        variant="outlined"
                      />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        )}
      </Paper>
    </Box>
  );
}
