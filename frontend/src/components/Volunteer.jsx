import {React, useEffect, useMemo,useState} from 'react'
import {Box,Typography,Drawer,IconButton,Divider,Card,CardContent,Avatar,Chip,Stack, Button, Toolbar, Dialog, DialogTitle, DialogContent, DialogActions, TextField, Tooltip} from '@mui/material'
import CalendarViewMonthIcon from '@mui/icons-material/CalendarViewMonth';
import CloseIcon from '@mui/icons-material/Close';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import DeleteIcon from '@mui/icons-material/Delete';
import PersonIcon from '@mui/icons-material/Person';
import MemoryIcon from '@mui/icons-material/Memory';
import StorageIcon from '@mui/icons-material/Storage';
import ComputerIcon from '@mui/icons-material/Computer';
import DnsIcon from '@mui/icons-material/Dns';
import LanIcon from '@mui/icons-material/Lan';
import {MaterialReactTable} from 'material-react-table';
import AxiosInstance from './axios';

const Volunteer = () =>{
    const [myData, setMyData] = useState([]);
    const [drawerOpen, setDrawerOpen] = useState(false);
    const [selectedVolunteer, setSelectedVolunteer] = useState(null);
    const [deleteId, setDeleteId] = useState(null);

    const fetchData = () => {
      AxiosInstance.get(`volunteers/`).then((res) => {
        setMyData(res.data);
      }).catch(error => {
        console.error("Error fetching volunteers:", error);
        // Ne pas utiliser de données de fallback hardcodées
        setMyData([]);
      });
    };

    useEffect(() => {
      fetchData();
      const interval = setInterval(fetchData, 2000);
      return () => clearInterval(interval);
    }, []);

    const columns = useMemo(
        () => [
            {
              accessorKey:'name', 
              header: 'Name',
              Cell: ({ cell }) => (
                <Typography sx={{ color: '#FFFFFF', fontWeight: 500 }}>
                  {cell.getValue()}
                </Typography>
              )
            },
            {
              accessorKey:'status', 
              header: 'Status',
              Cell: ({ cell }) => {
                const status = cell.getValue();
                const statusColors = {
                  'available': { bg: 'rgba(0, 255, 136, 0.15)', color: '#00FF88', border: 'rgba(0, 255, 136, 0.3)' },
                  'busy': { bg: 'rgba(255, 165, 0, 0.15)', color: '#FFA500', border: 'rgba(255, 165, 0, 0.3)' },
                  'offline': { bg: 'rgba(136, 136, 136, 0.15)', color: '#888888', border: 'rgba(136, 136, 136, 0.3)' }
                };
                const style = statusColors[status] || statusColors['offline'];
                return (
                  <Chip 
                    label={status}
                    size="small"
                    sx={{
                      background: style.bg,
                      color: style.color,
                      border: `1px solid ${style.border}`,
                      fontWeight: 600,
                      letterSpacing: '0.3px'
                    }}
                  />
                );
              }
            },
            {
              accessorKey:'last_update', 
              header: 'Last Update', 
              Cell: ({ cell }) => {
                const date = new Date(cell.getValue());
                return (
                  <Typography sx={{ color: '#00B0F0', fontSize: '0.9rem' }}>
                    {date.toLocaleDateString()}
                  </Typography>
                );
              }
            },
            {
              accessorKey:'last_activity', 
              header: 'Last Activity', 
              Cell: ({ cell }) => (
                <Typography sx={{ color: '#00B0F0', fontSize: '0.9rem' }}>
                  {cell.getValue() ? new Date(cell.getValue()).toLocaleString() : '—'}
                </Typography>
              )
            },
            {
              accessorKey:'cpu_model', 
              header: 'CPU',
              Cell: ({ cell }) => (
                <Typography sx={{ color: '#FFFFFF', fontSize: '0.9rem' }}>
                  {cell.getValue()}
                </Typography>
              )
            },
            {
              accessorKey:'total_ram', 
              header: 'RAM (MB)',
              Cell: ({ cell }) => (
                <Typography sx={{ color: '#00D4FF', fontWeight: 600 }}>
                  {cell.getValue()}
                </Typography>
              )
            },
            {
                header: 'Actions',
                Cell: ({ row }) => (
                    <Stack direction="row" spacing={1}>
                        <Tooltip title="Delete">
                          <IconButton  
                            onClick={e => {e.stopPropagation(); handleDelete(row.original.id);}}
                            sx={{
                              color: '#FF4444',
                              background: 'rgba(220, 38, 38, 0.1)',
                              border: '1px solid rgba(220, 38, 38, 0.3)',
                              transition: 'all 0.3s ease',
                              '&:hover': {
                                background: 'rgba(220, 38, 38, 0.2)',
                                transform: 'translateY(-2px)',
                                boxShadow: '0 4px 12px rgba(220, 38, 38, 0.3)'
                              }
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                    </Stack>
                ),
                enableColumnActions: false,
                enableSorting: false,
                size: 80,
            }
        ],[])

    const handleRowClick = (row) => {
        setSelectedVolunteer(row.original);
        setDrawerOpen(true);
    };

    const handleDrawerClose = () => {
        setDrawerOpen(false);
        setSelectedVolunteer(null);
    };

    const handleDelete = (id) => {
        setDeleteId(id);
        if(window.confirm('Are you sure you want to delete this volunteer?')){
            AxiosInstance.delete(`volunteers/${id}/`).then(() => fetchData())
                .catch(error => {
                    console.error("Error deleting volunteer:", error);
                });
        }
    };

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
                <CalendarViewMonthIcon sx={{ mr: 2, color: '#00D4FF' }} />
                <Typography sx={{ 
                  fontWeight: 700,
                  letterSpacing: '0.5px',
                  background: 'linear-gradient(135deg, #FFFFFF 0%, #00D4FF 100%)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent'
                }} variant='h5'>
                  All Volunteers
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
                  data={myData}
                  muiTableBodyRowProps={({ row }) => ({
                      onClick: () => handleRowClick(row),
                      style: { cursor: 'pointer' },
                      sx: {
                        background: 'transparent',
                        transition: 'all 0.3s ease',
                        '&:hover': {
                          background: 'rgba(0, 180, 240, 0.05)',
                          transform: 'translateX(5px)'
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
                      },
                      '& .MuiSvgIcon-root': { color: '#00B0F0' }
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
                      },
                      '& .MuiSelect-select': { color: '#FFFFFF' }
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

            {/* Drawer for details */}
            <Drawer 
              anchor="right" 
              open={drawerOpen} 
              onClose={handleDrawerClose}
              PaperProps={{
                sx: {
                  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.98) 0%, rgba(0, 20, 64, 0.98) 100%)',
                  backdropFilter: 'blur(20px)',
                  borderLeft: '2px solid rgba(0, 180, 240, 0.3)',
                  boxShadow: '-8px 0 32px rgba(0, 32, 96, 0.7)'
                }
              }}
            >
                <Box sx={{ width: 400, p: 0, height: '100%' }}>
                    {/* Drawer Header */}
                    <Box sx={{
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'space-between',
                      background: 'linear-gradient(135deg, rgba(0, 180, 240, 0.2) 0%, rgba(0, 212, 255, 0.1) 100%)',
                      borderBottom: '2px solid rgba(0, 180, 240, 0.3)',
                      color: 'white', 
                      px: 3, 
                      py: 2
                    }}>
                        <Stack direction="row" alignItems="center" spacing={2}>
                            <Avatar sx={{ 
                              bgcolor: 'rgba(0, 212, 255, 0.2)', 
                              color: '#00D4FF',
                              border: '2px solid rgba(0, 212, 255, 0.3)'
                            }}>
                              <PersonIcon />
                            </Avatar>
                            <Typography variant="h6" sx={{ 
                              fontWeight: 700,
                              color: '#FFFFFF',
                              letterSpacing: '0.3px'
                            }}>
                              Volunteer Details
                            </Typography>
                        </Stack>
                        <IconButton 
                          onClick={handleDrawerClose} 
                          sx={{ 
                            color: '#00D4FF',
                            background: 'rgba(0, 180, 240, 0.1)',
                            border: '1px solid rgba(0, 180, 240, 0.3)',
                            '&:hover': {
                              background: 'rgba(0, 180, 240, 0.2)',
                              transform: 'rotate(90deg)'
                            },
                            transition: 'all 0.3s ease'
                          }}
                        >
                          <CloseIcon />
                        </IconButton>
                    </Box>

                    <Box sx={{ p: 3 }}>
                      <Card sx={{ 
                        boxShadow: '0 8px 32px rgba(0, 32, 96, 0.5)',
                        background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
                        backdropFilter: 'blur(20px)',
                        border: '2px solid rgba(0, 180, 240, 0.3)',
                        borderRadius: 2
                      }}>
                        <CardContent>
                            {selectedVolunteer && (
                                <Box>
                                    {/* General Info Section */}
                                    <Typography variant="subtitle1" sx={{ 
                                      fontWeight: 600, 
                                      mb: 2,
                                      color: '#00D4FF',
                                      letterSpacing: '0.3px'
                                    }}>
                                      General
                                    </Typography>
                                    <Divider sx={{ mb: 2, borderColor: 'rgba(0, 180, 240, 0.3)' }} />
                                    
                                    <Stack direction="row" alignItems="center" spacing={2} mb={2}>
                                        <Avatar sx={{ 
                                          bgcolor: 'rgba(0, 212, 255, 0.2)', 
                                          color: '#00D4FF', 
                                          width: 56, 
                                          height: 56, 
                                          fontSize: 24,
                                          border: '2px solid rgba(0, 212, 255, 0.3)',
                                          fontWeight: 700
                                        }}>
                                            {selectedVolunteer.name ? selectedVolunteer.name[0].toUpperCase() : '?'}
                                        </Avatar>
                                        <Box>
                                            <Typography variant="h6" sx={{ color: '#FFFFFF', fontWeight: 600 }}>
                                              {selectedVolunteer.name}
                                            </Typography>
                                            <Chip 
                                              label={selectedVolunteer.current_status} 
                                              size="small" 
                                              sx={{ 
                                                mt: 1,
                                                background: selectedVolunteer.current_status === 'available' 
                                                  ? 'rgba(0, 255, 136, 0.15)' 
                                                  : 'rgba(136, 136, 136, 0.15)',
                                                color: selectedVolunteer.current_status === 'available' ? '#00FF88' : '#888888',
                                                border: selectedVolunteer.current_status === 'available'
                                                  ? '1px solid rgba(0, 255, 136, 0.3)'
                                                  : '1px solid rgba(136, 136, 136, 0.3)',
                                                fontWeight: 600
                                              }} 
                                            />
                                        </Box>
                                    </Stack>

                                    <Typography sx={{ color: '#00B0F0', mb: 1, fontSize: '0.9rem' }}>
                                      <strong>Last Update:</strong> {new Date(selectedVolunteer.last_update).toLocaleString()}
                                    </Typography>
                                    <Typography sx={{ color: '#00B0F0', mb: 3, fontSize: '0.9rem' }}>
                                      <strong>Last Activity:</strong> {selectedVolunteer.last_activity ? new Date(selectedVolunteer.last_activity).toLocaleString() : '—'}
                                    </Typography>

                                    {/* Hardware Section */}
                                    <Typography variant="subtitle1" sx={{ 
                                      fontWeight: 600, 
                                      mt: 3, 
                                      mb: 2,
                                      color: '#00D4FF',
                                      letterSpacing: '0.3px',
                                      display: 'flex',
                                      alignItems: 'center'
                                    }}>
                                      <MemoryIcon fontSize="small" sx={{ mr: 1 }} /> Hardware
                                    </Typography>
                                    <Divider sx={{ mb: 2, borderColor: 'rgba(0, 180, 240, 0.3)' }} />
                                    
                                    <Stack spacing={1.5}>
                                        {[
                                          { label: 'CPU Model', value: selectedVolunteer.cpu_model },
                                          { label: 'CPU Cores', value: selectedVolunteer.cpu_cores },
                                          { label: 'Total RAM', value: selectedVolunteer.total_ram },
                                          { label: 'Available Storage', value: selectedVolunteer.available_storage },
                                          { label: 'Operating System', value: selectedVolunteer.operating_system },
                                          { label: 'GPU Available', value: selectedVolunteer.gpu_available ? 'Yes' : 'No' },
                                          { label: 'GPU Model', value: selectedVolunteer.gpu_model },
                                          { label: 'GPU Memory', value: selectedVolunteer.gpu_memory }
                                        ].map((item, idx) => (
                                          <Box key={idx} sx={{
                                            p: 1.5,
                                            background: 'rgba(0, 180, 240, 0.05)',
                                            borderRadius: 1,
                                            border: '1px solid rgba(0, 180, 240, 0.1)'
                                          }}>
                                            <Typography sx={{ color: '#00B0F0', fontSize: '0.85rem' }}>
                                              <strong>{item.label}:</strong>
                                            </Typography>
                                            <Typography sx={{ color: '#FFFFFF', fontSize: '0.9rem', mt: 0.5 }}>
                                              {item.value || '—'}
                                            </Typography>
                                          </Box>
                                        ))}
                                    </Stack>

                                    {/* Network Section */}
                                    <Typography variant="subtitle1" sx={{ 
                                      fontWeight: 600, 
                                      mt: 3, 
                                      mb: 2,
                                      color: '#00D4FF',
                                      letterSpacing: '0.3px',
                                      display: 'flex',
                                      alignItems: 'center'
                                    }}>
                                      <LanIcon fontSize="small" sx={{ mr: 1 }} /> Network
                                    </Typography>
                                    <Divider sx={{ mb: 2, borderColor: 'rgba(0, 180, 240, 0.3)' }} />
                                    
                                    <Stack spacing={1.5}>
                                        {[
                                          { label: 'IP Address', value: selectedVolunteer.ip_address },
                                          { label: 'Communication Port', value: selectedVolunteer.communication_port }
                                        ].map((item, idx) => (
                                          <Box key={idx} sx={{
                                            p: 1.5,
                                            background: 'rgba(0, 180, 240, 0.05)',
                                            borderRadius: 1,
                                            border: '1px solid rgba(0, 180, 240, 0.1)'
                                          }}>
                                            <Typography sx={{ color: '#00B0F0', fontSize: '0.85rem' }}>
                                              <strong>{item.label}:</strong>
                                            </Typography>
                                            <Typography sx={{ color: '#FFFFFF', fontSize: '0.9rem', mt: 0.5 }}>
                                              {item.value || '—'}
                                            </Typography>
                                          </Box>
                                        ))}
                                    </Stack>

                                    {/* Preferences Section */}
                                    <Typography variant="subtitle1" sx={{ 
                                      fontWeight: 600, 
                                      mt: 3, 
                                      mb: 2,
                                      color: '#00D4FF',
                                      letterSpacing: '0.3px',
                                      display: 'flex',
                                      alignItems: 'center'
                                    }}>
                                      <DnsIcon fontSize="small" sx={{ mr: 1 }} /> Preferences
                                    </Typography>
                                    <Divider sx={{ mb: 2, borderColor: 'rgba(0, 180, 240, 0.3)' }} />
                                    
                                    <Box sx={{
                                      p: 2,
                                      background: 'rgba(0, 0, 0, 0.3)',
                                      borderRadius: 1,
                                      border: '1px solid rgba(0, 180, 240, 0.2)',
                                      maxHeight: 200,
                                      overflowY: 'auto'
                                    }}>
                                      <Typography sx={{ 
                                        color: '#00D4FF', 
                                        fontSize: '0.85rem',
                                        fontFamily: 'monospace',
                                        whiteSpace: 'pre-wrap',
                                        wordBreak: 'break-word'
                                      }}>
                                        {JSON.stringify(selectedVolunteer.preferences, null, 2)}
                                      </Typography>
                                    </Box>
                                </Box>
                            )}
                        </CardContent>
                      </Card>
                    </Box>
                </Box>
            </Drawer>
        </Box>
    )
}

export default Volunteer