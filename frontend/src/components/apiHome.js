// Utility functions to fetch homepage data
import AxiosInstance from './axios';

export const fetchManagersCount = async () => {
  const res = await AxiosInstance.get('managers/');
  return Array.isArray(res.data) ? res.data.length : 0;
};

export const fetchVolunteersCount = async () => {
  const res = await AxiosInstance.get('volunteers/');
  return Array.isArray(res.data) ? res.data.length : 0;
};


export const fetchWorkflowsCount = async () => {
  const res = await AxiosInstance.get('workflows/');
  return Array.isArray(res.data) ? res.data.length : 0;
};

export const fetchTasksCount = async () => {
  const res = await AxiosInstance.get('tasks/');
  return Array.isArray(res.data) ? res.data.length : 0;
};

export const fetchRecentLogs = async () => {
  // Note: Vérifiez si cet endpoint existe réellement dans votre backend
  const res = await AxiosInstance.get('communication/logs/?limit=5');
  return Array.isArray(res.data) ? res.data : [];
};

export const fetchAnnouncements = async () => {
  // Note: Vérifiez si cet endpoint existe réellement dans votre backend
  const res = await AxiosInstance.get('communication/announcements/?limit=3');
  return Array.isArray(res.data) ? res.data : [];
};

export const fetchActiveVolunteers = async () => {
  const res = await AxiosInstance.get('volunteers/?status=available&limit=5');
  return Array.isArray(res.data) ? res.data : [];
};

export const fetchRunningWorkflows = async () => {
  const res = await AxiosInstance.get('workflows/?status=RUNNING');
  return Array.isArray(res.data) ? res.data : [];
};

export const fetchWorkflowTasks = async (workflowId) => {
  const res = await AxiosInstance.get(`tasks/?workflow=${workflowId}`);
  return Array.isArray(res.data) ? res.data : [];
};

export const fetchRunningWorkflowsWithTasks = async () => {
  const workflowsRes = await AxiosInstance.get('workflows/');
  const workflows = Array.isArray(workflowsRes.data) ? workflowsRes.data : [];

  // Récupérer les tâches pour chaque workflow
  const workflowsWithTasks = await Promise.all(
    workflows.map(async (wf) => {
      try {
        const tasksRes = await AxiosInstance.get(`tasks/?workflow=${wf.id}`);
        return {
          ...wf,
          tasks: Array.isArray(tasksRes.data) ? tasksRes.data : []
        };
      } catch (e) {
        return { ...wf, tasks: [] };
      }
    })
  );

  return workflowsWithTasks;
};

export async function fetchSystemHealth() {
  const res = await AxiosInstance.get('system-health/');
  return res.data;
}

export async function fetchWorkflowsByStatus() {
  const res = await AxiosInstance.get('analytics/workflows_by_status/');
  return res.data;
}

export async function fetchVolunteersByStatus() {
  const res = await AxiosInstance.get('analytics/volunteers_by_status/');
  return res.data;
}

// Nouvelles fonctions pour les analytics supplémentaires
export async function fetchTaskPerformance() {
  const res = await AxiosInstance.get('analytics/task_performance/');
  return res.data;
}

export async function fetchResourceUtilization() {
  const res = await AxiosInstance.get('analytics/resource_utilization/');
  return res.data;
}

export async function fetchCommunicationStats() {
  const res = await AxiosInstance.get('analytics/communication_stats/');
  return res.data;
}
