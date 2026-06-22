import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Settings } from 'lucide-react';

function Sidebar() {
  return (
    <aside className="sidebar">
      <div className="header__brand" style={{ marginBottom: '2rem' }}>
        <div className="header__logo">H</div>
        <div>
          <h1 className="header__title" style={{ fontSize: '20px' }}>HirenixAI</h1>
          <p className="header__subtitle">Candidate Ranking</p>
        </div>
      </div>
      
      <nav className="sidebar-nav">
        <NavLink to="/" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <LayoutDashboard size={20} />
          Overview
        </NavLink>
        <NavLink to="/candidates" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <Users size={20} />
          Talent Pool
        </NavLink>
        <NavLink to="/settings" className={({isActive}) => isActive ? "nav-item active" : "nav-item"}>
          <Settings size={20} />
          Configuration
        </NavLink>
      </nav>
    </aside>
  );
}

export default Sidebar;
