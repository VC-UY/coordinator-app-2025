import React, { useEffect, useState, useMemo } from 'react';
import { Box, Typography, CircularProgress, Dialog, DialogTitle, DialogContent, DialogActions, Button } from '@mui/material';
import { MaterialReactTable } from 'material-react-table';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import AxiosInstance from './axios';
import AssignmentIcon from '@mui/icons-material/Assignment';

function Workflows() {
  const [workflows, setWorkflows] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [selectedTask, setSelectedTask] = useState(null);
  const [taskDialogOpen, setTaskDialogOpen] = useState(false);
  const [expanded, setExpanded] = useState({});

  const fetchData = async () => {
    try {
      const wfRes = await AxiosInstance.get('workflows/');
      const workflowsWithTasks = await Promise.all(
        wfRes.data.map(async (wf) => {
          try {
            const tasksRes = await AxiosInstance.get(`tasks/?workflow=${wf.id}`);
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
    } catch (err) {
      console.error('Error loading workflows:', err);
      // Ne pas utiliser de données de fallback hardcodées
      setWorkflows([]);
      setError('Failed to load workflows');
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    const colors = {
      'CREATED': { bg: 'rgba(0, 180, 240, 0.15)', color: '#00B0F0', border: 'rgba(0, 180, 240, 0.3)' },
      'RUNNING': { bg: 'rgba(0, 255, 136, 0.15)', color: '#00FF88', border: 'rgba(0, 255, 136, 0.3)' },
      'COMPLETED': { bg: 'rgba(0, 255, 136, 0.2)', color: '#00FF88', border: 'rgba(0, 255, 136, 0.4)' },
      'PENDING': { bg: 'rgba(255, 165, 0, 0.15)', color: '#FFA500', border: 'rgba(255, 165, 0, 0.3)' },
      'FAILED': { bg: 'rgba(220, 38, 38, 0.15)', color: '#FF4444', border: 'rgba(220, 38, 38, 0.3)' }
    };
    return colors[status] || colors['PENDING'];
  };

  const columns = useMemo(
    () => [
      { 
        accessorKey: 'owner_email', 
        header: 'Manager',
        Cell: ({ cell, row }) => (
          <Typography sx={{ color: '#00B0F0', fontSize: '0.85rem' }}>
            {cell.getValue() || row.original.owner_username || '—'}
          </Typography>
        )
      },
      { 
        accessorKey: 'name', 
        header: 'Name',
        Cell: ({ cell }) => (
          <Typography sx={{ color: '#FFFFFF', fontWeight: 500 }}>
            {cell.getValue()}
          </Typography>
        )
      },
      { 
        accessorKey: 'status', 
        header: 'Status',
        Cell: ({ cell }) => {
          const style = getStatusColor(cell.getValue());
          return (
            <Box sx={{
              display: 'inline-block',
              px: 2,
              py: 0.5,
              borderRadius: 2,
              background: style.bg,
              color: style.color,
              border: `1px solid ${style.border}`,
              fontWeight: 600,
              fontSize: '0.85rem',
              letterSpacing: '0.3px'
            }}>
              {cell.getValue()}
            </Box>
          );
        }
      },
      { 
        accessorKey: 'created_at', 
        header: 'Created At', 
        Cell: ({ cell }) => (
          <Typography sx={{ color: '#00B0F0', fontSize: '0.9rem' }}>
            {new Date(cell.getValue()).toLocaleDateString()}
          </Typography>
        )
      },
      { 
        accessorKey: 'tasks', 
        header: 'Number of Tasks', 
        Cell: ({ row }) => (
          <Typography sx={{ color: '#00D4FF', fontWeight: 700, fontSize: '1.1rem' }}>
            {row.original.tasks.length}
          </Typography>
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

  const renderDetailPanel = ({ row }) => (
    <Box sx={{ 
      p: 3, 
      background: 'linear-gradient(135deg, rgba(0, 180, 240, 0.05) 0%, rgba(0, 212, 255, 0.02) 100%)',
      borderTop: '2px solid rgba(0, 180, 240, 0.2)',
      borderBottom: '2px solid rgba(0, 180, 240, 0.2)'
    }}>
      <Typography variant="subtitle1" fontWeight={600} gutterBottom sx={{ color: '#00D4FF', letterSpacing: '0.3px' }}>
        Volunteers Assigned to Tasks
      </Typography>
      {row.original.taskError && (
        <Typography sx={{ color: '#FF4444', fontSize: '0.9rem' }}>
          Erreur lors du chargement des tâches pour ce workflow.
        </Typography>
      )}
      {row.original.tasks.length === 0 && !row.original.taskError && (
        <Typography sx={{ color: '#00B0F0', fontSize: '0.9rem' }}>
          Aucune tâche trouvée pour ce workflow.
        </Typography>
      )}
      {row.original.tasks.length > 0 && (
        <Box sx={{
          background: 'rgba(0, 0, 0, 0.2)',
          borderRadius: 2,
          border: '1px solid rgba(0, 180, 240, 0.2)',
          overflow: 'hidden',
          mt: 2
        }}>
          <MaterialReactTable
            columns={[
              {
                accessorKey: 'assigned_to',
                header: 'Volunteer (Assigned To)',
                Cell: ({ row }) => (
                  <Typography sx={{ color: '#FFFFFF', fontWeight: 500 }}>
                    {row.original.assigned_to?.name || '—'}
                  </Typography>
                ),
              },
              { 
                accessorKey: 'name', 
                header: 'Task Name',
                Cell: ({ cell }) => (
                  <Typography sx={{ color: '#00D4FF' }}>
                    {cell.getValue()}
                  </Typography>
                )
              },
              { 
                accessorKey: 'status', 
                header: 'Task Status',
                Cell: ({ cell }) => {
                  const style = getStatusColor(cell.getValue());
                  return (
                    <Box sx={{
                      display: 'inline-block',
                      px: 1.5,
                      py: 0.5,
                      borderRadius: 1.5,
                      background: style.bg,
                      color: style.color,
                      border: `1px solid ${style.border}`,
                      fontWeight: 600,
                      fontSize: '0.75rem'
                    }}>
                      {cell.getValue()}
                    </Box>
                  );
                }
              },
            ]}
            data={row.original.tasks}
            enableTopToolbar={false}
            enableBottomToolbar={false}
            muiTableBodyCellProps={{ 
              sx: { 
                py: 1.5, 
                cursor: 'pointer',
                borderBottom: '1px solid rgba(0, 180, 240, 0.1)'
              } 
            }}
            muiTableBodyRowProps={({ row: taskRow }) => ({ 
              onClick: () => handleTaskRowClick(taskRow.original),
              sx: {
                background: 'transparent',
                transition: 'all 0.3s ease',
                '&:hover': {
                  background: 'rgba(0, 180, 240, 0.05)',
                  transform: 'translateX(5px)'
                }
              }
            })}
            muiTableHeadCellProps={{
              sx: {
                background: 'rgba(0, 180, 240, 0.1)',
                color: '#00D4FF',
                fontWeight: 700,
                fontSize: '0.8rem',
                borderBottom: '2px solid rgba(0, 180, 240, 0.3)'
              }
            }}
            muiTableProps={{
              sx: {
                background: 'transparent',
                '& .MuiTableCell-root': {
                  color: '#FFFFFF'
                }
              }
            }}
            muiTablePaperProps={{
              sx: {
                background: 'transparent',
                boxShadow: 'none'
              }
            }}
          />
        </Box>
      )}
    </Box>
  );

  return (
    <Box sx={{ 
      p: { xs: 2, md: 4 }, 
      background: 'linear-gradient(180deg, #001440 0%, #002060 50%, #001440 100%)', 
      minHeight: '100vh' 
    }}>
      {/* Header */}
      <Box sx={{ 
        display: 'flex', 
        alignItems: 'center',
        background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.9) 0%, rgba(0, 20, 64, 0.9) 100%)',
        backdropFilter: 'blur(20px)',
        color: 'white', 
        borderRadius: 2, 
        px: 3, 
        py: 2, 
        mb: 3,
        border: '2px solid rgba(0, 180, 240, 0.3)',
        boxShadow: '0 8px 32px rgba(0, 32, 96, 0.5)'
      }}>
        <AssignmentIcon sx={{ mr: 2, color: '#00D4FF' }} />
        <Typography sx={{ 
          fontWeight: 700,
          letterSpacing: '0.5px',
          background: 'linear-gradient(135deg, #FFFFFF 0%, #00D4FF 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }} variant='h5'>
          All Workflows
        </Typography>
      </Box>

      {/* Table */}
      <Box sx={{
        background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
        backdropFilter: 'blur(20px)',
        borderRadius: 3,
        border: '2px solid rgba(0, 180, 240, 0.3)',
        boxShadow: '0 8px 32px rgba(0, 32, 96, 0.5)',
        overflow: 'hidden'
      }}>
        <MaterialReactTable
          columns={columns}
          data={workflows}
          enableExpanding
          renderDetailPanel={renderDetailPanel}
          muiTableBodyRowProps={({ row }) => ({ 
            sx: {
              background: 'transparent',
              transition: 'all 0.3s ease',
              cursor: 'pointer',
              '&:hover': {
                background: 'rgba(0, 180, 240, 0.05)'
              }
            }
          })}
          muiTableProps={{
            sx: {
              background: 'transparent',
              '& .MuiTableCell-root': {
                borderBottom: '1px solid rgba(0, 180, 240, 0.1)'
              }
            }
          }}
          muiTableHeadCellProps={{
            sx: {
              background: 'linear-gradient(135deg, rgba(0, 180, 240, 0.15) 0%, rgba(0, 212, 255, 0.1) 100%)',
              color: '#00D4FF',
              fontWeight: 700,
              letterSpacing: '0.5px',
              textTransform: 'uppercase',
              fontSize: '0.85rem',
              borderBottom: '2px solid rgba(0, 180, 240, 0.3)',
              '& .MuiTableSortLabel-root': {
                color: '#00D4FF',
                '&:hover': { color: '#00D4FF' },
                '&.Mui-active': { color: '#00D4FF' }
              },
              '& .MuiTableSortLabel-icon': {
                color: '#00D4FF !important'
              }
            }
          }}
          muiTableBodyCellProps={{
            sx: {
              color: '#FFFFFF',
              borderBottom: '1px solid rgba(0, 180, 240, 0.1)'
            }
          }}
          muiTopToolbarProps={{
            sx: {
              background: 'transparent',
              color: '#FFFFFF',
              '& .MuiIconButton-root': { color: '#00D4FF' },
              '& .MuiInputBase-root': {
                color: '#FFFFFF',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '2px solid rgba(0, 180, 240, 0.3)',
                borderRadius: '12px',
                '&:hover': { background: 'rgba(0, 0, 0, 0.4)' },
                '&.Mui-focused': {
                  borderColor: '#00D4FF',
                  boxShadow: '0 0 20px rgba(0, 212, 255, 0.3)'
                }
              },
              '& .MuiInputBase-input': {
                color: '#FFFFFF',
                '&::placeholder': { color: 'rgba(0, 180, 240, 0.6)' }
              }
            }
          }}
          muiBottomToolbarProps={{
            sx: {
              background: 'transparent',
              color: '#FFFFFF',
              '& .MuiTablePagination-root': { color: '#FFFFFF' },
              '& .MuiIconButton-root': {
                color: '#00D4FF',
                '&.Mui-disabled': { color: 'rgba(0, 180, 240, 0.3)' }
              },
              '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                color: '#00B0F0'
              }
            }
          }}
          muiTablePaperProps={{
            sx: {
              background: 'transparent',
              boxShadow: 'none'
            }
          }}
          muiExpandButtonProps={{
            sx: {
              color: '#00D4FF',
              background: 'rgba(0, 180, 240, 0.1)',
              border: '1px solid rgba(0, 180, 240, 0.3)',
              '&:hover': {
                background: 'rgba(0, 180, 240, 0.2)',
                transform: 'scale(1.1)'
              }
            }
          }}
        />
      </Box>

      {/* Task Detail Dialog */}
      <Dialog 
        open={taskDialogOpen} 
        onClose={handleTaskDialogClose} 
        maxWidth="sm" 
        fullWidth
        PaperProps={{
          sx: {
            background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.98) 0%, rgba(0, 20, 64, 0.98) 100%)',
            backdropFilter: 'blur(20px)',
            border: '2px solid rgba(0, 180, 240, 0.3)',
            borderRadius: 3,
            boxShadow: '0 12px 48px rgba(0, 32, 96, 0.7)'
          }
        }}
      >
        <DialogTitle sx={{ 
          background: 'linear-gradient(135deg, rgba(0, 180, 240, 0.2) 0%, rgba(0, 212, 255, 0.1) 100%)',
          borderBottom: '2px solid rgba(0, 180, 240, 0.3)',
          color: '#00D4FF',
          fontWeight: 700,
          letterSpacing: '0.5px'
        }}>
          Task Details
        </DialogTitle>
        <DialogContent dividers sx={{ 
          borderColor: 'rgba(0, 180, 240, 0.3)',
          color: '#FFFFFF'
        }}>
          {selectedTask && (
            <Box sx={{ '& > *': { mb: 2 } }}>
              {[
                { label: 'Name', value: selectedTask.name },
                { label: 'Description', value: selectedTask.description },
                { label: 'Status', value: selectedTask.status },
                { label: 'Command', value: selectedTask.command },
                { label: 'Volunteer', value: selectedTask.assigned_to?.name || '—' },
                { label: 'Created At', value: selectedTask.created_at ? new Date(selectedTask.created_at).toLocaleString() : '—' },
                { label: 'Updated At', value: selectedTask.updated_at ? new Date(selectedTask.updated_at).toLocaleString() : '—' }
              ].map((item, idx) => (
                <Box key={idx} sx={{
                  p: 2,
                  background: 'rgba(0, 180, 240, 0.05)',
                  borderRadius: 2,
                  border: '1px solid rgba(0, 180, 240, 0.2)'
                }}>
                  <Typography sx={{ 
                    color: '#00B0F0', 
                    fontWeight: 600, 
                    fontSize: '0.85rem',
                    mb: 0.5,
                    letterSpacing: '0.3px'
                  }}>
                    {item.label}
                  </Typography>
                  <Typography sx={{ color: '#FFFFFF', fontSize: '0.95rem' }}>
                    {item.value || '—'}
                  </Typography>
                </Box>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions sx={{ 
          background: 'linear-gradient(135deg, rgba(0, 180, 240, 0.1) 0%, rgba(0, 212, 255, 0.05) 100%)',
          borderTop: '2px solid rgba(0, 180, 240, 0.3)',
          p: 2
        }}>
          <Button 
            onClick={handleTaskDialogClose} 
            variant="contained"
            sx={{
              background: 'linear-gradient(135deg, #00B0F0 0%, #00D4FF 100%)',
              color: '#FFFFFF',
              fontWeight: 600,
              borderRadius: 2,
              border: '2px solid rgba(0, 212, 255, 0.4)',
              boxShadow: '0 4px 16px rgba(0, 180, 240, 0.3)',
              '&:hover': {
                background: 'linear-gradient(135deg, #00D4FF 0%, #00B0F0 100%)',
                transform: 'translateY(-2px)',
                boxShadow: '0 8px 24px rgba(0, 212, 255, 0.5)'
              }
            }}
          >
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}

export default Workflows;