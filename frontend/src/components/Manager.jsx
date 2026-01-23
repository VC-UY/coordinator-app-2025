import {React, useEffect, useMemo, useState} from 'react';
import {Box, Chip, Typography, Button, IconButton} from '@mui/material';
import {Link} from 'react-router-dom';
import CalendarViewMonthIcon from '@mui/icons-material/CalendarViewMonth';
import {MaterialReactTable} from 'material-react-table';
import AxiosInstance from './axios';
import DeleteIcon from '@mui/icons-material/Delete';

const Manager = () => {
  const [myData, setMyData] = useState([]);

  const fetchData = () => {
    AxiosInstance.get(`managers/`).then((res) => {
      setMyData(res.data);
    }).catch(error => {
      console.error("Error fetching managers:", error);
      // Ne pas utiliser de données de fallback hardcodées
      setMyData([]);
    });
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = (id) => {
    if(window.confirm('Are you sure you want to delete this manager?')){
      AxiosInstance.delete(`managers/${id}/`).then(() => fetchData());
    }
  };

  const handleToggleStatus = (manager) => {
    const newStatus = manager.status === 'active' ? 'suspended' : 'active';
    AxiosInstance.patch(`managers/${manager.id}/`, { status: newStatus })
      .then(() => fetchData());
    console.log(`Manager ${manager.id} ${manager.username} status changed to ${newStatus}`);
  };
    
  const columns = useMemo(
    () => [
      { 
        accessorKey: 'username', 
        header: 'Name',
        Cell: ({ cell }) => (
          <Typography sx={{ color: '#FFFFFF', fontWeight: 500 }}>
            {cell.getValue()}
          </Typography>
        )
      },
      { 
        accessorKey: 'email', 
        header: 'Email',
        Cell: ({ cell }) => (
          <Typography sx={{ color: '#00B0F0' }}>
            {cell.getValue()}
          </Typography>
        )
      },
      { 
        accessorKey: 'status', 
        header: 'Status',
        Cell: ({ cell }) => {
          const status = cell.getValue();
          return (
            <Chip 
              label={status}
              size="small"
              sx={{
                background: status === 'active' 
                  ? 'linear-gradient(135deg, rgba(0, 255, 136, 0.2) 0%, rgba(0, 200, 100, 0.1) 100%)'
                  : 'linear-gradient(135deg, rgba(255, 165, 0, 0.2) 0%, rgba(255, 140, 0, 0.1) 100%)',
                color: status === 'active' ? '#00FF88' : '#FFA500',
                border: status === 'active' 
                  ? '1px solid rgba(0, 255, 136, 0.3)'
                  : '1px solid rgba(255, 165, 0, 0.3)',
                fontWeight: 600,
                letterSpacing: '0.3px'
              }}
            />
          );
        }
      },
      { 
        accessorKey: 'registration_date', 
        header: 'Registration Date', 
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
        accessorKey: 'last_login', 
        header: 'Last Login', 
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
        header: 'Actions',
        Cell: ({ row }) => (
          <Box sx={{ display: 'flex', flexWrap: 'nowrap', gap: '8px' }}>
            <Button
              variant="outlined"
              size="small"
              onClick={() => handleToggleStatus(row.original)}
              sx={{
                background: row.original.status === 'active' 
                  ? 'rgba(255, 165, 0, 0.1)'
                  : 'rgba(0, 255, 136, 0.1)',
                color: row.original.status === 'active' ? '#FFA500' : '#00FF88',
                borderColor: row.original.status === 'active' 
                  ? 'rgba(255, 165, 0, 0.3)'
                  : 'rgba(0, 255, 136, 0.3)',
                fontWeight: 600,
                letterSpacing: '0.3px',
                transition: 'all 0.3s ease',
                '&:hover': {
                  background: row.original.status === 'active' 
                    ? 'rgba(255, 165, 0, 0.2)'
                    : 'rgba(0, 255, 136, 0.2)',
                  borderColor: row.original.status === 'active' ? '#FFA500' : '#00FF88',
                  transform: 'translateY(-2px)',
                  boxShadow: row.original.status === 'active' 
                    ? '0 4px 12px rgba(255, 165, 0, 0.3)'
                    : '0 4px 12px rgba(0, 255, 136, 0.3)'
                }
              }}
            >
              {row.original.status === 'active' ? 'Suspend' : 'Activate'}
            </Button>
            <IconButton 
              onClick={() => handleDelete(row.original.id)}
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
              <DeleteIcon />
            </IconButton>
          </Box>
        ),
        enableColumnActions: false,
        enableSorting: false,
        size: 120,
      }
    ],
    []
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
        <CalendarViewMonthIcon sx={{ mr: 2, color: '#00D4FF' }} />
        <Typography sx={{ 
          fontWeight: 700,
          letterSpacing: '0.5px',
          background: 'linear-gradient(135deg, #FFFFFF 0%, #00D4FF 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent'
        }} variant='h5'>
          All Managers
        </Typography>
      </Box>

      {/* Table Container */}
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
              '& .Mui-TableHeadCell-Content': {
                color: '#00D4FF'
              },
              '& .MuiTableSortLabel-root': {
                color: '#00D4FF',
                '&:hover': {
                  color: '#00D4FF'
                },
                '&.Mui-active': {
                  color: '#00D4FF'
                }
              },
              '& .MuiTableSortLabel-icon': {
                color: '#00D4FF !important'
              }
            }
          }}
          muiTableBodyRowProps={({ row }) => ({
            sx: {
              background: 'transparent',
              transition: 'all 0.3s ease',
              '&:hover': {
                background: 'rgba(0, 180, 240, 0.05)',
                transform: 'translateX(5px)'
              }
            }
          })}
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
              '& .MuiIconButton-root': {
                color: '#00D4FF'
              },
              '& .MuiInputBase-root': {
                color: '#FFFFFF',
                background: 'rgba(0, 0, 0, 0.3)',
                border: '2px solid rgba(0, 180, 240, 0.3)',
                borderRadius: '12px',
                '&:hover': {
                  background: 'rgba(0, 0, 0, 0.4)'
                },
                '&.Mui-focused': {
                  borderColor: '#00D4FF',
                  boxShadow: '0 0 20px rgba(0, 212, 255, 0.3)'
                }
              },
              '& .MuiInputBase-input': {
                color: '#FFFFFF',
                '&::placeholder': {
                  color: 'rgba(0, 180, 240, 0.6)'
                }
              },
              '& .MuiSvgIcon-root': {
                color: '#00B0F0'
              }
            }
          }}
          muiBottomToolbarProps={{
            sx: {
              background: 'transparent',
              color: '#FFFFFF',
              '& .MuiTablePagination-root': {
                color: '#FFFFFF'
              },
              '& .MuiIconButton-root': {
                color: '#00D4FF',
                '&.Mui-disabled': {
                  color: 'rgba(0, 180, 240, 0.3)'
                }
              },
              '& .MuiTablePagination-selectLabel, & .MuiTablePagination-displayedRows': {
                color: '#00B0F0'
              },
              '& .MuiSelect-select': {
                color: '#FFFFFF'
              },
              '& .MuiTablePagination-actions': {
                '& .MuiIconButton-root': {
                  background: 'rgba(0, 180, 240, 0.1)',
                  border: '1px solid rgba(0, 180, 240, 0.3)',
                  margin: '0 4px',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    background: 'rgba(0, 180, 240, 0.2)',
                    borderColor: '#00D4FF',
                    transform: 'translateY(-2px)'
                  },
                  '&.Mui-disabled': {
                    background: 'transparent',
                    borderColor: 'rgba(0, 180, 240, 0.1)'
                  }
                }
              }
            }
          }}
          muiTablePaperProps={{
            sx: {
              background: 'transparent',
              boxShadow: 'none'
            }
          }}
          muiSearchTextFieldProps={{
            placeholder: 'Search managers...',
            sx: {
              '& .MuiOutlinedInput-root': {
                color: '#FFFFFF',
                background: 'rgba(0, 0, 0, 0.3)',
                borderRadius: '12px',
                '& fieldset': {
                  borderColor: 'rgba(0, 180, 240, 0.3)',
                  borderWidth: '2px'
                },
                '&:hover fieldset': {
                  borderColor: 'rgba(0, 180, 240, 0.5)'
                },
                '&.Mui-focused fieldset': {
                  borderColor: '#00D4FF',
                  boxShadow: '0 0 20px rgba(0, 212, 255, 0.3)'
                }
              },
              '& .MuiInputBase-input': {
                color: '#FFFFFF',
                '&::placeholder': {
                  color: 'rgba(0, 180, 240, 0.6)',
                  opacity: 1
                }
              }
            }
          }}
          muiSelectCheckboxProps={{
            sx: {
              color: '#00D4FF',
              '&.Mui-checked': {
                color: '#00D4FF'
              }
            }
          }}
          muiSelectAllCheckboxProps={{
            sx: {
              color: '#00D4FF',
              '&.Mui-checked': {
                color: '#00D4FF'
              }
            }
          }}
        />
      </Box>
    </Box>
  );
};

export default Manager;