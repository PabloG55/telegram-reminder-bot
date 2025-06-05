import { useEffect, useState } from 'react';
import { auth } from "./firebase";
import axios from 'axios';
import { Link } from 'react-router-dom';

const BASE_URL = process.env.REACT_APP_API_URL || "http://localhost:5000";

function Dashboard() {
  const [tasks, setTasks] = useState([]);
  const [description, setDescription] = useState('');
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedTime, setSelectedTime] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [uid, setUid] = useState(null);  // <-- Track UID

  useEffect(() => {
    const unsubscribe = auth.onAuthStateChanged((user) => {
      if (user) {
        setUid(user.uid);
      } else {
        console.warn("❌ No user signed in.");
      }
    });

    return () => unsubscribe();
  }, []);

  useEffect(() => {
    if (uid) {
      fetchTasks(uid);
    }
  }, [uid]);

  const fetchTasks = async (userId) => {
    setIsLoading(true);
    try {
      const res = await axios.get(`${BASE_URL}/api/tasks?user_id=${userId}`);
      setTasks(res.data);
    } catch (error) {
      console.error("Failed to fetch tasks:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleAdd = async () => {
    if (!description.trim() || !uid) return;

    const finalDate = selectedDate || getDefaultEndTime();
    const finalTime = selectedTime || '23:59';
    const fullDatetime = `${finalDate}T${finalTime}`;

    try {
      await axios.post(`${BASE_URL}/api/tasks/create`, {
        user_id: uid,
        description,
        scheduled_time: fullDatetime
      });
      setDescription('');
      setSelectedDate('');
      setSelectedTime('');
      fetchTasks(uid);
    } catch (error) {
      console.error("Failed to add task:", error);
    }
  };

  const handleComplete = async (id) => {
    try {
      await axios.post(`${BASE_URL}/api/tasks/${id}/complete`, {
        user_id: uid
      });
      const audio = new Audio('/done.mp3');
      fetchTasks(uid);
      audio.play();
    } catch (error) {
      console.error("Failed to complete task:", error);
    }
  };

  const handleReschedule = async (id) => {
    try {
      await axios.post(`${BASE_URL}/api/tasks/${id}/reschedule`, {
        user_id: uid
      });
      const audio = new Audio('/reschedule.mp3');
      fetchTasks(uid);
      audio.play();
    } catch (error) {
      console.error("Failed to reschedule task:", error);
    }
  };

  const handleDelete = async (id) => {
    try {
      await axios.delete(`${BASE_URL}/api/tasks/${id}`, {
        params: { user_id: uid }
      });
      fetchTasks(uid);
    } catch (error) {
      console.error("Failed to delete task:", error);
    }
  };

  const getDefaultEndTime = () => {
    const now = new Date();
    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-500';
      case 'done':
        return 'bg-green-500';
      case 'overdue':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter') {
      event.preventDefault();
      handleAdd();
    }
  };

  const groupTasksByDate = (tasks) => {
    const today = new Date();
    today.setHours(0, 0, 0, 0);

    const currentWeek = getWeek(today);
    const currentYear = today.getFullYear();

    const groups = {
      'My Day': [],
      'This Week': [],
      'Next Week': [],
      'Later': []
    };

    for (const task of tasks) {
      const taskDate = new Date(task.scheduled_time);
      taskDate.setHours(0, 0, 0, 0);

      const taskWeek = getWeek(taskDate);
      const taskYear = taskDate.getFullYear();

      if (taskDate.getTime() === today.getTime()) {
        groups['My Day'].push(task);
      } else if (taskYear === currentYear && taskWeek === currentWeek) {
        groups['This Week'].push(task);
      } else if (taskYear === currentYear && taskWeek === currentWeek + 1) {
        groups['Next Week'].push(task);
      } else {
        groups['Later'].push(task);
      }
    }

    return groups;
  };


  const getWeek = (date) => {
    const firstDayOfYear = new Date(date.getFullYear(), 0, 1);
    const pastDays = Math.floor((date - firstDayOfYear) / (24 * 60 * 60 * 1000));
    return Math.ceil((pastDays + firstDayOfYear.getDay() + 1) / 7);
  };

  return (

      <div className="container max-w-4xl mx-auto py-8 px-4 relative">
        {/* Logout Button */}
        <button
            onClick={() => {
              auth.signOut().then(() => {
                localStorage.removeItem("tg_id");
                window.location.href = "/login";
              });
            }}
            className="absolute top-4 right-4 px-3 py-1 bg-gray-200 hover:bg-gray-300 rounded text-sm"
        >
          Logout
        </button>

        <div className="flex items-center justify-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">Botifier</h1>
        </div>


        <div className="bg-white rounded-lg shadow-md mb-8 overflow-hidden">
          <div className="p-5 border-b border-gray-200">
            <h2 className="text-xl font-semibold text-gray-700">Add New Task</h2>
          </div>
          <div className="p-5">
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4">
              <div className="md:col-span-6">
                <input
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="What do you need to do?"
                    value={description}
                    onChange={e => setDescription(e.target.value)}
                    onKeyDown={handleKeyDown}
                />
              </div>
              <div className="md:col-span-3">
                <input
                    type="date"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={selectedDate}
                    onChange={e => setSelectedDate(e.target.value)}
                    onKeyDown={handleKeyDown}
                />
              </div>
              <div className="md:col-span-3">
                <input
                    type="time"
                    className="w-full px-4 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    value={selectedTime}
                    onChange={e => setSelectedTime(e.target.value)}
                    onKeyDown={handleKeyDown}
                />
              </div>
              <div className="md:col-span-2">
                <button
                    className="w-full px-4 py-2 bg-blue-600 text-white font-medium rounded-md hover:bg-blue-700 transition-colors duration-150 flex items-center justify-center"
                    onClick={handleAdd}
                >
                  <span className="mr-1">Add</span>
                  <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Tasks List */}
        {isLoading ? (
            <div className="text-center py-10">
              <div className="inline-block animate-spin rounded-full h-8 w-8 border-4 border-gray-300 border-t-blue-600"></div>
              <p className="mt-2 text-gray-600">Loading tasks...</p>
            </div>
        ) : tasks.length === 0 ? (
            <div className="text-center py-10 bg-white rounded-lg shadow-md">
              <svg xmlns="http://www.w3.org/2000/svg" className="h-16 w-16 mx-auto text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <p className="mt-4 text-gray-600 text-lg">No tasks yet. Add your first task above!</p>
            </div>
        ) : (
            <div className="space-y-8">
              {Object.entries(groupTasksByDate(tasks)).map(([group, groupTasks]) => (
                groupTasks.length > 0 && (
                  <div key={group} className="space-y-4">
                    <h2 className="text-xl font-semibold text-gray-700 mb-4">{group}</h2>
                    {groupTasks.map(task => (
                      <div key={task.id} className="bg-white rounded-lg shadow-md overflow-hidden hover:shadow-lg transition-shadow duration-200">
                        <div className="p-5 flex flex-col md:flex-row justify-between items-start md:items-center">
                          <div className="flex-grow mb-4 md:mb-0">
                            <div className="flex items-center mb-1">
                              <h3 className="font-medium text-lg text-gray-800 mr-3">{task.description}</h3>
                              <span className={`px-2 py-1 rounded-full text-xs font-medium text-white ${getStatusColor(task.status)}`}>
                                {task.status}
                              </span>
                            </div>
                            <p className="text-gray-500 flex items-center">
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4 mr-1" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                              </svg>
                              {new Date(task.scheduled_time).toLocaleString()}
                            </p>
                          </div>
                          <div className="flex space-x-2">
                            {task.status !== 'done' && (
                              <button
                                className="p-2 bg-green-100 text-green-600 rounded-md hover:bg-green-200 transition-colors"
                                onClick={() => handleComplete(task.id)}
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                </svg>
                              </button>
                            )}
                            {task.status === 'done' && (
                              <button
                                className="p-2 bg-yellow-100 text-yellow-700 rounded-md hover:bg-yellow-200 transition-colors"
                                onClick={() => handleReschedule(task.id)}
                                title="Reschedule Task"
                              >
                                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                                </svg>
                              </button>
                            )}
                            <Link
                              to={`/edit/${task.id}`}
                              className="p-2 bg-blue-100 text-blue-600 rounded-md hover:bg-blue-200 transition-colors"
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                              </svg>
                            </Link>
                            <button
                              className="p-2 bg-red-100 text-red-600 rounded-md hover:bg-red-200 transition-colors"
                              onClick={() => handleDelete(task.id)}
                            >
                              <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                              </svg>
                            </button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )
              ))}
            </div>
)}

        {/* Calendar Link */}
        <div className="text-center mt-8">
          <Link
              to="/calendar"
              className="inline-flex items-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            View Calendar
          </Link>
        </div>
      </div>
  );
}

export default Dashboard;