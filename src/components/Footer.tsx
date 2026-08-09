import { Gamepad2 } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function Footer() {
  return (
    <footer className="footer">
      <div className="footer-inner">
        <Link to="/" className="brand"><span className="brand-mark"><Gamepad2 size={19} /></span>GameGenie AI</Link>
        <p>Find your next game. Shape the next one.</p>
        <span>© {new Date().getFullYear()} GameGenie AI</span>
      </div>
    </footer>
  );
}
