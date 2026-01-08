import { useState } from 'react';
import './RightSidebar.css';

function RightSidebar() {
  const [currentDate] = useState(new Date());

  // Generate calendar days for the current month
  const generateCalendar = () => {
    const year = currentDate.getFullYear();
    const month = currentDate.getMonth();
    const firstDay = new Date(year, month, 1).getDay();
    const daysInMonth = new Date(year, month + 1, 0).getDate();

    const days = [];

    // Add empty cells for days before month starts
    for (let i = 0; i < firstDay; i++) {
      days.push({ date: null, completed: false });
    }

    // Add actual days
    for (let i = 1; i <= daysInMonth; i++) {
      days.push({
        date: i,
        completed: i === 6, // Mock: Day 6 is completed
        today: i === currentDate.getDate()
      });
    }

    return days;
  };

  const calendar = generateCalendar();
  const monthName = currentDate.toLocaleString('default', { month: 'long' });

  const popularConcepts = [
    { name: 'Transformations', count: 1370, color: 'primary' },
    { name: 'Actions', count: 2184, color: 'secondary' },
    { name: 'Joins', count: 486, color: 'primary' },
    { name: 'Aggregations', count: 1150, color: 'secondary' },
    { name: 'Window Functions', count: 1312, color: 'primary' },
    { name: 'DataFrames', count: 398, color: 'secondary' },
    { name: 'RDD Operations', count: 1325, color: 'primary' },
    { name: 'Partitioning', count: 179, color: 'secondary' },
    { name: 'Caching', count: 147, color: 'primary' },
    { name: 'Broadcast', count: 278, color: 'secondary' },
    { name: 'UDFs', count: 404, color: 'primary' },
    { name: 'SQL Queries', count: 344, color: 'secondary' },
  ];

  return (
    <aside className="right-sidebar">
      <div className="right-sidebar-content">
        {/* Progress Calendar */}
        <div className="calendar-widget">
          <div className="calendar-header">
            <div className="calendar-title">
              <span className="calendar-label">Day</span>
              <span className="calendar-day">{currentDate.getDate()}</span>
            </div>
            <div className="calendar-nav">
              <button className="calendar-nav-btn">‹</button>
              <button className="calendar-nav-btn">›</button>
            </div>
          </div>

          <div className="calendar-month">{monthName}</div>

          <div className="calendar-grid">
            <div className="calendar-weekdays">
              {['S', 'M', 'T', 'W', 'T', 'F', 'S'].map((day, i) => (
                <div key={i} className="calendar-weekday">{day}</div>
              ))}
            </div>
            <div className="calendar-days">
              {calendar.map((day, i) => (
                <div
                  key={i}
                  className={`calendar-day ${day.completed ? 'completed' : ''} ${day.today ? 'today' : ''} ${!day.date ? 'empty' : ''}`}
                >
                  {day.date || ''}
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Streak Tracking */}
        <div className="streak-widget">
          <div className="streak-header">
            <span className="streak-icon">🔥</span>
            <span className="streak-label">Weekly Premium</span>
            <span className="streak-badge">1 day left</span>
          </div>
          <div className="streak-days">
            {['U1', 'U2', 'U3', 'U4', 'U5'].map((day, i) => (
              <div key={i} className={`streak-day ${i === 0 ? 'active' : ''}`}>
                {day}
              </div>
            ))}
          </div>
          <div className="streak-redeem">
            <span className="streak-redeem-icon">💎</span>
            <span className="streak-redeem-text">0 Redeem</span>
            <button className="streak-redeem-btn">Rules</button>
          </div>
        </div>

        {/* Popular Spark Concepts */}
        <div className="concepts-widget">
          <div className="concepts-header">
            <span className="concepts-title">Trending Concepts</span>
            <div className="concepts-nav">
              <button className="concepts-nav-btn">‹</button>
              <button className="concepts-nav-btn">›</button>
            </div>
          </div>

          <div className="concepts-search">
            <input
              type="text"
              placeholder="Search for a concept..."
              className="concepts-search-input"
            />
          </div>

          <div className="concepts-list">
            {popularConcepts.map((concept, i) => (
              <button key={i} className={`concept-tag concept-tag-${concept.color}`}>
                <span className="concept-name">{concept.name}</span>
                <span className="concept-count">{concept.count}</span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}

export default RightSidebar;
