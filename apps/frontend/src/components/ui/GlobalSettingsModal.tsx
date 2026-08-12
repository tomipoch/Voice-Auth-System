import { useSettingsModal } from '../../hooks/useSettingsModal';
import SettingsModal from './SettingsModal';

const GlobalSettingsModal = () => {
  const { isOpen, closeModal } = useSettingsModal();

  return <SettingsModal isOpen={isOpen} onClose={closeModal} />;
};

export default GlobalSettingsModal;
