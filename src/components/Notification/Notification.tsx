import { useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../../store';
import { removeNotification } from '../../store/dashboardSlice';
import './Notification.css';

export function Notification() {
  const dispatch = useAppDispatch();
  const notifications = useAppSelector(state => state.dashboard.notifications);

  useEffect(() => {
    notifications.forEach(notif => {
      const timer = setTimeout(() => {
        dispatch(removeNotification(notif.id));
      }, 4000);
      return () => clearTimeout(timer);
    });
  }, [notifications, dispatch]);

  if (notifications.length === 0) return null;

  return (
    <div className="notification-container">
      {notifications.map(notif => (
        <div key={notif.id} className={`notification notification-${notif.type}`}>
          <span className="notification-icon">
            {notif.type === 'success' && '\u2713'}
            {notif.type === 'error' && '\u2717'}
            {notif.type === 'warning' && '!'}
            {notif.type === 'info' && 'i'}
          </span>
          <span className="notification-message">{notif.message}</span>
          <button
            className="notification-close"
            onClick={() => dispatch(removeNotification(notif.id))}
          >
            x
          </button>
        </div>
      ))}
    </div>
  );
}
