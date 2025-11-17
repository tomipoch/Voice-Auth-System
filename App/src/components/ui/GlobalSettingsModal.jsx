import { useSettingsModal } from '../../hooks/useSettingsModal';
import SettingsModal from './SettingsModal';

const GlobalSettingsModal = () => {
  const { isSettingsModalOpen, closeSettingsModal } = useSettingsModal();

  return <SettingsModal isOpen={isSettingsModalOpen} onClose={closeSettingsModal} />;
};

export default GlobalSettingsModal;
