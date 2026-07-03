import AxiosInstance from './axios';

const asList = (data) => (Array.isArray(data) ? data : []);

const toChart = (data) => {
  if (Array.isArray(data)) {
    return data
      .filter((item) => item && item.name != null)
      .map((item) => ({ name: String(item.name), value: Number(item.value) || 0 }));
  }
  if (data && typeof data === 'object') {
    return Object.entries(data).map(([name, value]) => ({
      name,
      value: Number(value) || 0,
    }));
  }
  return [];
};

export const fetchManagers = async () => {
  const res = await AxiosInstance.get('managers/');
  return asList(res.data);
};

export const fetchVolunteers = async () => {
  const res = await AxiosInstance.get('volunteers/');
  return asList(res.data);
};

export const fetchWorkflows = async (params = {}) => {
  const res = await AxiosInstance.get('workflows/', { params });
  return asList(res.data);
};

export const fetchTasks = async (params = {}) => {
  const res = await AxiosInstance.get('tasks/', { params });
  return asList(res.data);
};

export const fetchManagersCount = async () => (await fetchManagers()).length;
export const fetchVolunteersCount = async () => (await fetchVolunteers()).length;
export const fetchWorkflowsCount = async () => (await fetchWorkflows()).length;
export const fetchTasksCount = async () => (await fetchTasks()).length;

export const fetchActiveVolunteers = async () => {
  const list = await fetchVolunteers();
  return list
    .filter((v) => ['available', 'busy'].includes(v.current_status || v.status))
    .slice(0, 8);
};

export const fetchWorkflowsWithTasks = async () => {
  const workflows = await fetchWorkflows();
  return Promise.all(
    workflows.map(async (wf) => {
      try {
        const tasks = await fetchTasks({ workflow: wf.id });
        return { ...wf, tasks };
      } catch {
        return { ...wf, tasks: [] };
      }
    }),
  );
};

export const fetchSystemHealth = async () => {
  const res = await AxiosInstance.get('system-health/');
  return res.data || {};
};

export const fetchWorkflowsByStatus = async () => {
  try {
    const res = await AxiosInstance.get('analytics/workflows_by_status/');
    return toChart(res.data);
  } catch {
    const workflows = await fetchWorkflows();
    const counts = workflows.reduce((acc, wf) => {
      const status = wf.status || 'UNKNOWN';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});
    return toChart(counts);
  }
};

export const fetchVolunteersByStatus = async () => {
  try {
    const res = await AxiosInstance.get('analytics/volunteers_by_status/');
    return toChart(res.data);
  } catch {
    const volunteers = await fetchVolunteers();
    const counts = volunteers.reduce((acc, v) => {
      const status = v.current_status || v.status || 'UNKNOWN';
      acc[status] = (acc[status] || 0) + 1;
      return acc;
    }, {});
    return toChart(counts);
  }
};

export const fetchTaskPerformance = async () => {
  try {
    const res = await AxiosInstance.get('analytics/task_performance/');
    return asList(res.data);
  } catch {
    return [];
  }
};

export const fetchResourceUtilization = async () => {
  try {
    const res = await AxiosInstance.get('analytics/resource_utilization/');
    return asList(res.data);
  } catch {
    return [];
  }
};

export const fetchCommunicationStats = async () => {
  try {
    const res = await AxiosInstance.get('stats/');
    return res.data || {};
  } catch {
    return {};
  }
};
