import type { Metadata } from 'next';
import LandingPage from '@/components/landing/LandingPage';

export const metadata: Metadata = {
  title: 'Lume — Autonomous research agent for computer science',
  description:
    'Lume scopes your research question, reviews the literature, writes and runs your experiments in an isolated sandbox, and drafts the paper. Every citation points to a real passage; every number points to a real run.',
};

export default function Page() {
  return <LandingPage />;
}
