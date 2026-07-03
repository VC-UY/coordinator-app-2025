import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Box, Typography, Paper, CircularProgress, Chip, Stack, Button,
  Accordion, AccordionSummary, AccordionDetails, Table, TableBody,
  TableCell, TableHead, TableRow, TextField, MenuItem,
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import RefreshIcon from '@mui/icons-material/Refresh';
import { Link, useSearchParams } from 'react-router-dom';
import { fetchWorkflowsWithTasks, fetchManagers } from './apiHome';

const cardSx = {
  p: 3,
  borderRadius: 2,
  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
  border: '2px solid rgba(0, 180, 240, 0.3)',
};

const statusColor = (status) => {
  const map = {
    RUNNING: '#00FF88',
    COMPLETED: '#00D4FF',
    FAILED: '#FF4444',
    PENDING: '#FFA500',
    CREATED: '#00B0F0',
  };
  return map[status] || '#94A3B8';
};

export default function Workflows() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [workflows, setWorkflows] = useState([]);
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const managerFilter = searchParams.get('manager') || 'all';
  const statusFilter = searchParams.get('status') || 'all';

  const setManagerFilter = (value) => {
    const next = new URLSearchParams(searchParams);
    if (value === 'all') next.delete('manager');
    else next.set('manager', value);
    setSearchParams(next);
  };

  const setStatusFilter = (value) => {
    const next = new URLSearchParams(searchParams);
    if (value === 'all') next.delete('status');
    else next.set('status', value);
    setSearchParams(next);
  };

  const load = useCallback(async () => {
    try {
      const [wf, mgr] = await Promise.all([fetchWorkflowsWithTasks(), fetchManagers()]);
      setWorkflows(wf);
      setManagers(mgr);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Impossible de charger les workflows.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
    const timer = setInterval(load, 10000);
    return () => clearInterval(timer);
  }, [load]);

  const filtered = useMemo(() => {
    return workflows.filter((wf) => {
      const ownerKeys = [wf.owner_email, wf.owner_username, wf.owner].filter(Boolean);
      const managerOk = managerFilter === 'all' || ownerKeys.includes(managerFilter);
      const statusOk = statusFilter === 'all' || wf.status === statusFilter;
      return managerOk && statusOk;
    });
  }, [workflows, managerFilter, statusFilter]);

  const grouped = useMemo(() => {
    const groups = {};
    filtered.forEach((wf) => {
      const key = wf.owner_email || wf.owner_username || wf.owner || 'Sans manager';
      if (!groups[key]) {
        groups[key] = {
          label: wf.owner_email || wf.owner_username || 'Sans manager',
          ownerId: wf.owner,
          workflows: [],
        };
      }
      groups[key].workflows.push(wf);
    });
    return Object.values(groups).sort((a, b) => a.label.localeCompare(b.label));
  }, [filtered]);

  const managerOptions = useMemo(() => {
    const fromManagers = managers.map((m) => ({
      value: m.email || m.username || m.id,
      label: m.email || m.username,
    }));
    const fromWorkflows = workflows.map((wf) => ({
      value: wf.owner_email || wf.owner_username || wf.owner,
      label: wf.owner_email || wf.owner_username || wf.owner,
    })).filter((item) => item.value);
    const map = new Map();
    [...fromManagers, ...fromWorkflows].forEach((item) => {
      if (item.value) map.set(item.value, item.label);
    });
    return Array.from(map.entries()).map(([value, label]) => ({ value, label }));
  }, [managers, workflows]);

  const statuses = useMemo(
    () => [...new Set(workflows.map((wf) => wf.status).filter(Boolean))],
    [workflows],
  );

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
          <Typography variant="h4" fontWeight={800} color="#fff">Workflows</Typography>
          <Typography color="#00B0F0">Organises par manager / utilisateur</Typography>
        </Box>
        <Button startIcon={<RefreshIcon />} onClick={load} sx={{ color: '#00D4FF' }}>
          Actualiser
        </Button>
      </Stack>

      <Paper elevation={0} sx={{ ...cardSx, mb: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            select
            label="Manager"
            value={managerFilter}
            onChange={(e) => setManagerFilter(e.target.value)}
            size="small"
            sx={{ minWidth: 240 }}
          >
            <MenuItem value="all">Tous les managers</MenuItem>
            {managerOptions.map((opt) => (
              <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label="Statut"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            size="small"
            sx={{ minWidth: 180 }}
          >
            <MenuItem value="all">Tous les statuts</MenuItem>
            {statuses.map((status) => (
              <MenuItem key={status} value={status}>{status}</MenuItem>
            ))}
          </TextField>
        </Stack>
      </Paper>

      {error && <Typography color="#FF4444" mb={2}>{error}</Typography>}

      {grouped.length === 0 ? (
        <Paper elevation={0} sx={cardSx}>
          <Typography color="#94A3B8">Aucun workflow trouve.</Typography>
        </Paper>
      ) : (
        grouped.map((group) => (
          <Accordion
            key={group.label}
            defaultExpanded
            sx={{
              mb: 2,
              background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
              border: '2px solid rgba(0, 180, 240, 0.3)',
              color: '#fff',
              '&:before': { display: 'none' },
            }}
          >
            <AccordionSummary expandIcon={<ExpandMoreIcon sx={{ color: '#00D4FF' }} />}>
              <Stack direction="row" spacing={2} alignItems="center">
                <Typography fontWeight={700}>{group.label}</Typography>
                <Chip size="small" label={`${group.workflows.length} workflow(s)`} sx={{ color: '#00D4FF' }} />
              </Stack>
            </AccordionSummary>
            <AccordionDetails>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ color: '#00B0F0' }}>Nom</TableCell>
                    <TableCell sx={{ color: '#00B0F0' }}>Type</TableCell>
                    <TableCell sx={{ color: '#00B0F0' }}>Statut</TableCell>
                    <TableCell sx={{ color: '#00B0F0' }}>Taches</TableCell>
                    <TableCell sx={{ color: '#00B0F0' }}>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {group.workflows.map((wf) => (
                    <TableRow key={wf.id}>
                      <TableCell sx={{ color: '#fff' }}>{wf.name}</TableCell>
                      <TableCell sx={{ color: '#cbd5e1' }}>{wf.workflow_type || '—'}</TableCell>
                      <TableCell>
                        <Chip
                          size="small"
                          label={wf.status}
                          sx={{ color: statusColor(wf.status), borderColor: statusColor(wf.status) }}
                          variant="outlined"
                        />
                      </TableCell>
                      <TableCell sx={{ color: '#fff' }}>{(wf.tasks || []).length}</TableCell>
                      <TableCell>
                        <Button
                          component={Link}
                          to={`/tasks?workflow=${wf.id}`}
                          size="small"
                          sx={{ color: '#00D4FF' }}
                        >
                          Voir taches
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>

              {group.workflows.map((wf) => (
                (wf.tasks || []).length > 0 && (
                  <Box key={`${wf.id}-tasks`} sx={{ mt: 2, p: 2, borderRadius: 2, background: 'rgba(0,0,0,0.2)' }}>
                    <Typography variant="subtitle2" color="#00B0F0" mb={1}>
                      Taches de {wf.name}
                    </Typography>
                    <Stack spacing={1}>
                      {(wf.tasks || []).map((task) => (
                        <Stack key={task.id} direction="row" justifyContent="space-between" spacing={2}>
                          <Typography color="#fff" variant="body2">{task.name}</Typography>
                          <Stack direction="row" spacing={1}>
                            <Chip size="small" label={task.status} sx={{ color: '#fff' }} />
                            <Typography variant="body2" color="#94A3B8">
                              {task.assigned_to_name || 'non assignee'}
                            </Typography>
                          </Stack>
                        </Stack>
                      ))}
                    </Stack>
                  </Box>
                )
              ))}
            </AccordionDetails>
          </Accordion>
        ))
      )}
    </Box>
  );
}
