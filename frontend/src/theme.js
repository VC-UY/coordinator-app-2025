import { createTheme } from '@mui/material/styles';

// Charte graphique de l'application
const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#3B82F6', // Bleu cyan lumineux
      light: '#60A5FA',
      dark: '#2563EB',
    },
    secondary: {
      main: '#60A5FA',
      light: '#93C5FD',
      dark: '#3B82F6',
    },
    background: {
      default: '#0A1628', // Bleu foncé profond
      paper: '#1E293B', // Fond semi-transparent
    },
    text: {
      primary: '#FFFFFF', // Texte principal blanc
      secondary: '#94A3B8', // Texte secondaire
      disabled: '#CBD5E1',
    },
    divider: '#334155', // Bordures subtiles
  },
  typography: {
    fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      color: '#FFFFFF',
      fontWeight: 700,
    },
    h2: {
      color: '#FFFFFF',
      fontWeight: 700,
    },
    h3: {
      color: '#FFFFFF',
      fontWeight: 600,
    },
    h4: {
      color: '#FFFFFF',
      fontWeight: 600,
    },
    h5: {
      color: '#FFFFFF',
      fontWeight: 600,
    },
    h6: {
      color: '#FFFFFF',
      fontWeight: 600,
    },
    body1: {
      color: '#FFFFFF',
    },
    body2: {
      color: '#FFFFFF',
    },
  },
  components: {
    MuiCssBaseline: {
      styleOverrides: {
        body: {
          background: 'linear-gradient(135deg, #0A1628 0%, #1A2942 50%, #0A1628 100%)',
          backgroundAttachment: 'fixed',
          minHeight: '100vh',
        },
      },
    },
    MuiPaper: {
      styleOverrides: {
        root: {
          backgroundColor: '#1E293B',
          backdropFilter: 'blur(10px)',
          border: '1px solid #334155',
          color: '#FFFFFF',
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundColor: '#1E293B',
          backdropFilter: 'blur(10px)',
          border: '1px solid #334155',
          color: '#FFFFFF',
        },
      },
    },
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1E293B',
          backdropFilter: 'blur(10px)',
          borderBottom: '1px solid #334155',
          color: '#FFFFFF',
        },
      },
    },
    MuiDrawer: {
      styleOverrides: {
        paper: {
          backgroundColor: '#1E293B',
          backdropFilter: 'blur(10px)',
          borderRight: '1px solid #334155',
          color: '#FFFFFF',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          fontWeight: 600,
        },
        contained: {
          backgroundColor: '#3B82F6',
          color: '#FFFFFF',
          '&:hover': {
            backgroundColor: '#2563EB',
            boxShadow: '0 4px 20px rgba(59, 130, 246, 0.4)',
          },
        },
        outlined: {
          borderColor: '#3B82F6',
          color: '#60A5FA',
          '&:hover': {
            borderColor: '#60A5FA',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
          },
        },
        text: {
          color: '#60A5FA',
          '&:hover': {
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
          },
        },
      },
    },
    MuiChip: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          color: '#FFFFFF',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          fontWeight: 600,
        },
      },
    },
    MuiTableCell: {
      styleOverrides: {
        root: {
          borderBottom: '1px solid #334155',
          color: '#FFFFFF',
          backgroundColor: 'transparent',
        },
        head: {
          color: '#60A5FA',
          fontWeight: 700,
          backgroundColor: 'rgba(59, 130, 246, 0.1)',
        },
      },
    },
    MuiTableRow: {
      styleOverrides: {
        root: {
          '&:hover': {
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
          },
        },
      },
    },
    MuiDialog: {
      styleOverrides: {
        paper: {
          backgroundColor: '#1E293B',
          backdropFilter: 'blur(10px)',
          border: '1px solid #334155',
          color: '#FFFFFF',
        },
      },
    },
    MuiDialogTitle: {
      styleOverrides: {
        root: {
          color: '#FFFFFF',
          fontWeight: 700,
        },
      },
    },
    MuiDialogContent: {
      styleOverrides: {
        root: {
          color: '#FFFFFF',
        },
      },
    },
    MuiDialogContentText: {
      styleOverrides: {
        root: {
          color: '#FFFFFF',
        },
      },
    },
    MuiTextField: {
      styleOverrides: {
        root: {
          '& .MuiOutlinedInput-root': {
            color: '#FFFFFF',
            backgroundColor: 'rgba(51, 65, 85, 0.3)',
            '& fieldset': {
              borderColor: '#334155',
            },
            '&:hover fieldset': {
              borderColor: '#3B82F6',
            },
            '&.Mui-focused fieldset': {
              borderColor: '#3B82F6',
              boxShadow: '0 0 10px rgba(59, 130, 246, 0.3)',
            },
          },
          '& .MuiInputLabel-root': {
            color: '#60A5FA',
            '&.Mui-focused': {
              color: '#60A5FA',
            },
          },
          '& .MuiInputBase-input': {
            color: '#FFFFFF',
          },
        },
      },
    },
    MuiSelect: {
      styleOverrides: {
        root: {
          color: '#FFFFFF',
          backgroundColor: 'rgba(51, 65, 85, 0.3)',
          '& .MuiOutlinedInput-notchedOutline': {
            borderColor: '#334155',
          },
          '&:hover .MuiOutlinedInput-notchedOutline': {
            borderColor: '#3B82F6',
          },
          '&.Mui-focused .MuiOutlinedInput-notchedOutline': {
            borderColor: '#3B82F6',
          },
        },
        icon: {
          color: '#60A5FA',
        },
      },
    },
    MuiMenuItem: {
      styleOverrides: {
        root: {
          color: '#FFFFFF',
          backgroundColor: '#1E293B',
          '&:hover': {
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
          },
          '&.Mui-selected': {
            backgroundColor: 'rgba(59, 130, 246, 0.3)',
            '&:hover': {
              backgroundColor: 'rgba(59, 130, 246, 0.4)',
            },
          },
        },
      },
    },
    MuiTab: {
      styleOverrides: {
        root: {
          color: '#60A5FA',
          fontWeight: 600,
          '&.Mui-selected': {
            color: '#3B82F6',
          },
          '&:hover': {
            color: '#3B82F6',
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
          },
        },
      },
    },
    MuiTabs: {
      styleOverrides: {
        root: {
          backgroundColor: 'rgba(30, 41, 59, 0.5)',
          borderRadius: '8px',
        },
        indicator: {
          backgroundColor: '#3B82F6',
          height: 3,
        },
      },
    },
    MuiList: {
      styleOverrides: {
        root: {
          backgroundColor: '#1E293B',
        },
      },
    },
    MuiListItem: {
      styleOverrides: {
        root: {
          color: '#FFFFFF',
          '&:hover': {
            backgroundColor: 'rgba(59, 130, 246, 0.1)',
          },
        },
      },
    },
    MuiListItemText: {
      styleOverrides: {
        primary: {
          color: '#FFFFFF',
        },
        secondary: {
          color: '#60A5FA',
        },
      },
    },
    MuiListItemIcon: {
      styleOverrides: {
        root: {
          color: '#60A5FA',
        },
      },
    },
    MuiIconButton: {
      styleOverrides: {
        root: {
          color: '#60A5FA',
          '&:hover': {
            backgroundColor: 'rgba(59, 130, 246, 0.2)',
          },
        },
      },
    },
    MuiTooltip: {
      styleOverrides: {
        tooltip: {
          backgroundColor: '#1E293B',
          border: '1px solid #334155',
          color: '#FFFFFF',
          fontSize: '0.875rem',
        },
      },
    },
    MuiAlert: {
      styleOverrides: {
        root: {
          backgroundColor: '#1E293B',
          border: '1px solid #334155',
          color: '#FFFFFF',
        },
        standardSuccess: {
          backgroundColor: 'rgba(16, 185, 129, 0.2)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          color: '#10B981',
        },
        standardError: {
          backgroundColor: 'rgba(239, 68, 68, 0.2)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          color: '#EF4444',
        },
        standardWarning: {
          backgroundColor: 'rgba(245, 158, 11, 0.2)',
          border: '1px solid rgba(245, 158, 11, 0.3)',
          color: '#F59E0B',
        },
        standardInfo: {
          backgroundColor: 'rgba(59, 130, 246, 0.2)',
          border: '1px solid rgba(59, 130, 246, 0.3)',
          color: '#3B82F6',
        },
      },
    },
  },
});

export default theme;