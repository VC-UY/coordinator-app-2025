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
  const res = await AxiosInstance.get('logs/logs/?limit=5');
  return Array.isArray(res.data) ? res.data : [];
};

export const fetchAnnouncements = async () => {
  const res = await AxiosInstance.get('announcements/?limit=3');
  return Array.isArray(res.data) ? res.data : [];
};

export const fetchActiveVolunteers = async () => {
  const res = await AxiosInstance.get('volunteers/');
  const list = Array.isArray(res.data) ? res.data : [];
  return list.filter((v) => v.current_status === 'available' || v.status === 'available').slice(0, 5);
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

  const workflowsWithTasks = await Promise.all(
    workflows.map(async (wf) => {
      try {
        const tasksRes = await AxiosInstance.get(`tasks/?workflow=${wf.id}`);
        return { ...wf, tasks: Array.isArray(tasksRes.data) ? tasksRes.data : [] };
      } catch {
        return { ...wf, tasks: [] };
      }
    }),
  );
  return workflowsWithTasks;
};

export const fetchCommunicationStats = async () => {
  const res = await AxiosInstance.get('stats/');
  return res.data || {};
};
