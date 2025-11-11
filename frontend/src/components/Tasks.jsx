import React, { useEffect, useState, useMemo } from 'react';
import { Box, Typography, CircularProgress, Chip, Paper, IconButton, Tooltip } from '@mui/material';
import { MaterialReactTable } from 'material-react-table';
import AssignmentIcon from '@mui/icons-material/Assignment';
import RefreshIcon from '@mui/icons-material/Refresh';
import PersonIcon from '@mui/icons-material/Person';
import AccountTreeIcon from '@mui/icons-material/AccountTree';

const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const fetchData = async () => {
    try {
      // Uncomment when API is ready
      // const res = await AxiosInstance.get('api/tasks/');
      // setTasks(res.data);
      
      // Simulating API call
      setTimeout(() => {
        setTasks([]);
        setLoading(false);
        setLastUpdate(new Date());
      }, 500);
    } catch (error) {
      console.error('Error fetching tasks:', error);
      setTasks([]);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = (status) => {
    const colors = {
      'RUNNING': '#00B0F0',
      'PENDING': '#00D4FF',
      'COMPLETED': '#002060',
      'FAILED': '#001440'
    };
    return colors[status] || '#002060';
  };

  const getStatusLabel = (status) => {
    const labels = {
      'RUNNING': 'En cours',
      'PENDING': 'En attente',
      'COMPLETED': 'Terminé',
      'FAILED': 'Échoué'
    };
    return labels[status] || status;
  };

  const columns = useMemo(
    () => [
      { 
        accessorKey: 'name', 
        header: 'Nom de la tâche',
        size: 250,
        Cell: ({ cell }) => (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Box
              sx={{
                width: 8,
                height: 8,
                borderRadius: '50%',
                backgroundColor: '#00B0F0',
                animation: 'pulse 2s infinite'
              }}
            />
            <Typography sx={{ fontWeight: 500, color: '#002060' }}>
              {cell.getValue()}
            </Typography>
          </Box>
        )
      },
      { 
        accessorKey: 'status', 
        header: 'Statut',
        size: 150,
        Cell: ({ cell }) => (
          <Chip
            label={getStatusLabel(cell.getValue())}
            sx={{
              backgroundColor: getStatusColor(cell.getValue()),
              color: 'white',
              fontWeight: 600,
              borderRadius: '20px',
              px: 1
            }}
            size="small"
          />
        )
      },
      { 
        accessorKey: 'workflow', 
        header: 'Workflow',
        size: 200,
        Cell: ({ cell }) => (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AccountTreeIcon sx={{ fontSize: 18, color: '#00B0F0' }} />
            <Typography sx={{ color: '#001440' }}>
              {cell.getValue()?.name || '-'}
            </Typography>
          </Box>
        )
      },
      { 
        accessorKey: 'assigned_to', 
        header: 'Bénévole assigné',
        size: 180,
        Cell: ({ row }) => {
          const assigned = row.original.assigned_to;
          if (assigned && typeof assigned === 'object' && assigned.name) {
            return (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <PersonIcon sx={{ fontSize: 18, color: '#00D4FF' }} />
                <Typography sx={{ color: '#001440' }}>
                  {assigned.name}
                </Typography>
              </Box>
            );
          }
          return <Typography sx={{ color: '#999' }}>Non assigné</Typography>;
        }
      },
      { 
        accessorKey: 'created_at', 
        header: 'Date de création',
        size: 150,
        Cell: ({ cell }) => (
          <Typography sx={{ color: '#001440', fontSize: '0.875rem' }}>
            {new Date(cell.getValue()).toLocaleDateString('fr-FR')}
          </Typography>
        )
      },
      { 
        accessorKey: 'updated_at', 
        header: 'Dernière mise à jour',
        size: 150,
        Cell: ({ cell }) => (
          <Typography sx={{ color: '#001440', fontSize: '0.875rem' }}>
            {new Date(cell.getValue()).toLocaleDateString('fr-FR')}
          </Typography>
        )
      }
    ],
    []
  );

  return (
    <Box 
      sx={{ 
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)',
        p: { xs: 2, md: 4 }
      }}
    >
      <style>
        {`
          @keyframes pulse {
            0%, 100% { opacity: 1; transform: scale(1); }
            50% { opacity: 0.5; transform: scale(1.2); }
          }
          
          @keyframes spin {
            from { transform: rotate(0deg); }
            to { transform: rotate(360deg); }
          }
          
          @keyframes slideIn {
            from { opacity: 0; transform: translateY(-20px); }
            to { opacity: 1; transform: translateY(0); }
          }
        `}
      </style>

      {/* Header Section */}
      <Paper
        elevation={0}
        sx={{
          background: 'linear-gradient(135deg, #002060 0%, #001440 100%)',
          borderRadius: '24px',
          p: 3,
          mb: 3,
          position: 'relative',
          overflow: 'hidden',
          animation: 'slideIn 0.6s ease-out'
        }}
      >
        <Box
          sx={{
            position: 'absolute',
            top: -50,
            right: -50,
            width: 200,
            height: 200,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(0,176,240,0.15) 0%, transparent 70%)',
          }}
        />
        <Box
          sx={{
            position: 'absolute',
            bottom: -30,
            left: -30,
            width: 150,
            height: 150,
            borderRadius: '50%',
            background: 'radial-gradient(circle, rgba(0,212,255,0.15) 0%, transparent 70%)',
          }}
        />
        
        <Box sx={{ position: 'relative', zIndex: 1 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              <Box
                sx={{
                  backgroundColor: '#00B0F0',
                  borderRadius: '16px',
                  p: 1.5,
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                <AssignmentIcon sx={{ color: 'white', fontSize: 32 }} />
              </Box>
              <Box>
                <Typography 
                  variant='h4' 
                  sx={{ 
                    fontWeight: 700, 
                    color: 'white',
                    mb: 0.5
                  }}
                >
                  Gestion des Tâches
                </Typography>
                <Typography 
                  variant='body2' 
                  sx={{ 
                    color: '#00D4FF',
                    fontWeight: 500
                  }}
                >
                  VolunSys-UY1 - La puissance collective au service du calcul scientifique
                </Typography>
              </Box>
            </Box>
            
            <Tooltip title="Actualiser">
              <IconButton
                onClick={fetchData}
                sx={{
                  backgroundColor: 'rgba(0,176,240,0.2)',
                  color: '#00D4FF',
                  '&:hover': {
                    backgroundColor: 'rgba(0,176,240,0.3)',
                  }
                }}
              >
                <RefreshIcon sx={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
              </IconButton>
            </Tooltip>
          </Box>
          
          <Box sx={{ display: 'flex', gap: 3, mt: 3 }}>
            <Box
              sx={{
                backgroundColor: 'rgba(0,176,240,0.15)',
                borderRadius: '16px',
                p: 2,
                flex: 1,
                border: '1px solid rgba(0,176,240,0.3)'
              }}
            >
              <Typography sx={{ color: '#00D4FF', fontSize: '0.875rem', mb: 1 }}>
                Total des tâches
              </Typography>
              <Typography sx={{ color: 'white', fontSize: '2rem', fontWeight: 700 }}>
                {tasks.length}
              </Typography>
            </Box>
            
            <Box
              sx={{
                backgroundColor: 'rgba(0,212,255,0.15)',
                borderRadius: '16px',
                p: 2,
                flex: 1,
                border: '1px solid rgba(0,212,255,0.3)'
              }}
            >
              <Typography sx={{ color: '#00D4FF', fontSize: '0.875rem', mb: 1 }}>
                Dernière mise à jour
              </Typography>
              <Typography sx={{ color: 'white', fontSize: '1rem', fontWeight: 600 }}>
                {lastUpdate.toLocaleTimeString('fr-FR')}
              </Typography>
            </Box>
          </Box>
        </Box>
      </Paper>

      {/* Table Section */}
      <Paper
        elevation={0}
        sx={{
          borderRadius: '24px',
          overflow: 'hidden',
          animation: 'slideIn 0.8s ease-out',
          border: '1px solid rgba(0,32,96,0.1)'
        }}
      >
        {loading && tasks.length === 0 ? (
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', py: 8 }}>
            <CircularProgress sx={{ color: '#00B0F0' }} />
          </Box>
        ) : tasks.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 8 }}>
            <AssignmentIcon sx={{ fontSize: 64, color: '#00B0F0', mb: 2, opacity: 0.5 }} />
            <Typography sx={{ color: '#001440', fontSize: '1.25rem', fontWeight: 600 }}>
              Aucune tâche disponible
            </Typography>
            <Typography sx={{ color: '#666', mt: 1 }}>
              Les tâches apparaîtront ici une fois créées
            </Typography>
          </Box>
        ) : (
          <MaterialReactTable
            columns={columns}
            data={tasks}
            enableColumnResizing
            enableStickyHeader
            enableTopToolbar={false}
            enableBottomToolbar={true}
            muiTablePaperProps={{
              elevation: 0,
              sx: {
                borderRadius: 0
              }
            }}
            muiTableProps={{
              sx: {
                border: 'none'
              }
            }}
            muiTableHeadCellProps={{
              sx: {
                backgroundColor: '#002060',
                color: 'white',
                fontWeight: 700,
                fontSize: '0.875rem',
                borderBottom: '2px solid #00B0F0',
                py: 2
              }
            }}
            muiTableBodyCellProps={{
              sx: {
                borderBottom: '1px solid rgba(0,32,96,0.08)',
                py: 2
              }
            }}
            muiTableBodyRowProps={() => ({
              sx: {
                '&:hover': {
                  backgroundColor: 'rgba(0,176,240,0.04)',
                  transition: 'all 0.3s ease'
                }
              }
            })}
          />
        )}
      </Paper>
    </Box>
  );
};

export default Tasks;