import { Gamepad2, Menu, Sparkles, X } from 'lucide-react';
import { useState } from 'react';
import { NavLink } from 'react-router-dom';

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const close = () => setOpen(false);
  return (
    <header className="navbar">
      <div className="nav-inner">
        <NavLink to="/" className="brand" onClick={close} aria-label="GameGenie AI home">
          <span className="brand-mark"><Gamepad2 size={21} /></span>
          <span>GameGenie <b>AI</b></span>
        </NavLink>
        <button className="icon-btn menu-button" onClick={() => setOpen((value) => !value)} aria-label="Toggle navigation" aria-expanded={open}>
          {open ? <X /> : <Menu />}
        </button>
        <nav className={open ? 'nav-links open' : 'nav-links'} aria-label="Main navigation">
          <NavLink to="/" onClick={close}>Home</NavLink>
          <NavLink to="/discover" onClick={close}>Discover</NavLink>
          <NavLink to="/generator" onClick={close}>Generator</NavLink>
          <NavLink to="/generator" className="nav-cta" onClick={close}><Sparkles size={16} /> Create game</NavLink>
        </nav>
      </div>
    </header>
  );
}
