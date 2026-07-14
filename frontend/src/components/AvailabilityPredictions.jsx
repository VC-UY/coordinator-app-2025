import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Typography, Paper, CircularProgress, Button, Chip, Stack, Table, TableHead,
  TableRow, TableCell, TableBody, TextField, TableContainer,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AxiosInstance from './axios';

const cardSx = {
  p: 2.5,
  borderRadius: 2,
  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
  border: '2px solid rgba(0, 180, 240, 0.3)',
};

function pct(v) {
  if (v == null || Number.isNaN(Number(v))) return '—';
  return `${(Number(v) * 100).toFixed(0)}%`;
}

function num(v, digits = 1) {
  if (v == null || Number.isNaN(Number(v))) return '—';
  return Number(v).toFixed(digits);
}

function launchLabel(row) {
  if (row.error === 'timeout' && row.hybrid == null && !row.prediction_detail?.hybrid) {
    return 'INDISPONIBLE';
  }
  if (row.launch == null && row.launch_assumed) return 'ASSUMÉ';
  if (row.launch == null) return '—';
  return row.launch ? 'OUI' : 'NON';
}

function sourceShort(row) {
  const s = row?.source || '';
  if (s === 'redis_probe') return 'Redis live';
  if (s === 'site_telemetry_fallback') return 'fallback site';
  if (s === 'timeout') return 'timeout';
  return s || '—';
}

function detailOf(row) {
  return row?.prediction_detail && Object.keys(row.prediction_detail).length
    ? row.prediction_detail
    : row || {};
}

function reasonOf(row) {
  const d = detailOf(row);
  if (d.launch_block_reason) return d.launch_block_reason;
  if (row.launch_block_reason) return row.launch_block_reason;
  if (row.source === 'site_telemetry_fallback') return 'redis_live_down';
  if (row.error && row.error !== '—') return String(row.error).slice(0, 40);
  if (row.launch) return 'ok';
  if (row.launch === false) return 'below_threshold';
  return '—';
}

export default function AvailabilityPredictions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [probeId, setProbeId] = useState('5ac7e694-b604-4dc9-9ba6-662f56be47c8');
  const [probing, setProbing] = useState(false);
  const [lastProbe, setLastProbe] = useState(null);

  const load = useCallback(async () => {
    try {
      const res = await AxiosInstance.get('/availability-predictions/?limit=5');
      setData(res.data);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Impossible de charger les predictions.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, [load]);

  const probeNow = async () => {
    if (!probeId.trim()) return;
    setProbing(true);
    try {
      const res = await AxiosInstance.post('/availability-predictions/probe/', {
        volunteer_id: probeId.trim(),
      });
      setLastProbe(res.data);
      await load();
    } catch (err) {
      setLastProbe({ error: err.message || 'echec' });
    } finally {
      setProbing(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
        <CircularProgress sx={{ color: '#00D4FF' }} />
      </Box>
    );
  }

  const latest = Object.entries(data?.latest_by_volunteer || {});

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" alignItems={{ sm: 'center' }} mb={2} gap={1}>
        <Box>
          <Typography variant="h5" sx={{ color: '#fff', fontWeight: 700 }}>
            Predictions 15 min
          </Typography>
          <Typography sx={{ color: '#94a3b8', mt: 0.5, fontSize: 14 }}>
            Une ligne par machine. Launch = hybrid ≥ seuil (soft gate assignation).
          </Typography>
        </Box>
        <Button startIcon={<RefreshIcon />} onClick={load} variant="outlined" sx={{ color: '#00D4FF', borderColor: '#00D4FF' }}>
          Actualiser
        </Button>
      </Stack>

      {error && <Typography color="error" mb={2}>{error}</Typography>}

      <Paper sx={{ ...cardSx, mb: 2 }}>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={1.5} alignItems={{ sm: 'center' }}>
          <TextField
            size="small"
            fullWidth
            placeholder="UUID volontaire"
            value={probeId}
            onChange={(e) => setProbeId(e.target.value)}
            sx={{ input: { color: '#fff' } }}
          />
          <Button variant="contained" onClick={probeNow} disabled={probing} sx={{ bgcolor: '#00B0F0', whiteSpace: 'nowrap' }}>
            {probing ? '…' : 'Sonder'}
          </Button>
        </Stack>
        {lastProbe && (
          <Typography sx={{ mt: 1, color: '#94a3b8', fontSize: 12 }}>
            {sourceShort(lastProbe)} · launch={launchLabel(lastProbe)} · hybrid={pct(detailOf(lastProbe).hybrid ?? lastProbe.hybrid)} · {reasonOf(lastProbe)}
          </Typography>
        )}
      </Paper>

      <Paper sx={cardSx}>
        {latest.length === 0 ? (
          <Typography sx={{ color: '#94a3b8' }}>Aucune sonde — cliquez « Sonder ».</Typography>
        ) : (
          <TableContainer sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#67e8f9' }}>Machine</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Hybrid</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>ARX</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>GRU</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>CPU</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>RAM</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Seuil</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Launch</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Source</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Pourquoi</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {latest.map(([vid, row]) => {
                  const dd = detailOf(row);
                  return (
                    <TableRow key={vid} hover>
                      <TableCell sx={{ color: '#e2e8f0', fontFamily: 'monospace', fontSize: 12 }}>
                        {(dd.machine_id || row.machine_id || vid).toString().slice(0, 18)}
                      </TableCell>
                      <TableCell sx={{ color: '#e2e8f0' }}>{pct(dd.hybrid ?? row.hybrid)}</TableCell>
                      <TableCell sx={{ color: '#e2e8f0' }}>{pct(dd.linear ?? row.linear)}</TableCell>
                      <TableCell sx={{ color: '#e2e8f0' }}>{pct(dd.gru ?? row.gru)}</TableCell>
                      <TableCell sx={{ color: '#e2e8f0' }}>{num(dd.cpu_percent_current ?? row.cpu_percent_current)}</TableCell>
                      <TableCell sx={{ color: '#e2e8f0' }}>{num(dd.ram_percent_used_current ?? row.ram_percent_used_current)}</TableCell>
                      <TableCell sx={{ color: '#e2e8f0' }}>{num(dd.launch_threshold ?? dd.threshold ?? row.launch_threshold, 2)}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={launchLabel(row)}
                          sx={{
                            bgcolor: row.launch ? 'rgba(0,255,136,0.2)' : 'rgba(255,80,80,0.2)',
                            color: '#fff',
                          }}
                        />
                      </TableCell>
                      <TableCell sx={{ color: '#94a3b8', fontSize: 12 }}>{sourceShort(row)}</TableCell>
                      <TableCell sx={{ color: '#fbbf24', fontSize: 12 }}>{reasonOf(row)}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>
    </Box>
  );
}
