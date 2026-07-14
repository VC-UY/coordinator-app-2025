import React, { useCallback, useEffect, useState } from 'react';
import {
  Box, Typography, Paper, CircularProgress, Button, Chip, Stack, Table, TableHead,
  TableRow, TableCell, TableBody, TextField, TableContainer,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import AxiosInstance from './axios';

const cardSx = {
  p: 3,
  borderRadius: 2,
  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
  border: '2px solid rgba(0, 180, 240, 0.3)',
};

function pct(v) {
  if (v == null || Number.isNaN(Number(v))) return '—';
  return `${(Number(v) * 100).toFixed(0)} %`;
}

function num(v, digits = 1) {
  if (v == null || Number.isNaN(Number(v))) return '—';
  return Number(v).toFixed(digits);
}

function launchLabel(row) {
  if (row.error === 'timeout' && (row.hybrid == null) && !row.prediction_detail?.hybrid) {
    return 'INDISPONIBLE';
  }
  if (row.launch == null && row.launch_assumed) return 'ASSUMÉ (timeout)';
  if (row.launch == null) return '—';
  return row.launch ? 'OUI' : 'NON';
}

function sourceLabel(row) {
  const s = row?.source || '';
  if (s === 'redis_probe') return 'agent Redis (live)';
  if (s === 'site_telemetry_fallback') return 'fallback télémétrie site (pas Redis live)';
  if (s === 'timeout') return 'échec total (Redis + site)';
  return s || '—';
}

function detailOf(row) {
  return row?.prediction_detail && Object.keys(row.prediction_detail).length
    ? row.prediction_detail
    : row || {};
}

export default function AvailabilityPredictions() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [probeId, setProbeId] = useState('5ac7e694-b604-4dc9-9ba6-662f56be47c8');
  const [probeResult, setProbeResult] = useState(null);
  const [probing, setProbing] = useState(false);
  const [selected, setSelected] = useState(null);

  const load = useCallback(async () => {
    try {
      const res = await AxiosInstance.get('/availability-predictions/?limit=40');
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
    const t = setInterval(load, 8000);
    return () => clearInterval(t);
  }, [load]);

  const probeNow = async () => {
    if (!probeId.trim()) return;
    setProbing(true);
    try {
      const res = await AxiosInstance.post('/availability-predictions/probe/', {
        volunteer_id: probeId.trim(),
      });
      setProbeResult(res.data);
      setSelected(res.data);
      await load();
    } catch (err) {
      setProbeResult({ error: err.message || 'echec' });
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
  const history = data?.history || [];
  const fields = data?.fields || {};
  const focus = selected || (latest[0] && latest[0][1]) || null;
  const d = detailOf(focus || {});

  return (
    <Box sx={{ p: { xs: 2, md: 3 } }}>
      <Stack direction="row" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h5" sx={{ color: '#fff', fontWeight: 700 }}>
            Predictions disponibilite (15 min)
          </Typography>
          <Typography sx={{ color: '#94a3b8', mt: 0.5, maxWidth: 780 }}>
            Scores renvoyés par l&apos;agent volontaire (prediction_detail). Launch = hybrid ≥ seuil.
          </Typography>
        </Box>
        <Button startIcon={<RefreshIcon />} onClick={load} variant="outlined" sx={{ color: '#00D4FF', borderColor: '#00D4FF' }}>
          Actualiser
        </Button>
      </Stack>

      {error && <Typography color="error" mb={2}>{error}</Typography>}

      <Paper sx={{ ...cardSx, mb: 3 }}>
        <Typography sx={{ color: '#00D4FF', fontWeight: 600, mb: 1 }}>Champs prediction_detail</Typography>
        <Stack spacing={0.5}>
          {Object.entries(fields).map(([k, v]) => (
            <Typography key={k} sx={{ color: '#cbd5e1', fontSize: 13 }}>
              <Chip size="small" label={k} sx={{ mr: 1, bgcolor: 'rgba(0,180,240,0.2)', color: '#67e8f9' }} />
              {v}
            </Typography>
          ))}
        </Stack>
      </Paper>

      <Paper sx={{ ...cardSx, mb: 3 }}>
        <Typography sx={{ color: '#fff', fontWeight: 600, mb: 2 }}>Sonder un volontaire maintenant</Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} spacing={2}>
          <TextField
            size="small"
            fullWidth
            placeholder="UUID volontaire"
            value={probeId}
            onChange={(e) => setProbeId(e.target.value)}
            sx={{ input: { color: '#fff' }, label: { color: '#94a3b8' } }}
          />
          <Button variant="contained" onClick={probeNow} disabled={probing} sx={{ bgcolor: '#00B0F0', minWidth: 140 }}>
            {probing ? '…' : 'Sonder'}
          </Button>
        </Stack>
        {probeResult && (
          <Typography sx={{ mt: 1.5, color: '#94a3b8', fontSize: 12 }}>
            source={probeResult.source || '—'} · error={probeResult.error || '—'}
          </Typography>
        )}
      </Paper>

      {focus && (
        <Paper sx={{ ...cardSx, mb: 3 }}>
          <Typography sx={{ color: '#fff', fontWeight: 600, mb: 2 }}>
            Detail prediction (pourquoi disponible / pas disponible)
          </Typography>
          <Stack direction="row" spacing={1} mb={2} flexWrap="wrap" useFlexGap>
            <Chip label={`launch: ${launchLabel(focus)}`} sx={{ bgcolor: focus.launch ? 'rgba(0,255,136,0.25)' : 'rgba(255,120,80,0.25)', color: '#fff' }} />
            <Chip label={`hybrid ${pct(d.hybrid ?? focus.hybrid)}`} sx={{ color: '#67e8f9' }} />
            <Chip label={`seuil ${num(d.launch_threshold ?? d.threshold ?? focus.launch_threshold, 2)}`} sx={{ color: '#94a3b8' }} />
            <Chip label={d.label || focus.label || 'stay_soft_15m'} sx={{ color: '#cbd5e1' }} />
            <Chip label={sourceLabel(focus)} sx={{ color: '#fbbf24' }} />
            {(d.launch_block_reason || focus.launch_block_reason) && (
              <Chip label={`bloc: ${d.launch_block_reason || focus.launch_block_reason}`} sx={{ color: '#fda4af' }} />
            )}
          </Stack>
          {(focus.source === 'timeout' || focus.error === 'timeout') && focus.hybrid == null && (
            <Typography sx={{ color: '#fca5a5', mb: 2, fontSize: 14 }}>
              Pas de prediction modele : Redis n&apos;a pas repondu et le fallback site est indisponible.
              Les tirets ci-dessous ne sont PAS des scores ARX/GRU a 0 %.
            </Typography>
          )}
          {focus.source === 'site_telemetry_fallback' && (
            <Typography sx={{ color: '#fbbf24', mb: 2, fontSize: 14 }}>
              Redis live indisponible — scores issus de la derniere télémétrie syncée sur le site
              (bridge/agent). Verifier Redis :6380 et l&apos;abonnement du volontaire.
            </Typography>
          )}
          <Table size="small">
            <TableBody>
              {[
                ['linear (ARX)', pct(d.linear ?? focus.linear)],
                ['gru', pct(d.gru ?? focus.gru)],
                ['hybrid', pct(d.hybrid ?? focus.hybrid)],
                ['horizon_min', String(d.horizon_min ?? focus.horizon_min ?? 15)],
                ['launch_threshold', num(d.launch_threshold ?? d.threshold ?? focus.launch_threshold, 3)],
                ['cpu_percent_current', `${num(d.cpu_percent_current ?? focus.cpu_percent_current)} %`],
                ['ram_percent_used_current', `${num(d.ram_percent_used_current ?? focus.ram_percent_used_current)} %`],
                ['cpu_percent_avg_15m', `${num(d.cpu_percent_avg_15m ?? focus.cpu_percent_avg_15m)} %`],
                ['ram_percent_used_avg_15m', `${num(d.ram_percent_used_avg_15m ?? focus.ram_percent_used_avg_15m)} %`],
                ['samples_15m', String(d.samples_15m ?? focus.samples_15m ?? '—')],
                ['machine_id', String(d.machine_id ?? focus.machine_id ?? '—')],
                ['error', String(focus.error || '—')],
              ].map(([k, v]) => (
                <TableRow key={k}>
                  <TableCell sx={{ color: '#67e8f9', borderColor: 'rgba(255,255,255,0.06)', width: 240 }}>{k}</TableCell>
                  <TableCell sx={{ color: '#e2e8f0', borderColor: 'rgba(255,255,255,0.06)', fontFamily: 'monospace' }}>{v}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Paper>
      )}

      <Paper sx={{ ...cardSx, mb: 3 }}>
        <Typography sx={{ color: '#fff', fontWeight: 600, mb: 2 }}>Derniere prediction par volontaire</Typography>
        {latest.length === 0 ? (
          <Typography sx={{ color: '#94a3b8' }}>Aucune sonde enregistree — cliquez « Sonder ».</Typography>
        ) : (
          <TableContainer sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell sx={{ color: '#67e8f9' }}>Volontaire</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Hybrid</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>ARX</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>GRU</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>CPU</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>RAM</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Seuil</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Launch</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Source</TableCell>
                  <TableCell sx={{ color: '#67e8f9' }}>Erreur</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {latest.map(([vid, row]) => {
                  const dd = detailOf(row);
                  return (
                    <TableRow
                      key={vid}
                      hover
                      onClick={() => setSelected(row)}
                      sx={{ cursor: 'pointer' }}
                    >
                      <TableCell sx={{ color: '#e2e8f0', fontFamily: 'monospace', fontSize: 12 }}>{vid.slice(0, 13)}…</TableCell>
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
                      <TableCell sx={{ color: '#94a3b8', fontSize: 12 }}>{row.source || '—'}</TableCell>
                      <TableCell sx={{ color: '#fca5a5', fontSize: 11, maxWidth: 160 }}>{row.error || '—'}</TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </Paper>

      <Paper sx={cardSx}>
        <Typography sx={{ color: '#fff', fontWeight: 600, mb: 2 }}>Historique recent</Typography>
        <TableContainer sx={{ overflowX: 'auto' }}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: '#67e8f9' }}>Volontaire</TableCell>
                <TableCell sx={{ color: '#67e8f9' }}>Hybrid</TableCell>
                <TableCell sx={{ color: '#67e8f9' }}>ARX / GRU</TableCell>
                <TableCell sx={{ color: '#67e8f9' }}>CPU / RAM</TableCell>
                <TableCell sx={{ color: '#67e8f9' }}>Launch</TableCell>
                <TableCell sx={{ color: '#67e8f9' }}>Detail</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {history.map((row, i) => {
                const dd = detailOf(row);
                return (
                  <TableRow key={`${row.request_id || i}-${i}`} hover onClick={() => setSelected(row)} sx={{ cursor: 'pointer' }}>
                    <TableCell sx={{ color: '#e2e8f0', fontFamily: 'monospace', fontSize: 12 }}>
                      {String(row.volunteer_id || '').slice(0, 13) || '—'}
                    </TableCell>
                    <TableCell sx={{ color: '#e2e8f0' }}>{pct(dd.hybrid ?? row.hybrid)}</TableCell>
                    <TableCell sx={{ color: '#e2e8f0', fontSize: 12 }}>
                      {pct(dd.linear ?? row.linear)} / {pct(dd.gru ?? row.gru)}
                    </TableCell>
                    <TableCell sx={{ color: '#e2e8f0', fontSize: 12 }}>
                      {num(dd.cpu_percent_current ?? row.cpu_percent_current)} / {num(dd.ram_percent_used_current ?? row.ram_percent_used_current)}
                    </TableCell>
                    <TableCell sx={{ color: '#e2e8f0' }}>{launchLabel(row)}</TableCell>
                    <TableCell sx={{ color: '#94a3b8', fontSize: 12 }}>
                      {row.source || ''} {row.degraded ? '· degraded' : ''} {row.error || row.mode || dd.label || ''}
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>
    </Box>
  );
}
