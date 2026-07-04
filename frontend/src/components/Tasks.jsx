import React, { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Box, Typography, Paper, CircularProgress, Chip, Stack, Button,
  TextField, MenuItem, Table, TableBody, TableCell, TableHead, TableRow,
} from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import { useSearchParams, Link } from 'react-router-dom';
import { fetchTasks, fetchWorkflows, fetchManagers } from './apiHome';

const cardSx = {
  p: 3,
  borderRadius: 2,
  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.7) 0%, rgba(0, 20, 64, 0.7) 100%)',
  border: '2px solid rgba(0, 180, 240, 0.3)',
};

export default function Tasks() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [tasks, setTasks] = useState([]);
  const [workflows, setWorkflows] = useState([]);
  const [managers, setManagers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const workflowFilter = searchParams.get('workflow') || 'all';
  const managerFilter = searchParams.get('manager') || 'all';
  const statusFilter = searchParams.get('status') || 'all';

  const load = useCallback(async () => {
    try {
      const [wfList, mgrList] = await Promise.all([fetchWorkflows(), fetchManagers()]);
      setWorkflows(wfList);
      setManagers(mgrList);

      const params = {};
      if (workflowFilter !== 'all') params.workflow = workflowFilter;
      if (managerFilter !== 'all') {
        const manager = mgrList.find((m) => m.id === managerFilter || m.email === managerFilter);
        if (manager?.email) params.manager_email = manager.email;
        else if (manager?.id) params.owner = manager.id;
        else params.owner = managerFilter;
      }

      const taskList = await fetchTasks(params);
      setTasks(taskList);
      setError('');
    } catch (err) {
      console.error(err);
      setError('Impossible de charger les taches.');
    } finally {
      setLoading(false);
    }
  }, [workflowFilter, managerFilter]);

  useEffect(() => {
    load();
    // Rafraîchir souvent pour rester aligné avec Manager / volontaires
    const timer = setInterval(load, 4000);
    return () => clearInterval(timer);
  }, [load]);

  const filteredTasks = useMemo(() => {
    return tasks.filter((task) => statusFilter === 'all' || task.status === statusFilter);
  }, [tasks, statusFilter]);

  const statuses = useMemo(
    () => [...new Set(tasks.map((task) => task.status).filter(Boolean))],
    [tasks],
  );

  const updateParam = (key, value) => {
    const next = new URLSearchParams(searchParams);
    if (value === 'all') next.delete(key);
    else next.set(key, value);
    setSearchParams(next);
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
          <Typography variant="h4" fontWeight={800} color="#fff">Taches</Typography>
          <Typography color="#00B0F0">Par workflow et par manager</Typography>
        </Box>
        <Button startIcon={<RefreshIcon />} onClick={load} sx={{ color: '#00D4FF' }}>
          Actualiser
        </Button>
      </Stack>

      <Paper elevation={0} sx={{ ...cardSx, mb: 3 }}>
        <Stack direction={{ xs: 'column', md: 'row' }} spacing={2}>
          <TextField
            select
            label="Workflow"
            value={workflowFilter}
            onChange={(e) => updateParam('workflow', e.target.value)}
            size="small"
            sx={{ minWidth: 220 }}
          >
            <MenuItem value="all">Tous les workflows</MenuItem>
            {workflows.map((wf) => (
              <MenuItem key={wf.id} value={wf.id}>{wf.name}</MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label="Manager"
            value={managerFilter}
            onChange={(e) => updateParam('manager', e.target.value)}
            size="small"
            sx={{ minWidth: 220 }}
          >
            <MenuItem value="all">Tous les managers</MenuItem>
            {managers.map((m) => (
              <MenuItem key={m.id} value={m.id}>{m.email || m.username}</MenuItem>
            ))}
          </TextField>
          <TextField
            select
            label="Statut"
            value={statusFilter}
            onChange={(e) => updateParam('status', e.target.value)}
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

      <Paper elevation={0} sx={cardSx}>
        {filteredTasks.length === 0 ? (
          <Typography color="#94A3B8">Aucune tache trouvee.</Typography>
        ) : (
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell sx={{ color: '#00B0F0' }}>Tache</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Workflow</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Manager</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Volontaire</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Statut</TableCell>
                <TableCell sx={{ color: '#00B0F0' }}>Progression</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredTasks.map((task) => (
                <TableRow key={task.id}>
                  <TableCell sx={{ color: '#fff' }}>{task.name}</TableCell>
                  <TableCell>
                    {task.workflow ? (
                      <Button
                        component={Link}
                        to={`/tasks?workflow=${task.workflow}`}
                        size="small"
                        sx={{ color: '#00D4FF', textTransform: 'none' }}
                      >
                        {task.workflow_name || task.workflow}
                      </Button>
                    ) : '—'}
                  </TableCell>
                  <TableCell sx={{ color: '#00B0F0' }}>
                    {task.owner_email || task.owner_username || '—'}
                  </TableCell>
                  <TableCell sx={{ color: '#cbd5e1' }}>
                    {task.assigned_to_name || 'non assignee'}
                  </TableCell>
                  <TableCell>
                    <Chip size="small" label={task.status} sx={{ color: '#fff' }} variant="outlined" />
                  </TableCell>
                  <TableCell sx={{ color: '#fff' }}>{Math.round(task.progress || 0)}%</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </Paper>
    </Box>
  );
}
