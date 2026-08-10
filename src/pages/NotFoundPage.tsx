import { ArrowLeft, Compass } from 'lucide-react';
import { Link } from 'react-router-dom';

export default function NotFoundPage() {
  return <div className="page-width page-top empty-state not-found"><Compass /><span className="eyebrow">404</span><h1>Wrong side of the map</h1><p>The page you requested is not in this build.</p><Link to="/" className="button"><ArrowLeft /> Return home</Link></div>;
}
