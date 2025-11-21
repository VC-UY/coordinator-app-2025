import React, { useEffect, useState, useMemo } from 'react';
import {
  Box, Typography, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions, Button,
  IconButton, Chip, Snackbar, Alert, TextField, Select, MenuItem, FormControl, InputLabel
} from '@mui/material';
import { MaterialReactTable } from 'material-react-table';
import AxiosInstance from './axios';
import AssignmentIcon from '@mui/icons-material/Assignment';
import EditIcon from '@mui/icons-material/Edit';
import DeleteIcon from '@mui/icons-material/Delete';
import StopIcon from '@mui/icons-material/Stop';
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import AddIcon from '@mui/icons-material/Add';

function Workflows() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [selectedWorkflow, setSelectedWorkflow] = useState(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });

  // Form states for editing
  const [editForm, setEditForm] = useState({
    name: '',
    description: '',
    status: '',
    priority: 1
  });

  const fetchData = async () => {
    try {
      setLoading(true);
      const wfRes = await AxiosInstance.get('api/workflows/');
      const workflowsWithTasks = await Promise.all(
        wfRes.data.map(async (wf) => {
          try {
            const tasksRes = await AxiosInstance.get(`api/tasks/`);
            const filteredTasks = Array.isArray(tasksRes.data)
              ? tasksRes.data.filter(task => String(task.workflow) === String(wf.id))
              : [];
            return { ...wf, tasks: filteredTasks };
          } catch (taskErr) {
            console.error(`Error loading tasks for workflow ${wf.id}:`, taskErr);
            return { ...wf, tasks: [], taskError: true };
          }
        })
      );
      setWorkflows(workflowsWithTasks);
      setLoading(false);
    } catch (err) {
      console.error('Error loading workflows:', err);
      showSnackbar('Erreur lors du chargement des workflows', 'error');
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial fetch
    fetchData();

    // Set up interval for real-time updates every 3 seconds
    const interval = setInterval(fetchData, 3000);

    // Cleanup interval on component unmount
    return () => clearInterval(interval);
  }, []);

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
  };

  // Status color mapping
  const getStatusColor = (status) => {
    const colors = {
      'CREATED': 'default',
      'VALIDATED': 'info',
      'RUNNING': 'primary',
      'PAUSED': 'warning',
      'COMPLETED': 'success',
      'FAILED': 'error',
      'PENDING': 'secondary'
    };
    return colors[status] || 'default';
  };

  // Handle Edit
  const handleEditClick = (workflow) => {
    setSelectedWorkflow(workflow);
    setEditForm({
      name: workflow.name,
      description: workflow.description || '',
      status: workflow.status,
      priority: workflow.priority || 1
    });
    setEditDialogOpen(true);
  };

  const handleEditSubmit = async () => {
    try {
      await AxiosInstance.patch(`api/workflows/${selectedWorkflow.id}/`, editForm);
      showSnackbar('Workflow mis à jour avec succès', 'success');
      setEditDialogOpen(false);
      fetchData();
    } catch (error) {
      console.error('Error updating workflow:', error);
      showSnackbar('Erreur lors de la mise à jour du workflow', 'error');
    }
  };

  // Handle Delete
  const handleDeleteClick = (workflow) => {
    setSelectedWorkflow(workflow);
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    try {
      await AxiosInstance.delete(`api/workflows/${selectedWorkflow.id}/`);
      showSnackbar('Workflow supprimé avec succès', 'success');
      setDeleteDialogOpen(false);
      fetchData();
    } catch (error) {
      console.error('Error deleting workflow:', error);
      showSnackbar('Erreur lors de la suppression du workflow', 'error');
    }
  };

  // Handle Stop
  const handleStop = async (workflow) => {
    try {
      await AxiosInstance.post(`api/workflows/${workflow.id}/stop/`);
      showSnackbar(`Workflow "${workflow.name}" arrêté avec succès`, 'success');
      fetchData();
    } catch (error) {
      console.error('Error stopping workflow:', error);
      const message = error.response?.data?.message || 'Erreur lors de l\'arrêt du workflow';
      showSnackbar(message, 'error');
    }
  };

  // Handle Resume
  const handleResume = async (workflow) => {
    try {
      await AxiosInstance.post(`api/workflows/${workflow.id}/resume/`);
      showSnackbar(`Workflow "${workflow.name}" repris avec succès`, 'success');
      fetchData();
    } catch (error) {
      console.error('Error resuming workflow:', error);
      const message = error.response?.data?.message || 'Erreur lors de la reprise du workflow';
      showSnackbar(message, 'error');
    }
  };

  const columns = useMemo(
    () => [
      {
        accessorKey: 'name',
        header: 'Nom',
        size: 200
      },
      {
        accessorKey: 'workflow_type',
        header: 'Type',
        size: 150
      },
      {
        accessorKey: 'status',
        header: 'Statut',
        size: 120,
        Cell: ({ cell }) => (
          <Chip
            label={cell.getValue()}
            color={getStatusColor(cell.getValue())}
            size="small"
          />
        )
      },
      {
        accessorKey: 'priority',
        header: 'Priorité',
        size: 80
      },
      {
        accessorKey: 'created_at',
        header: 'Créé le',
        size: 120,
        Cell: ({ cell }) => new Date(cell.getValue()).toLocaleDateString('fr-FR')
      },
      {
        accessorKey: 'tasks',
        header: 'Tâches',
        size: 80,
        Cell: ({ row }) => row.original.tasks.length
      },
      {
        accessorKey: 'actions',
        header: 'Actions',
        size: 200,
        Cell: ({ row }) => (
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <IconButton
              size="small"
              color="primary"
              onClick={() => handleEditClick(row.original)}
              title="Modifier"
            >
              <EditIcon fontSize="small" />
            </IconButton>
            <IconButton
              size="small"
              color="error"
              onClick={() => handleDeleteClick(row.original)}
              title="Supprimer"
            >
              <DeleteIcon fontSize="small" />
            </IconButton>
            {['RUNNING', 'PENDING', 'ASSIGNING', 'SPLITTING'].includes(row.original.status) && (
              <IconButton
                size="small"
                color="warning"
                onClick={() => handleStop(row.original)}
                title="Arrêter"
              >
                <StopIcon fontSize="small" />
              </IconButton>
            )}
            {row.original.status === 'PAUSED' && (
              <IconButton
                size="small"
                color="success"
                onClick={() => handleResume(row.original)}
                title="Reprendre"
              >
                <PlayArrowIcon fontSize="small" />
              </IconButton>
            )}
          </Box>
        )
      },
    ], []
  );

  const handleTaskRowClick = (task) => {
    setSelectedTask(task);
    setTaskDialogOpen(true);
  };

  const handleTaskDialogClose = () => {
    setTaskDialogOpen(false);
    setSelectedTask(null);
  };

  // Rendu de la liste des tâches pour chaque workflow
  const renderDetailPanel = ({ row }) => (
    <Box sx={{ p: 2, background: '#f8fafc' }}>
      <Typography variant="subtitle1" fontWeight={600} gutterBottom>
        Tâches assignées aux volontaires
      </Typography>
      {row.original.taskError && (
        <Alert severity="error" sx={{ mb: 2 }}>
          Erreur lors du chargement des tâches pour ce workflow.
        </Alert>
      )}
      {row.original.tasks.length === 0 && !row.original.taskError && (
        <Typography color="text.secondary">
          Aucune tâche trouvée pour ce workflow.
        </Typography>
      )}
      {row.original.tasks.length > 0 && (
        <MaterialReactTable
          columns={[
            {
              accessorKey: 'assigned_to',
              header: 'Volontaire',
              Cell: ({ row }) => row.original.assigned_to?.name || '-',
            },
            { accessorKey: 'name', header: 'Nom de la tâche' },
            {
              accessorKey: 'status',
              header: 'Statut',
              Cell: ({ cell }) => (
                <Chip
                  label={cell.getValue()}
                  color={getStatusColor(cell.getValue())}
                  size="small"
                />
              )
            },
            {
              accessorKey: 'progress',
              header: 'Progression',
              Cell: ({ cell }) => `${cell.getValue() || 0}%`
            }
          ]}
          data={row.original.tasks}
          enableTopToolbar={false}
          enableBottomToolbar={false}
          muiTableBodyCellProps={{ sx: { py: 1, cursor: 'pointer' } }}
          muiTableBodyRowProps={({ row: taskRow }) => ({
            onClick: () => handleTaskRowClick(taskRow.original),
            sx: { '&:hover': { backgroundColor: '#f5f5f5' } }
          })}
        />
      )}
    </Box>
  );

  return (
    <Box sx={{ p: { xs: 2, md: 4 }, background: '#f5f6fa', minHeight: '100vh' }}>
      <Typography variant="h5" fontWeight={700} mb={3}>Gestion des Workflows</Typography>

      <Box sx={{ display: 'flex', alignItems: 'center', background: 'blue', color: 'white', borderRadius: 0.5, px: 2, py: 1, mb: 2 }}>
        <AssignmentIcon sx={{ mr: 1 }} />
        <Typography sx={{ fontWeight: 'bold' }} variant='subtitle2'>Tous les Workflows</Typography>
      </Box>

      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
          <CircularProgress />
        </Box>
      ) : (
        <MaterialReactTable
          columns={columns}
          data={workflows}
          enableExpanding
          renderDetailPanel={renderDetailPanel}
          muiTableBodyRowProps={() => ({ hover: true })}
          muiTableContainerProps={{ sx: { borderRadius: 2, boxShadow: 1, background: 'white' } }}
          initialState={{
            sorting: [{ id: 'created_at', desc: true }]
          }}
        />
      )}

      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Modifier le Workflow</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Nom"
              value={editForm.name}
              onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              fullWidth
            />
            <TextField
              label="Description"
              value={editForm.description}
              onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
              fullWidth
              multiline
              rows={3}
            />
            <FormControl fullWidth>
              <InputLabel>Statut</InputLabel>
              <Select
                value={editForm.status}
                label="Statut"
                onChange={(e) => setEditForm({ ...editForm, status: e.target.value })}
              >
                <MenuItem value="CREATED">Créé</MenuItem>
                <MenuItem value="VALIDATED">Validé</MenuItem>
                <MenuItem value="PENDING">En attente</MenuItem>
                <MenuItem value="RUNNING">En cours</MenuItem>
                <MenuItem value="PAUSED">En pause</MenuItem>
                <MenuItem value="COMPLETED">Terminé</MenuItem>
                <MenuItem value="FAILED">Échoué</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Priorité"
              type="number"
              value={editForm.priority}
              onChange={(e) => setEditForm({ ...editForm, priority: parseInt(e.target.value) })}
              fullWidth
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleEditSubmit} variant="contained" color="primary">
            Enregistrer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Confirmer la suppression</DialogTitle>
        <DialogContent>
          <Typography>
            Êtes-vous sûr de vouloir supprimer le workflow "{selectedWorkflow?.name}" ?
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            Cette action est irréversible et supprimera également toutes les tâches associées.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>Annuler</Button>
          <Button onClick={handleDeleteConfirm} variant="contained" color="error">
            Supprimer
          </Button>
        </DialogActions>
      </Dialog>

      {/* Task Detail Dialog */}
      <Dialog open={taskDialogOpen} onClose={handleTaskDialogClose} maxWidth="sm" fullWidth>
        <DialogTitle>Détails de la Tâche</DialogTitle>
        <DialogContent dividers>
          {selectedTask && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Nom</Typography>
                <Typography>{selectedTask.name}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Description</Typography>
                <Typography>{selectedTask.description || '-'}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Statut</Typography>
                <Chip
                  label={selectedTask.status}
                  color={getStatusColor(selectedTask.status)}
                  size="small"
                />
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Progression</Typography>
                <Typography>{selectedTask.progress || 0}%</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Commande</Typography>
                <Typography sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                  {selectedTask.command || '-'}
                </Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Volontaire assigné</Typography>
                <Typography>{selectedTask.assigned_to?.name || '-'}</Typography>
              </Box>
              <Box>
                <Typography variant="subtitle2" color="text.secondary">Créé le</Typography>
                <Typography>
                  {selectedTask.created_at ? new Date(selectedTask.created_at).toLocaleString('fr-FR') : '-'}
                </Typography>
              </Box>
              {selectedTask.start_time && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Démarré le</Typography>
                  <Typography>
                    {new Date(selectedTask.start_time).toLocaleString('fr-FR')}
                  </Typography>
                </Box>
              )}
              {selectedTask.end_time && (
                <Box>
                  <Typography variant="subtitle2" color="text.secondary">Terminé le</Typography>
                  <Typography>
                    {new Date(selectedTask.end_time).toLocaleString('fr-FR')}
                  </Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={handleTaskDialogClose} variant="contained">Fermer</Button>
        </DialogActions>
      </Dialog>

      {/* Snackbar for notifications */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
}

export default Workflows;
