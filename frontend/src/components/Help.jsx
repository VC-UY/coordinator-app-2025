import React, { useState } from 'react';
import {
  Box,
  Typography,
  Paper,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Grid,
  Card,
  CardContent,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Chip
} from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import HelpOutlineIcon from '@mui/icons-material/HelpOutline';
import DashboardIcon from '@mui/icons-material/Dashboard';
import GroupIcon from '@mui/icons-material/Group';
import AssignmentIcon from '@mui/icons-material/Assignment';
import SettingsIcon from '@mui/icons-material/Settings';
import SecurityIcon from '@mui/icons-material/Security';
import InfoIcon from '@mui/icons-material/Info';

const Help = () => {
  const [expanded, setExpanded] = useState('getting-started');

  const handleChange = (panel) => (event, isExpanded) => {
    setExpanded(isExpanded ? panel : false);
  };

  const quickLinks = [
    {
      title: 'Managing Volunteers',
      description: 'Learn how to add, monitor, and manage volunteers in your system',
      icon: <GroupIcon sx={{ color: '#00FF88' }} />,
      link: '/volunteer'
    },
    {
      title: 'Managing Workflows',
      description: 'Create and manage workflows to coordinate distributed tasks',
      icon: <AssignmentIcon sx={{ color: '#00B0F0' }} />,
      link: '/workflows'
    },
    {
      title: 'System Status',
      description: 'Monitor system health and connected clients in real-time',
      icon: <DashboardIcon sx={{ color: '#00D4FF' }} />,
      link: '/system-status'
    },
    {
      title: 'Security & Validation',
      description: 'Manage client validation, security alerts, and access control',
      icon: <SecurityIcon sx={{ color: '#FFA500' }} />,
      link: '/client-validation'
    }
  ];

  const faqSections = [
    {
      id: 'getting-started',
      title: 'Getting Started',
      questions: [
        {
          question: 'What is the Coordinator App?',
          answer: 'The Coordinator App is a distributed computing platform that helps manage volunteers (computing nodes), workflows, and tasks across multiple machines. It allows you to coordinate complex computational tasks and distribute them efficiently.'
        },
        {
          question: 'How do I add a new volunteer to the system?',
          answer: 'Volunteers are automatically registered when they connect to the coordinator. You can monitor new registration requests in the Client Validation page and approve or reject them based on your security requirements.'
        },
        {
          question: 'What are workflows and tasks?',
          answer: 'Workflows are collections of related tasks that need to be executed. Tasks are individual units of work that can be assigned to volunteers. Workflows can have dependencies between tasks, priorities, and resource requirements.'
        }
      ]
    },
    {
      id: 'managers',
      title: 'Managing Managers',
      questions: [
        {
          question: 'How do I create a new manager account?',
          answer: 'Navigate to the Managers page and click "Create New Manager". Fill in the username, email, and password fields. You can also set the initial status (active, inactive, or suspended).'
        },
        {
          question: 'What are the different manager statuses?',
          answer: 'Managers can have three statuses: Active (full access), Inactive (temporarily disabled), and Suspended (access revoked, usually for security reasons).'
        },
        {
          question: 'Can I delete a manager?',
          answer: 'Yes, you can delete a manager by clicking the delete icon in the managers list. This action will remove the manager from the system and publish a disconnect notification to all connected clients.'
        }
      ]
    },
    {
      id: 'volunteers',
      title: 'Managing Volunteers',
      questions: [
        {
          question: 'How do I monitor volunteer status?',
          answer: 'The Volunteer page shows real-time status of all connected volunteers including their availability (available, busy, offline), last activity, CPU model, RAM, and other technical specifications.'
        },
        {
          question: 'What does volunteer status mean?',
          answer: 'Available: volunteer is ready to accept tasks. Busy: volunteer is currently executing a task. Offline: volunteer is disconnected from the coordinator.'
        },
        {
          question: 'How can I view detailed volunteer information?',
          answer: 'Click on any volunteer row in the table to open a detailed drawer showing technical specifications, IP address, connection status, and resource utilization.'
        }
      ]
    },
    {
      id: 'workflows',
      title: 'Workflows & Tasks',
      questions: [
        {
          question: 'How do I create a workflow?',
          answer: 'Use the workflow creation form to define a new workflow. Specify the workflow name, type, priority, and any required resources. Once created, you can add tasks to the workflow.'
        },
        {
          question: 'How are tasks assigned to volunteers?',
          answer: 'Tasks are automatically assigned to available volunteers based on resource requirements, volunteer capabilities, and task priorities. You can also manually assign tasks if needed.'
        },
        {
          question: 'Can I stop or pause a running workflow?',
          answer: 'Yes, you can stop or pause workflows using the action buttons. Stopping a workflow will pause all associated tasks, and they can be resumed later.'
        },
        {
          question: 'What are task dependencies?',
          answer: 'Task dependencies define the execution order. A task with dependencies will only start when all its prerequisite tasks are completed successfully.'
        }
      ]
    },
    {
      id: 'security',
      title: 'Security & Validation',
      questions: [
        {
          question: 'How does client validation work?',
          answer: 'When a new client (volunteer or manager) attempts to connect, a registration request is created. Administrators can review these requests in the Client Validation page and approve or reject them.'
        },
        {
          question: 'What are security alerts?',
          answer: 'Security alerts are generated when suspicious activity is detected, such as multiple failed login attempts, unauthorized access attempts, or unusual network patterns.'
        },
        {
          question: 'How do I block an IP address?',
          answer: 'In the Client Validation page, navigate to the IP Blacklist tab. You can add IP addresses or ranges to block specific clients from connecting to the coordinator.'
        }
      ]
    },
    {
      id: 'troubleshooting',
      title: 'Troubleshooting',
      questions: [
        {
          question: 'Why are my volunteers not appearing?',
          answer: 'Make sure the volunteers are running and properly configured to connect to the coordinator. Check the network connection, coordinator URL, and ensure the volunteers have been approved in the Client Validation page.'
        },
        {
          question: 'Tasks are not being assigned. What should I check?',
          answer: 'Verify that: 1) Volunteers are in "available" status, 2) Task resource requirements match volunteer capabilities, 3) All task dependencies are satisfied, 4) The workflow is in a valid state (not paused or failed).'
        },
        {
          question: 'The dashboard shows no data. What could be wrong?',
          answer: 'This usually indicates a connection issue with the backend API. Check that the Django backend server is running, MongoDB is accessible, and there are no network issues. Check the browser console for specific error messages.'
        }
      ]
    }
  ];

  return (
    <Box sx={{
      p: { xs: 2, md: 4 },
      background: 'linear-gradient(180deg, #001440 0%, #002060 50%, #001440 100%)',
      minHeight: '100vh'
    }}>
      {/* Header */}
      <Paper
        elevation={0}
        sx={{
          p: 4,
          mb: 4,
          borderRadius: 3,
          textAlign: 'center',
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.9) 0%, rgba(0, 20, 64, 0.9) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 180, 240, 0.3)',
          boxShadow: '0 12px 48px rgba(0, 32, 96, 0.6)',
        }}
      >
        <HelpOutlineIcon sx={{ fontSize: 64, color: '#00D4FF', mb: 2 }} />
        <Typography variant="h4" fontWeight={700} gutterBottom sx={{
          background: 'linear-gradient(135deg, #FFFFFF 0%, #00D4FF 100%)',
          WebkitBackgroundClip: 'text',
          WebkitTextFillColor: 'transparent',
          letterSpacing: '0.5px'
        }}>
          Help & Documentation
        </Typography>
        <Typography variant="subtitle1" sx={{ color: '#00B0F0' }}>
          Find answers to common questions and learn how to use the Coordinator App
        </Typography>
      </Paper>

      {/* Quick Links */}
      <Typography variant="h5" fontWeight={600} mb={3} sx={{ color: '#FFFFFF' }}>
        Quick Links
      </Typography>
      <Grid container spacing={3} mb={4}>
        {quickLinks.map((link, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card
              sx={{
                height: '100%',
                background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
                backdropFilter: 'blur(20px)',
                border: '2px solid rgba(0, 180, 240, 0.3)',
                borderRadius: 2,
                transition: 'all 0.3s ease',
                cursor: 'pointer',
                '&:hover': {
                  transform: 'translateY(-8px)',
                  borderColor: '#00D4FF',
                  boxShadow: '0 12px 40px rgba(0, 180, 240, 0.3)'
                }
              }}
              onClick={() => window.location.href = link.link}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                  {link.icon}
                  <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF', ml: 1 }}>
                    {link.title}
                  </Typography>
                </Box>
                <Typography variant="body2" sx={{ color: '#00B0F0' }}>
                  {link.description}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* FAQ Sections */}
      <Typography variant="h5" fontWeight={600} mb={3} sx={{ color: '#FFFFFF' }}>
        Frequently Asked Questions
      </Typography>
      <Box>
        {faqSections.map((section) => (
          <Box key={section.id} mb={2}>
            <Typography variant="h6" fontWeight={600} sx={{ color: '#00D4FF', mb: 2 }}>
              {section.title}
            </Typography>
            {section.questions.map((item, index) => (
              <Accordion
                key={index}
                expanded={expanded === `${section.id}-${index}`}
                onChange={handleChange(`${section.id}-${index}`)}
                sx={{
                  mb: 1,
                  background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
                  backdropFilter: 'blur(20px)',
                  border: '2px solid rgba(0, 180, 240, 0.3)',
                  borderRadius: '8px !important',
                  '&:before': { display: 'none' },
                  '&.Mui-expanded': {
                    borderColor: '#00D4FF',
                  }
                }}
              >
                <AccordionSummary
                  expandIcon={<ExpandMoreIcon sx={{ color: '#00D4FF' }} />}
                  sx={{
                    '& .MuiAccordionSummary-content': {
                      my: 2
                    }
                  }}
                >
                  <Typography fontWeight={500} sx={{ color: '#FFFFFF' }}>
                    {item.question}
                  </Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Divider sx={{ mb: 2, borderColor: 'rgba(0, 180, 240, 0.3)' }} />
                  <Typography sx={{ color: '#00B0F0' }}>
                    {item.answer}
                  </Typography>
                </AccordionDetails>
              </Accordion>
            ))}
          </Box>
        ))}
      </Box>

      {/* Additional Resources */}
      <Paper
        elevation={0}
        sx={{
          p: 3,
          mt: 4,
          borderRadius: 2,
          background: 'linear-gradient(135deg, rgba(0, 32, 96, 0.6) 0%, rgba(0, 20, 64, 0.6) 100%)',
          backdropFilter: 'blur(20px)',
          border: '2px solid rgba(0, 180, 240, 0.3)'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <InfoIcon sx={{ color: '#00D4FF', mr: 1 }} />
          <Typography variant="h6" fontWeight={600} sx={{ color: '#FFFFFF' }}>
            Additional Resources
          </Typography>
        </Box>
        <List>
          <ListItem>
            <ListItemIcon>
              <Chip label="API" size="small" sx={{ bgcolor: '#00B0F0', color: '#001440' }} />
            </ListItemIcon>
            <ListItemText
              primary="API Documentation"
              secondary="Access the full API documentation at /api/docs/ for detailed endpoint information"
              primaryTypographyProps={{ sx: { color: '#FFFFFF' } }}
              secondaryTypographyProps={{ sx: { color: '#00B0F0' } }}
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <Chip label="LOGS" size="small" sx={{ bgcolor: '#00FF88', color: '#001440' }} />
            </ListItemIcon>
            <ListItemText
              primary="System Logs"
              secondary="View detailed system logs in the Logs page for debugging and monitoring"
              primaryTypographyProps={{ sx: { color: '#FFFFFF' } }}
              secondaryTypographyProps={{ sx: { color: '#00B0F0' } }}
            />
          </ListItem>
          <ListItem>
            <ListItemIcon>
              <Chip label="SUPPORT" size="small" sx={{ bgcolor: '#FFA500', color: '#001440' }} />
            </ListItemIcon>
            <ListItemText
              primary="Technical Support"
              secondary="For technical support and bug reports, contact your system administrator"
              primaryTypographyProps={{ sx: { color: '#FFFFFF' } }}
              secondaryTypographyProps={{ sx: { color: '#00B0F0' } }}
            />
          </ListItem>
        </List>
      </Paper>
    </Box>
  );
};

export default Help;
