import { lazy, Suspense } from 'react';
import { Route, Routes } from 'react-router-dom';
import MainLayout from './layouts/MainLayout';
import LandingPage from './pages/LandingPage';

const DiscoverPage = lazy(() => import('./pages/DiscoverPage'));
const GameDetailPage = lazy(() => import('./pages/GameDetailPage'));
const GeneratorPage = lazy(() => import('./pages/GeneratorPage'));
const SpaceShooterPage = lazy(() => import('./pages/SpaceShooterPage'));
const NotFoundPage = lazy(() => import('./pages/NotFoundPage'));

function RouteFallback() {
  return <div className="page-width page-top route-loader" role="status"><span /><p>Loading experience...</p></div>;
}

export default function App() {
  return (
    <Routes>
      <Route element={<MainLayout />}>
        <Route index element={<LandingPage />} />
        <Route path="discover" element={<Suspense fallback={<RouteFallback />}><DiscoverPage /></Suspense>} />
        <Route path="games/:gameId" element={<Suspense fallback={<RouteFallback />}><GameDetailPage /></Suspense>} />
        <Route path="generator" element={<Suspense fallback={<RouteFallback />}><GeneratorPage /></Suspense>} />
        <Route path="play/space-shooter" element={<Suspense fallback={<RouteFallback />}><SpaceShooterPage /></Suspense>} />
        <Route path="*" element={<Suspense fallback={<RouteFallback />}><NotFoundPage /></Suspense>} />
      </Route>
    </Routes>
  );
}
