import React from 'react';

export interface ModalProps extends React.HTMLAttributes<HTMLDivElement> {
  open?: boolean;
  onClose?: () => void;
}

export const Modal: React.FC<ModalProps> = (props) => {
  return <div {...props} />;
};

export default Modal;
