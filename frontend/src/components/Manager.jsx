import React, { useEffect, useState } from 'react';
import { Box, Typography, IconButton, Button } from '@mui/material';
import RefreshIcon from '@mui/icons-material/Refresh';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import CancelIcon from '@mui/icons-material/Cancel';
import DeleteIcon from '@mui/icons-material/Delete';
import ShieldIcon from '@mui/icons-material/Shield';
import EmailIcon from '@mui/icons-material/Email';
import CalendarTodayIcon from '@mui/icons-material/CalendarToday';
import AccessTimeIcon from '@mui/icons-material/AccessTime';
import PersonIcon from '@mui/icons-material/Person';
import PersonOffIcon from '@mui/icons-material/PersonOff';
import AxiosInstance from './axios';

const Manager = () => {
  const [myData, setMyData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());

  const fetchData = async () => {
    try {
      const res = await AxiosInstance.get('api/managers/');
      setMyData(res.data);
      setLoading(false);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Error fetching managers:', error);
      setMyData([]);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 2000);
    return () => clearInterval(interval);
  }, []);

  const handleDelete = (id) => {
    if (window.confirm('Êtes-vous sûr de vouloir supprimer ce gestionnaire ?')) {
      AxiosInstance.delete(`api/managers/${id}/`).then(() => fetchData());
    }
  };

  const handleToggleStatus = (manager) => {
    const newStatus = manager.status === 'active' ? 'suspended' : 'active';
    AxiosInstance.patch(`api/managers/${manager.id}/`, { status: newStatus })
      .then(() => fetchData());
    console.log(`Manager ${manager.id} ${manager.username} status changed to ${newStatus}`);
  };

  const activeCount = myData.filter(m => m.status === 'active').length;
  const suspendedCount = myData.filter(m => m.status === 'suspended').length;

  return (
    <Box sx={{ minHeight: '100vh', background: 'linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%)', p: { xs: 2, md: 4 } }}>
      <style>{`
        @keyframes pulse-dot {
          0%, 100% { opacity: 1; transform: scale(1); }
          50% { opacity: 0.5; transform: scale(1.3); }
        }
        
        @keyframes float {
          0%, 100% { transform: translateY(0px); }
          50% { transform: translateY(-10px); }
        }
        
        @keyframes slide-in {
          from { opacity: 0; transform: translateY(-20px); }
          to { opacity: 1; transform: translateY(0); }
        }
      `}</style>

      {/* Header Section */}
      <Box
        sx={{
          position: 'relative',
          background: 'linear-gradient(135deg, #002060 0%, #001440 100%)',
          borderRadius: '24px',
          p: 4,
          mb: 3,
          overflow: 'hidden',
          animation: 'slide-in 0.6s ease-out'
        }}
      >
        {/* Decorative circles */}
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
          {/* Top row */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 3 }}>
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
                <ShieldIcon sx={{ color: 'white', fontSize: 32 }} />
              </Box>
              <Box>
                <Typography variant='h4' sx={{ fontWeight: 700, color: 'white', mb: 0.5 }}>
                  Gestion des Gestionnaires
                </Typography>
                <Typography variant='body2' sx={{ color: '#00D4FF', fontWeight: 500 }}>
                  Administration et supervision des comptes gestionnaires
                </Typography>
              </Box>
            </Box>
            
            <IconButton
              onClick={fetchData}
              sx={{
                backgroundColor: 'rgba(0,176,240,0.2)',
                color: '#00D4FF',
                '&:hover': { backgroundColor: 'rgba(0,176,240,0.3)' }
              }}
            >
              <RefreshIcon sx={{ animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            </IconButton>
          </Box>
          
          {/* Stats cards */}
          <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(4, 1fr)' }, gap: 2 }}>
            <Box
              sx={{
                backgroundColor: 'rgba(0,176,240,0.15)',
                borderRadius: '16px',
                p: 2,
                border: '1px solid rgba(0,176,240,0.3)'
              }}
            >
              <Typography sx={{ color: '#00D4FF', fontSize: '0.875rem', mb: 1 }}>
                Total des gestionnaires
              </Typography>
              <Typography sx={{ color: 'white', fontSize: '2rem', fontWeight: 700 }}>
                {myData.length}
              </Typography>
            </Box>
            
            <Box
              sx={{
                backgroundColor: 'rgba(0,212,255,0.15)',
                borderRadius: '16px',
                p: 2,
                border: '1px solid rgba(0,212,255,0.3)'
              }}
            >
              <Typography sx={{ color: '#00D4FF', fontSize: '0.875rem', mb: 1 }}>
                Actifs
              </Typography>
              <Typography sx={{ color: 'white', fontSize: '2rem', fontWeight: 700 }}>
                {activeCount}
              </Typography>
            </Box>
            
            <Box
              sx={{
                backgroundColor: 'rgba(0,20,64,0.4)',
                borderRadius: '16px',
                p: 2,
                border: '1px solid rgba(0,176,240,0.3)'
              }}
            >
              <Typography sx={{ color: '#00D4FF', fontSize: '0.875rem', mb: 1 }}>
                Suspendus
              </Typography>
              <Typography sx={{ color: 'white', fontSize: '2rem', fontWeight: 700 }}>
                {suspendedCount}
              </Typography>
            </Box>
            
            <Box
              sx={{
                backgroundColor: 'rgba(0,32,96,0.3)',
                borderRadius: '16px',
                p: 2,
                border: '1px solid rgba(0,176,240,0.3)'
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
      </Box>

      {/* Table Section */}
      <Box
        sx={{
          backgroundColor: 'white',
          borderRadius: '24px',
          overflow: 'hidden',
          boxShadow: '0 2px 8px rgba(0,0,0,0.05)',
          border: '1px solid rgba(0,32,96,0.1)',
          animation: 'slide-in 0.8s ease-out'
        }}
      >
        {loading && myData.length === 0 ? (
          <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', py: 10 }}>
            <Box sx={{ position: 'relative', width: 64, height: 64, mb: 2 }}>
              <Box
                sx={{
                  width: '100%',
                  height: '100%',
                  border: '4px solid rgba(0,176,240,0.2)',
                  borderRadius: '50%',
                  position: 'absolute'
                }}
              />
              <Box
                sx={{
                  width: '100%',
                  height: '100%',
                  border: '4px solid #00B0F0',
                  borderTopColor: 'transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite',
                  position: 'absolute'
                }}
              />
            </Box>
            <Typography sx={{ color: '#002060', fontWeight: 500 }}>
              Chargement des gestionnaires...
            </Typography>
          </Box>
        ) : myData.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 10 }}>
            <Box sx={{ animation: 'float 3s ease-in-out infinite', display: 'inline-block', mb: 2 }}>
              <ShieldIcon sx={{ fontSize: 64, color: '#00B0F0', opacity: 0.5 }} />
            </Box>
            <Typography sx={{ color: '#001440', fontSize: '1.25rem', fontWeight: 600, mb: 1 }}>
              Aucun gestionnaire disponible
            </Typography>
            <Typography sx={{ color: '#666' }}>
              Les gestionnaires apparaîtront ici une fois créés
            </Typography>
          </Box>
        ) : (
          <Box sx={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ backgroundColor: '#002060' }}>
                  <th style={{ textAlign: 'left', padding: '16px 24px', color: 'white', fontWeight: 700, fontSize: '0.875rem' }}>
                    Nom d'utilisateur
                  </th>
                  <th style={{ textAlign: 'left', padding: '16px 24px', color: 'white', fontWeight: 700, fontSize: '0.875rem' }}>
                    Email
                  </th>
                  <th style={{ textAlign: 'left', padding: '16px 24px', color: 'white', fontWeight: 700, fontSize: '0.875rem' }}>
                    Statut
                  </th>
                  <th style={{ textAlign: 'left', padding: '16px 24px', color: 'white', fontWeight: 700, fontSize: '0.875rem' }}>
                    Date d'inscription
                  </th>
                  <th style={{ textAlign: 'left', padding: '16px 24px', color: 'white', fontWeight: 700, fontSize: '0.875rem' }}>
                    Dernière connexion
                  </th>
                  <th style={{ textAlign: 'center', padding: '16px 24px', color: 'white', fontWeight: 700, fontSize: '0.875rem' }}>
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {myData.map((manager, index) => (
                  <tr 
                    key={manager.id || index}
                    style={{ 
                      borderBottom: '1px solid rgba(0,32,96,0.1)',
                      transition: 'background-color 0.3s'
                    }}
                    onMouseEnter={(e) => e.currentTarget.style.backgroundColor = 'rgba(0,176,240,0.05)'}
                    onMouseLeave={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    <td style={{ padding: '16px 24px' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5 }}>
                        <Box
                          sx={{
                            width: 40,
                            height: 40,
                            background: 'linear-gradient(135deg, #00B0F0 0%, #00D4FF 100%)',
                            borderRadius: '50%',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            color: 'white',
                            fontWeight: 700
                          }}
                        >
                          {manager.username.charAt(0).toUpperCase()}
                        </Box>
                        <Typography sx={{ color: '#002060', fontWeight: 500 }}>
                          {manager.username}
                        </Typography>
                      </Box>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#001440' }}>
                        <EmailIcon sx={{ fontSize: 16, color: '#00B0F0' }} />
                        {manager.email}
                      </Box>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <Box
                        sx={{
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: 1,
                          backgroundColor: manager.status === 'active' ? '#00B0F0' : '#001440',
                          color: 'white',
                          px: 2,
                          py: 1,
                          borderRadius: '20px',
                          fontSize: '0.875rem',
                          fontWeight: 600
                        }}
                      >
                        {manager.status === 'active' ? (
                          <CheckCircleIcon sx={{ fontSize: 16 }} />
                        ) : (
                          <CancelIcon sx={{ fontSize: 16 }} />
                        )}
                        {manager.status === 'active' ? 'Actif' : 'Suspendu'}
                      </Box>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#001440', fontSize: '0.875rem' }}>
                        <CalendarTodayIcon sx={{ fontSize: 16, color: '#00D4FF' }} />
                        {new Date(manager.registration_date).toLocaleDateString('fr-FR')}
                      </Box>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, color: '#001440', fontSize: '0.875rem' }}>
                        <AccessTimeIcon sx={{ fontSize: 16, color: '#00D4FF' }} />
                        {new Date(manager.last_login).toLocaleDateString('fr-FR')}
                      </Box>
                    </td>
                    <td style={{ padding: '16px 24px' }}>
                      <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1 }}>
                        <Button
                          onClick={() => handleToggleStatus(manager)}
                          variant="contained"
                          startIcon={manager.status === 'active' ? <PersonOffIcon /> : <PersonIcon />}
                          sx={{
                            backgroundColor: manager.status === 'active' ? '#001440' : '#00B0F0',
                            color: 'white',
                            borderRadius: '12px',
                            fontWeight: 600,
                            fontSize: '0.75rem',
                            textTransform: 'none',
                            '&:hover': {
                              backgroundColor: manager.status === 'active' ? '#002060' : '#00D4FF'
                            }
                          }}
                        >
                          {manager.status === 'active' ? 'Suspendre' : 'Activer'}
                        </Button>
                        <IconButton
                          onClick={() => handleDelete(manager.id)}
                          sx={{
                            border: '2px solid #002060',
                            color: '#002060',
                            '&:hover': {
                              backgroundColor: '#002060',
                              color: 'white'
                            }
                          }}
                        >
                          <DeleteIcon sx={{ fontSize: 18 }} />
                        </IconButton>
                      </Box>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </Box>
        )}
      </Box>
    </Box>
  );
};

export default Manager;