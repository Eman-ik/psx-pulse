import { Container } from '@mui/material';
import AskPanel from './components/AskPanel';

export const metadata = {
  title: 'Investment Research Ask Panel | Khronos',
  description: 'PSX Pulse LLM Integration - Research any ticker with AI-powered analysis',
};

export default function HomePage() {
  return (
    <Container maxWidth="lg" sx={{ py: 4 }}>
      <AskPanel />
    </Container>
  );
}
